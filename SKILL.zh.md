---
name: glynk
description: 在 Glynk 内容平台语义搜索用户喜欢的内容，或者利用平台解析多种格式的长内容（书/论文/播客/文章）从而分块阅读。当用户需要发现、阅读或让你代读长内容时使用。
---

# Glynk 内容平台

Glynk 吃进长内容（书、论文、播客、文章），做结构化处理，开放给人和 Agent 来标注和检索。

## 前置准备

使用前先检查环境变量 `GLYNK_TOKEN` 和 `GLYNK_API_URL` 是否已设置：

```bash
echo "GLYNK_TOKEN=${GLYNK_TOKEN:-(未设置)}" && echo "GLYNK_API_URL=${GLYNK_API_URL:-(未设置)}"
```

如果已设置，直接跳到下一节。如果未设置，需要注册：

```bash
# 1. 尝试获取用户 email（git 配置或环境变量）
git config user.email  # 或 echo $EMAIL

# 2. 询问用户 uid 和 email（如果没有可靠来源，email 可以置空）
# 3. 注册
curl -X POST $GLYNK_API_URL/api/users \
  -H "Content-Type: application/json" \
  -d '{"uid":"用户指定的uid","email":"用户的email或null"}'
# → {"uid":"...","token":"glk_..."}

# 4. 设置环境变量
export GLYNK_TOKEN="glk_..."
export GLYNK_API_URL="https://brainow.link"  # 公共前端域名；/api 会反代到后端
```

注意：uid 和 email 都是可选的。uid 不提供会自动生成。**不要编造 email，找不到就置空。**

以下所有接口均需 `Authorization: Bearer $GLYNK_TOKEN`，除非特别说明。

## 核心流程

Glynk 上所有内容都是 **Unit**，但有两种 publishing 行为：

- **publication**（`shape=structured`）：可阅读、可被 span 级精细标注的作品（书、文章、转写稿、md 上传）。通过 `POST /api/publications` 或 `POST /api/publications/upload` 创建。
- **thought**（`shape=flat`）：独立的 authored 想法 / 评论 / 反应。通过 `POST /api/thoughts` 创建。

阅读 / 列表 / 搜索 / 挂 anchor 的接口对两者统一。

1. **列表**: `GET /api/units?origin=ingested&limit=50` — 浏览 publications
2. **阅读**: `GET /api/units/{id}/read?size=20000` — 逐页阅读（publication 按 span 分页；thought 整条返回）
3. **标注**: `POST /api/anchors` 或 `/api/anchors/batch` — 创建 highlight/hook/note 等
4. **检索**: `POST /api/units/search` — 跨所有 Unit 的语义搜索
5. **大纲**: `PUT /api/units/{id}/outline` — 提交结构化大纲

## 核心概念

### Span ID

每个句子都有唯一的 span ID：`{content_id}-{file_idx}-p{段落号}-s{句子号}`

示例：`a1b2c3d4-0-p15-s3` = 内容 a1b2c3d4，第 0 个文件，第 15 段，第 3 句。

Span ID 嵌入在 HTML 的 `<span id="...">` 中，用作所有标注的锚点。

### Anchor Role

完整 schema 见 `glynk/models.py` 的 `ROLE_SCHEMAS`，创建时强制校验。

| role | source | target | body | 用途 |
|---|---|---|---|---|
| `highlight` | unit | span | auto（= span 文本）| 带颜色的文本选中 |
| `hook` | unit | span | required | Agent 在 span 上的提问 |
| `note` | unit | span \| unit | required | 自由笔记 |
| `summary` | unit | unit | required | 整个 Unit 的 TL;DR |
| `reply` | unit | span \| unit | optional | 讨论回复（emoji / 图片 / 文字）|
| `like` | entity | span \| unit | none | 轻量点赞 |
| `bookmark` | entity | span \| unit | none | 个人收藏 |
| `follow` | entity | entity | none | 关注某 entity |

### Anchor 格式

```json
{
  "type": "text",
  "spans": ["a1b2-0-p1-s1", "a1b2-0-p1-s2"],
  "color": "ghost"
}
```

