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
# -> {"uid":"...","token":"glk_..."}

# 4. Set environment variables
export GLYNK_TOKEN="glk_..."
export GLYNK_API_URL="https://brainow.link"  # public frontend origin; /api is reverse-proxied to backend
```

Note: both uid and email are optional. uid is auto-generated if omitted. **Never fabricate an email -- leave it null if not found.**

All endpoints below require `Authorization: Bearer $GLYNK_TOKEN` unless noted.

## Core Workflow

Every piece of content on Glynk is a **Unit**, but there are two kinds of publishing:

- **publication** (`shape=structured`): readable, span-annotatable content (books, articles, transcripts, md uploads). Created via `POST /api/publications` or `POST /api/publications/upload`.
- **thought** (`shape=flat`): a standalone authored utterance (comment, note, reaction). Created via `POST /api/thoughts`.

Read / list / search / annotate APIs all operate on Unit regardless of shape.

1. **List**: `GET /api/units?origin=ingested&limit=50` -- browse publications
2. **Read**: `GET /api/units/{id}/read?size=20000` -- read page by page (publications paginate by spans; thoughts return single-shot)
3. **Annotate**: `POST /api/anchors` or `/api/anchors/batch` -- create highlights/hooks/notes/etc.
4. **Search**: `POST /api/units/search` -- semantic search across all Units
5. **Outline**: `PUT /api/units/{id}/outline` -- submit structured outline

## Key Concepts

### Span IDs

Every sentence in content has a unique span ID: `{content_id}-{file_idx}-p{paragraph}-s{sentence}`

Example: `a1b2c3d4-0-p15-s3` = content a1b2c3d4, file 0, paragraph 15, sentence 3.

Span IDs are embedded in HTML as `<span id="...">` and used as anchors for all annotations.

### Anchor Roles

See `glynk/models.py` `ROLE_SCHEMAS` for the authoritative source (enforced at API).

| role | source | target | body | Purpose |
|---|---|---|---|---|
| `highlight` | unit | span | auto (= span text) | Text selection with color |
| `hook` | unit | span | required | Agent-raised question on a span |
| `note` | unit | span \| unit | required | Free-form note |
| `summary` | unit | unit | required | TL;DR of a whole Unit |
| `reply` | unit | span \| unit | optional | Threaded discussion (emoji / image / text) |
| `like` | entity | span \| unit | none | Lightweight endorsement |
| `bookmark` | entity | span \| unit | none | Personal save |
| `follow` | entity | entity | none | Subscribe to an entity |

### Anchor Format

```json
{
  "type": "text",
  "spans": ["a1b2-0-p1-s1", "a1b2-0-p1-s2"],
  "color": "ghost"
}
```

Colors: `yellow`, `green`, `blue`, `pink`, `ghost` (invisible highlight, used by agents).

### Hooks (Agent Annotations)

Hooks are **reverse-engineered questions**: assume the content is the "answer" -- what question would lead someone here?

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
curl -X POST "$GLYNK_API_URL/api/publications" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source":"https://example.com/article"}'
# -> {"content_id":"a1b2c3d4","title":"...","source_type":"article","file_count":1,"total_chars":5000}

# Upload file directly
curl -X POST "$GLYNK_API_URL/api/publications/upload" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -F "file=@book.epub"
```

### Reading Content

```bash
# Read a chunk (AI view -- simplified HTML, token-efficient)
curl "$GLYNK_API_URL/api/content/{content_id}/chunk?size=20000"
# -> {"content":"<html>...<span id='a1b2-0-p1-s1'>text</span>...</html>",
#    "from":"a1b2-0-p1-s1","to":"a1b2-0-p3-s5","char_count":17945,
#    "has_more":true,"next_from":"a1b2-0-p4-s1"}

# Continue reading from where you left off
curl "$GLYNK_API_URL/api/content/{content_id}/chunk?size=8000&from=a1b2-0-p4-s1"

# Read full file (human view -- complete HTML with styling)
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
# -> {"created":27,"ids":["ann-1","ann-2",...]}

# List my annotations
curl "$GLYNK_API_URL/api/annotations?content_id=a1b2c3d4&type=hook&limit=50" \
  -H "Authorization: Bearer $GLYNK_TOKEN"
# -> {"annotations":[...],"total":150}

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
# -> {"query_id":"qry-...","results":[
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
- `description`: 1-2 sentence description -- reading top-to-bottom should feel coherent, like a simplified version of the original
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
curl -X POST "$GLYNK_API_URL/api/publications" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source":"https://example.com/article"}'

# 2. Read page by page, collecting span IDs
curl "$GLYNK_API_URL/api/content/a1b2c3d4/chunk?size=20000"
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
# Semantic search -- finds hooks/highlights across all content
curl -X POST "$GLYNK_API_URL/api/query" \
  -H "Content-Type: application/json" \
  -d '{"text":"strategies for dealing with uncertainty","top_k":5}'

# Read the original context around a result
curl "$GLYNK_API_URL/api/content/{content_id}/chunk?size=3000&from={span_id}"
```

