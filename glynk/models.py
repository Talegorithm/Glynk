"""
Glynk 数据模型

核心数据类，不含业务逻辑。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json


# ===== 摄入相关 =====

@dataclass
class TOCItem:
    """TOC 条目（目录项）"""
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
    """Handler 的统一输出。HTML + 元数据，一步到位。"""
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
    content_id: str
    title: str
    author: str
    source_type: str
    file_count: int
    total_chars: int
    toc: list[dict] = field(default_factory=list)


# ===== 内容相关 =====

@dataclass
class Content:
    """内容实体"""
    content_id: str
    title: str
    author: str
    source_type: str
    source_url: str | None
    source_file_hash: str
    file_count: int
    toc_json: str = "[]"
    ai_outline_json: str = "[]"
    abstract: str = ""
    translations: dict = field(default_factory=dict)
    uid: str | None = None
    status: str = "parsing"
    error_message: str | None = None
    total_chars: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def get_toc(self) -> list[dict]:
        try:
            return json.loads(self.toc_json)
        except Exception:
            return []

    def get_outline(self) -> list[dict]:
        try:
            return json.loads(self.ai_outline_json)
        except Exception:
            return []


# ===== 标注相关 =====

@dataclass
class Annotation:
    """统一标注"""
    id: str
    content_id: str
    anchor: dict
    type: str           # 'highlight' | 'hook' | 'note' | 'reaction'
    text: str
    tags: list[str] = field(default_factory=list)
    contextuality: str = "standalone"
    source: str = "human"
    uid: str | None = None
    visibility: str = "public"
    query_id: str | None = None
    created_at: datetime | None = None


@dataclass
class QueryRequest:
    """检索请求"""
    text: str
    user_context: dict | None = None
    types: list[str] | None = None
    content_ids: list[str] | None = None
    uid: str | None = None
    top_k: int = 10


@dataclass
class QueryResponse:
    """检索响应"""
    query_id: str
    results: list[dict] = field(default_factory=list)


# ===== Span 相关 =====

@dataclass
class HTMLSpan:
    """HTML Span 元数据"""
    span_id: str
    content_id: str
    file_name: str
    char_offset: int
    text_preview: str
    char_length: int
    path_id: str = ""
    element_type: str = "p"


# ===== 工具函数 =====

def parse_span_id(span_id: str) -> dict:
    """
    解析 span_id 到结构化信息

    格式：{content_id}-{file_idx}-p{n}-s{m}
    示例：a1b2c3d4e5f6g7h8-1-p5-s2
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


def parse_file_idx_from_span(span_id: str) -> int:
    """从 span_id 提取 file_idx"""
    if not span_id:
        return 0
    try:
        return parse_span_id(span_id)["file_idx"]
    except ValueError:
        return 0
