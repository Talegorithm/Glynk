# Glynk

[English](README.md)

世界上有无数好书、好论文、好播客。但你永远找不完——内容太多了，搜索引擎只能找到页面，找不到洞见。

Glynk 把这些内容结构化，让你和你的 AI Agent 都能阅读、搜索、标注——用同样的工具。你的 Agent 帮你找到此刻最相关的那个段落。当你阅读和高亮时，下一个人的 Agent 也更容易找到它。

**[glynk.wiki](https://glynk.wiki)** — 试试看。书籍、论文、播客、文章——已经结构化、可检索。带上你的 Agent。

## 怎么用

你和你的 Agent 用同样的三种方式找内容——只是看到的视图不同：

**按结构浏览。** 每份内容有目录和 AI 生成的大纲。你的 Agent 扫描大纲来决定哪些值得深入。你在阅读器里浏览同一份大纲。

**按语义搜索。** 在所有人的高亮、标注、摘要中做语义搜索。你的 Agent 通过 API 搜索。你通过同一个界面搜索。

**顺序阅读。** 同一个接口，游标翻页。你的 Agent 读到的是省 tokens 的简化 HTML。你读到的是完整渲染的页面，支持翻译。同样的内容，同样的 span ID，不同的渲染。

**所有人的阅读帮到所有人。** 当你的 Agent 标记了一段相关内容，或者你高亮了一句话，这个信号是共享的。好内容自然浮现——不靠推荐算法，靠真实的阅读。

## 使用 glynk.wiki

```bash
# 获取 token
curl -X POST https://glynk.wiki/users

# 你的 Agent 搜索相关内容
curl -X POST https://glynk.wiki/query \
  -H "Authorization: Bearer <token>" \
  -d '{"text": "信息不足时如何做决策", "top_k": 5}'
# → 返回书籍和论文中的相关段落，附带阅读链接

# 打开链接——在浏览器中阅读、高亮、做笔记
# https://glynk.wiki/content/a1b2c3d4/browse?file_idx=0&loc=...
```

你的 Agent 也可以向共享图书馆贡献内容和标注。详见 [API 文档](https://glynk.wiki/docs)。

## 自部署：处理私有内容

Glynk 是开源的。你可以运行自己的实例，用于内部知识库、私有文档或研究资料。

自部署的核心价值：一套强大的流水线，把各种格式的文档（PDF、EPUB、网页、播客）变成干净的、句子级可寻址的 HTML——并提供两种输出模式：

```
GET /content/{id}/read?view=ai      → 简化 HTML，给 Agent（省 tokens）
GET /content/{id}/read?view=human   → 完整 HTML，给人（支持翻译）
```

```bash
git clone https://github.com/Talegorithm/glynk.git
cd glynk
pip install -r requirements.txt

cp .env.example .env
# 编辑 .env，填入 PostgreSQL 和 API 凭据

python -m glynk.storage.postgres --init
uvicorn glynk.main:app --host 0.0.0.0 --port 8000
```

```bash
# 导入任意文档
curl -X POST http://localhost:8000/ingest \
  -H "Authorization: Bearer <token>" \
  -d '{"source": "path/to/book.epub"}'

# 同一个接口，不同视图
curl "http://localhost:8000/content/{id}/read?view=ai&size=12000"    # Agent 用
curl "http://localhost:8000/content/{id}/read?view=human&lang=zh"    # 人用
```

### 前置条件

- Python 3.11+
- PostgreSQL + [pgvector](https://github.com/pgvector/pgvector)
- Azure OpenAI API key（用于检索 embedding）

## API 概览

| 端点 | 说明 |
|---|---|
| `POST /ingest` | 提交 URL 或文件。返回结构化内容供 Agent 使用。 |
| `GET /content/{id}/read` | 阅读内容。`?view=ai` 给 Agent，`?view=human` 给人。`?lang=zh` 翻译。 |
| `POST /query` | 在内容库中检索。 |
| `POST /annotate` | 添加标注（高亮、笔记、主题等）。 |
| `GET /annotations` | 你的阅读历史。 |
| `POST /sources` | 订阅 RSS，自动定时导入。 |

运行后访问 `/docs` 查看完整 API 文档。

## 架构

详见 [docs/architecture.md](docs/architecture.md)。

```
ingestion/     任意格式 → 带句子级 ID 的统一 HTML
content/       一个 read 接口，两种视图（ai/human）+ 翻译
annotation/    统一存储 + 语义检索（PostgreSQL + pgvector）
```

## 许可

AGPL v3
