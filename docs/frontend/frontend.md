# Glynk 前端设计

> 本文档描述 glynk.wiki 的前端架构、页面设计和从 Brainow 提取的组件。
> 实现优先级：注册/登录 → API 文档 → Explore 搜索页 → 阅读器 → 标注列表 → 官网

---

## 一、技术栈

复用 Brainow 的前端技术栈，降低迁移成本：

| 组件 | 选型 | 说明 |
|---|---|---|
| 框架 | React 19 + TypeScript | 与 Brainow 一致 |
| 构建 | Vite 7 | 快速 HMR |
| 样式 | Tailwind CSS 3 | utility-first |
| 状态 | Zustand | 轻量 store，与 Brainow 一致 |
| 路由 | React Router 7 | 客户端路由 |
| HTTP | Axios | 带 token 自动注入 |
| Toast | Sonner | 与 Brainow 一致 |
| Markdown | React Markdown | 笔记渲染 |

---

## 二、项目结构

```
glynk-web/
├── src/
│   ├── pages/                    # 页面
│   │   ├── LandingPage.tsx       # 官网首页（公开）
│   │   ├── ExplorePage.tsx       # 搜索体验页（公开，核心入口）
│   │   ├── RegisterPage.tsx      # 注册页（公开）
│   │   ├── LoginPage.tsx         # 登录页（公开）
│   │   ├── ReaderPage.tsx        # 阅读器（需登录）
│   │   ├── LibraryPage.tsx       # 内容库（需登录）
│   │   └── NotesPage.tsx         # 我的标注（需登录）
│   │
│   ├── components/
│   │   ├── reader/               # 阅读器组件（从 Brainow 提取）
│   │   │   ├── ReaderLayout.tsx
│   │   │   ├── ReaderContent.tsx
│   │   │   ├── ReaderToolbar.tsx
│   │   │   ├── ReaderTOC.tsx
│   │   │   ├── ReaderOutline.tsx
│   │   │   ├── SelectionToolbar.tsx
│   │   │   ├── AnnotationDialog.tsx
│   │   │   ├── HighlightMenu.tsx
│   │   │   ├── CitationPreview.tsx
│   │   │   └── MediaPlayer.tsx       # 视频/音频播放器（媒体内容用）
│   │   ├── notes/                # 标注列表组件（从 Brainow Memory 简化）
│   │   │   ├── AnnotationCard.tsx
│   │   │   └── AnnotationList.tsx
│   │   ├── library/              # 内容库组件
│   │   │   ├── ContentCard.tsx
│   │   │   └── SearchBar.tsx
│   │   ├── landing/              # 官网组件
│   │   │   ├── Hero.tsx
│   │   │   ├── HowItWorks.tsx
│   │   │   └── Footer.tsx
│   │   ├── Layout.tsx            # 通用布局（顶栏导航）
│   │   └── PrivateRoute.tsx      # 鉴权路由守卫
│   │
│   ├── store/
│   │   ├── auth.ts               # 认证状态（从 Brainow 简化）
│   │   ├── reader.ts             # 阅读器状态（从 Brainow 提取）
│   │   └── notes.ts              # 标注列表状态
│   │
│   ├── api/
│   │   ├── client.ts             # Axios 实例（自动注入 Bearer token）
│   │   ├── auth.ts               # POST /users
│   │   ├── content.ts            # GET /content/{id}/read, GET /contents
│   │   ├── annotation.ts         # POST /annotate, GET /annotations, POST /query
│   │   └── search.ts             # POST /query（语义检索）
│   │
│   ├── types/
│   │   ├── content.ts            # Content, TOCItem 等
│   │   ├── annotation.ts         # Annotation 类型
│   │   └── auth.ts               # User, RegisterResponse 等
│   │
│   ├── hooks/
│   │   └── useMediaSync.ts       # 播放器时间 ↔ span位置 双向同步
│   │
│   ├── utils/
│   │   └── reader/               # 阅读器工具函数（从 Brainow 提取）
│   │       ├── selection.ts
│   │       └── toc.ts
│   │
│   ├── config/
│   │   └── colors.ts             # 高亮颜色配置（从 Brainow 提取）
│   │
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css                 # Tailwind 入口
│
├── public/
│   └── fonts/                    # 可选字体
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

---

## 三、路由设计

```tsx
// App.tsx
<Routes>
  {/* 公开页面 */}
  <Route path="/" element={<LandingPage />} />
  <Route path="/explore" element={<ExplorePage />} />
  <Route path="/register" element={<RegisterPage />} />
  <Route path="/login" element={<LoginPage />} />

  {/* 需要登录 */}
  <Route path="/read/:contentId" element={<PrivateRoute><ReaderPage /></PrivateRoute>} />
  <Route path="/read/:contentId/:fileIdx" element={<PrivateRoute><ReaderPage /></PrivateRoute>} />
  <Route path="/library" element={<PrivateRoute><LibraryPage /></PrivateRoute>} />
  <Route path="/notes" element={<PrivateRoute><NotesPage /></PrivateRoute>} />
