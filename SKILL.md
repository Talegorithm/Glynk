---
name: glynk
description: Semantic search across user's content on the Glynk platform, or use the platform to parse and chunk-read long-form content (books, papers, podcasts, articles). Use when the user needs to discover, read, or have you read long content on their behalf.
---

# Glynk Content Platform

Glynk ingests long-form content (books, papers, podcasts, articles), performs structured processing, and exposes it for annotation and semantic search by humans and agents.

## Prerequisites

First check if environment variables are already set:

```bash
echo "GLYNK_TOKEN=${GLYNK_TOKEN:-(not set)}" && echo "GLYNK_API_URL=${GLYNK_API_URL:-(not set)}"
```

If set, skip to the next section. Otherwise, register:

```bash
# 1. Try to find user's email (git config or environment)
git config user.email  # or echo $EMAIL

# 2. Ask user for uid and email (leave email null if no reliable source found)
# 3. Register
curl -X POST $GLYNK_API_URL/api/users \
  -H "Content-Type: application/json" \
  -d '{"uid":"user-specified-uid","email":"user-email-or-null"}'
# → {"uid":"...","token":"glk_..."}

# 4. Set environment variables
export GLYNK_TOKEN="glk_..."
export GLYNK_API_URL="http://127.0.0.1:5000"  # or production URL
```

Note: both uid and email are optional. uid is auto-generated if omitted. **Never fabricate an email — leave it null if not found.**

All endpoints below require `Authorization: Bearer $GLYNK_TOKEN` unless noted.

## Core Workflow

1. **Search**: `POST /api/query` — discover content via semantic search across annotations
2. **Read**: `GET /api/content/{id}/chunk?size=20000` — read content page by page (AI-optimized HTML)
3. **Annotate**: `POST /api/annotate` or `/api/annotate/batch` — create hooks/highlights/notes
4. **Outline**: `PUT /api/content/{id}/outline` — submit structured outline (after reading all content)

## Key Concepts

### Span IDs

Every sentence in content has a unique span ID: `{content_id}-{file_idx}-p{paragraph}-s{sentence}`

Example: `a1b2c3d4-0-p15-s3` = content a1b2c3d4, file 0, paragraph 15, sentence 3.

Span IDs are embedded in HTML as `<span id="...">` and used as anchors for all annotations.

### Annotation Types

| Type | Purpose |
|------|---------|
| `hook` | Reverse-engineered question — what curiosity does this content answer? |
| `highlight` | Text selection with color |
| `note` | Free-form note attached to spans |
| `reaction` | Quick reaction (emoji, etc.) |

### Anchor Format

```json
{
  "type": "text",
  "spans": ["a1b2-0-p1-s1", "a1b2-0-p1-s2"],
  "color": "yellow"
}
```

Colors: `yellow`, `green`, `blue`, `pink`, `ghost` (invisible highlight, used by agents).

### Hooks (Agent Annotations)

Hooks are **reverse-engineered questions**: assume the content is the "answer" — what question would lead someone here?

- Decontextualized: understandable without reading the source
- Precise: point to 1-N consecutive spans that directly answer the question
- Thought-provoking: dialectical or insightful, not information restatement
- Tagged: 2-5 abstract keywords for discoverability

Good: "How do you make decisions with incomplete information?"
Bad: "What does Peter Thiel think about secrets?"

## API Reference

### Content

```bash
# Get content metadata + TOC + outline
curl "$GLYNK_API_URL/api/content/{content_id}"

# Ingest from URL
curl -X POST "$GLYNK_API_URL/api/ingest" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source":"https://example.com/article"}'
# → {"content_id":"a1b2c3d4","title":"...","source_type":"article","file_count":1,"total_chars":5000}

# Upload file directly
curl -X POST "$GLYNK_API_URL/api/ingest/upload" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -F "file=@book.epub"
```

### Reading Content

```bash
# Read a chunk (AI view — simplified HTML, token-efficient)
curl "$GLYNK_API_URL/api/content/{content_id}/chunk?size=8000"
# → {"content":"<html>...<span id='a1b2-0-p1-s1'>text</span>...</html>",
#    "from":"a1b2-0-p1-s1","to":"a1b2-0-p3-s5","char_count":7945,
#    "has_more":true,"next_from":"a1b2-0-p4-s1"}

# Continue reading from where you left off
curl "$GLYNK_API_URL/api/content/{content_id}/chunk?size=8000&from=a1b2-0-p4-s1"

# Read full file (human view — complete HTML with styling)
curl "$GLYNK_API_URL/api/content/{content_id}/file"
```

**Pagination**: use `next_from` from each response as the `from` parameter for the next request. Continue until `has_more` is `false`.

### Annotations

```bash
# Create single annotation
curl -X POST "$GLYNK_API_URL/api/annotate" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "a1b2c3d4",
    "anchor": {"type":"text","spans":["a1b2-0-p5-s1","a1b2-0-p5-s2"],"color":"ghost"},
    "type": "hook",
    "text": "How do you make decisions with incomplete information?",
    "tags": ["decision-making", "uncertainty"],
    "contextuality": "standalone"
  }'

# Batch create (preferred for agents)
curl -X POST "$GLYNK_API_URL/api/annotate/batch" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"annotations":[...]}'
# → {"created":27,"ids":["ann-1","ann-2",...]}

# List my annotations
curl "$GLYNK_API_URL/api/annotations?content_id=a1b2c3d4&type=hook&limit=50" \
  -H "Authorization: Bearer $GLYNK_TOKEN"
# → {"annotations":[...],"total":150}

# Update annotation
curl -X PATCH "$GLYNK_API_URL/api/annotations/{annotation_id}" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Updated question"}'

# Delete annotation
curl -X DELETE "$GLYNK_API_URL/api/annotations/{annotation_id}" \
  -H "Authorization: Bearer $GLYNK_TOKEN"
```

