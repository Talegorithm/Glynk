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

    def read_file(self, content_id: str, file_idx: int = None, from_span: str = None,
                  lang: str = None, uid: str = None) -> ReadResponse:
        """加载完整文件（前端阅读器使用）"""
        if file_idx is None:
            if from_span:
                parsed = parse_span_id(from_span)
                file_idx = parsed['file_idx']
            else:
                file_idx = 0

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

        # 翻译
        translation_status = "original"
        if lang:
            translated_path = self.html_root / content_id / f"{file_idx}.{lang}.html"
            if translated_path.exists():
                html = translated_path.read_text(encoding='utf-8')
                translation_status = "translated"
            else:
                translation_status = "not_available"

        annotations = self.db.get_annotations(content_id, uid=uid) if self.db else []

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

    def read_chunk(self, content_id: str, size: int, from_span: str = None,
                   uid: str = None) -> ReadResponse:
        """加载指定字数的切片（AI Agent使用）"""
        if from_span:
            parsed = parse_span_id(from_span)
            file_idx = parsed['file_idx']
        else:
            file_idx = 0

        start = from_span or self._get_first_span(content_id, file_idx)

        if not start or not self._span_exists(content_id, start):
            for idx in range(file_idx, file_idx + 50):
                start = self._get_first_span(content_id, idx)
                if start:
                    break

        if not start:
            return ReadResponse(content="", from_span="", to_span="",
                                char_count=0, has_more=False)

        located = self.locator.get_content_from_location(content_id, start, size)
        html = to_ai_view(located.html)  # AI filter
        
        has_more = located.has_more
        next_from = self._get_next_span(content_id, located.end_location) if has_more else None

        annotations = self.db.get_annotations(content_id, uid=uid) if self.db else []

        return ReadResponse(
            content=html,
            from_span=located.start_location,
            to_span=located.end_location,
            char_count=located.char_count,
            has_more=has_more,
            next_from=next_from,
            translation_status="original",
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