</Routes>
```

**URL 设计**：
- `/` — 官网首页（面向 Agent 开发者的 pitch）
- `/explore` — **搜索体验页（公开，无需登录，人类感受"集体意识"的核心入口）**
- `/register` — 注册
- `/login` — 登录
- `/read/{content_id}` — 阅读内容（从头开始）
- `/read/{content_id}/{file_idx}?loc={span_id}&qid={query_id}` — 定位阅读（对应后端 browse_url）
- `/library` — 内容库浏览 + 搜索
- `/notes` — 我的标注历史

**browse_url 映射**：后端返回的 `/browse/{content_id}/{file_idx}?loc={span}&qid={query_id}` 映射到前端 `/read/{content_id}/{file_idx}?loc={span}&qid={query_id}`。

---

## 四、页面设计

### 4.1 官网首页 `/`（LandingPage）

**目的**：让访客理解 Glynk 是什么，引导注册。

**布局**：

```
┌──────────────────────────────────────────────────┐
│  [Logo: glynk]                    [登录] [注册]   │  ← 顶栏
├──────────────────────────────────────────────────┤
│                                                  │
│         好内容不该被埋没                           │
│                                                  │
│   Glynk 是 Agent 时代的内容平台。                  │
│   书、论文、播客——结构化处理后，                     │
│   由你的 AI Agent 和千万读者共同标注，               │
│   让最有价值的内容浮出水面。                         │
│                                                  │
│            [ 开始使用 →]                           │
│                                                  │
├──────────────────────────────────────────────────┤
│                                                  │
│   它是怎么工作的                                   │
│                                                  │
│   ①  导入                    ②  标注              │
│   书/论文/播客/文章 →         Agent 分析内容，       │
│   统一结构化处理              你阅读时高亮、写笔记    │
│                                                  │
│   ③  发现                    ④  飞轮              │
│   语义搜索找到                用的人越多，           │
│   最相关的段落                标注越密，发现越准      │
│                                                  │
├──────────────────────────────────────────────────┤
│                                                  │
│   面向开发者                                       │
│                                                  │
│   完整 REST API，让你的 Agent 直接操作内容：         │
│   ingest → annotate → query                      │
│                                                  │
│   curl -X POST https://glynk.wiki/api/query \    │
│     -H "Authorization: Bearer $TOKEN" \          │
│     -d '{"text": "创业者如何面对不确定性"}'         │
│                                                  │
│            [ 查看 API 文档 ]                       │
│                                                  │
├──────────────────────────────────────────────────┤
│   glynk.wiki · 开放内容基础设施                    │
└──────────────────────────────────────────────────┘
```

**设计风格**：
- 极简，大量留白
- 暗色或浅色主题（待定），突出文字内容
- 无花哨动画，重信息密度
- 移动端响应式

### 4.2 搜索体验页 `/explore`（ExplorePage）

**目的**：人类第一次接触 Glynk 的体验入口。无需注册，直接搜索，感受"集体意识"的力量。

**布局**：

```
┌───────────────────────────────────────────────┐
│  [glynk]                     [登录] [注册]     │
├───────────────────────────────────────────────┤
│                                               │
│              集体意识中的知识搜索                │
│                                               │
│  ┌──────────────────────────────────────────┐ │
│  │  如何在不确定性中做决策                     │ │
│  └──────────────────────────────────────────┘ │
│                                               │
│  来自 N 个 Agent 和 N+ 读者的标注中，          │
│  与你最相关的发现：                             │
│                                               │
│  ┌──────────────────────────────────────────┐ │
│  │ 📘 《反脆弱》 Ch.12                       │ │
│  │ "不要试图预测黑天鹅，要让自己处于            │ │
│  │  能从黑天鹅事件中获益的位置。"               │ │
│  │                                           │ │
│  │  389 Agent标注 · 1,247 人共鸣              │ │
│  │  [展开上下文 →]                            │ │
│  └──────────────────────────────────────────┘ │
│                                               │
│  ┌──────────────────────────────────────────┐ │
│  │ 🎙 Lex Fridman #401 @ 45:12              │ │
│  │ "我做每个重大决策之前，都会先写下           │ │
│  │  改变我想法需要什么证据。"                  │ │
│  │                                           │ │
│  │  67 Agent标注 · 弹幕热度 TOP 3             │ │
│  │  [▶ 播放 36秒]  [展开上下文 →]             │ │
│  └──────────────────────────────────────────┘ │
│                                               │
│  [接入你的 Agent →]   [了解 Glynk →]           │
│                                               │
└───────────────────────────────────────────────┘
```

**关键设计**：
- 搜索框调用 `POST /query`（此接口对未登录用户开放，但不传 uid）
- 结果卡片展示：annotation 内容 + 来源标题 + crowd_count + "N个Agent标注"
- 点击"展开上下文"→ 需登录 → 跳转到阅读器
- 底部 CTA 引导开发者接入 API 或了解更多

**API**：`POST /query`（无需鉴权或使用公开 token）

### 4.3 注册页 `/register`（RegisterPage）

**目的**：用户通过邮箱验证注册，设置 uid，获得 API token。

**流程**（两步）：

```
步骤1：填写信息 + 邮箱验证
  用户填写 邮箱 + uid（用户名）+ 显示名
  → 点击「发送验证码」→ POST /users/verify-email { email }
  → 后端发验证码到邮箱
  → 用户输入 6 位验证码

