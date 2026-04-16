# Glynk 架构设计

> 本文档指导实现。需求见 `requirements.md`。

---

## 核心结构

Glynk做三件事，架构围绕这三件事组织：

```
核心1：任意格式 → 统一HTML            → ingestion/ 模块
       将EPUB/PDF/URL/音频转为带span_id的标准HTML，这是唯一事实源。

核心2：基于统一HTML的双视图           → content/ 模块
       AI视图：简化HTML（保留结构+span_id，去装饰），省tokens，Agent拿去标注。
       人类视图：完整HTML，可读、可标注、可翻译。

核心3：基于精准span的多元annotation   → annotation/ 模块
       Agent和人类的标注统一存储，都锚定在span上。
       标注越多 → 检索越准 → 内容越容易被发现。
```

---

## 一、技术栈

| 组件 | 选型 | 说明 |
|---|---|---|
| Web框架 | FastAPI | 复用Resonote经验 |
| 数据库 | PostgreSQL + pgvector | 6张表，向量搜索内嵌在annotations表 |
| 文件存储 | 本地文件系统 | HTML文件，按content_id组织 |
| Embedding | Azure OpenAI text-embedding-3-large | 3072维，Content-DB唯一的外部AI依赖 |
| 后台任务 | APScheduler | 仅RSS定时拉取 |
| Python | 3.11+ | async/await |

**向量搜索策略**：当前用pgvector（零额外基础设施），通过VectorStore抽象层隔离。规模超过10M标注后可切换Milvus，只需新增一个实现类。

---

## 二、项目结构

```
glynk/
├── main.py                         # FastAPI入口，路由注册，生命周期管理
├── config.py                       # 配置类（见第四节）
├── models.py                       # 数据模型（见第三节）
│
│   ══════ 核心1：任意格式 → 统一HTML ══════
│
├── ingestion/                      # 格式转换 + 结构化处理
│   ├── pipeline.py                 # IngestionPipeline
│   ├── format_utils/               # 格式工具（被content_type内部调用，不直接暴露）
│   │   ├── pdf.py                  #   MinerU调用、Markdown→HTML
│   │   ├── pdf_markdown_converter.py
│   │   ├── epub.py                 #   ebooklib读取
│   │   ├── html.py                 #   文件读取、trafilatura提取
│   │   ├── audio.py                #   音视频转录（优先官方字幕 → 阿里云听悟）
│   │   └── subtitle.py             #   字幕解析（SRT/VTT/ASS → 带时间戳的句子列表）
│   ├── handler/                    # 内容类型handler（主角，每个handler知道怎么最好地处理该类型）
│   │   ├── base.py                 #   ContentTypeHandler接口, ParsedContent数据类
│   │   ├── academic_paper.py       #   论文：用format_utils/pdf → 在MinerU原始输出上提取abstract/作者/TOC
│   │   ├── wechat_article.py       #   微信文章：用format_utils/html → WeChat CSS选择器提取
│   │   ├── book.py                 #   书籍：用format_utils/epub → 从EPUB package直接读元数据
│   │   ├── video.py                #   视频/播客：官方字幕优先 → 听悟转写 → 图文HTML + 媒体源 + 可折叠章节
│   │   ├── generic_article.py      #   通用文章：用format_utils/html + trafilatura
│   │   └── fallback.py             #   兜底：按文件扩展名选format_util → h1取标题
│   ├── registry.py                 # 内容类型选择（来源提示 > 自动检测 > 兜底）
│   └── processing/                 # HTML标准化（从Resonote复制）
│       ├── html_processor.py       #   HTMLProcessor（三阶段流水线）
│       ├── sentence_annotator.py   #   SentenceAnnotator（注入span_id）
│       ├── rich_media_enhancer.py  #   RichMediaEnhancer
│       ├── span_extractor.py       #   SpanExtractor
│       └── path_assigner.py        #   PathAssigner
│
│   ══════ 核心2：基于统一HTML的双视图 ══════
│
├── content/                        # 内容的两种视图 + 翻译
│   ├── reader.py                   # 统一read接口（复用Resonote ReaderService）
│   ├─��� ai_view.py                  # AI视图过滤：去装饰标签，保留结构+span_id
│   ├── locator.py                  # span定位工具（从Resonote复制）
│   └── translation.py              # 懒翻译：按需翻译+缓存（从Resonote复制）
│
│   ══════ 核心3：基于精准span的多元annotation ══════
│
├── annotation/                     # 标注CRUD + 语义检索
│   ├── service.py                  # AnnotationService（CRUD + embedding）
│   ├── search.py                   # 语义检索引擎
│   └── vector_store.py             # VectorStore协议 + PgVectorStore实现
│
│   ══════ 基础设施 ══════
│
├── storage/                        # 存储层
│   └── postgres.py                 # PostgresStore（6张表 + pgvector）
│
├── embedding/                      # Embedding生成（从Resonote简化）
│   └── service.py                  # generate_embedding / generate_embeddings
│
├── api/                            # REST API
│   ├── ingest_router.py            # POST /ingest
│   ├── content_router.py           # GET /read（统一阅读接口，view=ai|human）
│   ├── annotation_router.py        # POST /annotate, GET /annotations, POST /query
│   ├── source_router.py            # RSS源管理
│   ├── feedback_router.py          # POST /feedback
│   └── auth.py                     # token验证中间件
│
└── worker/                         # 后台任务
    ├── rss_fetcher.py              # RSS定时拉取
    └── translator.py               # 翻译后台任务（按需触发）
```

**三个核心 → 三个顶层模块**：`ingestion/`（格式→HTML）、`content/`（双视图）、`annotation/`（标注+检索）。其余是基础设施。

---

## 三、数据模型

### 3.1 PostgreSQL表