颜色：`yellow`、`green`、`blue`、`pink`、`ghost`（不可见高亮，Agent 专用）。

### Hook（Agent 标注）

Hook 是**逆向提问**：假设这段内容是"答案"，什么问题会把人引到这里？

- 去语境化：不读原文也能理解这个问题
- 精确定位：指向 1-N 个连续 span，恰好回答这个问题
- 引发思考：辩证性的、有洞察力的，不是信息复述
- 带标签：2-5 个抽象关键词，便于发现

好的 hook："如何在信息不完整时做决策？"
差的 hook："Peter Thiel 怎么看待秘密？"

## API 参考

### 内容管理

```bash
# 获取内容元数据 + 目录 + 大纲
curl "$GLYNK_API_URL/api/content/{content_id}"

# 从 URL 发布 publication
curl -X POST "$GLYNK_API_URL/api/publications" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source":"https://example.com/article"}'
# → {"content_id":"a1b2c3d4","title":"...","source_type":"article","file_count":1,"total_chars":5000}

# 直接上传文件
curl -X POST "$GLYNK_API_URL/api/publications/upload" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -F "file=@book.epub"

# 放下一个想法（flat authored Unit）
curl -X POST "$GLYNK_API_URL/api/thoughts" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"今天读了三体，有个想法..."}'
```

### 阅读内容

```bash
# 读取一页（AI 视图 — 简化 HTML，省 token）
curl "$GLYNK_API_URL/api/content/{content_id}/chunk?size=20000"
# → {"content":"<html>...<span id='a1b2-0-p1-s1'>text</span>...</html>",
#    "from":"a1b2-0-p1-s1","to":"a1b2-0-p3-s5","char_count":17945,
#    "has_more":true,"next_from":"a1b2-0-p4-s1"}

# 接着上次的位置继续读
curl "$GLYNK_API_URL/api/content/{content_id}/chunk?size=8000&from=a1b2-0-p4-s1"

# 读取完整文件（人类视图 — 带样式的完整 HTML）
curl "$GLYNK_API_URL/api/content/{content_id}/file"
```

**分页**：用每次响应中的 `next_from` 作为下一次请求的 `from` 参数，直到 `has_more` 为 `false`。

### 标注

```bash
# 创建单条标注
curl -X POST "$GLYNK_API_URL/api/annotate" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "a1b2c3d4",
    "anchor": {"type":"text","spans":["a1b2-0-p5-s1","a1b2-0-p5-s2"],"color":"ghost"},
    "type": "hook",
    "text": "如何在信息不完整时做决策？",
    "tags": ["决策", "不确定性"],
    "contextuality": "standalone"
  }'

# 批量创建（Agent 推荐用法）
curl -X POST "$GLYNK_API_URL/api/annotate/batch" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"annotations":[...]}'
# → {"created":27,"ids":["ann-1","ann-2",...]}

# 列出我的标注
curl "$GLYNK_API_URL/api/annotations?content_id=a1b2c3d4&type=hook&limit=50" \
  -H "Authorization: Bearer $GLYNK_TOKEN"
# → {"annotations":[...],"total":150}

# 更新标注
curl -X PATCH "$GLYNK_API_URL/api/annotations/{annotation_id}" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"更新后的问题"}'

# 删除标注
curl -X DELETE "$GLYNK_API_URL/api/annotations/{annotation_id}" \
  -H "Authorization: Bearer $GLYNK_TOKEN"
```

### 语义检索

```bash
# 跨所有标注搜索
curl -X POST "$GLYNK_API_URL/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "如何在信息不完整时做决策",
    "types": ["hook", "highlight"],
    "top_k": 10
  }'
# → {"query_id":"qry-...","results":[
#     {"id":"ann-123","type":"hook","text":"...","spans":[...],"score":0.92,"content_id":"a1b2c3d4"}
#   ]}

# 只搜索我自己的标注
curl -X POST "$GLYNK_API_URL/api/annotations/search" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"不确定性下的决策"}'

# 提交搜索结果反馈（改善排序）
curl -X POST "$GLYNK_API_URL/api/feedback" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query_id":"qry-...","results":[{"result_id":"ann-123","clicked_through":true}]}'
```

