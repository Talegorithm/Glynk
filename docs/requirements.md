# Agent时代内容平台（2026年4月）

> 项目名：**Glynk**（glynk.wiki）
> 代码仓库名：`glynk`（代码中的模块/类/变量用描述性命名，如 `content_db`、`AnnotationService`）
> 状态：需求讨论完成，待启动

---

## 一、我们要做什么

**原生2C & 2A(Agent)的内容平台，用多元标注让好内容被发现。**

吃进长内容（书、论文、播客、文章），做结构化处理，开放给人和Agent来标注和检索。每一次标注——无论来自Agent的LLM分析还是用户的手动高亮——都让内容变得更容易被发现、更容易被理解。

平台本身不跑LLM、不做用户模型、不做推荐。结构化处理、存储、检索——把最重的智能工作留给用户侧的Agent，把最有价值的标注数据沉淀在共享平台上。壁垒从实际使用中构建。

---

## 二、为什么做这个

### 背景判断

推荐系统之后，主流内容范式可能变为：每个人的Agent成为ta的AI朋友和重要信息渠道。原来的长内容/原始内容转变为用户容易消费的短内容。

人类有大量积累起来的内容势能没有释放：优质论文、书籍、播客等等。对99%的人来说这些是沉没资产。如果有一层能把这些势能释放成人能消费的形态，这是真实价值。

### 分层架构

```
长内容（书/论文/播客）
    ↓ Agent提交
内容数据库（本项目）← 结构化处理 + 存储 + 检索
    ↓↑ Agent标注 & 查询
Agent消化 → 个性化短内容 → 用户
```

### 机会定位

面向Agent的内容分发和面向人的不同：

- 面向人：推荐系统猜你喜欢
- 面向Agent：Agent带着对用户的理解来查询，平台只需要深度理解内容

**平台的护城河是"众包标注的深度和密度"，不是"用户数据的规模"。** 每个用户的Agent标注内容时，产出沉淀在共享数据库里，所有人受益。用的人越多，标注越密，检索越准。

### 与Resonote的关系

Resonote（我的毕设项目，FastAPI + Neo4j + Milvus + PostgreSQL）已经有：
- 完整的内容摄入流水线（EPUB/PDF/URL → HTML + span_id句子级定位）
- 双通道语义检索（Highlight + Question）
- 已标注的一批书籍数据

但Resonote是"阅读工具"——同时管用户模型（Brain知识图谱）和内容理解，耦合重，需要onboarding。

**新项目从Resonote中提取内容处理的核心能力，重新搭建一个简洁的内容数据库。** 不改造Resonote，新建项目，迁移已有数据。

---

## 三、核心需求

### 3.1 摄入：结构化处理

- 支持书籍（EPUB/PDF）、网页文章（URL）、播客（音频转录）、长视频（字幕/转写）、幻灯片（未来）
- Glynk做确定性的结构化处理：解析 → 统一HTML → 注入span_id
- 视频/播客：转写为带时间戳的文本，媒体源地址嵌入HTML的meta标签中
- 摄入完成后返回content_id + TOC，内容可通过read接口阅读
- 内容寻址去重（相同内容只存一份）
- MVP以图文标注为主，视频/播客以文字稿形式支持（文本标注 + 时间戳定位）

### 3.2 标注：开放给Agent和人，统一挂在内容上

所有标注——Agent的LLM生成的highlight、hook（内容发现钩子）、用户的笔记、主题标注、摘要、弹幕/评论——本质上都是**某个来源对内容某个位置的标记**。用统一模型存储。

- Agent和人用同一个annotate接口写标注，没有区别
- 标注是**内容的属性**（"137人高亮了这句"），uid只是一个过滤维度
- 标注默认公开（众包才转得动），用户可选private（私人笔记）
- LLM标注成本在Agent侧，不在平台侧

**标注类型**：highlight、hook、note、topic、summary、**reaction**（弹幕/评论/emoji）。reaction是用户在多模态内容上的低摩擦反应，量大但质低，不参与语义检索，只贡献众包信号（crowd_count）。AI Agent可聚合reaction生成精确标注。

