# 视频/播客摄入模块

> 详细设计：转录策略、听悟 API 集成、HTML 输出格式。
> 架构总览见 `../architecture.md` 的 VideoHandler 部分。

---

## 一、转录策略

优先使用官方字幕（零成本），无字幕时调阿里云听悟离线转写。

```
1. 官方字幕（零成本，最快）
   YouTube → yt-dlp 提取CC字幕（SRT/VTT）
   Bilibili → API提取字幕JSON
   播客RSS → transcript字段（如有）
   用户上传 → 附带的SRT/VTT/ASS文件

2. 阿里云听悟（兜底，需API调用）
   调用听悟离线转写 API
   支持：mp3/wav/mp4/mkv/webm 等主流格式（≤6GB，≤6h）
   返回：逐句时间戳 + 说话人识别 + 自动分章节 + 口语书面化
```

---

## 二、数据结构

```python
@dataclass
class Sentence:
    text: str
    start_ms: int           # 起始时间（毫秒）
    end_ms: int             # 结束时间（毫秒）
    speaker_id: str | None  # 说话人ID（如有）

@dataclass
class Chapter:
    headline: str           # 章节标题
    summary: str            # 章节摘要
    start_ms: int
    end_ms: int

@dataclass
class TranscriptionResult:
    sentences: list[Sentence]
    chapters: list[Chapter]
    duration_ms: int
    language: str
```

---

## 三、听悟 API 集成（format_utils/audio.py）

### 3.1 调用流程

```python
async def transcribe_with_tingwu(file_url: str, config: TranscriptionConfig) -> TranscriptionResult:
    """
    调用阿里云听悟离线转写。

    API: PUT /openapi/tingwu/v2/tasks?type=offline
    域名: tingwu.cn-beijing.aliyuncs.com
    版本: 2023-09-30

    流程：
      1. CreateTask → 返回 TaskId
      2. 轮询 GET /openapi/tingwu/v2/tasks/{TaskId}（间隔1分钟）
         直到 TaskStatus = 'COMPLETED' | 'FAILED'
      3. 下载 Result.Transcription URL → 解析转写JSON
      4. 下载 Result.AutoChapters URL → 解析章节JSON
    """
```

### 3.2 CreateTask 请求参数

```python
{
    "AppKey": "{config.tingwu_app_key}",
    "Input": {
        "FileUrl": "https://...",          # 必须是公网HTTP URL
        "SourceLanguage": "cn",            # cn | en | auto | multilingual
        "TaskKey": "glynk_{content_id}"
    },
    "Parameters": {
        "Transcription": {
            "DiarizationEnabled": True,    # 说话人识别
            "Diarization": {
                "SpeakerCount": 0          # 0=自动判断人数
            }
        },
        "AutoChaptersEnabled": True,       # 自动分章节
        "TextPolishEnabled": True          # 口语书面化
    }
}
```

注意事项：
- FileUrl 必须是公网可访问的 HTTP/HTTPS 地址（推荐阿里云 OSS 预签名 URL）
- 本地文件需先上传到 OSS 再提交 URL
- 签名 URL 有效期建议 ≥3h（听悟任务可能排队）
- QPS 限制：CreateTask 20/s，GetTaskInfo 100/s

### 3.3 转写结果结构（Transcription JSON）

```json
{
    "TaskId": "...",
    "Transcription": {
        "AudioInfo": {
            "Size": 670663,
            "Duration": 10394,       // 毫秒
            "SampleRate": 48000,
            "Language": "cn"
        },
        "Paragraphs": [
            {
                "ParagraphId": "...",
                "SpeakerId": "1",    // 说话人ID
                "Words": [
                    {
                        "Id": 10,
                        "SentenceId": 1,     // 同一SentenceId的words组装成一句话
                        "Start": 4970,       // 毫秒
                        "End": 5560,
                        "Text": "您好，"
                    },
                    {
                        "Id": 20,
                        "SentenceId": 1,
                        "Start": 5730,
                        "End": 6176,
                        "Text": "我是"
                    }
                ]
            }
        ]
    }
}
```

### 3.4 章节结果结构（AutoChapters JSON）

```json
{
    "TaskId": "...",
    "AutoChapters": [
        {
            "Id": 1,
            "Start": 1930,          // 毫秒
            "End": 283874,
            "Headline": "阿里巴巴云栖大会及技术责任",
            "Summary": "云栖大会作为中国产业界的盛会..."
        },
        {
            "Id": 2,
            "Start": 284050,
            "End": 452084,
            "Headline": "云计算：推动中国走向现代化",
            "Summary": "平头哥围绕云计算场景..."
        }
    ]
}
```