```sql
-- ========== 内容 ==========

CREATE TABLE contents (
    content_id TEXT PRIMARY KEY,            -- sha256(file_bytes)[:16]
    title TEXT NOT NULL DEFAULT '',
    author TEXT NOT NULL DEFAULT '',
    source_type TEXT NOT NULL,              -- 'epub' | 'pdf' | 'url' | 'wechat' | 'podcast' | 'video' | 'slides'
    source_url TEXT,                        -- 原始URL（如有）
    source_file_hash TEXT NOT NULL,         -- sha256完整hash，用于去重
    file_count INT NOT NULL DEFAULT 0,      -- HTML文件数量
    toc_json TEXT DEFAULT '[]',             -- 原始目录结构JSON（解析时提取）
    ai_outline_json TEXT DEFAULT '[]',     -- AI生成的大纲JSON（官方Agent通读后提交，有嵌套层级）
    abstract TEXT DEFAULT '',
    translations JSONB DEFAULT '{}',        -- 元数据翻译 {"zh": {"title":"...","author":"...","abstract":"..."}}
    uid TEXT,                               -- 提交者uid（溯源）
    status TEXT NOT NULL DEFAULT 'parsing', -- 'parsing' | 'ready' | 'failed'
    error_message TEXT,
    total_chars INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_contents_hash ON contents(source_file_hash);
CREATE INDEX idx_contents_status ON contents(status);

-- ========== 统一标注（核心表） ==========
-- 需要: CREATE EXTENSION vector;

CREATE TABLE annotations (
    id TEXT PRIMARY KEY,                    -- 'ann-{uuid}'
    content_id TEXT NOT NULL REFERENCES contents(content_id) ON DELETE CASCADE,

    -- 位置（多模态锚定）
    anchor JSONB NOT NULL,                  -- 锚定信息，按类型不同结构不同（见下方说明）
    -- MVP:    {"type": "text", "spans": ["a1b2-0-p15-s3", "a1b2-0-p15-s4"]}
    -- 未来:   {"type": "time", "spans": [...], "time_start": 1410.5, "time_end": 1425.3}
    -- 未来:   {"type": "region", "page": 3, "x": 0.12, "y": 0.35, "w": 0.4, "h": 0.25}
    -- 复合:   {"type": "composite", "spans": [...], "time_start": ..., "time_end": ...}

    -- 标注内容
    type TEXT NOT NULL,                     -- 'highlight' | 'hook' | 'note' | 'reaction'
    text TEXT NOT NULL,                     -- 标注者的贡献（reaction时为弹幕/评论原文）
    tags TEXT[] DEFAULT '{}',               -- 自由标签，如 ARRAY['Insight','创业','AI']
    contextuality TEXT DEFAULT 'standalone', -- 'standalone' | 'embedded'

    -- 来源
    source TEXT NOT NULL,                   -- 'agent' | 'human'
    uid TEXT,                               -- 创建者uid
    visibility TEXT NOT NULL DEFAULT 'public', -- 'public' | 'private'
    query_id TEXT,                          -- 归因到哪次查询（可选）

    -- 向量
    embedding vector(3072),                 -- pgvector: 语义向量
    -- 注意: reaction 类型不生成 embedding（文本太短/太模糊，不参与语义检索）
    -- AnnotationService.create 中按 type 判断是否生成

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 常规索引
CREATE INDEX idx_ann_content ON annotations(content_id);
CREATE INDEX idx_ann_uid ON annotations(uid) WHERE uid IS NOT NULL;
CREATE INDEX idx_ann_type ON annotations(type);
CREATE INDEX idx_ann_visibility ON annotations(visibility);
CREATE INDEX idx_ann_tags ON annotations USING gin(tags);  -- 支持 WHERE tags @> ARRAY['Insight']
CREATE INDEX idx_ann_anchor ON annotations USING gin(anchor);  -- 支持 anchor->'spans' 查询

-- 向量索引（HNSW，cosine距离）
CREATE INDEX idx_ann_embedding ON annotations
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 256);

-- 常用过滤的partial向量索引（可选，加速热门查询路径）
CREATE INDEX idx_ann_emb_public ON annotations
    USING hnsw (embedding vector_cosine_ops)
    WHERE visibility = 'public';

-- ========== 查询记录 ==========

CREATE TABLE queries (
    query_id TEXT PRIMARY KEY,              -- 'qry-{uuid}'
    uid TEXT,
    user_context JSONB,                     -- Agent传入的用户context
    query_text TEXT,
    result_ids TEXT[],                      -- 返回的annotation IDs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========== 反馈 ==========

CREATE TABLE feedback (
    id TEXT PRIMARY KEY,                    -- 'fb-{uuid}'
    query_id TEXT REFERENCES queries(query_id),
    result_id TEXT NOT NULL,                -- annotation ID
    presented BOOLEAN DEFAULT false,
    clicked_through BOOLEAN DEFAULT false,
    agent_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========== RSS源 ==========

CREATE TABLE rss_sources (
    id TEXT PRIMARY KEY,                    -- 'rss-{uuid}'
    url TEXT NOT NULL,
    name TEXT DEFAULT '',
    content_type TEXT,                      -- 可选：指定内容类型，如 'academic_paper'、'wechat_article'
    schedule TEXT DEFAULT 'daily',          -- 'hourly' | 'daily' | 'weekly'
    max_items INT DEFAULT 5,
    enabled BOOLEAN DEFAULT true,
    filters JSONB DEFAULT '{}',             -- 可选过滤条件
    created_by TEXT,                        -- uid
    last_fetched_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========== 用户 ==========

CREATE TABLE users (
    uid TEXT PRIMARY KEY,                   -- 用户自选，如 'sunlit'（小写字母+数字+连字符，3-20字符）
    token TEXT UNIQUE NOT NULL,             -- Bearer token（glk_ 前缀）
    email TEXT UNIQUE NOT NULL,             -- 注册邮箱（用于验证 + token找回）
    name TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========== 翻译状态追踪 ==========
-- 翻译结果存文件（{content_id}/0.zh.html），此表只追踪状态

CREATE TABLE translations (
    content_id TEXT NOT NULL REFERENCES contents(content_id) ON DELETE CASCADE,
    file_idx INT NOT NULL,
    language TEXT NOT NULL,                  -- 'zh' | 'en'
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'translating' | 'completed' | 'failed'
    progress FLOAT DEFAULT 0,               -- 0.0 ~ 1.0
    total_paragraphs INT DEFAULT 0,
    translated_paragraphs INT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    PRIMARY KEY (content_id, file_idx, language)
);
```

### 3.2 annotations各字段在不同type下的含义

| type | text字段含义 | spans粒度 | 典型来源 |
|---|---|---|---|
| **hook** | 反推出的问题：读者可能出于什么困惑而来，这段内容恰好回答了 | 精确到回答该问题的具体句子 | 官方Agent预标注 |
| **highlight** | 为什么这段值得注意 | 用户/Agent选中的范围 | 用户Agent或人 |
| **note** | 任意评论、感想、提问 | 用户选中的范围 | 人 |

**tags**：自由标签，所有type通用。标注者想贴什么都行（如 `["Insight", "创业决策"]`）。不按type预设不同词表。用GIN索引支持高效过滤。

**contextuality**：该标注脱离上下文是否仍有意义。`standalone` = 独立可读，`embedded` = 需要看原文才能理解。