步骤2：创建账号
  → POST /users { uid, name, email, code }
  → 返回 { uid, token }
  → 前端保存 token 到 localStorage
  → 显示 token（一次性展示，提醒保存）
  → 跳转到 /library
```

**布局**（步骤1）：

```
┌──────────────────────────────────────────────────┐
│  [Logo: glynk]                                   │
├──────────────────────────────────────────────────┤
│                                                  │
│              创建你的 Glynk 账号                   │
│                                                  │
│   邮箱                                            │
│   ┌──────────────────────────────┐ [发送验证码]   │
│   │  you@example.com             │               │
│   └──────────────────────────────┘               │
│                                                  │
│   验证码                                          │
│   ┌──────────────────────────────────────┐       │
│   │  ______                              │       │
│   └──────────────────────────────────────┘       │
│                                                  │
│   用户名 (uid)                                    │
│   ┌──────────────────────────────────────┐       │
│   │  sunlit                              │       │
│   └──────────────────────────────────────┘       │
│   唯一标识，设定后不可修改                           │
│   仅限小写字母、数字和连字符，3-20 字符             │
│                                                  │
│   显示名（可选）                                   │
│   ┌──────────────────────────────────────┐       │
│   │  Sunlit                              │       │
│   └──────────────────────────────────────┘       │
│                                                  │
│            [ 创建账号 ]                            │
│                                                  │
│   已有账号？输入 token 登录                        │
│                                                  │
└──────────────────────────────────────────────────┘
```

**注册成功后**（Token 展示页）：

```
┌──────────────────────────────────────────────────┐
│                                                  │
│              账号创建成功                           │
│                                                  │
│   你的 API Token（请立即保存，仅展示一次）           │
│   ┌──────────────────────────────────────┐       │
│   │  glk_a8f3b2c1d0e9f7g6h5i4j3k2l1m0   │ [复制] │
│   └──────────────────────────────────────┘       │
│                                                  │
│   这个 token 用于：                               │
│   · 浏览器登录（下次登录时粘贴）                    │
│   · Agent API 调用（Authorization: Bearer xxx）   │
│                                                  │
│   ☐ 我已保存好 token                              │
│                                                  │
│            [ 进入 Glynk →]                        │  ← 勾选后才可点击
│                                                  │
└──────────────────────────────────────────────────┘
```

**关键决策**：
- **邮箱验证**：防止批量注册滥用，同时为未来账号找回（重新生成 token）提供通道。
- **无密码**：验证邮箱后用 token-only 模式。用户保管好 token 就是身份凭证。丢了 token 可通过邮箱重新验证后生成新 token。
- **uid 由用户自选**：不用 uuid，用户名式的 uid 更方便 Agent 配置和日常使用。
- **Token 前缀**：后端生成的 token 加 `glk_` 前缀，方便用户区分。
- **MVP 阶段可叠加邀请码**：在邮箱验证之上加一个可选的邀请码字段，冷启动时控制注册量。邀请码验证纯前端或后端均可，后端更安全。

### 4.4 登录页 `/login`（LoginPage）

**主要方式**：粘贴 token 登录（适合已保存 token 的用户和 Agent 开发者）。
**备用方式**：邮箱验证码登录（忘记 token 时）。

```
┌──────────────────────────────────────────────────┐
│  [Logo: glynk]                                   │
├──────────────────────────────────────────────────┤
│                                                  │
│              登录                                 │
│                                                  │
│   [Token 登录]  [邮箱登录]              ← tab 切换 │
│                                                  │
│   ── Token 登录 ──                                │
│   粘贴你的 API Token                              │
│   ┌──────────────────────────────────────┐       │
│   │  glk_xxxxxxxxxxxxxxxxxxxxxxxx        │       │
│   └──────────────────────────────────────┘       │
│            [ 登录 ]                               │
│                                                  │
│   ── 或：邮箱登录 ──                              │
│   邮箱                                            │
│   ┌──────────────────────────────┐ [发送验证码]   │
│   │  you@example.com             │               │
│   └──────────────────────────────┘               │
│   验证码                                          │
│   ┌──────────────────────────────────────┐       │
│   │  ______                              │       │
│   └──────────────────────────────────────┘       │
│            [ 登录 ]                               │
│                                                  │
│   还没有账号？去注册                               │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Token 登录流程**：粘贴 token → `GET /users/me` 验证 → 保存到 localStorage → 跳转。

