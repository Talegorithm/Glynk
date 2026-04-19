# 音视频阅读器（前端需求）

> 对应后端摄入：`../modules/video-ingestion.md`。
> 现有阅读器总体架构：`./frontend.md`。
> 本文只写"要做什么 + 后端给什么"，不规定实现。

## 后端已产出（前端可依赖）

**HTML 结构**（见 `../modules/video-ingestion.md` "HTML 输出契约"）

- `<head>` 带：
  - `<meta name="media-type" content="audio" | "video">` — 存在即进入媒体模式
  - `<meta name="media-src" content="/media/{unit_id}/{filename}">` — 媒体文件地址
- 正文每条 ASR 句子：`<p><span id="{unit_id}-{file_idx}-p{n}-s{m}" data-time-start="{秒}" data-time-end="{秒}">文字</span></p>`
- 时间单位：**秒**（浮点）

**媒体文件端点**

- `GET /media/{unit_id}/{filename}` 直接返回媒体文件
- 支持标准 HTTP Range 请求（静态文件服务，适合 `<audio>`/`<video>` 流式播放）

**Unit metadata**

```
unit.metadata.media = {
  "type": "audio" | "video",
  "filename": "...",
  "duration_ms": 123456,
  "asr_model": "qwen3-asr-flash-filetrans"
}
```

## 功能需求

### F1. 媒体模式检测

HTML 含 `media-type` meta 标签 → 进入媒体模式；否则走现有文字阅读模式。两种模式的路由、权限、URL 参数完全一致。

### F2. 播放器

- 桌面：播放器与文字可同屏共存（不遮挡主阅读区）
- 移动：页面下滚时播放器仍保持可见/可控（PiP 或固定小窗）
- 标准控件：播放/暂停、进度条、倍速（至少 0.75×/1×/1.25×/1.5×/2×）、音量
- 视频：额外支持全屏

### F3. 双向时间同步（核心）

- **播放 → 文字**：当前播放时间落在某 span 的 `[data-time-start, data-time-end]` 区间 → 该 span 高亮 "正在播"；可选自动滚动带它到视野（默认开，用户可关）
- **文字 → 播放**：点击任意 span → 播放器 seek 到该 span 的 `data-time-start`，延续当前播放状态（在播则继续播、暂停则停在该位置）

### F4. 标注

复用现有 anchor 流程。文字选择 / 高亮 / 写笔记的交互与纯文字模式一致；anchor 不需要新字段，时间信息由 span 隐式承载。

### F5. URL 定位

`?loc={span_id}` 参数已有 → 媒体模式下同样支持：加载后跳到该 span 且播放器 seek 到对应时间（不自动播放）。

## 非目标（MVP 不做）

- **词级高亮**：字级时间戳在后端 `/media/{unit_id}/asr_raw.json` 归档，HTML 不暴露；v2 再说
- **纯时间段 anchor**（无文字选区）：现有 span-anchor 已够
- **说话人标签 / 章节折叠**：后端暂不生成相应结构；前端不处理
- **边播边翻译**：翻译通道和当前一致，不在此模块

## 参考

- `../modules/video-ingestion.md` — HTML 输出契约、Unit metadata、media 端点
- `./frontend.md` — 阅读器总体架构（4.5 节包含媒体模式的早期设计示意，实现以本文为准）
- `../glynk-data-model.md` — span_id / Anchor 模型
