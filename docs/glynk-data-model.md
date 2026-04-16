# Glynk 数据模型

> 技术 reference · 2026-04-12
> 一步到位，替换现有 schema

---

## 核心：3 张表

### Entity

```sql
CREATE TABLE entities (
  id            TEXT PRIMARY KEY,         -- ULID
  kind          TEXT NOT NULL DEFAULT 'human',  -- human | ai
  state         TEXT NOT NULL DEFAULT 'active', -- active | dormant | claimed
  display_name  TEXT NOT NULL DEFAULT '',
  bio           TEXT DEFAULT '',
  agent_uri     TEXT,                     -- A2A IM 可达性（nullable）
  inspired_by   TEXT REFERENCES entities(id),   -- AI 分身指向原作者
  created_at    TIMESTAMPTZ DEFAULT NOW()
);
```

### Unit

```sql
CREATE TABLE units (
  id            TEXT PRIMARY KEY,         -- ingested 用 sha256[:16]；authored 用 ULID
  author_id     TEXT NOT NULL REFERENCES entities(id),
  origin        TEXT NOT NULL,            -- ingested | authored
  shape         TEXT NOT NULL DEFAULT 'flat',   -- flat | structured
  body          JSONB NOT NULL,           -- flat: {html} | structured: {toc, files, media}
  visibility    JSONB DEFAULT '{"type":"private"}',
  metadata      JSONB DEFAULT '{}',       -- title, tags, source_url, material_type, genre, ...
  vector        vector(3072),             -- nullable；短 Unit 直接 embed，长 Unit 通过 chunk 派生
  vector_text   TEXT,                     -- 被 embed 的原文
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_units_author ON units(author_id);
CREATE INDEX idx_units_origin ON units(origin);
CREATE INDEX idx_units_metadata ON units USING GIN(metadata);
CREATE INDEX idx_units_vector ON units USING ivfflat(vector vector_cosine_ops) WITH (lists = 100);
```

### Anchor

```sql
CREATE TABLE anchors (
  id              TEXT PRIMARY KEY,       -- ULID
  source_type     TEXT NOT NULL,          -- unit | entity
  source_unit     TEXT REFERENCES units(id) ON DELETE CASCADE,
  source_entity   TEXT REFERENCES entities(id),
  target_type     TEXT NOT NULL,          -- unit | span | entity
  target_unit     TEXT REFERENCES units(id),
  target_span     TEXT,                   -- span_id：{unit_id}-{file_idx}-p{n}-s{m}
  target_entity   TEXT REFERENCES entities(id),
  role            TEXT NOT NULL,          -- highlight | hook | note | reaction | like | follow | ...
  metadata        JSONB DEFAULT '{}',     -- color, offsets, emoji, ...
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_anchors_source_unit ON anchors(source_unit);
CREATE INDEX idx_anchors_target_unit ON anchors(target_unit);
CREATE INDEX idx_anchors_target_span ON anchors(target_span);
CREATE INDEX idx_anchors_source_entity ON anchors(source_entity);
CREATE INDEX idx_anchors_target_entity ON anchors(target_entity);
CREATE INDEX idx_anchors_role ON anchors(role);
```

---

## Anchor 使用模式：讨论线程

回复一段话或一条 Unit 时，**同时挂两个 Anchor**：

```
Unit A（一级回复 on 某段文本）
  └─ Anchor(target_span=某段, role=reply)

Unit B（回复 A）
  ├─ Anchor(target_span=某段, role=reply)       ← 主题锚
  └─ Anchor(target_unit=A, role=reply_to)        ← 父节点锚

Unit C（回复 B）
  ├─ Anchor(target_span=某段, role=reply)
  └─ Anchor(target_unit=B, role=reply_to)
```

**为什么两个**：主题锚保证"查这段话下所有讨论"是一次扁平查询；父节点锚保证可重建对话树。冗余是刻意的，换查询效率和语义清晰。

**深度无限制**——前端决定显示策略（缩进 / 折叠 / 展开独立页）。

**每条回复仍是独立 Unit**——可被单独语义搜索、被第三方 anchor、出现在作者的 Units 列表里。

---

## Embedding 策略

默认 embed，但满足以下任一条件**不 embed**（vector 留 null）：