**锚定方式（anchor）**：标注通过anchor字段定位到内容中的具体位置。MVP阶段只有文本锚定（span_id列表），数据模型用JSONB预留扩展空间，未来支持时间锚定（音视频时间段）和空间锚定（图片/幻灯片区域）。anchor只负责定位（WHERE），对内容的理解（WHAT/WHY）放在标注的text和tags中。

### 3.3 发现内容：三种方式，人和Agent通用

人和Agent用同样的方式发现和阅读内容，只是view不同（AI视图省tokens去装饰，人类视图完整可读）：

1. **TOC导航**：通过目录结构挑选感兴趣的部分
2. **搜索**：语义搜索标注，找到相关段落
3. **顺序阅读**：从某个位置开始，指定阅读量，往后读

```
统一的read接口：
  GET /content/{id}/read?from={span}&size={chars}&view={ai|human}&lang={xx}
  
  view=ai    → Agent用，简化HTML
  view=human → 人用，完整HTML，支持翻译
  不传size   → 返回当前文件剩余内容（按自然章节）
  传size     → 返回指定量，游标式翻页
```

### 3.4 个人历史：按uid筛标注

- 获取"我标注过的所有内容"
- 按内容/类型/关键词筛选
- 可选：语义搜索"我之前记过一个关于决策的笔记"

### 3.5 内容源管理：支持RSS配置

- 数据库存储RSS源配置，定时拉取（拉取到的内容自动做结构化处理）
- RSS源的发现和制作由外部Agent完成（搜索、评估、组装配置），调add_source提交
- 数据库只负责机械执行：按配置定时拉取 → 结构化处理 → 入库
- 也支持用户/Agent直接指定URL或文件导入

### 3.6 平台不跑LLM

- Glynk只做结构化处理（确定性代码）和embedding生成（便宜、可预测）
- 所有需要LLM的标注工作由Agent在自己侧完成，通过annotate接口写回
- Agent可以用任何模型、任何策略来标注

### 3.7 质量飞轮

每个人的自然行为——Agent分析内容、用户高亮句子、发弹幕——都沉淀在共享平台上，帮助其他人更好地发现内容。

```
Agent分析内容 → 自然产出标注 → 写回Glynk
  → 其他Agent搜索时命中这些标注
    → 用户打开阅读/观看 → 高亮、写笔记、发弹幕
      → 精确标注直接提升内容质量
      → 模糊反应(reaction)由AI Agent聚合解读为精确标注
        → 众包信号提升 → 更多人发现 → ...
```

用户不一定需要"标注"——在多模态内容上，发弹幕、评论、emoji等低摩擦的反应同样有价值。AI Agent将这些模糊信号转化为精确的、可检索的标注。

### 3.8 身份与鉴权

- 注册需要邮箱验证（防批量滥用 + token找回通道），uid由用户自选
- 每个用户一个Bearer token（glk_前缀），token-only模式，无密码
- Agent调用API带token → 平台识别用户
- Agent返回的browse_url内嵌query_id → 用户打开阅读器后，标注自动归因到这次推荐
- Agent和阅读器共用同一套身份体系
- MVP阶段可叠加邀请码控制注册量

---

## 四、设计原则

### 内容为中心，不做用户模型

平台只做内容的结构化和存储。了解用户是Agent的事。不需要Brain知识图谱、Topic订阅、个性化推荐。零onboarding。

### 不跑LLM，纯基础设施

Content-DB只做确定性的结构化处理 + 存储 + embedding检索。所有需要LLM的工作（内容标注、内容发现、RSS制作、用户对话、内容创作）都在外部Agent中运行，通过接口操作数据库。平台成本可预测、可控。

### 开放共享

数据库是开放的共享池。每个用户/Agent导入的内容和标注沉淀在一起，所有人受益。标注默认公开，用户可选private。质量靠众包重叠自然涌现（5个Agent独立标注同一句话 = 大概率好内容）。