**anchor**：锚定信息，JSONB 格式。MVP 阶段只有 `text` 类型：
```json
{"type": "text", "spans": ["a1b2-0-p15-s3", "a1b2-0-p15-s4"]}
```
未来扩展 `time`（音视频时间段）、`region`（图片/幻灯片区域）、`composite`（复合锚定）。anchor 只负责定位 WHERE，对内容的理解（WHAT/WHY）放在 text/tags 中。

需要获取被标注的原文时，通过 `anchor.spans` 从HTML文件重建（复用Resonote的HTMLReconstructor逻辑）。

**公开标注的API响应不包含uid**，只返回标注内容和众包计数。

### 3.3 文件系统

```
{DATA_ROOT}/html/{content_id}/
├── 0.html            # 原文
├── 0.zh.html         # 中文翻译（懒生成，完成后写入）
├── 1.html
├── 1.zh.html
└── ...

{DATA_ROOT}/uploads/          # 临时上传目录
{DATA_ROOT}/failed/           # 摄入失败的文件
```

### 3.4 Python数据类

```python
# models.py — 只放核心数据类，不放业务逻辑

@dataclass
class Content:
    content_id: str
    title: str
    author: str
    source_type: str          # 'epub' | 'pdf' | 'url' | 'wechat' | 'podcast' | 'video' | 'slides'
    source_url: str | None
    source_file_hash: str
    file_count: int
    toc_json: str
    abstract: str
    status: str               # 'parsing' | 'ready' | 'failed'
    total_chars: int

@dataclass
class Annotation:
    id: str
    content_id: str
    anchor: dict              # 锚定信息，如 {"type": "text", "spans": ["a1b2-0-p15-s3"]}
    type: str                 # 'highlight' | 'hook' | 'note' | 'topic' | 'summary' | 'reaction'
    text: str                 # 标注者的贡献（reaction时为弹幕/评论原文）
    tags: list                # List[str] — 自由标签
    contextuality: str        # 'standalone' | 'embedded'
    source: str               # 'agent' | 'human'
    uid: str | None
    visibility: str           # 'public' | 'private'
    query_id: str | None

# SpanRange, ParsedContent, HTMLSpan 等从Resonote复制的模型保留原样
```

---

## 四、配置

```python
# config.py

@dataclass
class StorageConfig:
    postgres_host: str      # env: POSTGRES_HOST
    postgres_port: int      # env: POSTGRES_PORT
    postgres_user: str      # env: POSTGRES_USER
    postgres_password: str  # env: POSTGRES_PASSWORD
    postgres_db: str = "glynk"
    data_root: Path = Path("/data/glynk")  # HTML文件 + 上传目录

@dataclass
class EmbeddingConfig:
    api_key: str            # env: AZURE_OPENAI_API_KEY
    endpoint: str           # env: AZURE_OPENAI_ENDPOINT
    model: str = "text-embedding-3-large"
    dimension: int = 3072
    batch_size: int = 100

@dataclass
class TranslationConfig:
    enabled: bool = True            # 总开关，用量过大时可关闭
    model: str = "gpt-4o-mini"      # 翻译用的LLM
    batch_size: int = 20            # 每批翻译的段落数
    supported_languages: list = field(default_factory=lambda: ["zh", "en"])

@dataclass
class TranscriptionConfig:
    tingwu_access_key: str      # env: TINGWU_ACCESS_KEY
    tingwu_access_secret: str   # env: TINGWU_ACCESS_SECRET
    tingwu_app_key: str         # env: TINGWU_APP_KEY
    enable_diarization: bool = True    # 说话人识别
    enable_auto_chapters: bool = True  # 自动分章节

@dataclass
class AppConfig:
    storage: StorageConfig
    embedding: EmbeddingConfig
    translation: TranslationConfig = TranslationConfig()
    transcription: TranscriptionConfig | None = None  # 不配置则视频转录不可用
    rss_check_interval_hours: int = 24
```

---

## 五、模块设计

### 5.1 摄入模块

#### ingestion/handler/base.py — 内容类型handler接口

```python
@dataclass
class ParsedContent:
    """handler的统一输出。HTML + 元数据，一步到位。"""
    raw_html_parts: list[str]       # 原始HTML片段列表
    file_names: list[str]           # 对应文件名
    images: dict[str, bytes]        # 图片资源 {路径: 二进制}
    title: str = ""
    author: str = ""
    abstract: str = ""
    toc: list[dict] = field(default_factory=list)
    cover_image: str | None = None
    content_type: str = "generic"   # 'academic_paper' | 'wechat_article' | 'book' | 'generic'

class ContentTypeHandler(Protocol):
    """
    内容类型handler。每个handler知道怎么最好地处理该类型的内容。
    内部调用format_utils完成格式转换，在原始格式上提取元数据。
    """
    def supports(self, file_path: Path, source_hint: str = "") -> bool:
        """是否能处理这个文件。可以参考文件扩展名和来源提示。"""
        ...
    def parse(self, file_path: Path) -> ParsedContent:
        """解析文件，返回HTML + 元数据。"""
        ...
```

#### ingestion/handler 各实现的职责

```python
class AcademicPaperHandler(ContentTypeHandler):
    """论文。内部调用format_utils/pdf（MinerU），在MinerU的Markdown原始输出上提取abstract、作者模式、标题编号TOC。"""
    def supports(self, file_path, source_hint=""):
        return file_path.suffix == '.pdf'  # 也可以通过source_hint='arxiv.org'直接命中

class BookHandler(ContentTypeHandler):
    """书籍。内部调用format_utils/epub（ebooklib），直接从EPUB package读取元数据、封面、TOC——不用从HTML猜。"""
    def supports(self, file_path, source_hint=""):
        return file_path.suffix == '.epub'

class WeChatArticleHandler(ContentTypeHandler):
    """微信文章。内部调用format_utils/html读文件，用WeChat专属CSS选择器提取标题/作者/正文。"""
    def supports(self, file_path, source_hint=""):
        return source_hint == 'mp.weixin.qq.com' or self._detect_wechat_html(file_path)

class VideoHandler(ContentTypeHandler):
    """视频/播客。转录策略：优先使用官方字幕 → 无字幕时调阿里云听悟转写。
    
    转录来源优先级：
    1. 内容源自带字幕（YouTube/B站的CC字幕、播客RSS的transcript字段）
    2. 用户上传时附带的SRT/VTT/ASS字幕文件
    3. 阿里云听悟离线转写（兜底，支持说话人识别 + 自动分章节）
    
    输出：图文HTML + 媒体源。HTML结构：
    - <meta name="media-src"> 嵌入视频/音频源地址
    - 听悟/字幕的自动章节 → <details><summary>可折叠标题</summary>...</details>
    - 每句话一个<span>，data-time-start/data-time-end记录起止秒数
    - 点击span → 前端跳转到视频对应位置（grounding）
    """
    def supports(self, file_path, source_hint=""):
        return (file_path.suffix in ('.mp4', '.mkv', '.webm', '.mp3', '.m4a', '.wav')
                or source_hint in ('youtube.com', 'bilibili.com'))

class GenericArticleHandler(ContentTypeHandler):
    """通用网页文章。内部调用format_utils/html + trafilatura。"""
    def supports(self, file_path, source_hint=""):
        return file_path.suffix in ('.html', '.htm')

class FallbackHandler(ContentTypeHandler):
    """兜底。按文件扩展名选format_util，h1取标题，meta取作者。"""
    def supports(self, file_path, source_hint=""):
        return True  # 永远兜底
```