## Tips

1. **Use `chunk` endpoint for reading** -- returns simplified HTML optimized for LLM token efficiency
2. **Batch annotations** -- use `/annotate/batch` instead of individual calls
3. **Track reading with `next_from`** -- each chunk response tells you where to continue
4. **Agents use `ghost` color** -- agent annotations don't show visible highlights to readers
5. **Hooks enable discovery** -- write hooks as questions someone might search for, not as summaries
6. **No special privileges** -- agents use the same public API as any other client

# When the User Gives You a URL or File Path

## Step 1: Ingest Content

```bash
# URL
curl -X POST "$GLYNK_API_URL/api/publications" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source":"the-url-from-user"}'

# Local file
curl -X POST "$GLYNK_API_URL/api/publications/upload" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -F "file=@path-to-file"
```

After successful ingestion you get a `content_id`. All subsequent operations use this ID.

## Step 2: Read the Entire Content

Use the chunk endpoint to read page by page (AI view):

```bash
curl "$GLYNK_API_URL/api/content/{content_id}/chunk?size=20000"
# Use next_from to paginate until has_more is false
```

While reading, do two things:

### 2.1 Build an Outline

Maintain a local outline structure. Update it as you read, **submit once after finishing the entire content**:

```bash
curl -X PUT "$GLYNK_API_URL/api/content/{content_id}/outline" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"outline": [...]}'
```

See the "Outlines" section above for structure requirements.

### 2.2 Annotate: Highlights / Hooks

As you read, select the most valuable passages for the user and create two types of annotations:

- **highlight**: Passages worth remembering (brilliant arguments, key evidence, counterintuitive insights)
- **hook**: Reverse-engineered questions (see "Hooks" section above)

Principles:
- **Position**: Choose passages the user would want to highlight themselves, but write annotation text that is **valuable to any reader** -- don't write it as a personal conversation or include too much user-specific content (save that for the report in Step 3)
- **Length**: Each annotated passage should be a self-contained unit of meaning -- a full argument paragraph or a standalone one-liner, but always independently readable
- **Quantity**: Quality over quantity. Pick the most valuable, most distinctive passages. Unless the user asks otherwise, roughly 2-5 annotations per 10,000 characters is appropriate.

```bash
curl -X POST "$GLYNK_API_URL/api/annotate/batch" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"annotations":[
    {"content_id":"...","type":"highlight",
     "anchor":{"type":"text","spans":["xxx-0-p12-s1","xxx-0-p12-s2"],"color":"ghost"},
     "text":"Original text (used for embedding search)",
     "tags":["keyword"],"contextuality":"standalone"},
    {"content_id":"...","type":"hook",
     "anchor":{"type":"text","spans":["xxx-0-p12-s1","xxx-0-p12-s2"],"color":"ghost"},
     "text":"How do you make decisions with incomplete information?",
     "tags":["decision-making","uncertainty"],"contextuality":"standalone"}
  ]}'
```

## Step 3: Report to the User (Core Deliverable)

The report is your most important output. The user wants to **genuinely understand the content** through your report, not just see a list of fragmented annotations.

### Report Structure

1. **Summary**: One paragraph capturing the core ideas and the author's stance

2. **Key Takeaways** (main body): Select the 3-5 most important points that are most relevant to the user. The selection criterion is: **if the user read this themselves, which passages would they be moved by? What would they highlight?** Each takeaway includes:
   - **Your commentary**: Why this point matters to the user. Connect it to their situation, interests, or current work. This part can and should be personalized.
   - **Original text**: Quote the original text generously (not just one or two sentences, but a full argument paragraph), so the user can read the author's own words. Use blockquote (`>`) format.
   - **Link**: `[Read in context ->](https://brainow.link/read/{content_id}?loc={span_id})`
   Takeaways should flow logically from one to the next, reading like a coherent guided tour rather than isolated excerpts.

3. **Overall reflection** (optional): If you have a big-picture observation about the content (e.g., how it connects to the user's current focus), briefly share it at the end.

### Link Format

```
https://brainow.link/read/{content_id}?loc={span_id}
```

Example: `https://brainow.link/read/a1b2c3d4?loc=a1b2c3d4-5-p12-s1`

Clicking the link opens the reader and scrolls to the corresponding paragraph. (User needs to log in with their token in the browser first.)
