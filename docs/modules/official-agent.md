# Glynk 官方Agent

> 官方Agent通读每一篇入库的内容，生成AI大纲和hooks，让内容可被搜索发现。
>
> 官方Agent使用和第三方Agent完全相同的Glynk接口，没有特殊权限。

---

## 一、产出

官方Agent通读全文后产出两样东西：

### AI大纲

一个有嵌套层级的JSON结构，整体提交给Glynk，存在 `contents.ai_outline_json`。

每个条目包含 title（标题）、description（一句话简介）、span_id（对应内容中的起始位置）。

```json
[
  {
    "title": "不确定性下的决策框架",
    "description": "论证了创业者面对不确定性时不应等待完整信息，而应主动行动",
    "span_id": "a1b2-0-p1-s1",
    "children": [
      {
        "title": "等待是最大的风险",
        "description": "信息永远不会完整，等待本身就是一种决策，且通常是最差的",
        "span_id": "a1b2-0-p5-s1",
        "children": []
      },
      {
        "title": "贝叶斯框架的应用",
        "description": "将每次行动视为一次贝叶斯更新，通过小实验逐步逼近真相",
        "span_id": "a1b2-0-p15-s1",
        "children": []
      }
    ]
  }
]
```

AI大纲替代了单独的summary和结构化的topic——大纲条目的description就是summary，大纲的层级结构本身就表达了内容的主题组织。

### Hooks

多条annotation，每条是一个**反推出来的问题**，精确指向内容中回答这个问题的具体句子。

核心思路（沿袭Resonote的question提取）：**假设这段内容是"答案"，读者可能出于什么困惑、兴趣提出了一个问题，而这段内容恰好提供了启发？**

```json
{
  "type": "hook",
  "text": "信息不完整的时候，等待和行动哪个风险更大？",
  "spans": ["a1b2-0-p8-s2", "a1b2-0-p8-s3"],
  "tags": ["决策", "不确定性", "创业"],
  "contextuality": "standalone"
}
```

关键要求：
- **问题要脱离具体情节**：让没读过这本书的人也能理解（"信息不完整时怎么决策"而不是"Peter Thiel认为什么"）
- **spans精确到回答这个问题的具体句子**（1-N个连续span），不是整个chunk
- **问题要有思辨性、情感性或启发性**，不是对信息的重述
- 如果一段内容信息太薄弱，不要强行生成hook

Hook是搜索的核心入口——Agent搜索"信息不足时如何做决策"时，命中的是hook的embedding，然后通过spans直接定位到原文中回答这个问题的那几句话。

Hook上的tags替代了单独的topic标注。

---

## 四、存储

| 产出 | 存储位置 | 说明 |
|---|---|---|
| AI大纲 | `contents.ai_outline_json` | 整体JSON，和toc_json并列 |
| Hooks | `annotations`表 | type='hook'，spans精确到句子 |

---

## 五、触发

- RSS拉取新内容入库后自动触发
- 用户提交内容时可选触发（`POST /ingest`的`auto_annotate`参数）
- 可手动重新触发（删除旧标注后重跑）

---

## 六、成本估算

| 项目 | 估算 |
|---|---|
| 每页输入 | ~12k chars内容 + 大纲JSON（~1-3k chars）≈ 5k tokens |
| 每页输出 | ~300 tokens（大纲更新 + hooks） |
| 一本20页的书 | ~100k input + 6k output tokens |
| 用gpt-4o-mini | 约 $0.01-0.03/本书 |

---

## 七、与Glynk平台的关系

官方Agent使用标准API：

```
GET  /content/{id}              → 获取内容信息和TOC
GET  /content/{id}/read         → 逐页读取（view=ai, size=12000）
PUT  /content/{id}              → 提交AI大纲（ai_outline_json）
POST /annotate/batch            → 提交hooks
```

官方Agent不在Glynk仓库内。它是一个独立服务，通过HTTP API交互。