#### ingestion/registry.py — 内容类型选择

```python
class HandlerRegistry:
    """
    选择最合适的handler。优先级：
    1. 来源指定（RSS配置里的content_type字段）
    2. 来源提示匹配（URL域名 → handler）
    3. handler自己判断（文件扩展名 + 内容检测）
    4. 兜底
    """

    def __init__(self):
        self.handlers: list[ContentTypeHandler] = [
            AcademicPaperHandler(),
            BookHandler(),
            VideoHandler(),
            WeChatArticleHandler(),
            GenericArticleHandler(),
            FallbackHandler(),         # 永远兜底
        ]

        # 来源提示 → handler的快速映射
        self.source_map: dict[str, str] = {
            'arxiv.org': 'academic_paper',
            'mp.weixin.qq.com': 'wechat_article',
            'youtube.com': 'video',
            'bilibili.com': 'video',
        }

    def resolve(self, file_path: Path,
                content_type: str = None,
                source_hint: str = "") -> ContentTypeHandler:
        """
        Args:
            file_path: 文件路径
            content_type: 明确指定的内容类型（如RSS源配置中指定）
            source_hint: 来源提示（如URL域名）
        """
        # 1. 明确指定 → 直接用
        if content_type:
            return self._get_by_name(content_type)

        # 2. 来源提示 → 快速映射
        if source_hint in self.source_map:
            return self._get_by_name(self.source_map[source_hint])

        # 3. handler自己判断
        for handler in self.handlers:
            if handler.supports(file_path, source_hint):
                return handler

        # 4. 不会到这里（FallbackHandler永远返回True）
```

**选择示例：**

```
RSS配置指定 content_type='academic_paper'
  → 直接用 AcademicPaperHandler，不检测

来源是 arxiv.org（URL自动提取）
  → source_map命中 → AcademicPaperHandler

来源是 mp.weixin.qq.com
  → source_map命中 → WeChatArticleHandler

一个.epub文件，没有来源提示
  → BookHandler.supports() 返回True → BookHandler

一个.html文件，来源未知
  → WeChatArticleHandler.supports() 检测HTML内容，没有WeChat结构
  → GenericArticleHandler.supports() 返回True → GenericArticleHandler

来源是 youtube.com
  → source_map命中 → VideoHandler

一个.mp4文件
  → VideoHandler.supports() 返回True → VideoHandler
```

#### ingestion/handler/video.py — 视频/播客转录

转录策略：优先提取官方字幕（YouTube CC、B站字幕、播客RSS transcript），无字幕时调阿里云听悟离线转写（说话人识别 + 自动分章节 + 口语书面化）。

输出：带时间戳的图文HTML。每个 `<span>` 带 `data-time-start/end`（秒），章节用 `<details><summary>` 可折叠，媒体源地址嵌入 `<meta>` 标签。span_id 格式和纯文本内容统一。

详细设计（听悟API集成、结果解析、HTML结构）见 [`modules/video-ingestion.md`](modules/video-ingestion.md)。

#### ingestion/pipeline.py — 摄入流水线

```python
class IngestionPipeline:
    """结构化处理流水线。不跑LLM，只做确定性处理。"""

    def __init__(self, config: AppConfig, db: PostgresStore):
        self.registry = HandlerRegistry()
        self.config = config
        self.db = db

    async def ingest(self, source: str | Path, uid: str = None,
                     content_type: str = None,
                     source_hint: str = "") -> IngestResult:
        """
        摄入内容。

        Args:
            source: URL字符串 或 本地文件Path
            uid: 提交者uid（溯源）
            content_type: 明确指定内容类型（如RSS配置中指定），跳过检测
            source_hint: 来源提示（如 'arxiv.org'），帮助选择handler

        Returns:
            IngestResult: {content_id, title, author, toc, file_count, total_chars}
        """
        # 1. 获取文件（URL则下载到临时目录，并从URL提取source_hint）
        file_path = await self._resolve_source(source)
        if not source_hint and isinstance(source, str):
            source_hint = urlparse(source).netloc  # 'arxiv.org', 'mp.weixin.qq.com'

        # 2. 计算content_id + 去重检查
        content_id = self._calculate_content_id(file_path)
        existing = self.db.get_content(content_id)
        if existing:
            raise ContentAlreadyExistsError(existing)

        # 3. 选择handler，一步完成解析（HTML + 元数据）
        handler = self.registry.resolve(file_path, content_type, source_hint)
        parsed = handler.parse(file_path)

        # 4. HTML标准化（三阶段流水线：规范化 → 富媒体增强 → span_id注入）
        processed_files = []
        for file_idx, raw_html in enumerate(parsed.raw_html_parts):
            processor = HTMLProcessor(content_id, file_idx)
            result = processor.process(raw_html, parsed.images)
            processed_files.append(result)
            self._save_html(content_id, file_idx, result.html)

        # 5. 保存 + 返回结果
        total_chars = sum(r.sentence_count * 50 for r in processed_files)  # 估算
        content = Content(
            content_id=content_id,
            title=parsed.title,
            author=parsed.author,
            source_type=parsed.content_type,
            source_url=source if isinstance(source, str) and source.startswith('http') else None,
            source_file_hash=self._calculate_file_hash(file_path),
            file_count=len(processed_files),
            toc_json=json.dumps(parsed.toc),
            abstract=parsed.abstract,
            uid=uid,
            status='ready',
            total_chars=total_chars,
        )
        self.db.create_content(content)

        return IngestResult(
            content_id=content_id,
            title=parsed.title,
            author=parsed.author,
            toc=parsed.toc,
            file_count=len(processed_files),
            total_chars=total_chars,
        )
```

