"""
Glynk - Agent时代内容平台

FastAPI 入口，路由注册，生命周期管理。
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

from glynk.config import AppConfig
from glynk.storage.postgres import PostgresStore
from glynk.content.reader import ReaderService
from glynk.annotation.service import AnchorService
from glynk.annotation.search import RetrievalEngine
from glynk.annotation.vector_store import PgVectorStore
from glynk.ingestion.pipeline import IngestionPipeline
from glynk.worker.rss_fetcher import RSSFetcher

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # ===== Startup =====
    config = AppConfig.from_env()

    config.storage.html_root.mkdir(parents=True, exist_ok=True)
    config.storage.uploads_root.mkdir(parents=True, exist_ok=True)

    db = PostgresStore(config.storage)
    PostgresStore._instance = db

    file_store = config.create_file_store()

    vector_store = PgVectorStore(db)
    anchor_service = AnchorService(db, vector_store, config.embedding)
    retrieval_engine = RetrievalEngine(db, vector_store, config.embedding)
    reader_service = ReaderService(file_store=file_store, db=db)
    pipeline = IngestionPipeline(config, db, file_store)

    # Inject services
    from glynk.api.ingest_router import set_pipeline
    from glynk.api.content_router import set_reader, set_retrieval_engine
    from glynk.api.annotation_router import set_services

    set_pipeline(pipeline)
    set_reader(reader_service)
    set_retrieval_engine(retrieval_engine)
    set_services(anchor_service, retrieval_engine)

    # RSS scheduler
    rss_fetcher = RSSFetcher(db, pipeline)

    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            rss_fetcher.fetch_all,
            'interval',
            hours=config.rss_check_interval_hours,
        )
        scheduler.start()
        logger.info(f"RSS scheduler started (interval: {config.rss_check_interval_hours}h)")
    except ImportError:
        logger.warning("APScheduler not installed, RSS fetching disabled")

    logger.info("Glynk started successfully")

    yield

    # ===== Shutdown =====
    try:
        scheduler.shutdown()
    except Exception:
        pass
    logger.info("Glynk shutdown")


# ===== App =====

app = FastAPI(
    title="Glynk",
    description="Agent时代内容平台",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from glynk.api.user_router import router as auth_router
from glynk.api.ingest_router import router as ingest_router
from glynk.api.content_router import router as unit_router
from glynk.api.annotation_router import router as anchor_router
from glynk.api.source_router import router as source_router
from glynk.api.feedback_router import router as feedback_router
from glynk.api.internal_router import router as internal_router

app.include_router(auth_router, prefix="/api")
app.include_router(ingest_router, prefix="/api")
app.include_router(unit_router, prefix="/api")
app.include_router(anchor_router, prefix="/api")
app.include_router(source_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")
app.include_router(internal_router, prefix="/api")


# ===== Media =====

@app.get("/media/{content_id}/{filename}")
async def get_media(content_id: str, filename: str):
    config = AppConfig.from_env()
    file_path = config.storage.html_root / content_id / filename
    if file_path.exists():
        return FileResponse(file_path)
    # 本地没有 —— 如果配了 REMOTE_FILE_BASE，重定向到远程
    # （对应 RemoteFileStore：写走 /api/internal/files/，读走 /media/）
    if config.remote_file_base:
        remote_url = f"{config.remote_file_base.rstrip('/')}/media/{content_id}/{filename}"
        return RedirectResponse(url=remote_url, status_code=307)
    return JSONResponse(status_code=404, content={"error": "File not found"})


@app.get("/health")
async def health():
    return {"status": "ok", "service": "glynk"}


@app.get("/")
async def root():
    return {
        "service": "Glynk",
        "description": "Agent时代内容平台",
        "version": "0.2.0",
        "docs": "/docs",
    }