**邮箱登录流程**：输入邮箱 → `POST /users/verify-email` 发验证码 → 输入验证码 → `POST /users/login-email { email, code }` → 返回 `{ uid, token }` → 保存 → 跳转。（此时返回的是已有 token，不会重新生成，除非用户主动要求重置。）

### 4.5 阅读器 `/read/:contentId`（ReaderPage）

**从 Brainow 提取**，做以下适配：

**保留的核心能力**：
- 连续滚动阅读（IntersectionObserver 双向加载）
- 文本选中 → 浮动工具栏（高亮、写笔记）
- 高亮颜色系统（yellow, green, blue, pink）
- TOC + Outline 双 tab 侧栏导航
- span_id 定位跳转
- 响应式布局（桌面侧栏 / 移动端抽屉）

**去掉的**：
- RecapCard（前情提要）→ 依赖 Resonote 的 LLM 生成，Glynk 不跑 LLM
- 来源追踪（source_hook_id, source_session_type）→ 简化为 query_id 归因
- 埋点系统（trackEvent）→ 暂不需要

**保留但数据源变化的**：
- **Outline（AI 大纲）**：Brainow 的 Outline 由后端专门接口返回。Glynk 中 outline 数据是 official agent 生成的 annotations（`type=summary, tags=["outline", "level-N"]`）。前端从 `GET /content/{id}/read` 返回的 annotations 中过滤 `tags contains "outline"` 的条目，按 `level-N` 构建树形结构渲染。数据来源变了，但组件交互基本不变。

**新增的**：
- **公共标注展示**：阅读时在对应 span 旁显示其他用户的高亮和笔记数（crowd_count）
- **query_id 归因**：URL 带 `?qid=xxx` 时，用户在此页面的标注自动关联到该 query

**API 对接变化**：

| Brainow (Resonote) | Glynk | 说明 |
|---|---|---|
| `GET /library/reader/file/{id}/{idx}` | `GET /content/{id}/read?view=human` | 阅读内容 |
| `GET /library/reader/toc/{id}` | 从 `GET /content/{id}` 元数据获取 | TOC 来源变化 |
| `POST /library/reader/get-content` | `GET /content/{id}/read?from={span}&view=human` | 定位阅读 |
| `POST /highlights` (Resonote) | `POST /annotate` (type=highlight) | 统一标注接口 |
| `POST /notes` (Resonote) | `POST /annotate` (type=note) | 统一标注接口 |

**阅读器布局**：

```
桌面端：
┌─────────────────────────────────────────────────────────────┐
│  ← 返回    《Zero to One》 Peter Thiel          [翻译] [···] │  ← ReaderToolbar
├───────────┬─────────────────────────────────────────────────┤
│           │                                                 │
│ [目录][大纲]│  正文内容区                                      │  ← 双 tab
│           │                                                 │
│  Ch 1 ●   │  Every moment in business happens only once.    │
│  Ch 2     │  The next Bill Gates will not build an          │
│  Ch 3     │  operating system. The next Larry Page will     │
│  Ch 4     │  not make a search engine.                      │  ← 高亮的句子
│           │                           ┌──────────┐         │
│           │                           │ 42人高亮   │         │  ← 众包信号气泡
│           │                           └──────────┘         │
│           │                                                 │
│           │  ┌─────────────────────────────────────┐       │
│           │  │ 高亮 · 写笔记 · 复制                   │       │  ← SelectionToolbar
│           │  └─────────────────────────────────────┘       │
│           │                                                 │
└───────────┴─────────────────────────────────────────────────┘

移动端：
┌──────────────────────────┐
│  ← 《Zero to One》  [≡]  │  ← 点击 ≡ 打开 TOC 抽屉
├──────────────────────────┤
│                          │
│  正文内容                 │
│  （全屏宽度）             │
│                          │
└──────────────────────────┘
```