**摄入只做结构化处理（parse → HTML标准化 → 保存），不做切分。** 切分是阅读时动态完成的（见content/reader.py的read接口）。

**与Resonote的差异：**
- 内容类型handler替代单层parser选择，有降级链
- `source_hint` 从URL自动提取（arxiv.org → 学术论文，mp.weixin.qq.com → 微信文章）
- 去掉 `AnalysisConfig`、所有LLM相关逻辑
- 去掉虚拟切分（不再有leaves表，内容直接以HTML文件存储）
- `ingest()` 返回内容元数据（content_id + TOC），不返回leaves

**从Resonote迁移时的拆分：**

| Resonote文件 | Glynk去向 | 提取什么 |
|---|---|---|
| `parser/pdf.py` | `format_utils/pdf.py` + `handler/academic_paper.py` | 格式工具（MinerU）和handler（论文元数据）分开 |
| `parser/pdf_markdown_converter.py` | `format_utils/pdf_markdown_converter.py` | 不改 |
| `parser/epub.py` | `format_utils/epub.py` + `handler/book.py` | ebooklib读取 和 书籍元数据分开 |
| `parser/html.py` | `format_utils/html.py` + `handler/generic_article.py` | 文件读取 和 trafilatura提取分开 |
| `parser/wechat.py` | `handler/wechat_article.py` | 内部调用format_utils/html |
| `ingestion.py:_select_parser` | `registry.py` | 重写为handler选择 |
| `library/splitting/` | **不复制** | 切分逻辑不再需要 |

### 5.2 annotation/service.py — 标注服务

```python
class AnnotationService:
    """标注的CRUD + 向量索引。不含任何LLM逻辑。"""

    def __init__(self, db: PostgresStore, vector_store: VectorStore, embedding_config: EmbeddingConfig):
        self.db = db
        self.vector_store = vector_store
        self.embedding_config = embedding_config

    # reaction 类型不生成 embedding（文本太短/太模糊，不参与语义检索）
    EMBEDDING_TYPES = {'highlight', 'hook', 'note', 'topic', 'summary'}

    async def create(self, annotation: Annotation) -> Annotation:
        """
        创建单条标注。非reaction类型生成embedding并存入向量存储。

        Args:
            annotation: Annotation对象（id可为None，自动生成）

        Returns:
            创建后的Annotation（含生成的id）
        """
        if not annotation.id:
            annotation.id = f"ann-{uuid4().hex[:12]}"

        # reaction 不生成 embedding
        vector = None
        if annotation.type in self.EMBEDDING_TYPES:
            vector = await generate_embedding(annotation.text, self.embedding_config)

        # 存PostgreSQL（含embedding列，reaction时为None）
        self.db.create_annotation(annotation, embedding=vector)

        return annotation

    async def create_batch(self, annotations: list[Annotation]) -> list[Annotation]:
        """批量创建标注。"""
        for ann in annotations:
            if not ann.id:
                ann.id = f"ann-{uuid4().hex[:12]}"

        # 分离需要embedding的和不需要的
        need_embedding = [a for a in annotations if a.type in self.EMBEDDING_TYPES]
        no_embedding = [a for a in annotations if a.type not in self.EMBEDDING_TYPES]

        # 批量生成embedding（仅非reaction）
        vectors = {}
        if need_embedding:
            texts = [a.text for a in need_embedding]
            vecs = await generate_embeddings(texts, self.embedding_config)
            vectors = {a.id: v for a, v in zip(need_embedding, vecs)}

        # 批量存PostgreSQL
        all_vectors = [vectors.get(a.id) for a in annotations]
        self.db.create_annotations_batch(annotations, embeddings=all_vectors)

        return annotations

    def get_by_content(self, content_id: str, uid: str = None) -> list[dict]:
        """获取某内容的所有标注（public + 该用户的private）。"""
        return self.db.get_annotations(content_id=content_id, uid=uid)

    def get_by_uid(self, uid: str, content_id: str = None,
                   type: str = None, limit: int = 50, offset: int = 0) -> list[dict]:
        """获取某用户的标注历史。"""
        return self.db.get_user_annotations(
            uid=uid, content_id=content_id, type=type,
            limit=limit, offset=offset,
        )

    async def search_user_annotations(self, uid: str, query: str, top_k: int = 10) -> list[dict]:
        """语义搜索某用户的标注。"""
        vector = await generate_embedding(query, self.embedding_config)
        return await self.vector_store.search(
            vector=vector, top_k=top_k,
            filters={"uid": uid},
        )
```

### 5.3 retrieval/vector_store.py — 向量存储抽象层

```python
class VectorStore(Protocol):
    """
    向量存储接口。
    当前用PgVectorStore实现（pgvector），规模超过10M标注后可切换MilvusVectorStore。
    """
    async def search(self, vector: list[float], top_k: int,
                     filters: dict = None) -> list[dict]:
        """
        语义搜索。

        Args:
            vector: 查询向量 (3072维)
            top_k: 返回数量
            filters: 过滤条件，如 {"type": ["highlight","hook"], "visibility": "public", "uid": "user-xxx"}

        Returns:
            [{"id": "ann-xxx", "score": 0.87, "content_id": "...", "type": "...", ...}, ...]
        """
        ...


class PgVectorStore(VectorStore):
    """pgvector实现。直接在annotations表上做向量搜索。"""

    def __init__(self, db: PostgresStore):
        self.db = db

    async def search(self, vector: list[float], top_k: int,
                     filters: dict = None) -> list[dict]:
        """
        在annotations表上执行 WHERE + ORDER BY embedding <=> query LIMIT top_k。
        pgvector的HNSW索引自动加速。
        """
        # 构建SQL
        conditions = []
        params = [str(vector)]  # $1 = 查询向量

        if filters:
            if "type" in filters:
                types = filters["type"] if isinstance(filters["type"], list) else [filters["type"]]
                conditions.append(f"type = ANY(${len(params)+1})")
                params.append(types)
            if "content_ids" in filters:
                conditions.append(f"content_id = ANY(${len(params)+1})")
                params.append(filters["content_ids"])
            if "uid" in filters and filters.get("include_private"):
                conditions.append(f'(visibility = \'public\' OR uid = ${len(params)+1})')
                params.append(filters["uid"])
            else:
                conditions.append("visibility = 'public'")

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        sql = f"""
            SELECT id, content_id, type, text, anchor, tags, source, uid,
                   1 - (embedding <=> $1::vector) as score
            FROM annotations
            {where}
            ORDER BY embedding <=> $1::vector
            LIMIT {top_k}
        """
        return self.db.execute_query(sql, params)
```

