# Glynk

Agent时代内容平台。吃进长内容（书/论文/播客/文章），做结构化处理，开放给人和Agent来标注和检索。

## Tech Stack

- **Backend**: FastAPI + Python 3.11+
- **Database**: PostgreSQL + pgvector (向量搜索)
- **Embedding**: Azure OpenAI text-embedding-3-large (3072维)
- **Background**: APScheduler (RSS定时拉取)

## Project Structure

```
glynk/
├── main.py                 # FastAPI入口
├── config.py               # 配置
├── models.py               # 数据模型
├── ingestion/              # 核心1：任意格式 → 统一HTML
│   ├── pipeline.py         # 摄入流水线
│   ├── registry.py         # Handler选择
│   ├── handler/            # 内容类型handler
│   ├── format_utils/       # 格式工具
│   └── processing/         # HTML处理（从Resonote复制）
├── content/                # 核心2：双视图阅读
│   ├── reader.py           # 统一read接口
│   ├── ai_view.py          # AI视图过滤
│   └── locator.py          # Span定位
├── annotation/             # 核心3：标注+检索
│   ├── service.py          # CRUD + embedding
│   ├── search.py           # 语义检索引擎
│   └── vector_store.py     # pgvector搜索
├── storage/postgres.py     # PostgreSQL存储
├── embedding/service.py    # Embedding生成
├── api/                    # REST API
└── worker/rss_fetcher.py   # RSS拉取
```

## Running

```bash
pip install -r requirements.txt
uvicorn glynk.main:app --reload --port 5000
```

## Key Design

- 平台不跑LLM，只做结构化处理和embedding检索
- 统一标注模型：highlight/hook/note/reaction
- span_id格式：`{content_id}-{file_idx}-p{n}-s{m}`
- 内容寻址去重：`content_id = sha256(file)[:16]`
