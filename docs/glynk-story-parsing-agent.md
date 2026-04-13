# Glynk 故事解析 Agent 设计背景

> 供新 session 讨论用的上下文文档
> 2026-04-12

---

## Glynk 是什么

面向人和 Agent 的内容平台。基本单位是 **Unit**（可寻址的想法/内容片段）。用户和 Agent 往里"放下"想法，Agent 在空间里语义漫游，把相关内容带回。详见 `analysis/glynk-overview.md`。

## 数据模型（只列相关部分）

三张核心表：

```
Entity    — 谁（人 / AI / dormant 原作者）
Unit      — 地点（一段可寻址内容，有 body + vector + metadata）
Anchor    — 边（Unit↔Unit / Unit↔Span / Entity↔Unit 的有类型关系）
```

**长 Unit 的预处理模式**：长内容（书/小说）不整体 embed，而是产生一批**派生 Unit**，各自带 vector，通过 anchor 锚回原文段落。

```
原文 Unit（一本小说）
  └─ 派生 Unit（角色描写）  anchor(role=extracted_from, target_span=第3章某段)
  └─ 派生 Unit（关键场景）  anchor(role=extracted_from, target_span=第7章某段)
  └─ 派生 Unit（叙事模式）  anchor(role=extracted_from, target_span=多处)
```

## 故事解析 Agent 的任务

输入：一个已摄入的虚构作品 Unit（小说/动漫脚本/电影剧本/...）

输出：一批派生 Unit，每个代表一个可独立检索、可被 anchor 的故事素材。

## 需要提取的素材类型（初步）

| 类型 | 说明 | 搜索场景举例 |
|---|---|---|
| **character** | 角色描写：性格、外观、关键台词、成长弧线 | "天才少年被迫隐藏实力" |
| **scene** | 场景描写：氛围、感官细节、空间 | "雨天的城市" |
| **beat** | 情节节拍：转折点、高潮、情绪转换 | "从敌对到信任的关系转变" |
| **dialogue** | 金句/关键对话 | "令人心碎的告别台词" |
| **setting** | 世界观设定：规则、历史、地理 | "赛博朋克世界的底层社会" |
| **trope** | 叙事模式/母题 | "反派其实是对的" |
| **relationship** | 关系动态：人物之间的张力和演变 | "师徒反目" |

这只是初步分类。**类型是开集**——通过 Unit.metadata.material_type 标记，不需要改 schema。

## 每个派生 Unit 的结构

```jsonc
{
  // Unit 字段
  "id": "ulid",
  "author": "story_parser_agent_entity_id",
  "origin": "authored",       // agent 产出的
  "shape": "flat",
  "body": { "html": "提取出的素材正文（自然语言描述）" },
  "vector": [/* embedding */],
  "metadata": {
    "material_type": "character",        // 素材类型
    "genre": ["fantasy", "coming-of-age"],
    "mood": ["bittersweet"],
    "source_work": "《某某小说》",
    "source_author": "原作者名",
    "extraction_confidence": 0.85        // 可选：提取置信度
  },

  // 关联的 Anchor
  "anchors": [{
    "target_type": "span",
    "target_unit": "原文unit_id",
    "target_span": "原文中对应段落的span_id",
    "role": "extracted_from"
  }]
}
```

## 需要在新 session 讨论的问题

1. **提取粒度**：一个角色出现在多处，是提取成一个汇总 Unit（"角色全貌"）还是多个 Unit（"角色在第3章"、"角色在第7章"）？还是都要？
2. **提取 prompt 设计**：是整本书一次性提取，还是按章节分段处理？上下文窗口限制怎么处理？
3. **跨作品关联**：两本不同小说里出现相似的 trope / 角色原型，要不要自动 anchor？还是留给漫游时的语义搜索自然匹配？
4. **质量控制**：提取结果要不要经过人工审核再入库？还是先全部入库、标记置信度，让用户的 Agent 在漫游时按置信度过滤？
5. **增量提取**：用户读完某章后做了标注，Agent 能不能根据标注"追加提取"新的素材（用户标注 = 兴趣信号 → 值得深挖的方向）？
6. **多模态**：动漫/电影的截图、分镜、配色 → 这些视觉素材怎么存？Unit.body 支持图片引用吗？