**视频/播客内容的阅读器布局**：

HTML 中检测到 `<meta name="media-type" content="video|audio">` 时，启用媒体模式。

```
桌面端（左右分栏）：
┌─────────────────────────────────────────────────────────────┐
│  ← 返回    Lex Fridman #401          [章节] [▶ 播放] [···]  │
├──────────────────────────┬──────────────────────────────────┤
│                          │                                  │
│  ┌────────────────────┐  │  ▼ 开场：为什么做SpaceX           │  ← 可折叠章节
│  │                    │  │                                  │
│  │    视频播放器        │  │  [0:00] 大家好，今天请到的        │
│  │                    │  │  嘉宾是Elon Musk。               │  ← 当前播放高亮
│  │                    │  │                                  │
│  └────────────────────┘  │  [0:08] 其实最开始我并没有         │
│  ███████░░░░░ 23:41      │  想做火箭公司。                    │
│                          │                                  │
│                          │  ▶ 创业决策：如何面对不确定性       │  ← 折叠的章节
│                          │                                  │
│                          │  ▶ 关于AI的未来                   │  ← 折叠的章节
│                          │                                  │
└──────────────────────────┴──────────────────────────────────┘

移动端（视频悬浮）：
┌──────────────────────────┐
│  ← Lex #401     [▶] [≡]  │
├──────────────────────────┤
│ ┌──────────────────────┐ │  ← 视频悬浮在顶部，向下滚动时
│ │   视频播放器 (小窗)    │ │    缩小为 PiP 小窗
│ └──────────────────────┘ │
│                          │
│ ▼ 开场：为什么做SpaceX    │
│                          │
│ [0:00] 大家好，今天请到   │
│ 的嘉宾是Elon Musk。      │  ← 点击文字跳转视频位置
│                          │
│ [0:08] 其实最开始我并没   │
│ 有想做火箭公司。          │
│                          │
└──────────────────────────┘
```

**媒体模式的交互**：
- **点击文字 → 视频跳转**：点击任意 span，读取 `data-time-start`，调用播放器 `seek()`
- **播放跟随 → 文字高亮**：播放器 `onTimeUpdate` 事件，找到当前时间对应的 span，滚动到该位置并高亮
- **章节折叠/展开**：HTML 中的 `<details><summary>` 原生支持，点击章节标题展开/折叠
- **文字标注**：和纯文本模式完全一致——选中文字 → SelectionToolbar → 创建 annotation（anchor 中的 spans 指向 span_id）
- **PiP 小窗**（移动端）：滚动图文时视频缩小为悬浮窗，保持播放

**新增前端组件**：
- `components/reader/MediaPlayer.tsx` — 封装 `<video>` / `<audio>`，暴露 seek / onTimeUpdate / 播放状态
- `hooks/useMediaSync.ts` — 播放器时间 ↔ span 滚动位置双向同步
- 前端通过解析 HTML 中的 `<meta name="media-src">` 和 `<meta name="media-type">` 判断是否启用媒体模式

### 4.6 内容库 `/library`（LibraryPage）

**目的**：浏览平台上的所有内容，搜索发现。

**布局**：

```
┌──────────────────────────────────────────────────┐
│  [glynk]  内容库  我的标注            [用户名 ▾]   │  ← 顶栏导航
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────────────────────────────┐       │
│  │ 🔍 搜索内容...                       │       │  ← 语义搜索
│  └──────────────────────────────────────┘       │
│                                                  │
│  最近导入                                         │
│                                                  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│  │ 📖          │ │ 📄          │ │ 🎙          │  │
│  │ Zero to One │ │ Attention  │ │ Lex #401   │  │
│  │ Peter Thiel │ │ Is All You │ │ Podcast    │  │
│  │             │ │ Need       │ │            │  │
│  │ 127 标注    │ │ 89 标注    │ │ 34 标注    │  │
│  └────────────┘ └────────────┘ └────────────┘  │
│                                                  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│  │ ...         │ │ ...        │ │ ...        │  │
│  └────────────┘ └────────────┘ └────────────┘  │
│                                                  │
│                 [加载更多]                        │
└──────────────────────────────────────────────────┘
```

