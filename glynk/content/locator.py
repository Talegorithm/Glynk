"""
SpanLocator - 基于 span_id 的内容定位器

从 Resonote 复制，去掉 Redis 缓存，简化 config 依赖。
"""
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup, Tag
from dataclasses import dataclass

from glynk.models import parse_span_id
from glynk.storage.file_store import FileStore, LocalFileStore

logger = logging.getLogger(__name__)


@dataclass
class LocatedContent:
    start_location: str
    end_location: str
    html: str
    text: str
    char_count: int
    has_more: bool


class SpanLocator:

    def __init__(self, html_root: Path = None, file_store: FileStore = None):
        self.file_store = file_store or LocalFileStore(html_root or Path("/data/glynk/html"))

    def get_content_from_location(self, content_id: str, start_location: str,
                                  target_chars: int) -> LocatedContent:
        start_parsed = parse_span_id(start_location)
        start_file_idx = start_parsed['file_idx']

        all_spans = self._load_spans_from_file_idx(content_id, start_file_idx, forward=True)

        if not all_spans:
            raise ValueError(f"Cannot load spans for content {content_id} from file {start_file_idx}")

        start_idx = None
        for i, span in enumerate(all_spans):
            if span['span_id'] == start_location:
                start_idx = i
                break

        if start_idx is None:
            raise ValueError(f"Location {start_location} not found")

        accumulated_chars = 0
        end_idx = start_idx
        selected_spans = []

        for i in range(start_idx, len(all_spans)):
            span = all_spans[i]
            if span['char_length'] == 0 or not span['text'].strip():
                continue
            selected_spans.append(span)
            accumulated_chars += span['char_length']
            if accumulated_chars >= target_chars:
                end_idx = i
                break
        else:
            end_idx = len(all_spans) - 1

        has_more = end_idx < len(all_spans) - 1

        if selected_spans:
            end_location = selected_spans[-1]['span_id']
            html, text = self._reconstruct_html(selected_spans)
        else:
            end_location = start_location
            html = ""
            text = ""
            accumulated_chars = 0

        return LocatedContent(
            start_location=start_location,
            end_location=end_location,
            html=html,
            text=text,
            char_count=accumulated_chars,
            has_more=has_more,
        )

    def _load_spans_from_file_idx(self, content_id: str, start_file_idx: int,
                                  forward: bool = True) -> List[dict]:
        all_spans = []
        max_files = 5

        if forward:
            for offset in range(max_files):
                file_idx = start_file_idx + offset
                spans = self._load_spans_from_file(content_id, file_idx)
                if not spans:
                    break
                all_spans.extend(spans)
        else:
            for offset in range(max_files):
                file_idx = start_file_idx - offset
                if file_idx < 0:
                    break
                spans = self._load_spans_from_file(content_id, file_idx)
                if not spans:
                    break
                all_spans = spans + all_spans

        return all_spans

    def _load_spans_from_file(self, content_id: str, file_idx: int) -> List[dict]:
        html_content = self.file_store.read_html(content_id, f"{file_idx}.html")
        if html_content is None:
            return []

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            spans = []
            for span_tag in soup.find_all('span', id=True):
                span_id = span_tag.get('id')
                text = span_tag.get_text()
                spans.append({
                    'span_id': span_id,
                    'text': text,
                    'char_length': len(text),
                    'element': span_tag,
                })
            return spans
        except Exception as e:
            logger.error(f"Error loading spans from {file_path}: {e}")
            return []

    def _reconstruct_html(self, spans: List[dict]) -> Tuple[str, str]:
        html_parts = []
        current_parent_name = None
        current_parent_html = []

        for span in spans:
            span_tag = span['element']
            parent = span_tag.parent
            parent_name = parent.name if parent else None

            if parent_name != current_parent_name:
                if current_parent_html:
                    if current_parent_name:
                        html_parts.append(
                            f"<{current_parent_name}>{''.join(current_parent_html)}</{current_parent_name}>"
                        )
                    else:
                        html_parts.append(''.join(current_parent_html))
                current_parent_name = parent_name
                current_parent_html = []

            current_parent_html.append(str(span_tag))

        if current_parent_html:
            if current_parent_name:
                html_parts.append(
                    f"<{current_parent_name}>{''.join(current_parent_html)}</{current_parent_name}>"
                )
            else:
                html_parts.append(''.join(current_parent_html))

        html = '\n'.join(html_parts)
        text = ''.join(span['text'] for span in spans)
        return html, text
