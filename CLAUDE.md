# Glynk

Agent时代内容平台。吃进长内容（书/论文/播客/文章），做结构化处理，开放给人和Agent来标注和检索。

## Tech Stack

- **Backend**: FastAPI + Python 3.11+
- **Database**: PostgreSQL + pgvector (向量搜索)
- **Embedding**: Azure OpenAI text-embedding-3-large (3072维)
- **Background**: APScheduler (RSS定时拉取)
- **Frontend**: React 19 + TypeScript, Vite + Tailwind CSS v4, Zustand, React Router 7
- **Agent**: cyber-agent 框架 (/Users/sunlit/Code/Agent)

## Project Structure

```
glynk/
├── main.py                 # FastAPI入口
├── config.py               # 配置
├── models.py               # 数据模型（TOCItem, Content, Annotation 等）
├── ingestion/              # 核心1：任意格式 → 统一HTML
│   ├── pipeline.py         # 摄入流水线（含 TOC href→span_id 映射）
│   ├── registry.py         # Handler选择
│   ├── handler/            # 内容类型handler
│   ├── format_utils/       # 格式工具（epub, pdf, html）
│   └── processing/         # HTML处理（从Resonote复制）
├── content/                # 核心2：双视图阅读
│   ├── reader.py           # 统一read接口（文件级/分页级）
│   ├── ai_view.py          # AI视图过滤
│   └── locator.py          # Span定位
├── annotation/             # 核心3：标注+检索
│   ├── service.py          # CRUD + embedding + delete/update
│   ├── search.py           # 语义检索引擎
│   └── vector_store.py     # pgvector搜索
├── storage/postgres.py     # PostgreSQL存储（9张表）
├── embedding/service.py    # Embedding生成
├── api/                    # REST API
│   ├── content_router.py   # 内容读取/详情/进度/会话
│   ├── annotation_router.py # 标注CRUD + 检索
│   └── ...
├── agent/                  # 官方标注Agent
│   ├── tools.py            # 4个工具（list/read/outline/annotations）
│   ├── annotator.prompt    # Agent提示词
│   └── run.py              # 运行入口
└── worker/rss_fetcher.py   # RSS拉取

glynk-web/src/
├── api/                    # HTTP客户端层
├── types/                  # TypeScript类型
├── store/
│   ├── auth.ts             # 认证状态
│   └── reader.ts           # 阅读器状态（文件加载/跳转/TOC）
├── config/colors.ts        # 高亮颜色系统
├── utils/reader/           # 选区/高亮/TOC工具
├── components/reader/      # 阅读器组件（从Brainow迁移）
│   ├── ReaderLayout.tsx    # 响应式布局（侧栏+内容+移动端抽屉）
│   ├── ReaderContent.tsx   # 核心：文件渲染/滚动加载/选区/高亮回显
│   ├── ReaderToolbar.tsx   # 顶部工具栏
│   ├── ReaderTOC.tsx       # 目录侧栏
│   ├── ReaderOutline.tsx   # AI大纲侧栏
│   ├── SelectionToolbar.tsx # 文本选中工具栏
│   ├── AnnotationDialog.tsx # 笔记对话框
│   ├── HighlightMenu.tsx   # 高亮点击菜单
│   └── CitationPreview.tsx # 引注预览
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
- 统一标注模型：highlight/hook/note/reaction
- span_id格式：`{content_id}-{file_idx}-p{n}-s{m}`
- 内容寻址去重：`content_id = sha256(file)[:16]`

### Annotation Anchor 格式

标注的 `anchor` 是 JSONB，格式由创建者决定：

```jsonc
// 用户在阅读器中手动高亮（精确选区）
{ "type": "text_selection", "spans": [...], "startSpanId": "...", "endSpanId": "...", "startOffset": 5, "endOffset": 10, "color": "yellow" }

// Agent 创建的标注（span级别）
{ "type": "text", "spans": [...], "color": "ghost" }
```

颜色在创建时决定，渲染时读取 `anchor.color`。没有 `color` 的标注不显示高亮。

### 阅读器（从 Brainow 迁移）

阅读器核心组件从 `/Users/sunlit/Code/Brainow` 迁移，主要适配：
- Brainow 按 `fileIdx` 整文件加载 → Glynk 也是整文件加载（`GET /content/{id}/read` 不传 `size`）
- Brainow 的 `anchor_location`/`selection` → Glynk 统一用 `anchor` JSONB
- Brainow 的 RecapCard (SSE) 未迁移（无后端支持）
- 保留：连续滚动、高亮颜色、TOC/Outline、脚注预览、KaTeX、翻译、会话追踪、阅读进度

### 图片路径

HTML 中图片 src 为 `/media/{content_id}/{filename}`，后端 `/media/{content_id}/{filename}` 路由提供静态文件。
Vite dev proxy 需要配置 `/media` 转发。

### 数据库

9张表：contents, annotations, queries, feedback, rss_sources, users, translations, reading_progress, reading_sessions。
pgvector IVFFlat 索引（3072维，HNSW 限制 2000 维）。
