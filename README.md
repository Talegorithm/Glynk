# Glynk

[中文](README.zh.md)

There are millions of great books, papers, and podcasts out there. You'll never find the best parts on your own — there's too much, and search engines only find pages, not insights.

Glynk structures all of that content so both you and your AI agent can read it, search it, and annotate it — using the same tools. Your agent finds the exact paragraph that matters to you right now. When you read and highlight, that helps the next person's agent find it too.

**[glynk.wiki](https://glynk.wiki)** — Try it. Books, papers, podcasts, articles — already structured and searchable. Bring your agent.

## How it works

You and your agent use the same three ways to find content — just through different views:

**Browse by structure.** Every piece of content has a table of contents and an AI-generated outline. Your agent scans the outline to decide what's worth reading. You browse the same outline in the reader.

**Search by meaning.** Semantic search across everything that's been highlighted, annotated, and summarized. Your agent searches programmatically. You search through the same interface.

**Read sequentially.** One endpoint, cursor-based. Your agent reads in token-efficient simplified HTML. You read in a full rendered view with translation support. Same content, same span IDs, different rendering.

**Everyone's reading helps everyone.** When your agent marks a passage as relevant, or you highlight a sentence, that signal is shared. The best content surfaces naturally — not through a recommendation algorithm, but through real reading.

## Use glynk.wiki

```bash
# Get a token
curl -X POST https://glynk.wiki/users

# Your agent searches for relevant content
curl -X POST https://glynk.wiki/query \
  -H "Authorization: Bearer <token>" \
  -d '{"text": "how to make decisions with incomplete information", "top_k": 5}'
# → annotated passages from books and papers, with links to read the original

# Open the link — read in the browser, highlight, take notes
# https://glynk.wiki/content/a1b2c3d4/browse?file_idx=0&loc=...
```

Your agent can also contribute content and annotations to the shared library. See [API docs](https://glynk.wiki/docs) for details.

## Self-host for private content

Glynk is open source. Run your own instance for internal knowledge bases, proprietary documents, or research collections.

The core value of self-hosting: a robust pipeline that turns messy documents (PDFs, EPUBs, web pages, podcasts) into clean, sentence-addressable HTML — readable by both humans and agents through the same API:

```
GET /content/{id}/read?view=ai      → simplified HTML for agents (token-efficient)
GET /content/{id}/read?view=human   → full HTML for readers (with translation)
```

```bash
git clone https://github.com/Talegorithm/glynk.git
cd glynk
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your PostgreSQL and API credentials

python -m glynk.storage.postgres --init
uvicorn glynk.main:app --host 0.0.0.0 --port 8000
```

```bash
# Ingest any document
curl -X POST http://localhost:8000/ingest \
  -H "Authorization: Bearer <token>" \
  -d '{"source": "path/to/book.epub"}'

# Same endpoint, different views
curl "http://localhost:8000/content/{id}/read?view=ai&size=12000"    # for agents
curl "http://localhost:8000/content/{id}/read?view=human&lang=zh"    # for humans
```

### Requirements

- Python 3.11+
- PostgreSQL with [pgvector](https://github.com/pgvector/pgvector)
- Azure OpenAI API key (for search embeddings)

## API overview

| Endpoint | Description |
|---|---|
| `POST /ingest` | Submit a URL or file. Returns structured content for your agent. |
| `GET /content/{id}/read` | Read content. `?view=ai` for agents, `?view=human` for readers. `?lang=zh` for translation. |
| `POST /query` | Search across the library. |
| `POST /annotate` | Add an annotation (highlight, note, topic, etc). |
| `GET /annotations` | Your reading history. |
| `POST /sources` | Subscribe to an RSS feed for automatic ingestion. |

Full docs at `/docs` when running.

## Architecture

See [docs/architecture.md](docs/architecture.md).

```
ingestion/     Any format → unified HTML with sentence-level IDs
content/       One read API, two views (ai/human) + translation
annotation/    Unified storage + semantic search (PostgreSQL + pgvector)
```

## License

MIT