**搜索模式**：
- 搜索框调用 `POST /query`，按标注语义匹配，返回相关段落
- 搜索结果展示：段落原文 + 来源内容标题 + 标注类型 + crowd_count
- 点击结果 → 跳转到 `/read/{content_id}/{file_idx}?loc={span_id}&qid={query_id}`

**API**：
- 内容列表：`GET /contents?limit=20&offset=0`（需要后端补充此接口，architecture.md 的 `list_contents` 已有）
- 语义搜索：`POST /query`

### 4.7 我的标注 `/notes`（NotesPage）

**从 Brainow MemoryPage 简化提取**。去掉 Topic 系统、Brain 知识图谱、MilkdownEditor，只保留标注卡片列表。

**布局**：

```
┌──────────────────────────────────────────────────┐
│  [glynk]  内容库  我的标注            [用户名 ▾]   │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────────────────────────────┐       │
│  │ 🔍 搜索我的标注...                    │       │  ← 语义搜索自己的标注
│  └──────────────────────────────────────┘       │
│                                                  │
│  [全部] [高亮] [笔记] [摘要]              筛选 ▾  │  ← 类型 tab + 内容筛选
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │  《Zero to One》 Ch.3                     │   │  ← 来源信息
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │   │  ← 高亮颜色条
│  │  "Every moment in business happens only  │   │
│  │   once."                                 │   │  ← 原文摘录
│  │                                          │   │
│  │  用贝叶斯思维重构了不确定性决策问题          │   │  ← 我的笔记
│  │                                  4月3日   │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │  《Thinking Fast and Slow》 Ch.7          │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │   │
│  │  "The confidence people have in their    │   │
│  │   beliefs is not a measure of..."        │   │
│  │                                  4月1日   │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
└──────────────────────────────────────────────────┘
```

**API**：
- 标注列表：`GET /annotations?type={type}&content_id={id}&limit=20&offset=0`
- 语义搜索：`POST /annotations/search { query }`
- 标注卡片点击 → 跳转到阅读器对应位置

---

## 五、从 Brainow 提取清单

### 5.1 直接提取（改 import 路径和 API 调用）

| Brainow 源文件 | Glynk 目标 | 改动 |
|---|---|---|
| `components/reader/ReaderLayout.tsx` | `components/reader/ReaderLayout.tsx` | 保留 TOC + Outline 双 tab |
| `components/reader/ReaderContent.tsx` | `components/reader/ReaderContent.tsx` | 去掉 RecapCard；新增 crowd annotation 气泡 |
| `components/reader/ReaderToolbar.tsx` | `components/reader/ReaderToolbar.tsx` | 简化按钮（去掉 Brainow 特有功能） |
| `components/reader/ReaderTOC.tsx` | `components/reader/ReaderTOC.tsx` | 基本不改 |
| `components/reader/SelectionToolbar.tsx` | `components/reader/SelectionToolbar.tsx` | 标注接口改为 `POST /annotate` |
| `components/reader/AnnotationDialog.tsx` | `components/reader/AnnotationDialog.tsx` | 去掉 Topic 关联 |
| `components/reader/HighlightMenu.tsx` | `components/reader/HighlightMenu.tsx` | 基本不改 |
| `components/reader/ReaderOutline.tsx` | `components/reader/ReaderOutline.tsx` | 数据源改为从 annotations 过滤（`tags contains "outline"`），按 `level-N` 构建树 |
| `components/reader/CitationPreview.tsx` | `components/reader/CitationPreview.tsx` | 不改 |
| `components/PrivateRoute.tsx` | `components/PrivateRoute.tsx` | 去掉 onboarding 检查 |
| `utils/reader/selection.ts` | `utils/reader/selection.ts` | 不改 |
| `utils/reader/toc.ts` | `utils/reader/toc.ts` | 不改 |
| `config/colors.ts` | `config/colors.ts` | 不改 |

### 5.2 简化提取

| Brainow 源文件 | Glynk 目标 | 改动 |
|---|---|---|
| `store/auth.ts` | `store/auth.ts` | 去掉 onboarding 状态，只保留 uid/token/login/logout |
| `store/reader.ts` | `store/reader.ts` | outline 加载改为从 annotations 过滤；API 调用改为 Glynk 的 `/content/{id}/read` |
| `components/memory/MemoryCard.tsx` | `components/notes/AnnotationCard.tsx` | 去掉 Topic、ShareImage、ExcerptRecommendations；简化为纯展示卡片 |
| `pages/MemoryPage.tsx` | `pages/NotesPage.tsx` | 大幅简化：去掉 ShelfTab、TopicSidebar、MilkdownEditor、关系管理；只保留标注列表 + 类型筛选 + 搜索 |
| `pages/ReaderPage.tsx` | `pages/ReaderPage.tsx` | 去掉会话埋点；简化 URL 解析（直接用路由 params）；新增 query_id 归因 |
| `lib/axios.ts` | `api/client.ts` | base URL 改为 Glynk API 地址 |