- **字符数 < 30**（去标点和 emoji 后）
- **metadata.skip_embedding = true**（用户/Agent 显式标记）
- **role 不在 EMBEDDING_ROLES**（纯关系类 anchor 不触发 embed）

EMBEDDING_ROLES = { `highlight`, `hook`, `note`, `reply`, `topic`, `summary` }

非 EMBEDDING_ROLES 的 anchor（`reaction` / `like` / `follow` / `reply_to` / `bookmark` 等）要么没有 source Unit body（纯关系），要么是结构性指针——都不需要 embed。

**Vector 字段 nullable**，未来可补 embed（如"这条短回复被很多人引用了→值得 embed"）。

---

## Sidecar 表

### Auth（从 Entity 分离）

```sql
CREATE TABLE auth (
  entity_id   TEXT PRIMARY KEY REFERENCES entities(id),
  token       TEXT UNIQUE NOT NULL,
  email       TEXT UNIQUE NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### 用户态

```sql
CREATE TABLE reading_progress (
  entity_id   TEXT NOT NULL REFERENCES entities(id),
  unit_id     TEXT NOT NULL REFERENCES units(id),
  span_id     TEXT NOT NULL,
  updated_at  TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (entity_id, unit_id)
);

CREATE TABLE reading_sessions (
  id              TEXT PRIMARY KEY,
  entity_id       TEXT NOT NULL REFERENCES entities(id),
  unit_id         TEXT NOT NULL REFERENCES units(id),
  started_at      TIMESTAMPTZ DEFAULT NOW(),
  ended_at        TIMESTAMPTZ,
  duration_seconds INTEGER,
  source          TEXT DEFAULT 'manual'
);
```

### 行为日志

```sql
CREATE TABLE event_log (
  id            TEXT PRIMARY KEY,
  actor_id      TEXT NOT NULL REFERENCES entities(id),
  event_type    TEXT NOT NULL,   -- search | click | dwell | anchor_create | revisit | ...
  subject_unit  TEXT REFERENCES units(id),
  subject_span  TEXT,
  payload       JSONB DEFAULT '{}',
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_event_actor ON event_log(actor_id);
CREATE INDEX idx_event_type ON event_log(event_type);
CREATE INDEX idx_event_unit ON event_log(subject_unit);
```

### 配置

```sql
CREATE TABLE rss_sources (
  id            TEXT PRIMARY KEY,
  url           TEXT NOT NULL,
  name          TEXT DEFAULT '',
  content_type  TEXT,
  schedule      TEXT DEFAULT 'daily',
  max_items     INT DEFAULT 5,
  enabled       BOOLEAN DEFAULT true,
  filters       JSONB DEFAULT '{}',
  created_by    TEXT REFERENCES entities(id),
  last_fetched_at TIMESTAMPTZ,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 现有表 → 新表映射

### contents → units

| 旧字段 | 新位置 |
|---|---|
| content_id | unit.id（保留 sha256[:16]）|
| title | metadata.title |
| author | 创建 dormant Entity，unit.author_id 指向它 |
| source_type | metadata.source_type |
| source_url | metadata.source_url |
| source_file_hash | metadata.source_file_hash |
| file_count | body.file_count |
| toc_json | body.toc |
| ai_outline_json | metadata.ai_outline |
| abstract | metadata.abstract |
| uid | metadata.imported_by（**不是 author**）|
| status | metadata.status |
| total_chars | metadata.total_chars |
| language | metadata.language |

### annotations → units + anchors

| 旧字段 | 新位置 |
|---|---|
| id | unit.id |
| content_id | anchor.target_unit |
| anchor.spans | anchor.target_span |
| anchor.color/offsets | anchor.metadata |
| type | anchor.role |
| text | unit.body.html |
| tags | unit.metadata.tags |
| source | 映射到 entity.kind（human/ai）|
| uid | unit.author_id（通过 entity）|
| visibility | unit.visibility |
| embedding | unit.vector |

### users → entities + auth

| 旧字段 | 新位置 |
|---|---|
| uid | entity.id |
| name | entity.display_name |
| token | auth.token |
| email | auth.email |
| preferred_lang | entity metadata 或 auth 表 |