### 5.4 retrieval/engine.py — 检索引擎

```python
class RetrievalEngine:
    """语义检索。通过VectorStore抽象层搜索。"""

    def __init__(self, db: PostgresStore, vector_store: VectorStore, embedding_config: EmbeddingConfig):
        self.db = db
        self.vector_store = vector_store
        self.embedding_config = embedding_config

    async def query(self, request: QueryRequest) -> QueryResponse:
        """
        核心检索。

        Args:
            request: QueryRequest
                text: str               — 查询文本
                user_context: dict?     — Agent传入的用户context
                types: list[str]?       — 标注类型过滤，默认 ['highlight','hook']
                content_ids: list[str]? — 限定内容范围
                uid: str?               — 同时搜该用户的private标注
                top_k: int              — 返回数量，默认10

        Returns:
            QueryResponse
                query_id: str
                results: list[QueryResult] — 每项含annotation + 内容元数据 + browse_url
        """
        # 1. 生成查询向量
        vector = await generate_embedding(request.text, self.embedding_config)

        # 2. 构建过滤条件
        filters = {}
        if request.types:
            filters["type"] = request.types
        if request.content_ids:
            filters["content_ids"] = request.content_ids
        if request.uid:
            filters["uid"] = request.uid
            filters["include_private"] = True

        # 3. 向量搜索（通过VectorStore抽象层）
        raw_results = await self.vector_store.search(
            vector=vector, top_k=request.top_k, filters=filters,
        )

        # 4. 补全内容元数据（title, author等）
        results = self._enrich_results(raw_results)

        # 5. 用众包信号重排序
        results = self._rerank_with_crowd_signal(results)

        # 6. 记录查询
        query_id = f"qry-{uuid4().hex[:12]}"
        self.db.create_query(query_id, request.uid, request.user_context,
                             request.text, [r["id"] for r in results])

        # 7. 构造browse_url
        for r in results:
            spans = r["anchor"].get("spans", [])
            span_id = spans[0] if spans else ""
            file_idx = parse_file_idx_from_span(span_id)
            r["browse_url"] = f"/browse/{r['content_id']}/{file_idx}?loc={span_id}&qid={query_id}"

        return QueryResponse(query_id=query_id, results=results)

    def _rerank_with_crowd_signal(self, results: list) -> list:
        """用众包信号加权排序。"""
        for r in results:
            spans = r["anchor"].get("spans", [])
            span_id = spans[0] if spans else ""
            crowd = self.db.get_span_crowd_count(span_id)
            r["final_score"] = r["score"] * 0.8 + min(math.log(crowd + 1) / 5, 1.0) * 0.2
        results.sort(key=lambda r: r["final_score"], reverse=True)
        return results
```

### 5.5 storage/postgres.py — PostgreSQL存储

```python
class PostgresStore:
    """PostgreSQL存储层。单例。"""

    _instance = None

    @classmethod
    def get_instance(cls, config: StorageConfig = None) -> 'PostgresStore':
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance

    def __init__(self, config: StorageConfig):
        self.pool = ThreadedConnectionPool(1, 10,
            host=config.postgres_host, port=config.postgres_port,
            user=config.postgres_user, password=config.postgres_password,
            dbname=config.postgres_db)
        self._init_tables()

    # --- Contents ---
    def create_content(self, content: Content) -> bool: ...
    def get_content(self, content_id: str) -> dict | None: ...
    def list_contents(self, limit: int = 100, offset: int = 0) -> list[dict]: ...

    # --- Annotations ---
    def create_annotation(self, ann: Annotation, embedding: list[float] = None) -> bool: ...
    def create_annotations_batch(self, anns: list[Annotation], embeddings: list[list[float]] = None) -> int: ...
    def get_annotations(self, content_id: str, uid: str = None) -> list[dict]:
        """返回该内容的public标注 + 该uid的private标注。"""
        ...
    def get_user_annotations(self, uid: str, content_id: str = None,
                             type: str = None, limit: int = 50, offset: int = 0) -> list[dict]: ...

    # --- 众包信号 ---
    def get_span_crowd_count(self, span_id: str) -> int:
        """某个span被多少不同uid标注过。"""
        # SELECT COUNT(DISTINCT uid) FROM annotations
        # WHERE anchor->'spans' ? {span_id} AND visibility = 'public'
        ...

    # --- Queries ---
    def create_query(self, query_id, uid, user_context, text, result_ids) -> bool: ...

    # --- Feedback ---
    def create_feedback(self, feedback) -> bool: ...

    # --- RSS Sources ---
    def create_source(self, source) -> bool: ...
    def list_sources(self, enabled_only: bool = True) -> list[dict]: ...
    def update_source_last_fetched(self, source_id: str) -> bool: ...

    # --- Users ---
    def create_user(self, uid: str, token: str, email: str, name: str = "") -> bool: ...
    def get_user_by_token(self, token: str) -> dict | None: ...
    def get_user_by_email(self, email: str) -> dict | None: ...
```

---

## 六、REST API

### 鉴权

所有接口（除 `POST /users`、`POST /users/verify-email`、`POST /users/login-email` 外）需要 `Authorization: Bearer <token>` header。

```python
# api/auth.py
async def get_current_user(request: Request, db: PostgresStore) -> dict:
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    user = db.get_user_by_token(token)
    if not user:
        raise HTTPException(401, "Invalid token")
    return user
```

### 6.1 POST /ingest

```python
# 请求
{
    "source": "https://arxiv.org/abs/2301.00001"  # URL或本地文件路径
}
# 或 multipart/form-data 上传文件

# 响应 200
{
    "content_id": "a1b2c3d4e5f6g7h8",
    "title": "Attention Is All You Need",
    "author": "Vaswani et al.",
    "source_type": "pdf",
    "file_count": 1,
    "total_chars": 98000,
    "toc": [
        {"title": "Abstract", "span_id": "a1b2-0-p1-s1"},
        {"title": "1 Introduction", "span_id": "a1b2-0-p5-s1"},
        ...
    ]
}

# 响应 409（内容已存在）
{
    "error": "content_already_exists",
    "content_id": "a1b2c3d4e5f6g7h8"
}
```

### 6.2 PUT /content/{content_id}/outline — 提交AI大纲

```python
# 请求：整体JSON，有嵌套层级
PUT /content/a1b2c3d4e5f6g7h8/outline
{
    "outline": [
        {
            "title": "不确定性下的决策框架",
            "description": "论证了创业者面对不确定性时不应等待完整信息",
            "span_id": "a1b2-0-p1-s1",
            "children": [
                {
                    "title": "等待是最大的风险",
                    "description": "信息永远不会完整，等待本身是最差的决策",
                    "span_id": "a1b2-0-p5-s1",
                    "children": []
                }
            ]
        }
    ]
}

# 响应 200
{"ok": true}
```

