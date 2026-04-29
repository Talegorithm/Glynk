---
name: glk-read
description: 帮用户阅读 Glynk 平台上的长内容（书/论文/文章），逐页阅读、生成标注和汇报。当用户发来 URL、文件、或指定内容让你阅读时使用。
---

# Glynk 阅读

帮用户阅读长内容，生成标注（hook / highlight）和大纲，最后向用户汇报。

前置：需要环境变量 `GLYNK_TOKEN`。`GLYNK_API_URL` 默认使用公共入口 `https://brainow.link`；如果手动设置，也应指向前端域名，由同域 `/api` 反代到后端，不要使用后端 IP 或本地端口。所有接口均需 `Authorization: Bearer $GLYNK_TOKEN`。

## 核心概念

### Span ID

每个句子都有唯一的 span ID：`{content_id}-{file_idx}-p{段落号}-s{句子号}`

示例：`a1b2c3d4-0-p15-s3` = 内容 a1b2c3d4，第 0 个文件，第 15 段，第 3 句。

Span ID 嵌入在 HTML 的 `<span id="...">` 中，用作所有标注的锚点。

### Anchor Role（阅读 skill 里常用的几种）

| role | body | 适用场景 |
|------|------|---------|
| `highlight` | 自动（= span 文本） | 标记"这段值得"，带颜色 |
| `hook` | required | 阅读中冒出的问题 / 洞察 |
| `note` | required | 自由笔记、引申、反驳 |
| `summary` | required | 整段/整篇的 TL;DR |

完整 role 列表（`reply` / `like` / `bookmark` / `follow` 等）见 `glynk/models.py` 的 `ROLE_SCHEMAS`。

### Anchor metadata 格式

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

---

## 步骤 1：获取内容

如果用户给了 URL 或文件路径，先发布为 publication：

```bash
# URL
curl -X POST "$GLYNK_API_URL/api/publications" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source":"用户给的URL"}'

# 本地文件（epub/pdf/html/md）
curl -X POST "$GLYNK_API_URL/api/publications/upload" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -F "file=@文件路径"
```

发布成功后获得 `content_id`（= Unit id），后续操作基于此 ID。

如果用户指定已有内容，先获取详情和目录：

```bash
curl "$GLYNK_API_URL/api/units/{content_id}" \
  -H "Authorization: Bearer $GLYNK_TOKEN"
# → {content_id, title, author, source_type, file_count, total_chars, toc, outline}
```

## 步骤 2：逐页阅读

用 read 接口逐页阅读（AI 视图 — 简化 HTML，省 token）：

```bash
# 首页
curl "$GLYNK_API_URL/api/units/{content_id}/read?size=20000" \
  -H "Authorization: Bearer $GLYNK_TOKEN"
# → {"content":"<html>...<span id='a1b2-0-p1-s1'>text</span>...</html>",
#    "from":"a1b2-0-p1-s1","to":"a1b2-0-p3-s5","char_count":17945,
#    "has_more":true,"next_from":"a1b2-0-p4-s1"}

# 翻页：用响应中的 next_from
curl "$GLYNK_API_URL/api/units/{content_id}/read?size=20000&from={next_from}" \
  -H "Authorization: Bearer $GLYNK_TOKEN"

# 读取完整文件（人类视图 — 带样式的完整 HTML）
curl "$GLYNK_API_URL/api/units/{content_id}/read" \
  -H "Authorization: Bearer $GLYNK_TOKEN"
```

用 `next_from` 翻页，直到 `has_more` 为 `false`。

阅读过程中做两件事：

### 2.1 积累大纲

在本地维护一个大纲结构。边读边更新，**读完全文后一次性提交**（不要边读边提交）。

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

### 2.2 从用户的兴趣出发做标注

边读边挑选对用户最有价值的段落，创建两种标注：

- **highlight**：值得记住的原文段落（精彩论述、关键论据、反直觉观点）
- **hook**：逆向提问（参考上方「Hook」章节）

