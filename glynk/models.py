"""
Glynk 数据模型

核心：Entity / Unit / Anchor
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import json


# ===== Core: Entity / Unit / Anchor =====

@dataclass
class Entity:
    """参与者（人 / AI）"""
    id: str
    kind: str = 'human'          # human | ai
    state: str = 'active'        # active | dormant | claimed
    display_name: str = ''
    bio: str = ''
    agent_uri: str | None = None
    inspired_by: str | None = None
    created_at: datetime | None = None


@dataclass
class Unit:
    """信息单元"""
    id: str
    author_id: str
    origin: str                  # ingested | authored
    shape: str = 'flat'          # flat | structured
    body: dict = field(default_factory=dict)
    visibility: dict = field(default_factory=lambda: {"type": "public"})
    metadata: dict = field(default_factory=dict)
    vector: list[float] | None = None
    vector_text: str | None = None
    created_at: datetime | None = None


@dataclass
class Anchor:
    """锚点：连接两个实体。role 的允许集合见 ROLE_SCHEMAS。"""
    id: str
    source_type: str             # unit | entity
    source_unit: str | None = None
    source_entity: str | None = None
    target_type: str = 'unit'    # unit | span | entity
    target_unit: str | None = None
    target_span: str | None = None
    target_entity: str | None = None
    role: str = ''               # see ROLE_SCHEMAS
    metadata: dict = field(default_factory=dict)
    created_at: datetime | None = None


# ===== Role 分类与 schema =====
#
# role 描述 Anchor 的关系性质。每个 role 都约束了 (source_type, target_type, body)，
# AnchorService 创建时按 ROLE_SCHEMAS 校验。Unit.metadata.role 是从对应 Anchor 复制的
# 冗余字段，用于搜索过滤 —— 不要和 ROLE_SCHEMAS 分叉。
#
# body 语义：
#   required - source Unit 必须有非空 body（hook/note/summary 的价值在于写了什么）
#   optional - source Unit 可有 body 可无（reply 可以是 emoji / 图片 / 文字）
#   auto     - body 存在且语义为 target span 的副本（highlight）
#   none     - source 是 entity，不涉及 Unit body（like/bookmark/follow）

ROLE_SCHEMAS: dict[str, dict] = {
    'highlight': {'source': 'unit',   'target': ('span',),        'body': 'auto'},
    'hook':      {'source': 'unit',   'target': ('span',),        'body': 'required'},
    'note':      {'source': 'unit',   'target': ('span', 'unit'), 'body': 'required'},
    'summary':   {'source': 'unit',   'target': ('unit',),        'body': 'required'},
    'reply':     {'source': 'unit',   'target': ('span', 'unit'), 'body': 'optional'},
    'like':      {'source': 'entity', 'target': ('span', 'unit'), 'body': 'none'},
    'bookmark':  {'source': 'entity', 'target': ('span', 'unit'), 'body': 'none'},
    'follow':    {'source': 'entity', 'target': ('entity',),      'body': 'none'},
}


def validate_anchor(role: str, source_type: str, target_type: str,
                    has_body: bool) -> None:
    """按 ROLE_SCHEMAS 校验 anchor 参数。不合法抛 ValueError。"""
    schema = ROLE_SCHEMAS.get(role)
    if not schema:
        raise ValueError(
            f"Unknown role {role!r}. Allowed: {sorted(ROLE_SCHEMAS.keys())}"
        )
    if source_type != schema['source']:
        raise ValueError(
            f"Role {role!r} requires source_type={schema['source']!r}, "
            f"got {source_type!r}"
        )
    if target_type not in schema['target']:
        raise ValueError(
            f"Role {role!r} allows target_type in {schema['target']}, "
            f"got {target_type!r}"
        )
    body = schema['body']
    if body == 'required' and not has_body:
        raise ValueError(f"Role {role!r} requires non-empty body")
    if body == 'none' and has_body:
        raise ValueError(
            f"Role {role!r} has source=entity; body is not allowed"
        )


# ===== Ingestion =====

@dataclass
class TOCItem:
    """TOC 条目"""
    title: str
    href: str
    level: int = 1
    children: List[TOCItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "href": self.href,
            "level": self.level,
            "children": [c.to_dict() for c in self.children],
        }

    @staticmethod
    def from_dict(data: dict) -> TOCItem:
        return TOCItem(
            title=data["title"],
            href=data.get("href", ""),
            level=data.get("level", 1),
            children=[TOCItem.from_dict(c) for c in data.get("children", [])],
        )


@dataclass
class ParsedContent:
    """Handler 的统一输出"""
    raw_html_parts: list[str]
    file_names: list[str] = field(default_factory=list)
    images: dict[str, bytes] = field(default_factory=dict)
    title: str = ""
    author: str = ""
    abstract: str = ""
    toc: list[TOCItem] = field(default_factory=list)
    cover_image: str | None = None
    content_type: str = "generic"


@dataclass
class IngestResult:
    """摄入结果"""
    unit_id: str
    title: str
    author: str
    author_entity_id: str
    source_type: str
    file_count: int
    total_chars: int
    toc: list[dict] = field(default_factory=list)


# ===== Retrieval =====

@dataclass
class QueryRequest:
    """检索请求"""
    text: str
    roles: list[str] | None = None
    unit_ids: list[str] | None = None
    entity_id: str | None = None
    top_k: int = 10


@dataclass
class QueryResponse:
    """检索响应"""
    query_id: str
    results: list[dict] = field(default_factory=list)


# ===== Span =====

@dataclass
class HTMLSpan:
    """HTML Span 元数据"""
    span_id: str
    unit_id: str
    file_name: str
    char_offset: int
    text_preview: str
    char_length: int
    path_id: str = ""
    element_type: str = "p"


# ===== Utility =====

def parse_span_id(span_id: str) -> dict:
    """
    解析 span_id

    格式：{unit_id}-{file_idx}-p{n}-s{m}
    """
    parts = span_id.split("-")
    if len(parts) != 4:
        raise ValueError(f"Invalid span_id format: {span_id}")

    content_id = parts[0]
    file_idx_str = parts[1]
    p_part = parts[2]
    s_part = parts[3]

    if not p_part.startswith("p") or not s_part.startswith("s"):
        raise ValueError(f"Invalid span_id format: {span_id}")

    return {
        "content_id": content_id,
        "file_idx": int(file_idx_str),
        "file_name": f"{file_idx_str}.html",
        "paragraph": int(p_part[1:]),
        "sentence": int(s_part[1:]),
    }


def expand_span_id(span_id: str, unit_id: str) -> str:
    """补全短格式 span_id"""
    if not span_id or not unit_id:
        return span_id
    if span_id.startswith(unit_id):
        return span_id
    parts = span_id.split('-')
    if len(parts) == 3 and parts[1].startswith('p') and parts[2].startswith('s'):
        return f"{unit_id}-{span_id}"
    return span_id


def parse_file_idx_from_span(span_id: str) -> int:
    """从 span_id 提取 file_idx"""
    if not span_id:
        return 0
    try:
        return parse_span_id(span_id)["file_idx"]
    except ValueError:
        return 0