覆盖式写入 `contents.ai_outline_json`。通常由官方Agent通读全文后一次性提交。

### 6.3 POST /annotate

```python
# 请求：单条标注
{
    "content_id": "a1b2c3d4e5f6g7h8",
    "anchor": {"type": "text", "spans": ["a1b2-0-p15-s3", "a1b2-0-p15-s4"]},
    "type": "highlight",
    "text": "用贝叶斯思维重构了不确定性决策问题，非常精辟",
    "tags": ["Insight", "创业决策"],
    "contextuality": "standalone",
    "visibility": "public"
}

# 响应 201
{
    "id": "ann-3f8a9b2c1d0e",
    "content_id": "a1b2c3d4e5f6g7h8",
    ...
}
```

### 6.4 POST /annotate/batch

```python
# 请求：批量标注
{
    "annotations": [
        {
            "content_id": "a1b2c3d4e5f6g7h8",
            "anchor": {"type": "text", "spans": ["a1b2-0-p15-s3"]},
            "type": "highlight",
            "text": "标注内容...",
            "tags": ["Insight"],
            "contextuality": "standalone",
            "visibility": "public"
        },
        ...
    ]
}

# 响应 201
{
    "created": 15,
    "ids": ["ann-xxx", "ann-yyy", ...]
}
```

### 6.5 POST /query

```python
# 请求
{
    "text": "关于创业者面对不确定性如何做决策",
    "user_context": {                          # 可选
        "situation": "正在考虑从大公司离职创业",
        "interests": ["创业", "决策"]
    },
    "types": ["highlight", "hook"],            # 可选，默认 highlight+hook
    "content_ids": null,                       # 可选，限定范围
    "top_k": 10
}

# 响应 200
{
    "query_id": "qry-7a8b9c0d1e2f",
    "results": [
        {
            "annotation_id": "ann-3f8a9b2c1d0e",
            "content_id": "a1b2c3d4e5f6g7h8",
            "content_title": "Zero to One",
            "content_author": "Peter Thiel",
            "type": "highlight",
            "text": "标注文本...",
            "tags": ["Insight"],
            "contextuality": "standalone",
            "anchor": {"type": "text", "spans": ["a1b2-0-p15-s3"]},
            "score": 0.87,
            "crowd_count": 42,                  # 多少人标注了这个位置
            "browse_url": "/browse/a1b2c3d4e5f6g7h8/0?loc=a1b2-0-p15-s3&qid=qry-7a8b9c0d1e2f"
        },
        ...
    ]
}
```

### 6.6 GET /content/{content_id}/read — 统一阅读接口

人和AI共用同一个接口，通过 `view` 参数区分渲染方式。

```python
# 参数
GET /content/{content_id}/read?from={span}&size={chars}&view={ai|human}&lang={xx}

# from:  起始span_id（可选，默认从头开始）
# size:  读取字符数（可选，默认当前文件剩余内容）
# view:  ai = 简化HTML（去装饰标签），human = 完整HTML（默认human）
# lang:  翻译语言（可选，仅human视图）
```

```python
# 人类阅读（不传size → 按文件自然边界）
GET /content/a1b2c3d4/read?view=human

# 人类阅读 + 定位到具体位置
GET /content/a1b2c3d4/read?from=a1b2-0-p15-s3&view=human

# 人类阅读 + 翻译
GET /content/a1b2c3d4/read?view=human&lang=zh

# Agent阅读（传size → 按指定量读取，跨文件透明处理）
GET /content/a1b2c3d4/read?size=12000&view=ai

# Agent继续读下一页
GET /content/a1b2c3d4/read?from=a1b2-0-p46-s1&size=12000&view=ai
```

```python
# 响应 200（通用格式）
{
    "content": "...",                       # HTML内容（AI视图去装饰，人类视图完整）
    "from": "a1b2-0-p1-s1",                # 实际起始span
    "to": "a1b2-0-p45-s3",                 # 实际结束span
    "char_count": 11800,
    "has_more": true,
    "next_from": "a1b2-0-p46-s1",          # 下次传这个继续读
    "translation_status": "original",       # 仅human+lang时有意义
    "annotations": [                        # 该范围内的public标注（不含uid）
        {"id": "ann-xxx", "type": "highlight", "text": "...", "anchor": {"type": "text", "spans": [...]}, "crowd_count": 42},
        ...
    ]
}
```

**实现**：复用Resonote的ReaderService和SpanLocator（已验证），在输出前加view过滤层。
- 不传size → 加载当前文件剩余内容（自然章节单元，渲染最安全）
- 传size → 从from位置读指定量，在块元素边界（`<p>`、`<h2>`等）对齐切分点
- 跨文件透明处理（span_id自带file_idx）

**翻译机制**（仅human视图）：
- 翻译结果存为文件（`0.zh.html`），和原文并排，永久缓存
- 按段落翻译（每批20段），支持断点续传
- span_id在翻译后完全保持不变——标注在原文和译文上通用
- 同一内容的翻译被所有用户共享（通过content_id去重）
- `config.translation.enabled = false` 一键关闭

### 6.7 GET /content/{content_id}/outline — 获取AI大纲

```python
GET /content/a1b2c3d4e5f6g7h8/outline

# 响应 200（有大纲）
{
    "outline": [
        {"title": "...", "description": "...", "span_id": "...", "children": [...]},
        ...
    ]
}

# 响应 200（无大纲）
{"outline": []}
```

### 6.8 GET /annotations

```python
# 获取用户自己的标注历史
GET /annotations?content_id=a1b2&type=note&limit=20&offset=0

# 响应 200
{
    "annotations": [...],
    "total": 47
}
```

### 6.9 POST /annotations/search

```python
# 语义搜索用户的标注
{
    "query": "我之前记过一个关于决策的笔记"
}

# 响应 200
{
    "results": [
        {"id": "ann-xxx", "text": "...", "score": 0.82, ...},
        ...
    ]
}
```

### 6.10 POST /feedback

```python
{
    "query_id": "qry-7a8b9c0d1e2f",
    "results": [
        {"result_id": "ann-xxx", "presented": true, "clicked_through": false,
         "agent_summary": "用户听了摘要后讨论了创业风险"}
    ]
}
```

### 6.11 RSS源管理

