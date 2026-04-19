---
name: glk-source
description: 给一个内容线索（可能是社媒分享URL），追溯到第一手/官方内容，整理好后加入 Glynk。
disable-model-invocation: false
---

**目标**：把一个外部 URL 变成 Glynk 里一条高质量的 publication unit。"高质量"的前提是——内容来自**第一手源**，不是社媒平台的转述或片段。

前置：`GLYNK_TOKEN` / `GLYNK_API_URL` 环境变量（和 `glk-add` 共用）。

## 工作流程

**不重复摄入**：调研前先用 Glynk search / get 看看该内容是否已经入库。已存在则返回 existing unit_id。

### 1. 追到官方源：以输入 URL 为线索，找到内容的**原始发布位置**

- **不接受社媒/聚合/转述作为第一手源。域名不是判据，正文才是。** 很多内容是**编译 / 译介 / 摘要 / 报道**（关键词 "编译" "编辑" "来源" "整理自" "做客 XX 播客" "访谈" "论文" 等）。必须**读正文判断**，识别原始源（YouTube 视频、英文博客、播客、论文、推特线程等），再追过去。
- 如果追不到原始源，宁可失败也不要把二手版本入库。
- 元数据（标题、作者、发布时间、源 URL）**必须来自官方页面**，不要从转述里抄。

### 2. 取内容（按优先级）

**A. 第一方发布的原文（首选）**

作者自己发的文章、博客、Substack post、论文：
- 抓原文 → 整理成干净 markdown（保留图片、合理的标题层级）
- 用 `glk-add/upload_md.py` 上传
- Frontmatter 填 `title` / `author`

**B. 媒体文件（视频/播客，没有作者整理好的 transcript 时）**

优先级：**视频 > 纯音频 > 平台 auto CC**。
- **视频优先**：只要原内容是视频（YouTube 录播、有屏幕演示/人脸的播客等），**一律下载 mp4**。视频提供更完整的阅读体验（屏幕演示、可见身体语言），ASR 转写的质量不受容器影响，DashScope 接受 mp4 passthrough，无需 ffmpeg。纯音频下载只在来源本来就是音频（小宇宙、Apple Podcasts 纯播客）时用。
- 用 `yt-dlp` 下载时显式选合并流：`yt-dlp -f "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]" --merge-output-format mp4 <url>`。不要被 `--list-formats` 列表前面的 audio-only 条目误导。
- 上传：`glk-add/upload_media.py <file> --title ... --source-url ... --author ...`（后端 Qwen3-ASR 自动句/字级时间戳对齐）。
- **YouTube auto CC 不是官方 transcript**。它是机器字幕，质量通常劣于直接 ASR；只有当媒体下载受阻（超长、付费、地区封锁等）且作者自己给了 transcript 时，才用作者版本的 transcript 走 A 路径。

**C. 都拿不到**：不允许降级

返回失败并说明原因（"视频需登录"、"内容被删除"、"追到的源是聚合转述"）。不要兜底塞一个质量不高的版本进去。

### 3. 审阅结果，做必要的处理，或者在内容不对的情况下尝试其他获取策略

## 与其他 skill 的关系

- **`glk-add`**：本 skill 的下游。所有真正的"入库"动作都通过 `glk-add` 的 URL/文件/媒体上传通路完成。本 skill 只负责"找对源 + 整理到 glk-add 能吃的形态"。
- **`glk-search`**：查询已有内容。摄入前可先查，摄入后可回访。

## 平台 tips（遇到一个记一条）

- **微信公众号文章**（`mp.weixin.qq.com`）：
  - 抓原文要带浏览器 UA，否则拿到拦截页，且同一 IP 抓太频繁会掉到 captcha 页。示例：
    ```bash
    curl -sL -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15" <url>
    ```