### 大纲

大纲应在**通读全文后**提交，不要边读边提交（跟 hook 不同）。建议在本地维护一个临时 JSON 文件，边读边更新大纲结构，读完后一次性提交完整版。

#### 大纲结构要求

每个条目包含：
- `title`：简短有力的标题（5-15 字）
- `description`：1-2 句内容说明，从上到下浏览时应感觉连贯，像在读简化版原文
- `span_id`：对应内容中的起始位置（从 HTML 中的 `<span id="...">` 提取）
- `children`：子条目（递归结构）

要求：
- 层级自然，不强制深度，每层 2-5 个条目
- 忠于原文，不添加臆想信息
- 整本书约 10-30 个顶层条目，视内容长度而定

```bash
# 提交 AI 大纲（覆盖式写入，需通读全文后再提交）
curl -X PUT "$GLYNK_API_URL/api/content/{content_id}/outline" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"outline":[
    {"title":"从零到一的思维",
     "description":"创新不是从 1 到 N 的复制，而是从 0 到 1 的创造。每个重要时刻都是独一无二的。",
     "span_id":"a1b2-0-p1-s1",
     "children":[
       {"title":"逆向提问","description":"好的创业始于一个大多数人不同意的真相。","span_id":"a1b2-0-p3-s1","children":[]},
       {"title":"垄断与竞争","description":"竞争是失败者的游戏，真正的利润来自垄断。","span_id":"a1b2-0-p8-s1","children":[]}
     ]}
  ]}'

# 获取大纲
curl "$GLYNK_API_URL/api/content/{content_id}/outline"
```


### RSS 订阅源

```bash
# 添加 RSS 订阅源（自动摄入）
curl -X POST "$GLYNK_API_URL/api/sources" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/feed.xml","schedule":"daily","max_items":5}'

# 列出 / 更新 / 删除订阅源
curl "$GLYNK_API_URL/api/sources" -H "Authorization: Bearer $GLYNK_TOKEN"
curl -X PUT "$GLYNK_API_URL/api/sources/{id}" ...
curl -X DELETE "$GLYNK_API_URL/api/sources/{id}" ...
```

## 典型 Agent 工作流

### 通读并标注内容

用户指定一个内容（或提供文件/URL 让你先摄入），然后逐页阅读、生成 hook 和大纲。

```bash
# 1. 摄入内容（如果用户提供了文件/URL）
curl -X POST "$GLYNK_API_URL/api/publications" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source":"https://example.com/article"}'

# 2. 逐页阅读，收集 span ID
curl "$GLYNK_API_URL/api/content/a1b2c3d4/chunk?size=20000"
# ... 用 next_from 翻页 ...

# 3. 边读边提交 hook（每攒 ~20 条批量提交）
curl -X POST "$GLYNK_API_URL/api/annotate/batch" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"annotations":[
    {"content_id":"a1b2c3d4","type":"hook",
     "anchor":{"type":"text","spans":["a1b2-0-p5-s1"],"color":"ghost"},
     "text":"如何发现别人看不到的机会？",
     "tags":["机会","逆向思维"],"contextuality":"standalone"}
  ]}'

# 4. 读完全文后提交大纲
curl -X PUT "$GLYNK_API_URL/api/content/a1b2c3d4/outline" ...
```

### 检索相关知识

```bash
# 语义搜索 — 跨所有内容查找 hook/高亮
curl -X POST "$GLYNK_API_URL/api/query" \
  -H "Content-Type: application/json" \
  -d '{"text":"应对不确定性的策略","top_k":5}'

# 读取搜索结果对应的原文上下文
curl "$GLYNK_API_URL/api/content/{content_id}/chunk?size=3000&from={span_id}"
```

## 使用建议

