"""
Reader Service - 统一 read 接口

人和 AI 共用同一个接口，通过 view 参数区分渲染方式。
"""
import json
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from bs4 import BeautifulSoup

from glynk.content.locator import SpanLocator
from glynk.content.ai_view import to_ai_view
from glynk.models import parse_span_id

logger = logging.getLogger(__name__)


@dataclass
class ReadResponse:
    content: str
    from_span: str
    to_span: str
    char_count: int
    has_more: bool
    next_from: str | None = None
    translation_status: str = "original"
    annotations: list = None

    def __post_init__(self):
        if self.annotations is None:
            self.annotations = []


class ReaderService:
    """阅读器服务"""

    def __init__(self, html_root: Path, db=None):
        self.html_root = html_root
        self.locator = SpanLocator(html_root=html_root)
        self.db = db

    def read(self, content_id: str, from_span: str = None,
             size: int = None, view: str = "human",
             lang: str = None, uid: str = None) -> ReadResponse:
        """
        统一阅读接口。

        Args:
            content_id: 内容ID
            from_span: 起始 span_id（可选，默认从头）
            size: 读取字符数（可选，默认当前文件剩余）
            view: 'ai' 或 'human'
            lang: 翻译语言（仅 human 视图）
            uid: 用户 uid（用于获取 private 标注）
        """
        if from_span:
            parsed = parse_span_id(from_span)
            file_idx = parsed['file_idx']
        else:
            file_idx = 0

        if size:
            # 按指定量读取
            start = from_span or self._get_first_span(content_id, file_idx)

            # 如果指定的 span 或文件不存在，向后找有内容的文件
            if not start or not self._span_exists(content_id, start):
                for idx in range(file_idx, file_idx + 50):
                    start = self._get_first_span(content_id, idx)
                    if start:
                        break

            if not start:
                return ReadResponse(content="", from_span="", to_span="",
                                    char_count=0, has_more=False)

            located = self.locator.get_content_from_location(content_id, start, size)
            html = located.html
            from_span_actual = located.start_location
            to_span_actual = located.end_location
            char_count = located.char_count
            has_more = located.has_more

            # Calculate next_from
            next_from = None
            if has_more:
                next_from = self._get_next_span(content_id, to_span_actual)
        else:
            # 加载整个文件，跳过空文件（封面/版权页等）
            html, from_span_actual, to_span_actual, char_count = self._load_file(
                content_id, file_idx
            )
            # 跳过没有 span 的文件（封面、版权页等）
            while not self._get_first_span(content_id, file_idx):
                file_idx += 1
                if not (self.html_root / content_id / f"{file_idx}.html").exists():
                    break
            html, from_span_actual, to_span_actual, char_count = self._load_file(
                content_id, file_idx
            )

            next_file = self.html_root / content_id / f"{file_idx + 1}.html"
            has_more = next_file.exists()
            next_from = self._get_first_span(content_id, file_idx + 1) if has_more else None

        # 翻译（human 视图 + 指定语言）
        translation_status = "original"
        if view == "human" and lang:
            translated_path = self.html_root / content_id / f"{file_idx}.{lang}.html"
            if translated_path.exists():
                html = translated_path.read_text(encoding='utf-8')
                translation_status = "translated"
            else:
                translation_status = "not_available"

        # AI 视图过滤
        if view == "ai":
            html = to_ai_view(html)

        # 获取该范围内的标注
        annotations = []
        if self.db:
            annotations = self.db.get_annotations(content_id, uid=uid)

        return ReadResponse(
            content=html,
            from_span=from_span_actual,
            to_span=to_span_actual,
            char_count=char_count,
            has_more=has_more,
            next_from=next_from,
            translation_status=translation_status,
            annotations=annotations,
        )

    def _load_file(self, content_id: str, file_idx: int) -> tuple:
        """加载整个文件内容"""
        file_path = self.html_root / content_id / f"{file_idx}.html"
        if not file_path.exists():
            return "", "", "", 0

        html = file_path.read_text(encoding='utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        char_count = len(text)

        spans = [s.get('id') for s in soup.find_all('span', id=True) if s.get('id')]
        from_span = spans[0] if spans else f"{content_id}-{file_idx}-p0-s0"
        to_span = spans[-1] if spans else from_span

        return html, from_span, to_span, char_count

    def _span_exists(self, content_id: str, span_id: str) -> bool:
        """Check if a span_id exists in its corresponding HTML file"""
        try:
            parsed = parse_span_id(span_id)
            file_path = self.html_root / content_id / f"{parsed['file_idx']}.html"
            if not file_path.exists():
                return False
            html = file_path.read_text(encoding='utf-8')
            return f'id="{span_id}"' in html
        except Exception:
            return False

    def _get_first_span(self, content_id: str, file_idx: int) -> Optional[str]:
        file_path = self.html_root / content_id / f"{file_idx}.html"
        if not file_path.exists():
            return None
        html = file_path.read_text(encoding='utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        first = soup.find('span', id=True)
        return first.get('id') if first else None

    def _get_next_span(self, content_id: str, current_span: str) -> Optional[str]:
        """Get the span after current_span"""
        parsed = parse_span_id(current_span)
        file_idx = parsed['file_idx']

        file_path = self.html_root / content_id / f"{file_idx}.html"
        if not file_path.exists():
            return None

        html = file_path.read_text(encoding='utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        spans = [s.get('id') for s in soup.find_all('span', id=True) if s.get('id')]

        try:
            idx = spans.index(current_span)
            if idx + 1 < len(spans):
                return spans[idx + 1]
        except ValueError:
            pass

        # Try next file
        next_span = self._get_first_span(content_id, file_idx + 1)
        return next_span
