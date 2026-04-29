---
name: glk-search
description: 在 Glynk 平台中语义搜索内容和标注，发现用户感兴趣的知识。当用户想找某个主题相关的内容、笔记或知识时使用。
---

# Glynk 搜索

在 Glynk 平台中搜索内容和标注，读取搜索结果的原文上下文。

前置：需要环境变量 `GLYNK_TOKEN`。`GLYNK_API_URL` 默认使用公共入口 `https://brainow.link`；如果手动设置，也应指向前端域名，由同域 `/api` 反代到后端，不要使用后端 IP 或本地端口。所有接口均需 `Authorization: Bearer $GLYNK_TOKEN`。

## 列出内容

```bash
# 全部内容
curl "$GLYNK_API_URL/api/units?limit=50" \
  -H "Authorization: Bearer $GLYNK_TOKEN"
# → {"contents":[{"content_id":"...","title":"...","author":"...","source_type":"...","total_chars":...}],"total":42}

# 只看导入的内容（书/论文/文章）
curl "$GLYNK_API_URL/api/units?origin=ingested&limit=50" \
  -H "Authorization: Bearer $GLYNK_TOKEN"

# 只看自己写的（标注/想法）
curl "$GLYNK_API_URL/api/units?author_id=me&limit=50" \
  -H "Authorization: Bearer $GLYNK_TOKEN"
```

## 语义搜索（跨所有内容）

```bash
curl -X POST "$GLYNK_API_URL/api/units/search" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "如何在信息不完整时做决策",
    "types": ["hook", "highlight"],
    "top_k": 10
  }'
# → {"query_id":"qry-...","results":[
#     {"id":"anc-123","type":"hook","text":"...","spans":[...],"score":0.92,"content_id":"a1b2c3d4"}
#   ]}
```

可用 `types` 过滤标注类型（hook / highlight / note），`content_ids` 限定搜索范围。

## 搜索自己的标注

```bash
curl -X POST "$GLYNK_API_URL/api/anchors/search" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"不确定性下的决策"}'
```

只在当前用户的 highlight / hook / note 中搜索。

## 读取搜索结果的原文上下文

找到感兴趣的结果后，读取原文上下文：

```bash
curl "$GLYNK_API_URL/api/units/{content_id}/read?size=3000&from={span_id}" \
  -H "Authorization: Bearer $GLYNK_TOKEN"
# → {"content":"<html>...</html>","from":"...","to":"...","has_more":true}
```

## 提交搜索反馈

```bash
curl -X POST "$GLYNK_API_URL/api/feedback" \
  -H "Authorization: Bearer $GLYNK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query_id":"qry-...","results":[{"result_id":"anc-123","clicked_through":true}]}'
```

## 阅读器链接

搜索结果可以生成阅读器直链，用户点击后在浏览器中定位到对应段落：

```
https://brainow.link/read/{content_id}?loc={span_id}
```