### 3.5 解析逻辑

```python
def parse_tingwu_result(transcription_json: dict, chapters_json: dict) -> TranscriptionResult:
    """
    将听悟返回的 JSON 转换为 TranscriptionResult。

    转写解析：
      Paragraphs → Words，按 SentenceId 聚合为 Sentence 列表。
      每个 Sentence:
        text = 同一 SentenceId 的所有 words.Text 拼接
        start_ms = 该句第一个 word.Start
        end_ms = 该句最后一个 word.End
        speaker_id = 所属 Paragraph.SpeakerId

    章节解析：
      AutoChapters[] 直接映射为 Chapter 列表。
    """
```

---

## 四、字幕解析（format_utils/subtitle.py）

```python
def parse_subtitle(subtitle_path: Path) -> list[Sentence]:
    """
    解析 SRT/VTT/ASS 字幕文件为 Sentence 列表。
    根据扩展名选择解析器（pysrt / webvtt-py）。
    每条字幕 → 一个 Sentence(text, start_ms, end_ms, speaker_id=None)
    """
```

---

## 五、VideoHandler 流程（handler/video.py）

```python
class VideoHandler:
    async def parse(self, file_path: Path) -> ParsedContent:
        # 1. 尝试提取官方字幕（零成本）
        subtitle = self._extract_subtitle(file_path, self.source_url)
        #   YouTube/B站 → yt-dlp --write-sub --skip-download
        #   播客RSS → transcript字段
        #   用户上传 → 同名SRT/VTT/ASS文件

        if subtitle:
            sentences = parse_subtitle(subtitle)
            chapters = self._guess_chapters(sentences)  # 按时间间隔猜测章节
        else:
            result = await transcribe_with_tingwu(self.file_url, self.config)
            sentences = result.sentences
            chapters = result.chapters

        # 2. 生成HTML
        html = self._build_html(sentences, chapters, media_src=self.source_url)

        return ParsedContent(
            raw_html_parts=[html],
            file_names=["0.html"],
            title=self._extract_title(),
            content_type="video",
        )
```

---

## 六、输出 HTML 结构

```html
<!-- 媒体源元信息 -->
<meta name="media-src" content="https://youtube.com/watch?v=xxx" />
<meta name="media-type" content="video" />

<!-- 标题 -->
<h1>Lex Fridman Podcast #401</h1>
<p class="meta">Elon Musk · 2024-01-15 · 2:03:15</p>

<!-- 章节1（可折叠）-->
<details open>
  <summary data-time-start="0" data-time-end="1230">
    <h2>开场：为什么做SpaceX</h2>
  </summary>
  <p class="chapter-summary">SpaceX的起源和早期挑战...</p>

  <p>
    <span id="xxx-0-p1-s1" data-time-start="0.0" data-time-end="3.2"
      >大家好，今天请到的嘉宾是Elon Musk。</span>
    <span id="xxx-0-p1-s2" data-time-start="3.2" data-time-end="7.8"
      >我们要聊的第一个话题是SpaceX的起源。</span>
  </p>

  <p>
    <span id="xxx-0-p2-s1" data-time-start="8.0" data-time-end="15.3"
      >其实最开始我并没有想做火箭公司。</span>
  </p>
</details>

<!-- 章节2 -->
<details>
  <summary data-time-start="1230" data-time-end="2850">
    <h2>创业决策：如何面对不确定性</h2>
  </summary>
  <p class="chapter-summary">讨论了创业者面对不确定性时的...</p>
  <!-- sentences... -->
</details>
```

**关键约定**：
- `data-time-start` / `data-time-end` 单位为**秒**（从听悟毫秒转换）
- span_id 格式不变：`{content_id}-{file_idx}-p{para}-s{sent}`，和纯文本内容统一
- 章节用 `<details><summary>` 原生可折叠，`<summary>` 也带时间范围
- 章节摘要（如有）用 `<p class="chapter-summary">` 标注
- 无章节时所有 sentences 直接输出，不包裹 `<details>`
- 媒体源在 `<meta>` 中，前端解析后渲染播放器

---

## 七、前端布局

详见 `../frontend/frontend.md` 的「视频/播客内容的阅读器布局」章节。

核心交互：
- PC 左右分栏（视频 | 图文），移动端视频悬浮 PiP
- 点击文字 → 视频跳转到对应 `data-time-start`
- 视频播放 → 文字自动跟随高亮
- 章节折叠/展开：`<details>` 原生支持
- 文字标注和纯文本模式完全一致（anchor.spans 指向 span_id）