### 统一标注模型

不把highlight、hook、note、topic、summary分成不同的表。它们本质上是同一种东西——"对内容某个位置的标记"——只是来源和类型不同。统一存储、统一检索。

---

## 五、接口设计

Content-DB对外只暴露这些接口：

### 写入

```
ingest(url | file)              导入内容，做结构化处理
  → 返回: {content_id, title, leaves: [{leaf_id, text, spans}...]}
  → Agent拿到结果后自行标注

annotate(content_id, anchor,    创建标注（Agent或人都调这个）
  type, text, source,           anchor: {"type":"text","spans":[...]}
  uid?, visibility?, ...)
  → Content-DB存储 + 生成embedding索引（reaction类型除外）

annotate/batch([...])           批量创建标注

add_source(rss_config)          添加RSS源配置
```

### 读取

```
query(text, user_context?,      语义检索标注，返回相关内容片段
      types?, tags?, uid?,
      top_k)
browse(content_id, location,    读原文 + 该区域的所有标注
       length?)
get_annotations(uid, ...)       获取某人的标注历史（支持语义搜索）
get_leaves(content_id)          获取某内容的Leaves（Agent拿去做标注用）
list_contents(...)              内容列表
list_sources()                  RSS源列表
```

### 反馈

```
POST /agent/feedback            Agent回传粗反馈（用户没打开阅读器时）
```

阅读器中的标注通过 `annotate` 接口自动采集，不需要额外反馈接口。

---

## 六、与外部系统的关系

```
┌───────────────────────────────────────┐
│  Agent框架（已有）                      │
│  ├── 内容获取Agent                     │  搜索信源 → add_source / ingest
│  ├── 标注Agent                        │  get_leaves → 跑LLM → annotate/batch
│  ├── 用户对话Agent                     │  带user_context → query
│  └── 内容创作Agent                     │  query → 生成短内容 → 发布到媒体矩阵
└──────────┬────────────────────────────┘
           │ 调用接口（LLM成本在这一层）
           ▼
┌───────────────────────────────────────┐
│  Content-DB（本项目）                   │
│  不跑LLM，只做：                       │
│  1. 结构化处理（parse → HTML → split） │
│  2. 存储（标注读写）                    │
│  3. 检索（embedding + 向量搜索）        │
│  4. RSS定时拉取（机械执行）              │
└───────────────────────────────────────┘
           ↑
           │ browse_url
┌───────────────────────────────────────┐
│  阅读器前端（复用Resonote）              │
│  用户阅读、高亮、写笔记                 │
│  标注通过annotate接口回流                │
└───────────────────────────────────────┘
```

---

## 七、MVP路径

### Phase 0：自己先用起来（0-1周）

- 新建项目，复制Resonote的parser/processing模块
- 搭建最小存储（PostgreSQL + pgvector）
- 实现ingest + annotate + query三个核心接口（标注用anchor JSONB）
- CLI导入种子内容（迁移Resonote已有的书 + 标注）
- 自己的Agent接入：ingest → 跑LLM标注 → annotate写回 → query检索

### Phase 1：完整API + 开发者入口（2-4周）

- 完整REST API（所有接口）
- 邮箱验证注册 + token鉴权
- RSS源管理 + 定时拉取
- 播客/视频转录解析器
- annotate/batch批量标注
- API文档页 + Explore搜索页（人类体验入口，无需登录）

### Phase 2：阅读器 + 飞轮启动（4-8周）

- 阅读器前端接入（复用Brainow Reader，加token鉴权和query_id归因）
- 众包质量信号聚合
- 开放小范围测试（邀请码控量）

### Phase 3：扩展（8周+）

- 更多内容格式支持（幻灯片等）
- reaction类型支持（弹幕/评论）
- 跨Agent协同过滤
- 开放注册

---

> 技术实现详见 `architecture.md`。Resonote参考见 `ref/resonote-library-reference.md`。
