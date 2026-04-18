# 视频/播客摄入

> 音视频 → 带时间戳的 HTML。转写属于后端（`../requirements.md` §3.6 "平台不跑 LLM" 的例外：ASR 作为结构化处理）。

## 入口

两条路径：

1. **有官方转写** — Agent 找到/整理为 md，走 `/api/publications/upload`（MarkdownHandler）。本模块不涉及。
2. **无官方转写** — Agent 提交媒体文件，后端转写。下文所述。

## API 契约

### `POST /api/publications/media/init`

请求：
| 字段 | 类型 | 说明 |
|---|---|---|
| `filename` | str | 含扩展名，必须为 mp3/wav（见下文格式要求） |
| `file_hash` | str | sha256 hex（64 字符），agent 计算，用于去重 |
| `media_type` | `"audio" \| "video"` | |
| `title` | str | |
| `source_url` | str? | 官方页面 URL（可选） |
| `author` | str? | |

响应：
| 字段 | 类型 | 说明 |
|---|---|---|
| `unit_id` | str | `file_hash[:16]` |
| `upload_url` | str? | OSS presigned PUT，30min 有效；`existing=true` 时为 null |
| `existing` | bool | 命中去重 |

### `POST /api/publications/media/finalize`

Agent 上传完成后调用。后端同步完成整条流水线并返回 IngestResult。

请求：所有 init 的字段 + `unit_id`。（无状态：后端不在 init 和 finalize 之间保存元数据。）

响应：与 `/api/publications` 的 IngestResult 相同。

## 后端流水线

```
OSS 对象（agent 已上传）
  → presigned GET URL
  → qwen3-asr-flash-filetrans (enable_words=true, language_hints=["zh","en"])
  → 句/字级时间戳 JSON
  → 生成 HTML（见下）
  → 下载 OSS 对象到 /media/{unit_id}/{filename}
  → 归档 ASR JSON 到 /media/{unit_id}/asr_raw.json
  → 删除 OSS 临时对象
  → 写 Unit
```

## HTML 输出契约

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="media-src" content="/media/{unit_id}/{filename}">
  <meta name="media-type" content="audio">
  <title>{title}</title>
</head>
<body>
  <h1>{title}</h1>
  <p><span id="{unit_id}-0-p1-s1"
           data-time-start="2.124"
           data-time-end="3.884">这么快看完了？</span></p>
  <p><span id="{unit_id}-0-p2-s1"
           data-time-start="7.564"
           data-time-end="7.724">小会。</span></p>
  ...
</body>
</html>
```

- 每条 ASR sentence → 独立 `<p><span>`，一句一段
- 时间戳单位：秒（float，ms 除以 1000）
- `span_id` 沿用既有格式 `{unit_id}-{file_idx}-p{n}-s{m}`
- 词级时间戳不进 HTML，保留在 `asr_raw.json` 中，阅读器需要时再 overlay

## Unit metadata

标准字段之外新增：

```jsonc
{
  "media": {
    "type": "audio" | "video",
    "filename": "clip.mp3",
    "duration_ms": 60000,
    "asr_model": "qwen3-asr-flash-filetrans"
  }
}
```

`source_type` 设为 `"audio"` 或 `"video"`。

## 格式要求

DashScope `qwen3-asr-flash-filetrans` 接受 mp3/wav；m4a/aac 等容器会报 "audio format illegal"。**Agent 必须在上传前转成 mp3**：

```bash
ffmpeg -i in.m4a -ar 16000 -ac 1 -c:a libmp3lame -b:a 64k out.mp3
```

## 依赖与配置

Python: `oss2`, `dashscope`（新增到 requirements.txt）。系统：无（ffmpeg 在 agent 侧）。

环境变量：
```
OSS_ENDPOINT=https://oss-cn-beijing.aliyuncs.com
OSS_BUCKET=qwen-transcribe
OSS_ACCESS_KEY_ID=...
OSS_ACCESS_KEY_SECRET=...
DASHSCOPE_API_KEY=...
```

## 非目标（后续再议）

- 说话人分离（Qwen3 不出，要补 pyannote 或降级听悟）
- 章节自动分段
- 口语润色（disfluency removal / restructure）——Qwen3 原文可用度已够，引入 LLM 会破坏"后端不跑 LLM"边界
- 词级时间戳的前端渲染（数据已留好）
- 超长媒体分 file_idx 多文件（MVP 全部塞 0.html）
