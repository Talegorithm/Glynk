"""
SpanExtractor - Span 元数据提取器

从 Resonote 复制，import 路径已调整。
"""
from bs4 import BeautifulSoup, Tag
from typing import List, Tuple
from glynk.models import HTMLSpan
import logging

logger = logging.getLogger(__name__)


class SpanExtractor:

    def __init__(self, content_id: str):
        self.content_id = content_id

    def extract_from_file(self, file_name: str, html_content: str) -> List[HTMLSpan]:
        if not html_content or not html_content.strip():
            return []

        soup = BeautifulSoup(html_content, 'lxml')
        sentence_spans = soup.find_all('span', id=True)

        if not sentence_spans:
            return []

        html_spans = []
        char_offset = 0

        for span_tag in sentence_spans:
            span_id = span_tag.get('id')
            if not span_id:
                continue

            text = span_tag.get_text()
            text_length = len(text)

            parent = span_tag.parent
            element_type = parent.name if parent and isinstance(parent, Tag) else 'unknown'

            text_preview = text[:200] if len(text) > 200 else text

            html_span = HTMLSpan(
                span_id=span_id,
                content_id=self.content_id,
                file_name=file_name,
                char_offset=char_offset,
                text_preview=text_preview,
                char_length=text_length,
                path_id="",
                element_type=element_type
            )
            html_spans.append(html_span)
            char_offset += text_length

        return html_spans

    def extract_from_files(self, html_files: List[Tuple[str, str]]) -> List[HTMLSpan]:
        all_spans = []
        for file_name, html_content in html_files:
            spans = self.extract_from_file(file_name, html_content)
            all_spans.extend(spans)
        return all_spans
