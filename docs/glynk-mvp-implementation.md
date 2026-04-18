# Glynk MVP 实现计划

> 2026-04-12 · Phase 0 工程任务拆解
> 一步到位替换现有 schema，无历史包袱

---

## 策略

**删掉旧表，建新表，改写所有代码**。现在没有用户数据，不需要迁移，不需要兼容层。所有后端代码统一到新的 Entity / Unit / Anchor 模型。

---

## Phase 0 前置：Corpus 播种

用改写后的 ingest pipeline 灌入一批你感兴趣的内容。**和开发并行——你选内容，我改代码。**

---

## 任务 1：数据层重建

**数据库**：
- 删除旧表（contents, annotations, users, queries, feedback, reading_progress, reading_sessions, translations, rss_sources）
- 创建新表（entities, units, anchors, auth, reading_progress, reading_sessions, event_log, rss_sources）
- 见 `glynk-data-model.md` 完整 DDL

**Python models**：
- 重写 `glynk/models.py`：Entity / Unit / Anchor dataclass
- 重写 `glynk/storage/postgres.py`：全部 CRUD 改为新表

**产出**：数据层完全切到新 schema

---

## 任务 2：Ingest pipeline 适配

**改写 `glynk/ingestion/pipeline.py`**：
- `ingest()` 产出 Unit(origin=ingested, shape=structured) 而不是 Content
- 为每个 author 创建 dormant Entity（去重：同名 author 复用同一个 Entity）
- content_id 生成逻辑不变（sha256[:16]），作为 Unit.id
- body = `{toc, files, media}` 格式
- metadata = `{title, abstract, source_type, source_url, ...}`
- HTML 处理、span_id 生成、文件存储逻辑不变——只是数据最终写入的表变了

**依赖**：任务 1

---

## 任务 3：API 重写

### Entity / Auth

```
POST   /auth/register    → 创建 Entity + auth record，返回 token
GET    /auth/me           → 当前用户 Entity
```

### Unit CRUD + 两种发布入口

```
# 创建入口分两类，反映两种 publishing 行为：
POST   /publications            → 从 URL 发布 publication（structured）
POST   /publications/upload     → 从文件（epub/pdf/html/md/zip）发布 publication
POST   /publications/media/*    → 音视频 publication（转写 + 时间戳）
POST   /thoughts                → 放下一个 thought（flat authored Unit）

# 老路径保留为 deprecated alias：
POST   /ingest, /ingest/upload, /ingest/media/*   → 等价于 /publications*
POST   /units                                      → 等价于 /thoughts

# 查询 / 读取 / 搜索 / 更新都对 Unit 统一（不分 publication / thought）：
GET    /units             → 列出（可按 origin / author_id 过滤）
GET    /units/{id}        → Unit 详情
DELETE /units/{id}        → 删除（ownership check）
GET    /units/{id}/read   → 读取内容（publication 按 span 分页，thought 整条返回）
POST   /units/search      → 语义检索（跨所有 Units）
```

### Unit outline

```
GET    /units/{id}/outline → 获取 AI outline
PUT    /units/{id}/outline → 提交 AI outline
```

### Anchor CRUD

```
POST   /anchors            → 创建 Anchor（标注 / 回复 / like / ...）
POST   /anchors/batch      → 批量创建
GET    /anchors             → 查询（按 target_unit / role / entity 过滤）
GET    /anchors/thread      → 某 span 下的讨论（按话题锚点扁平返回）
PATCH  /anchors/{id}        → 更新
DELETE /anchors/{id}        → 删除
```

### 其他

```
GET    /units/{id}/progress → 阅读进度
PUT    /units/{id}/progress → 保存阅读进度
POST   /reading-sessions   → 开始会话
PUT    /reading-sessions/{id}/end → 结束会话
POST   /sources            → RSS 源管理
```

**依赖**：任务 1、任务 2

---

## 任务 4：Agent tools 重写

```python
# 保留的工具（改为查新表）
list_contents  → list_units(limit, origin?, context)
read_content   → read_unit(unit_id, from_span, size, context)
submit_outline → submit_outline(unit_id, outline_json, context)

# 合并 / 改名
submit_annotations → create_anchors(unit_id, anchors_json, context)

# 新增
search_units(query, limit=10, context) → 语义搜索
save_thought(text, metadata={}, context)  → 将 Agent 产出存为 thought（flat authored Unit）
```

**依赖**：任务 3

---

## 任务 5：前端适配

**类型更新** `glynk-web/src/types/`：
- Content → Unit（字段映射）
- Annotation → Unit + Anchor
- User → Entity

**API client 更新** `glynk-web/src/api/`：
- 端点路径从 `/content/*` 改 `/units/*`
- 端点路径从 `/annotate` 改 `/anchors`
- 新增 `/units/search` 调用

**Reader 组件**：
- `useReaderStore` 里的 `contentId` → `unitId`，`contentMeta` → `unitMeta`
- 数据来源从 `/content/{id}/file` 改 `/units/{id}/read`
- 标注从 `/annotate` 改 `/anchors`
- **渲染逻辑不变**——HTML / span / highlight / TOC 这些都不变，只是数据来源换了

**新增页面**：
- Unit 写入页（文本框 + 提交 + 列表）——最简 UI

**依赖**：任务 3

---

## 任务 6："带回来"机制

### 被动模式

Agent skill `glynk_roam.md`：

```
当用户问"有什么和 X 相关的"：
1. search_units(X)
2. 对结果中的 ingested Unit，用 read_unit 补充上下文
3. 整理成"你之前想过 / 读过这些相关的东西"返回
4. 如果发现跨内容的意外关联，主动指出
```

### 主动探索

脚本 `scripts/explore_connections.py`：

```
1. 取用户最近 N 条 authored Units
2. 对每条跑 search_units
3. 过滤已展示过的结果
4. 把"意外的连接"存为 Unit(metadata.type=exploration)
5. 用户下次查看时展示
```

**依赖**：任务 4

---

## 执行顺序

```
Week 1
├─ 任务 1：数据层重建（新表 + models + storage）
├─ 任务 2：Ingest pipeline 适配
└─ [并行] 你选 corpus 书单 / 博客列表

Week 2
├─ 任务 3：API 重写
├─ 任务 4：Agent tools 重写
└─ 任务 5：前端适配（类型 + API client + Reader 改路由）

Week 3
├─ 给 ingested Units 的 abstract 批量生成 embedding
├─ 任务 6：Agent skill（被动 + 主动探索）
├─ Corpus 播种（跑 ingest）
└─ 端到端验证：你每天用，验证"被击中"
```

---

## 改动范围

| 层 | 重写 | 新增 | 不动 |
|---|---|---|---|
| **数据库** | 全部重建 | event_log | — |
| **models.py** | 全部重写 | — | — |
| **storage/postgres.py** | 全部重写 | — | — |
| **API** | 全部端点改路由和数据源 | /units/search, /auth/* | — |
| **Ingest pipeline** | pipeline.py 输出改为 Unit | — | handler/*, format_utils/*, processing/* |
| **Agent tools** | 4 个工具改为查新表 | search_units, save_thought | — |
| **前端 types** | Content→Unit, Annotation→Anchor | — | — |
| **前端 API client** | 端点路径全改 | units/search | — |
| **前端 Reader** | 数据源路由改 | Unit 写入页 | 渲染逻辑、组件结构 |
| **ingestion handlers** | — | — | 全部不动 |
| **HTML processing** | — | — | 全部不动 |