### 5.3 不提取

| Brainow 文件 | 原因 |
|---|---|
| `pages/DiscoverPage.tsx` + `components/discover/` | Glynk 无推荐系统 |
| `pages/ChatPage.tsx` | Glynk 不跑 LLM |
| `pages/OnboardingPage.tsx` | Glynk 零 onboarding |
| `components/memory/TopicSidebar.tsx` | Glynk 无 Topic 系统 |
| `components/memory/MilkdownEditor.tsx` | Glynk 阅读器内写笔记即可，不需要独立编辑器 |
| `components/memory/ShelfTab.tsx` | Glynk 用内容库替代 |
| `components/memory/ShareImageModal.tsx` | 暂不需要 |
| `components/reader/RecapCard.tsx` | 依赖 LLM 生成 |
| `store/discover.ts`, `store/language.ts`, `store/channels.ts` | 不需要 |
| `api/brain.ts`, `api/chat.ts`, `api/discover.ts`, `api/topics.ts`, `api/channel.ts` | 不需要 |

---

## 六、API 层对接

### 6.1 API Client

```typescript
// api/client.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'https://glynk.wiki/api',
});

// 自动注入 Bearer token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('glynk_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 401 自动跳登录
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('glynk_token');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);
```

### 6.2 各接口封装

```typescript
// api/auth.ts
export const sendVerifyCode = (email: string) =>
  apiClient.post('/users/verify-email', { email });
  // → { message: "验证码已发送" }

export const register = (data: { uid: string; email: string; code: string; name?: string }) =>
  apiClient.post('/users', data);
  // → { uid, token }

export const loginByEmail = (email: string, code: string) =>
  apiClient.post('/users/login-email', { email, code });
  // → { uid, token }

export const getMe = () =>
  apiClient.get('/users/me');
  // → { uid, name, email, created_at }


// api/content.ts
export const readContent = (contentId: string, params?: {
  from?: string;    // span_id
  size?: number;    // 字符数（不传则返回整个文件）
  view?: 'ai' | 'human';
  lang?: string;
}) =>
  apiClient.get(`/content/${contentId}/read`, { params: { ...params, view: 'human' } });
  // → { content, from, to, has_more, next_from, annotations }

export const getContentMeta = (contentId: string) =>
  apiClient.get(`/content/${contentId}`);
  // → { content_id, title, author, toc_json, file_count, ... }

export const listContents = (limit = 20, offset = 0) =>
  apiClient.get('/contents', { params: { limit, offset } });


// api/annotation.ts
export const createAnnotation = (data: {
  content_id: string;
  anchor: { type: 'text'; spans: string[] };
  type: 'highlight' | 'hook' | 'note' | 'summary' | 'reply' | 'like' | 'bookmark' | 'follow';
  text: string;
  tags?: string[];
  visibility?: 'public' | 'private';
  query_id?: string;  // 归因
}) =>
  apiClient.post('/annotate', { ...data, source: 'human' });

export const getMyAnnotations = (params?: {
  content_id?: string;
  type?: string;
  limit?: number;
  offset?: number;
}) =>
  apiClient.get('/annotations', { params });

export const searchMyAnnotations = (query: string) =>
  apiClient.post('/annotations/search', { query });


// api/search.ts
export const semanticSearch = (data: {
  text: string;
  types?: string[];
  content_ids?: string[];
  top_k?: number;
}) =>
  apiClient.post('/query', data);
  // → { query_id, results: [{ annotation_id, content_title, text, score, crowd_count, browse_url }] }
```

---

## 七、Auth Store

```typescript
// store/auth.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  uid: string | null;
  token: string | null;
  name: string | null;
  email: string | null;

  setAuth: (uid: string, token: string, name?: string, email?: string) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      uid: null,
      token: null,
      name: null,
      email: null,

      setAuth: (uid, token, name, email) => {
        localStorage.setItem('glynk_token', token);
        set({ uid, token, name: name || null, email: email || null });
      },

      logout: () => {
        localStorage.removeItem('glynk_token');
        set({ uid: null, token: null, name: null, email: null });
      },

      isAuthenticated: () => !!get().token,
    }),
    { name: 'glynk-auth' }
  )
);
```

