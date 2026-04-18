# Glynk 前端需求

> 给前端工程师 · 2026-04-12
> 配套阅读：`glynk-data-model.md`、`glynk-overview.md`

---

## 一、背景

Glynk 后端已完成 Entity / Unit / Anchor 三表 + Anchor API + 讨论线程支持 + embedding 跳过逻辑。前端基础迁移已完成（端点改为 `/units/*` 和 `/anchors/*`，类型层有 compat shape）。

本文档列出剩余的前端需求——只说**要什么**和**后端提供什么**，实现方式由你定。

---

## 二、新增功能

### 2.1 "放下"：用户直接创建 Unit

**用户场景**：用户想随手记一个想法 / 一段笔记 / 一个半成品命题——这个想法不一定挂在某本书的某段话上，它就是用户自己的一个独立 Unit。

**期望行为**：
- 用户能写一段文本（多行；可选 markdown 渲染）
- 可选附加标签
- 提交后即时反馈（"已放下"）
- 用户能看到自己放下过的 Units

**后端提供的 API**：

```
POST /thoughts
  Body: { text: string, metadata?: object }
  Response: { id: string }
  Auth: required
```

短文本（去标点 emoji 后 < 30 字符）后端会自动跳过 embedding，不影响功能。

（老路径 `POST /units` 是 deprecated alias，新代码请用 `/thoughts` —— 这样能把"放想法"和"发 publication"两种 publishing 动作在 API 上区分清楚。）

### 2.2 讨论线程

**用户场景**：用户在 Reader 里对某段话有想法，想发表一条回复；其他人/Agent 也可以对这段话回复，或者对别人的回复做嵌套回复。

**期望行为**：
- Reader 里点击 span 时，除现有的 highlight / note / hook 外，提供"回复"入口
- 该 span 已有讨论时显示标记（如 "N 人讨论"）
- 展开后看到树状结构的对话——用户能区分谁回复谁
- 每一层都能继续回复
- 深度无后端限制；前端选择展示策略（缩进 / 折叠 / 独立页面均可）

**数据模型规则**（详见 `glynk-data-model.md` "Anchor 使用模式：讨论线程"）：

每条回复都是一个独立 Unit，挂一条 Anchor：
- `target_span` = 话题锚（原文某段），**所有层级的 reply 都一致**
- `metadata.in_reply_to` = 父 reply 的 Unit id（一级回复留空）

一次扁平查询（按 `target_span` + `role='reply'`）即可拿到 thread 全部节点，前端在 metadata 上 group 构树。

**后端提供的 API**：

```
POST /anchors
  Body: {
    target_unit:  string         // 被回复内容所在 Unit
    target_span:  string?        // 被回复的具体段落
    role:         'reply'
    text:         string         // 回复内容（可选——支持 emoji/图片-only 的 reply，body=optional）
    in_reply_to:  string?        // 父回复 Unit ID（一级回复留空）；后端会写到 anchor.metadata.in_reply_to
  }
  Response: { id, source_unit_id, role, target_unit, target_span, metadata, ... }
  Auth: required
```

```
GET /anchors/thread
  Query: target_unit, target_span
  Response: { annotations: [...] }

  返回该 span 下所有可见 anchor 的扁平列表，前端用 metadata.in_reply_to 构树。
```

**关键性质**：每条回复**都是独立 Unit**（有自己的 id、可独立搜索、可被第三方引用）。前端实现时不要把它当成"评论数据"，要当成"挂在 thread 里的一等 Unit"。

## 三、既有功能扩展

### 3.1 NotesPage：增加"想法"维度

**现状**：NotesPage 现在只展示 highlight / hook / note（都是依附内容的标注）。

**需要新增**：展示用户直接放下的 standalone Units（无 target_span / target_unit 的 authored Unit）。

可以是新 tab，也可以是同一列表的不同筛选——UX 决定。

**后端提供的 API**：

```
GET /units
  Query: origin='authored', author_id?, limit, offset
  Response: { units / contents: [...], total }
```

> 如果当前 `GET /units` 不支持 `author_id=me` 过滤或不支持只取 `origin=authored`，向后端提需求补端点（建议名 `GET /units/mine`）。

### 3.2 Reader：在 span 上增加"回复"入口

**现状**：Reader 的 span popover 已有 highlight / note / hook 操作。

**需要新增**：
- "回复 / 加入讨论"入口
- 该 span 已有讨论时显示数量标记
- 展开 thread 视图

**约束**：不破坏现有 highlight / note / hook 流程。

---

## 四、约束

- 支持深色主题
- 所有新增文案走 i18n
- 不破坏现有 reader / annotation / library 流程
- 后端 API 字段以 `glynk/api/*.py` 中的 router 为准（如本文档与代码不一致，以代码为准）

---

## 五、文档索引

| 你想了解 | 看这份 |
|---|---|
| 数据模型 / Unit / Anchor 字段含义 | `glynk-data-model.md` |
| reply 双 anchor 规则 / embedding 策略 | `glynk-data-model.md` |
| 整体设计原则、为什么这么设计 | `glynk-design-principles.md` |
| 项目背景、新体验 | `glynk-overview.md` |
| 后端 API 详情 | `glynk/api/*.py` 各 router |

---

## 六、可能需要后端补的接口

实现中如发现以下需求，向后端提：

- `GET /units` 支持 `author_id=me` 过滤（或新增 `GET /units/mine`）——支撑 NotesPage 想法 tab
- `GET /anchors` 支持 `target_span` 过滤——支撑 thread 视图查询
- `GET /anchors/thread?target_unit=X&target_span=Y` 一次返回完整树（如 N+1 性能不可接受）

---

## 七、有疑问

- 后端 API 字段 → 直接看 `glynk/api/*.py`
- UX 决定（thread 是侧边栏还是 popover、缩进多少层）→ 你做合理判断，后续可调
- 数据模型边界 → `glynk-data-model.md`
- 不在文档里的需求 → 找产品对齐