### Semantic Search

```bash
# Search across all annotations
curl -X POST "$GLYNK_API_URL/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "How to make decisions with incomplete information",
    "types": ["hook", "highlight"],
    "top_k": 10
  }'
# → {"query_id":"qry-...","results":[
#     {"id":"ann-123","type":"hook","text":"...","spans":[...],"score":0.92,"content_id":"a1b2c3d4"}
#   ]}

# Search only my annotations
curl -X POST "$GLYNK_API_URL/api/annotations/search" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"decision making under uncertainty"}'

# Submit feedback on search results (improves ranking)
curl -X POST "$GLYNK_API_URL/api/feedback" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query_id":"qry-...","results":[{"result_id":"ann-123","clicked_through":true}]}'
```

### Outlines

Outlines should be submitted **after reading the entire content**, not incrementally (unlike hooks). Maintain a local temporary JSON file while reading, updating the outline structure as you go, then submit the complete version once finished.

#### Outline Structure Requirements

Each entry contains:
- `title`: Short, powerful title (5-15 characters)
- `description`: 1-2 sentence description — reading top-to-bottom should feel coherent, like a simplified version of the original
- `span_id`: Starting position in content (extracted from `<span id="...">` in HTML)
- `children`: Sub-entries (recursive)

Requirements:
- Natural hierarchy, no forced depth, 2-5 items per level
- Faithful to original content, no invented information
- Full-length book: 10-30 top-level items, depending on content length

```bash
# Submit AI outline (overwrites existing, submit after reading all content)
curl -X PUT "$GLYNK_API_URL/api/content/{content_id}/outline" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"outline":[
    {"title":"Zero to One Thinking",
     "description":"Innovation is not copying from 1 to N, but creating from 0 to 1. Every important moment is unique.",
     "span_id":"a1b2-0-p1-s1",
     "children":[
       {"title":"Contrarian Questions","description":"Great startups begin with a truth most people disagree with.","span_id":"a1b2-0-p3-s1","children":[]},
       {"title":"Monopoly vs Competition","description":"Competition is for losers; real profits come from monopoly.","span_id":"a1b2-0-p8-s1","children":[]}
     ]}
  ]}'

# Get outline
curl "$GLYNK_API_URL/api/content/{content_id}/outline"
```

### Reading Sessions & Progress

```bash
# Start a reading session
curl -X POST "$GLYNK_API_URL/api/reading-sessions" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content_id":"a1b2c3d4","source":"agent"}'
# → {"session_id":"rs-..."}

# End session
curl -X PUT "$GLYNK_API_URL/api/reading-sessions/{session_id}/end" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"duration_seconds":1234}'

# Save/get reading progress
curl -X PUT "$GLYNK_API_URL/api/content/{content_id}/progress" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"span_id":"a1b2-0-p15-s3"}'

curl "$GLYNK_API_URL/api/content/{content_id}/progress" \
  -H "Authorization: Bearer $GLYNK_TOKEN"
```

### RSS Sources

```bash
# Add RSS feed for auto-ingestion
curl -X POST "$GLYNK_API_URL/api/sources" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/feed.xml","schedule":"daily","max_items":5}'

# List / update / delete sources
curl "$GLYNK_API_URL/api/sources" -H "Authorization: Bearer $GLYNK_TOKEN"
curl -X PUT "$GLYNK_API_URL/api/sources/{id}" ...
curl -X DELETE "$GLYNK_API_URL/api/sources/{id}" ...
```

## Common Agent Workflows

### Read and Annotate Content

User specifies a content (or provides a file/URL to ingest first), then read page by page, generating hooks and outline.

```bash
# 1. Ingest content (if user provided a file/URL)
curl -X POST "$GLYNK_API_URL/api/ingest" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source":"https://example.com/article"}'

# 2. Read page by page, collecting span IDs
curl "$GLYNK_API_URL/api/content/a1b2c3d4/chunk?size=8000"
# ... use next_from to paginate ...

# 3. Submit hooks as you read (batch every ~20 hooks)
curl -X POST "$GLYNK_API_URL/api/annotate/batch" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"annotations":[
    {"content_id":"a1b2c3d4","type":"hook",
     "anchor":{"type":"text","spans":["a1b2-0-p5-s1"],"color":"ghost"},
     "text":"How do you identify opportunities others miss?",
     "tags":["opportunity","contrarian-thinking"],"contextuality":"standalone"}
  ]}'

# 4. Submit outline after reading all content
curl -X PUT "$GLYNK_API_URL/api/content/a1b2c3d4/outline" ...
```

### Search for Relevant Knowledge

```bash
# Semantic search — finds hooks/highlights across all content
curl -X POST "$GLYNK_API_URL/api/query" \
  -H "Content-Type: application/json" \
  -d '{"text":"strategies for dealing with uncertainty","top_k":5}'

# Read the original context around a result
curl "$GLYNK_API_URL/api/content/{content_id}/chunk?size=3000&from={span_id}"
```

## Tips

1. **Use `chunk` endpoint for reading** — it returns simplified HTML optimized for LLM token efficiency
2. **Batch annotations** — use `/annotate/batch` instead of individual calls
3. **Track reading with `next_from`** — each chunk response tells you where to continue
4. **Agents use `ghost` color** — agent annotations don't show visible highlights to readers
5. **Hooks enable discovery** — write hooks as questions someone might search for, not as summaries
6. **No special privileges** — agents use the same public API as any other client
