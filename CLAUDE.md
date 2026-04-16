# Glynk

Agent时代内容平台。吃进长内容（书/论文/播客/文章），做结构化处理，开放给人和Agent来标注和检索。

## Tech Stack

- **Backend**: FastAPI + Python 3.11+
- **Database**: PostgreSQL + pgvector (向量搜索)
- **Embedding**: Azure OpenAI text-embedding-3-large (3072维)
- **Background**: APScheduler (RSS定时拉取)
- **Frontend**: React 19 + TypeScript, Vite + Tailwind CSS v4, Zustand, React Router 7
- **Agent**: cyber-agent 框架 (/Users/sunlit/Code/Agent)

## Data Model (v2)

核心 3 张表：

- **entities** — 参与者（人 / AI），状态 active / dormant / claimed
- **units** — 信息单元（ingested 内容 或 authored 想法），body JSONB + vector 3072维
- **anchors** — 连接关系（标注、回复、like 等），source → target

Sidecar 表：auth, reading_progress, reading_sessions, event_log, rss_sources

详见 `docs/glynk-data-model.md`

## Project Structure

```
glynk/
├── main.py                 # FastAPI入口
├── config.py               # 配置
├── models.py               # Entity / Unit / Anchor dataclass
├── ingestion/              # 核心1：任意格式 → Unit(origin=ingested)
│   ├── pipeline.py         # 摄入流水线（含 author Entity 创建）
│   ├── registry.py         # Handler选择
│   ├── handler/            # 内容类型handler
│   ├── format_utils/       # 格式工具（epub, pdf, html）
│   └── processing/         # HTML处理
├── content/                # 核心2：双视图阅读
│   ├── reader.py           # 统一read接口（文件级/分页级）
│   ├── ai_view.py          # AI视图过滤
│   └── locator.py          # Span定位
├── annotation/             # 核心3：Anchor + 检索
│   ├── service.py          # AnchorService: CRUD + embedding
│   ├── search.py           # 语义检索引擎
│   └── vector_store.py     # pgvector on units table
├── storage/postgres.py     # PostgreSQL存储
├── embedding/service.py    # Embedding生成
├── api/                    # REST API
│   ├── auth.py             # Token验证中间件
│   ├── user_router.py      # POST /auth/register, GET /auth/me
│   ├── content_router.py   # /units/* (读取/详情/进度/会话/搜索)
│   ├── annotation_router.py # /anchors/* (CRUD + 检索)
│   ├── ingest_router.py    # /ingest
│   └── ...
├── agent/                  # 官方Agent工具
│   └── tools.py            # list_units/read_unit/create_anchors/search_units/save_unit
└── worker/rss_fetcher.py   # RSS拉取

glynk-web/src/
├── api/                    # HTTP客户端层
├── types/                  # TypeScript类型
├── store/
│   ├── auth.ts             # 认证状态
│   └── reader.ts           # 阅读器状态
├── components/reader/      # 阅读器组件
└── pages/                  # 页面
```

## Running

```bash
# 后端
pip install -r requirements.txt
uvicorn glynk.main:app --reload --port 8000

# 前端
cd glynk-web && npm install && npm run dev
```

## Key Design

- 平台不跑LLM，只做结构化处理和embedding检索
- 每个 Unit 归属真正作者（dormant Entity），导入者记在 metadata.imported_by
- 标注 = Unit(authored) + Anchor(连接到目标内容)
- span_id格式：`{unit_id}-{file_idx}-p{n}-s{m}`
- 内容寻址去重：`unit_id = sha256(file)[:16]`

### Anchor metadata 格式

Anchor 的 `metadata` 是 JSONB，格式由创建者决定：

```jsonc
// 用户高亮（精确选区）
{ "type": "text_selection", "spans": [...], "startSpanId": "...", "endSpanId": "...", "startOffset": 5, "endOffset": 10, "color": "yellow" }

// Agent 标注（span级别）
{ "type": "text", "spans": [...], "color": "ghost" }
```

### API 路径

```
POST /api/auth/register          → Entity + auth
GET  /api/auth/me
GET  /api/units                  → 列出
GET  /api/units/{id}             → 详情
GET  /api/units/{id}/read        → 阅读
PUT  /api/units/{id}/outline     → AI大纲
POST /api/units/search           → 语义检索
POST /api/anchors                → 创建标注
POST /api/anchors/batch          → 批量
GET  /api/anchors                → 查询
POST /api/ingest                 → 摄入
```

### 图片路径

HTML 中图片 src 为 `/media/{unit_id}/{filename}`，后端提供静态文件。

### 数据库

核心 3 表 + sidecar 表。pgvector 3072维。
