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
  id            TEXT PRIMARY KEY,         -- 随机 16 位 hex，创建时固定，永不变
  author_id     TEXT NOT NULL REFERENCES entities(id),
  origin        TEXT NOT NULL,            -- ingested | authored
  shape         TEXT NOT NULL DEFAULT 'flat',   -- flat | structured
  body          JSONB NOT NULL,           -- flat: {html} | structured: {toc, files, media}
  visibility    JSONB DEFAULT '{"type":"private"}',
  metadata      JSONB DEFAULT '{}',       -- title, tags, source_url, content_hash, ...
  vector        vector(3072),             -- nullable；短 Unit 直接 embed，长 Unit 通过 chunk 派生
  vector_text   TEXT,                     -- 被 embed 的原文
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_units_author ON units(author_id);
CREATE INDEX idx_units_origin ON units(origin);
CREATE INDEX idx_units_metadata ON units USING GIN(metadata);
CREATE INDEX idx_units_content_hash ON units((metadata->>'content_hash'));
CREATE INDEX idx_units_vector ON units USING ivfflat(vector vector_cosine_ops) WITH (lists = 100);
```

**Unit 身份 vs 内容指纹**：

- `unit_id` = 随机 16 位 hex，**创建时固定，永不变**。是身份码。
- `metadata.content_hash` = sha256(body)，**内容变就变**。是内容指纹，也是 ingest 去重的键。

这个拆分让"内容更新"成为可能——同一个 unit_id 在不同时间可以承载不同版本内容。阅读器链接、anchor 的 target_unit、阅读进度等都挂在稳定的 unit_id 上，不会因为内容更新而断。

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
  role            TEXT NOT NULL,          -- see glynk/models.py ROLE_SCHEMAS
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

## Anchor role 与 schema

Role 的允许取值和 (source, target, body) 约束在 [`glynk/models.py`](../glynk/models.py) 的 `ROLE_SCHEMAS` 里定义，创建时走 `validate_anchor` 强制校验。

| role | source | target | body | 谁用 |
|---|---|---|---|---|
| highlight | unit | span | auto（= target span 副本）| 人 + Agent |
| hook | unit | span | required | Agent 为主 |
| note | unit | span \| unit | required | 人为主 |
| summary | unit | unit | required | Agent 为主 |
| reply | unit | span \| unit | optional（文字 / emoji / 图片）| 人为主 |
| like | entity | span \| unit | none | 人 |
| bookmark | entity | span \| unit | none | 人 |
| follow | entity | entity | none | 人 |

role 只存在 anchor 上，Unit 不复制。搜索需要按 role 过滤时，用 LEFT JOIN 到 anchors 表走 `a.role`。

---

## Anchor 使用模式：讨论线程

回复用**一条 anchor + metadata 里的父节点指针**：

```
Unit A（一级回复 on 某段文本）
  └─ Anchor(target_span=某段, role=reply, metadata={})

Unit B（回复 A）
  └─ Anchor(target_span=某段, role=reply, metadata={in_reply_to: A.unit_id})

Unit C（回复 B）
  └─ Anchor(target_span=某段, role=reply, metadata={in_reply_to: B.unit_id})
```

- `target_span` 在每条 reply 上都保留，指向**话题锚点**（原文位置）—— "查这段话下所有讨论" 一次扁平 SQL 就够
- `metadata.in_reply_to` 承载**父节点指针**—— 前端据此 group 构树
- 不再创建额外的 `reply_to` anchor；旧设计里那条是死代码，且跟 ROLE_SCHEMAS 冲突

深度无限制；前端决定显示策略（缩进 / 折叠 / 展开独立页）。每条回复仍是独立 Unit，可被语义搜索、被第三方 anchor、出现在作者的 Units 列表里。

---

## Embedding 策略

决策集中在 [`glynk/embedding/service.py`](../glynk/embedding/service.py) 的 `maybe_embed(text, config, metadata)`。默认 embed，但满足以下任一条件**不 embed**（vector 留 null）：

- **有效字符数 < 30**（去标点和 emoji 后；`should_embed` 阈值）
- **metadata.skip_embedding = true**（用户/Agent 显式标记）
- **未配置 Azure OpenAI**

Embedding 决策**不看 role** —— ROLE_SCHEMAS 已经保证了 body 的存在性，短 body 的 role（如 emoji-only reply、highlight 的 span 副本）会被长度阈值自然过滤。Ingested Unit 不设 `vector_text`，自然不 embed。

**Vector 字段 nullable**，未来可补 embed（如"这条短回复被很多人引用了→值得 embed"）。

---

## Ingest / Update 语义

### 去重

只有一层：`metadata.content_hash`。

- 同内容再次 ingest → 命中 hash，幂等返回已有 Unit（不做任何工作）
- 不同内容（哪怕同 URL）→ 新建 Unit，新 `unit_id`
- URL 不是唯一键，只是 metadata 字段

### In-place 更新（`update_of`）

`POST /api/publications?update_of={unit_id}` 触发**原地更新**：

- `unit_id` 不变
- `body` / HTML 文件 / TOC / `metadata.content_hash` 全部替换
- `metadata.updated_by` / `metadata.updated_at` 记录更新操作
- **Span 级 anchor 自动迁移**（见下）

链接、阅读进度、别人的 anchor 的 `target_unit` 都不受影响，因为 unit_id 是稳定的。

### Span anchor 迁移（tier 1/2/3）

当一个 Unit 被 `update_of` 更新时，`[glynk/ingestion/anchor_migration.py](../glynk/ingestion/anchor_migration.py)` 自动对所有 `target_unit = unit_id AND target_span IS NOT NULL` 的 anchor 执行：

1. **Tier 1 `exact`**：旧 span 文本在新内容中唯一精确匹配 → 更新 `target_span`
2. **Tier 2 `fuzzy`**：相似度 ≥ 85%（SequenceMatcher）→ 更新 `target_span`，记录 `metadata.migration.similarity`
3. **Tier 3 `orphan`**：找不到 → `target_span = NULL`，`target_type = 'unit'`，`metadata.migration.original_text` 保留原文供后续人工/Agent 重定位

迁移结果写在 `metadata.migration = {confidence, old_span, similarity?, original_text?}` 里，`Unit.metadata.migration_stats` 记录总体统计。

Orphan 的 anchor 仍挂在新 Unit 上（只是没 span 位置），reader UI 可在"未对齐的标注"区展示。

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
| content_id | unit.id（老 Unit 的 ID 保留 sha256[:16]；新 Unit 的 ID 是随机 16 hex）|
| title | metadata.title |
| author | 创建 dormant Entity，unit.author_id 指向它 |
| source_type | metadata.source_type |
| source_url | metadata.source_url |
| source_file_hash | metadata.content_hash |
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