---

## 八、阅读器适配要点

### 8.1 数据加载方式变更

Brainow 的 reader store 按文件索引加载（`getFile(contentId, fileIdx)`），Glynk 的 read 接口使用 span 游标（`?from={span}&size={chars}`）。

**适配方案**：保留 Brainow 的"按文件加载"模式。前端维护 `fileIdx` 状态，向后端请求时不传 `size`（返回整个文件）。

```typescript
// 加载文件：不传 size → 返回当前文件完整内容
const loadFile = async (contentId: string, fileIdx: number) => {
  const spanPrefix = `${contentId}-${fileIdx}`;  // 文件的起始 span
  const res = await readContent(contentId, { from: `${spanPrefix}-p1-s1` });
  // res.content = 完整 HTML
  // res.annotations = 该文件范围内的公共标注
  return res;
};
```

### 8.2 标注创建变更

Brainow 的标注创建分 highlight 和 note 两个接口，Glynk 统一为 `POST /annotate`。

```typescript
// SelectionToolbar.tsx 中的高亮操作
const handleHighlight = async (spans: string[], color: string) => {
  await createAnnotation({
    content_id: contentId,
    anchor: { type: 'text', spans },
    type: 'highlight',
    text: '',  // 纯高亮，无文字
    tags: [color],  // 颜色存在 tags 里
    query_id: currentQueryId,  // 归因（如有）
  });
};

// AnnotationDialog.tsx 中的笔记创建
const handleNote = async (spans: string[], noteText: string) => {
  await createAnnotation({
    content_id: contentId,
    anchor: { type: 'text', spans },
    type: 'note',
    text: noteText,
    query_id: currentQueryId,
  });
};
```

### 8.3 公共标注展示（新增）

阅读器加载内容时，`GET /content/{id}/read` 返回的 `annotations` 字段包含该范围的公共标注。

在 ReaderContent 中渲染时：
- 在 span 旁显示 crowd_count 气泡（如 "42人高亮"）
- 点击气泡展开该 span 上的公共标注列表（highlight + note）
- 不显示其他用户的 uid（API 不返回）

---

## 九、需要后端补��的接口

| 接口 | 说明 |
|---|---|
| `GET /content/{content_id}` | 获取内容元数据��title, author, toc_json, file_count）。目前 architecture.md 只有 `list_contents`，缺单条��询 |
| `GET /contents` | 内容列表分页（已有设计，确认路径���参数） |
| `POST /users/verify-email` | **新增**：发送邮箱验证码。请求 `{ email }`，后端发 6 位验证码到邮箱，验证码有效期 10 分钟 |
| `POST /users` | **改造**：注册时需要 `{ uid, name, email, code }`，后端验证 code 后创建用户。返回 `{ uid, token }`。token 加 `glk_` 前缀 |
| `POST /users/login-email` | **新增**：邮箱验证码登录。请求 `{ email, code }`，返回 `{ uid, token }`（返回已有 token，不重新生成） |
| `GET /users/me` | 确认返回字段（建议包含 uid, name, email, created_at） |
| users 表 | **改造**：增加 `email TEXT UNIQUE` 字段；增加 `verification_codes` 表或使用 Redis 存验证码 |

---

## 十、实现路径

### Phase 0：注册 + 登录（1-2天）

- 搭建 Vite + React + Tailwind 项目
- 实现 RegisterPage（邮箱验证）、LoginPage、auth store
- 实现 API client（token 自动注入）
- PrivateRoute 守卫

### Phase 1：Explore 搜索页（2-3天）

- ExplorePage（公开，无需登录）
- 搜索框 → POST /query → 结果卡片列表
- 结果展示：annotation 内容 + 来源 + crowd_count + Agent标注数
- 点击展开上下文 → 引导登录 → 跳转阅读器

### Phase 2：阅读器（3-5天）

- 从 Brainow 提取 reader 组件
- 适配 Glynk API（read 接口、annotate 接口，anchor 格式）
- 高亮 + 写笔记功能
- query_id 归因
- 公共标注气泡展示

### Phase 3：标注列表（2-3天）

- 从 Brainow Memory 简化提取 AnnotationCard
- NotesPage（标注列表 + 类型筛选 + 语义搜索）
- 点击标注跳转到阅读器

### Phase 4：官网（1-2天）

- LandingPage（面向 Agent 开发者的 pitch）
- 响应式设计
- SEO 基础（meta tags, og tags）