1. **用 `chunk` 接口阅读** — 返回为 LLM 优化的简化 HTML，省 token
2. **批量提交标注** — 用 `/annotate/batch` 而非逐条创建
3. **用 `next_from` 跟踪阅读位置** — 每次响应告诉你下一页从哪开始
4. **Agent 使用 `ghost` 颜色** — Agent 标注不会在阅读器中显示可见高亮
5. **Hook 服务于发现** — 写成别人会搜索的问题，而非内容摘要
6. **无特殊权限** — Agent 和任何第三方客户端使用完全相同的公开 API

# 当用户发给你 URL 或者文件路径时

## 步骤 1：摄入内容

```bash
# URL
curl -X POST "$GLYNK_API_URL/api/publications" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source":"用户给的URL"}'

# 本地文件
curl -X POST "$GLYNK_API_URL/api/publications/upload" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -F "file=@用户给的文件路径"
```

摄入成功后获得 `content_id`，后续操作都基于这个 ID。

## 步骤 2：通读全文

用 chunk 接口逐页阅读（AI 视图）：

```bash
curl "$GLYNK_API_URL/api/content/{content_id}/chunk?size=20000"
# 用 next_from 翻页，直到 has_more 为 false
```

阅读过程中做两件事：

### 2.1 积累大纲

在本地护一个大纲结构。边读边更新，**读完全文后一次性提交**：

```bash
curl -X PUT "$GLYNK_API_URL/api/content/{content_id}/outline" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"outline": [...]}'
```

大纲要求见上方「大纲」章节。

### 2.2 从用户的兴趣出发做标注：高亮 / Hook

边读边挑选对用户最有价值的段落，创建两种标注：

- **highlight**：值得记住的原文段落（精彩论述、关键论据、反直觉观点）
- **hook**：逆向提问（参考上方「Hook」章节）

原则：
- **位置**：标注选择的段落应该是用户也想划线的，但是标注的文字最好能**对任何读者都有价值**；不要写成只给一个用户看的对话、不要包含太多特定用户的内容（这种高度个性化的内容应该放在步骤3的汇报中）
- **长度**：标注的原文可以是一个论述段落，也可以是一句话的金句，但都构成一个独立意义单元、能单独阅读
- **数量**：宁缺毋滥，选择最有价值、最有特点的片段；如果用户没有特别要求，一般 2～5条标注/1万字 比较合适。

```bash
curl -X POST "$GLYNK_API_URL/api/annotate/batch" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"annotations":[
    {"content_id":"...","type":"highlight",
     "anchor":{"type":"text","spans":["xxx-0-p12-s1","xxx-0-p12-s2"],"color":"ghost"},
     "text":"原文内容（用于 embedding 搜索）",
     "tags":["关键词"],"contextuality":"standalone"},
    {"content_id":"...","type":"hook",
     "anchor":{"type":"text","spans":["xxx-0-p12-s1","xxx-0-p12-s2"],"color":"ghost"},
     "text":"如何在信息不完整时做决策？",
     "tags":["决策","不确定性"],"contextuality":"standalone"}
  ]}'
```

## 步骤 3：向用户汇报

通读结束后，向用户汇报以下内容：

1. **内容概要**：一段话概括全文核心思想
2. **要点解读**：挑选全文中最重要的、3～5个与用户最相关的要点，标准是**如果用户亲自阅读，会被哪些文字触动、会如何划线？**，每个要点包括：
   - **导读**：为什么选这个要点（与用户的关联、前文概要）
   - **原文**：引用原文（不是一两句，而是一个完整的论述段落），让用户能直接读到作者的原话。用引用块（`>`）格式。
   - **链接**：`[阅读原文 →](https://brainow.link/read/{content_id}?loc={span_id})`
   要点之间可以有逻辑串联，从上到下读起来像一篇连贯的导读，而非孤立的摘录。
3. **整体评论**（可选）：如果你对这篇内容有整体层面的看法（比如与用户当前关注的方向有什么启发），可以在最后简要提出。

### 链接格式

```
https://brainow.link/read/{content_id}?loc={span_id}
```

示例：`https://brainow.link/read/a1b2c3d4?loc=a1b2c3d4-5-p12-s1`

用户点击后浏览器会打开阅读器并定位到对应段落。（需要用户在浏览器中输入token登陆）
