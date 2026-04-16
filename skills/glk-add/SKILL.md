---
name: glk-add
description: 将内容添加到 Glynk 平台，从而获取结构化的结果方便LLM处理，或者让用户在阅读器方便地中阅读、记录易于召回的笔记。支持 URL、本地文件（epub/pdf/html/md）、带图片的 Markdown、RSS 订阅。
disable-model-invocation: true
---

# Glynk 导入

将内容导入 Glynk 平台，支持多种来源和格式。

前置：需要环境变量 `GLYNK_TOKEN` 和 `GLYNK_API_URL`。所有接口均需 `Authorization: Bearer $GLYNK_TOKEN`。

## URL 导入

```bash
curl -X POST "$GLYNK_API_URL/api/ingest" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source":"https://example.com/article"}'
# → {"content_id":"a1b2c3d4","title":"...","source_type":"article","file_count":1,"total_chars":5000}
```

## 文件上传（epub / pdf / html / md）

```bash
curl -X POST "$GLYNK_API_URL/api/ingest/upload" \
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

脚本自动扫描 `![](本地路径)` 引用，将 md + 图片打包成 zip 上传到 `/api/ingest/upload`。默认从环境变量读取 `GLYNK_API_URL` 和 `GLYNK_TOKEN`。

### Markdown frontmatter

```yaml
---
title: 文章标题
author: 作者名
---
```

title 和 author 可选。不写 title 时从第一个标题提取。

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

导入成功后，如果需要阅读该内容，可以参照 ``glk-read`` skill。
