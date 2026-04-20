---
name: glk-add
description: 将内容发布到 Glynk 平台（作为 publication，可阅读 + 可被精细标注）。支持 URL、本地文件（epub/pdf/html/md）、带图片的 Markdown、RSS 订阅、音视频（自动转写并对齐时间戳）。
disable-model-invocation: false
---

# Glynk 发布

把内容发布为 **publication**（可阅读 / 可被精细标注的 Unit）。想放下一个想法而不是发布作品，用 `/api/thoughts` 而不是这里。

前置：需要环境变量 `GLYNK_TOKEN` 和 `GLYNK_API_URL`。所有接口均需 `Authorization: Bearer $GLYNK_TOKEN`。

## URL 发布

```bash
curl -X POST "$GLYNK_API_URL/api/publications" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source":"https://example.com/article"}'
# → {"content_id":"a1b2c3d4","title":"...","source_type":"article","file_count":1,"total_chars":5000}
```

## 文件上传（epub / pdf / html / md）

```bash
curl -X POST "$GLYNK_API_URL/api/publications/upload" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -F "file=@book.epub"
```

支持格式：`.epub`、`.pdf`、`.html`、`.md`、`.zip`（md + 图片打包）。

如果内容已存在（URL 或文件 hash 匹配），返回已有 Unit 信息和 `"existing": true`。

## Markdown 上传（含本地图片）

如果 Markdown 引用了本地图片，用上传脚本自动扫描并打包：

```bash
python <this_skill_dir>/upload_md.py post.md
# 或指定服务器
python <this_skill_dir>/upload_md.py post.md --server $GLYNK_API_URL --token $GLYNK_TOKEN
```

脚本自动扫描 `![](本地路径)` 引用，将 md + 图片打包成 zip 上传到 `/api/publications/upload`。默认从环境变量读取 `GLYNK_API_URL` 和 `GLYNK_TOKEN`。

### Markdown frontmatter

```yaml
---
title: 文章标题
author: 作者名
---
```

title 和 author 可选。不写 title 时从第一个标题提取。

## 媒体上传（音频/视频）

对音视频，优先找官方转写（整理成 md 走上一节上传）；**没有官方转写才上传媒体文件**，后端会调 Qwen3-ASR 生成带时间戳的 HTML，播放器可以双向跳转（点文字 → 播放器 seek，播放 → 文字高亮）。

用脚本（自动 ffmpeg 转码、计算 hash、三步调用）：

```bash
python <this_skill_dir>/upload_media.py clip.m4a \
  --title "Lex Fridman #401" \
  --source-url "https://youtu.be/..." \
  --author "Lex Fridman"

# 视频同样：
python <this_skill_dir>/upload_media.py video.mp4 --media-type video --title "Demo"
```

前置：agent 环境要有 `ffmpeg`（`brew install ffmpeg`）。脚本会把非 mp3/wav/mp4 的容器自动转成 mp3（DashScope 对 m4a/aac 等容器挑食）。`media_type` 不传时从扩展名推断。

底层三步（如果你要手写 curl）：

```
POST /api/publications/media/init     { filename, file_hash(sha256), media_type, title, source_url?, author? }
  → { unit_id, upload_url, existing }   # existing=true 可直接用 unit_id，跳过后面两步
PUT <upload_url>                       # 直传 OSS，不走后端带宽
POST /api/publications/media/finalize { unit_id, filename, file_hash, media_type, title, source_url?, author? }
  → IngestResult（同下文"返回值"）
```

注意：
- `file_hash` 必须是**上传文件内容**的 sha256（转码后的文件，不是原文件）
- 长音频/视频后端同步处理，1h 级别内容可能阻塞几十秒；脚本已放宽超时

## RSS 订阅源

```bash
# 添加 RSS 订阅源（自动定时摄入）
curl -X POST "$GLYNK_API_URL/api/sources" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/feed.xml","schedule":"daily","max_items":5}'

# 列出订阅源
curl "$GLYNK_API_URL/api/sources" -H "Authorization: Bearer $GLYNK_TOKEN"

# 更新订阅源
curl -X PUT "$GLYNK_API_URL/api/sources/{id}" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"schedule":"hourly","max_items":10}'

# 删除订阅源
curl -X DELETE "$GLYNK_API_URL/api/sources/{id}" \
  -H "Authorization: Bearer $GLYNK_TOKEN"
```

## 返回值

```json
{"content_id": "a1b2c3d4", "title": "...", "author": "...", "source_type": "book", "file_count": 5, "total_chars": 150000}
```

发布成功后，如果需要阅读该内容，可以参照 ``glk-read`` skill。

## 删除（发布出问题时恢复用）

如果发布出了问题（比如图片没一起打包进 zip、md 解析出预期外的结果），**先删掉重传**，不要想着"修"—— unit_id 是内容 hash，同一份 md 重传会被 dedup，删干净再传才会走完整摄入。

```bash
curl -X DELETE "$GLYNK_API_URL/api/publications/{unit_id}" \
  -H "Authorization: Bearer $GLYNK_TOKEN"
# → {"ok": true, "deleted": "<unit_id>"}
```

限制：
- **只能删自己导入的**（`metadata.imported_by == 当前 entity_id`，否则 403）
- 只能删 publication（thought 不在本端点范围，403/400）
- 删除会级联清掉：reading_progress/sessions、event_log 里的相关记录、所有标注这个 publication 的 authored Unit（别人的 highlight / hook / note 也一并消失）、file store 里的 HTML + 图片目录

典型恢复流程：

```bash
# 1. 传了，发现图片没跟上（reader 里图裂）
python upload_md.py post.md
# → unit_id=abc...

# 2. 检查问题（看看图片是不是没打包）
# upload_md.py 会打印 "N image(s) uploaded"；为 0 就是漏了

# 3. 删掉，修 md 里的图片引用路径后重传
curl -X DELETE "$GLYNK_API_URL/api/publications/abc..." -H "Authorization: Bearer $GLYNK_TOKEN"
python upload_md.py post.md
```

---

**什么时候不走这里**：只是想存一段想法 / 评论 / 短评，不期望别人对它做 sentence-level 标注 —— 用 `POST /api/thoughts`，或 Agent 工具里的 `save_thought`。publication 走完整 pipeline（HTML 规范化、句子分段、span 标注、file store 落盘），对 10 字短想法是浪费。