```python
POST /sources          # 添加RSS源
GET  /sources          # 列出RSS源
PUT  /sources/{id}     # 更新RSS源（enabled/schedule/filters）
DELETE /sources/{id}   # 删除RSS源
```

### 6.12 用户管理

```python
POST /users/verify-email   # 发送邮箱验证码（无需鉴权）→ {message: "验证码已发送"}
                           # 请求: {email}，后端发6位验证码到邮箱，有效期10分钟
POST /users                # 注册（无需鉴权）→ 返回 {uid, token}
                           # 请求: {uid, email, code, name?}，验证code后创建用户
                           # token 带 glk_ 前缀
POST /users/login-email    # 邮箱验证码登录（无需鉴权）→ 返回 {uid, token}
                           # 请求: {email, code}，返回已有token
GET  /users/me             # 获取当前用户信息 → {uid, name, email, created_at}
```

---

## 七、从Resonote复制的模块

### 复制清单

parser模块需要重构（详见5.1节），不是简单复制。processing直接复制。不复制splitting。

| 源路径 | 目标路径 | 改动 |
|---|---|---|
| `library/parser/pdf.py` | `ingestion/format_utils/pdf.py`（MinerU调用）+ `ingestion/handler/academic_paper.py`（论文元数据提取） | **拆分**：格式工具和handler分开。handler在MinerU原始输出上提取abstract |
| `library/parser/pdf_markdown_converter.py` | `ingestion/format_utils/pdf_markdown_converter.py` | 不改 |
| `library/parser/epub.py` | `ingestion/format_utils/epub.py`（ebooklib读取）+ `ingestion/handler/book.py`（从EPUB package直接读元数据） | **拆分**：元数据从package读，不从HTML猜 |
| `library/parser/html.py` | `ingestion/format_utils/html.py`（文件读取+trafilatura）+ `ingestion/handler/generic_article.py` | **拆分** |
| `library/parser/wechat.py` | `ingestion/handler/wechat_article.py` | 内部调用format_utils/html，加WeChat CSS提取 |
| `library/processing/html_processor.py` | `ingestion/processing/html_processor.py` | 不改 |
| `library/processing/sentence_annotator.py` | `ingestion/processing/sentence_annotator.py` | 不改 |
| `library/processing/rich_media_enhancer.py` | `ingestion/processing/rich_media_enhancer.py` | 不改 |
| `library/processing/span_extractor.py` | `ingestion/processing/span_extractor.py` | 不改 |
| `library/processing/path_assigner.py` | `ingestion/processing/path_assigner.py` | 不改 |
| `library/reader/service.py` | `content/reader.py` | 复用ReaderService核心逻辑，加view参数过滤 |
| `library/reader/locator.py` | `content/locator.py` | 不改 |
| `library/processing/html_reconstructor.py` | `content/ai_view.py` | 复用HTML重建，加装饰标签过滤 |
| `library/translation.py` | `content/translation.py` + `worker/translator.py` | 复用段落级翻译。加enabled开关 |
| `library/retrieval/vector_service.py` | `embedding/service.py` | 去掉common.cache依赖，简化 |
| `library/splitting/` | **不复制** | 不再需要预切分 |
| （新写）| `ingestion/handler/video.py` | **新增**：视频/播客handler，官方字幕优先→听悟转写兜底，输出图文HTML（可折叠章节+时间戳span+媒体meta） |
| （新写）| `ingestion/format_utils/audio.py` | **新增**：阿里云听悟离线转写封装（CreateTask→轮询→解析结果） |
| （新写）| `ingestion/format_utils/subtitle.py` | **新增**：字幕文件解析（SRT/VTT/ASS → 带时间戳的句子列表） |

### import路径修改

processing模块复制后批量替换：

```
from library.processing → from ingestion.processing
from library.models     → from models
from library.config     → from config
from library.storage    → from storage
from library.reader     → from reader
```

parser模块不是简单替换——需要拆分重构（见5.1节）。

### 需要从Resonote models.py保留的

- `ParsedContent`, `TOCItem` — parser返回值
- `HTMLSpan`, `SpanRange` — 切分系统的内部类型
- `parse_span_id()` — span_id解析工具函数

不需要的：`Highlight`, `Question`, `Channel`, `ChannelContent`, `ChannelSubscription`, `TopicSubscription`, `ContentStatus`（用字符串代替枚举）

### reader/service.py 适配

主要改动：
- `from library.storage.postgres_store import PostgresStore` → `from storage.postgres import PostgresStore`
- `ReaderService` 构造函数接收 `PostgresStore` 实例和 `data_root` 路径
- 去掉翻译相关逻辑（`reading_mode`, `translation_status`等）

---

## 八、worker/rss_fetcher.py

```python
class RSSFetcher:
    """RSS定时拉取。唯一的后台任务。"""

    def __init__(self, db: PostgresStore, pipeline: IngestionPipeline):
        self.db = db
        self.pipeline = pipeline

    async def fetch_all(self):
        """拉取所有启用的RSS源。由APScheduler定时调用。"""
        sources = self.db.list_sources(enabled_only=True)
        for source in sources:
            if self._should_fetch(source):
                await self._fetch_source(source)

    async def _fetch_source(self, source: dict):
        """拉取单个RSS源的新条目。"""
        feed = feedparser.parse(source['url'])
        new_entries = feed.entries[:source['max_items']]

        for entry in new_entries:
            url = entry.get('link')
            if not url:
                continue
            try:
                await self.pipeline.ingest(url, content_type=source.get('content_type'))
            except ContentAlreadyExistsError:
                continue  # 已有，跳过
            except Exception as e:
                logger.error(f"RSS ingest failed: {url} - {e}")

        self.db.update_source_last_fetched(source['id'])

    def _should_fetch(self, source: dict) -> bool:
        """根据schedule判断是否该拉取。"""
        ...

# main.py中注册：
# scheduler = AsyncIOScheduler()
# scheduler.add_job(rss_fetcher.fetch_all, 'interval', hours=config.rss_check_interval_hours)
```

---

## 九、依赖清单

```
# requirements.txt
fastapi
uvicorn
psycopg2-binary
pgvector             # pgvector Python绑定
openai               # Azure OpenAI embedding
httpx                # PDF parser API调用 + 听悟API调用
ebooklib             # EPUB解析
beautifulsoup4
lxml
jionlp               # 中文分句
feedparser           # RSS解析
apscheduler          # 定时任务
python-multipart     # 文件上传
yt-dlp               # YouTube/B站视频信息+字幕提取
pysrt                # SRT字幕解析
webvtt-py            # VTT字幕解析
alibabacloud-tingwu-2023-09-30  # 阿里云听悟SDK
```