**标注原则**：
- **位置**：标注选择的段落应该是用户也想划线的，但标注的文字最好能**对任何读者都有价值**；不要写成只给一个用户看的对话（高度个性化的内容放在步骤 3 的汇报中）
- **长度**：标注的原文可以是一个论述段落，也可以是一句话的金句，但都构成一个独立意义单元、能单独阅读
- **数量**：宁缺毋滥，选择最有价值、最有特点的片段；如果用户没有特别要求，一般 2～5 条标注/万字

每读几页，批量提交标注（每攒 ~20 条批量提交）：

```bash
curl -X POST "$GLYNK_API_URL/api/anchors/batch" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"anchors":[
    {"target_unit":"a1b2c3d4",
     "target_span":"a1b2c3d4-0-p12-s1",
     "role":"highlight",
     "metadata":{"type":"text","spans":["a1b2c3d4-0-p12-s1","a1b2c3d4-0-p12-s2"],"color":"ghost"},
     "text":"原文内容（用于 embedding 搜索）",
     "tags":["关键词"]},
    {"target_unit":"a1b2c3d4",
     "target_span":"a1b2c3d4-0-p5-s1",
     "role":"hook",
     "metadata":{"type":"text","spans":["a1b2c3d4-0-p5-s1","a1b2c3d4-0-p5-s2"],"color":"ghost"},
     "text":"如何在信息不完整时做决策？",
     "tags":["决策","不确定性"]}
  ]}'
# → {"created":2,"ids":["anc-xxx","anc-yyy"]}
```

## 步骤 3：读完后提交大纲

```bash
curl -X PUT "$GLYNK_API_URL/api/units/{content_id}/outline" \
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

# 获取已有大纲
curl "$GLYNK_API_URL/api/units/{content_id}/outline" \
  -H "Authorization: Bearer $GLYNK_TOKEN"
```

## 步骤 4：向用户汇报

通读结束后，向用户汇报以下内容：

1. **内容概要**：一段话概括全文核心思想
2. **要点解读**：挑选全文中最重要的、3～5 个与用户最相关的要点，标准是**如果用户亲自阅读，会被哪些文字触动、会如何划线？**，每个要点包括：
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

用户点击后浏览器会打开阅读器并定位到对应段落。

---

## 标注管理 API

```bash
# 创建单条标注
curl -X POST "$GLYNK_API_URL/api/anchors" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_unit":"a1b2c3d4",
    "target_span":"a1b2c3d4-0-p5-s1",
    "role":"hook",
    "metadata":{"type":"text","spans":["a1b2c3d4-0-p5-s1"],"color":"ghost"},
    "text":"如何在信息不完整时做决策？",
    "tags":["决策","不确定性"]
  }'

# 列出我的标注
curl "$GLYNK_API_URL/api/anchors?target_unit=a1b2c3d4&role=hook&limit=50" \
  -H "Authorization: Bearer $GLYNK_TOKEN"
# → {"annotations":[...],"total":150}

# 更新标注
curl -X PATCH "$GLYNK_API_URL/api/anchors/{anchor_id}" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"更新后的问题"}'

# 删除标注
curl -X DELETE "$GLYNK_API_URL/api/anchors/{anchor_id}" \
  -H "Authorization: Bearer $GLYNK_TOKEN"
```

## 使用建议

1. **用 `read?size=20000` 阅读** — 返回为 LLM 优化的简化 HTML，省 token
2. **批量提交标注** — 用 `/anchors/batch` 而非逐条创建
3. **用 `next_from` 跟踪阅读位置** — 每次响应告诉你下一页从哪开始
4. **Agent 使用 `ghost` 颜色** — 与用户使用的高亮区分
5. **Hook 服务于发现** — 写成别人会搜索的问题，而非内容摘要
6. **无特殊权限** — Agent 和任何第三方客户端使用完全相同的公开 API
