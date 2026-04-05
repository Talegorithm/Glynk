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
from fastapi.responses import FileResponse, JSONResponse

from glynk.config import AppConfig
from glynk.storage.postgres import PostgresStore
from glynk.content.reader import ReaderService
from glynk.annotation.service import AnnotationService
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

    # 确保数据目录存在
    config.storage.html_root.mkdir(parents=True, exist_ok=True)
    config.storage.uploads_root.mkdir(parents=True, exist_ok=True)

    # 初始化数据库
    db = PostgresStore(config.storage)
    PostgresStore._instance = db

    # 初始化服务
    vector_store = PgVectorStore(db)
    annotation_service = AnnotationService(db, vector_store, config.embedding)
    retrieval_engine = RetrievalEngine(db, vector_store, config.embedding)
    reader_service = ReaderService(html_root=config.storage.html_root, db=db)
    pipeline = IngestionPipeline(config, db)

    # 注入服务到路由
    from glynk.api.ingest_router import set_pipeline
    from glynk.api.content_router import set_reader
    from glynk.api.annotation_router import set_services

    set_pipeline(pipeline)
    set_reader(reader_service)
    set_services(annotation_service, retrieval_engine)

    # RSS 定时拉取
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
    description="Agent时代内容平台 - 多元标注让好内容被发现",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from glynk.api.user_router import router as user_router
from glynk.api.ingest_router import router as ingest_router
from glynk.api.content_router import router as content_router
from glynk.api.annotation_router import router as annotation_router
from glynk.api.source_router import router as source_router
from glynk.api.feedback_router import router as feedback_router

app.include_router(user_router)
app.include_router(ingest_router)
app.include_router(content_router)
app.include_router(annotation_router)
app.include_router(source_router)
app.include_router(feedback_router)


# ===== 静态文件：媒体（图片）=====

@app.get("/api/media/{content_id}/{filename}")
async def get_media(content_id: str, filename: str):
    """提供内容图片"""
    config = AppConfig.from_env()
    file_path = config.storage.html_root / content_id / filename
    if not file_path.exists():
        return JSONResponse(status_code=404, content={"error": "File not found"})
    return FileResponse(file_path)


# ===== Health =====

@app.get("/health")
async def health():
    return {"status": "ok", "service": "glynk"}


@app.get("/")
async def root():
    return {
        "service": "Glynk",
        "description": "Agent时代内容平台",
        "docs": "/docs",
    }
