"""
SentenceAnnotator - 句子级 ID 标注器（Phase 3）

从 Resonote 复制，import 路径已调整。
"""
from bs4 import BeautifulSoup, NavigableString, Tag
from dataclasses import dataclass
from typing import List, Optional, Any
import jionlp as jio
import logging

logger = logging.getLogger(__name__)

BLOCK_ELEMENTS = {
    'figure', 'div', 'table', 'blockquote', 'pre',
    'ul', 'ol', 'dl', 'section', 'article', 'aside', 'nav', 'hr',
    'details',
}

INLINE_FORMAT_TAGS = {
    'sup', 'sub', 'strong', 'em', 'mark', 'code',
    'small', 'cite', 'abbr', 'dfn', 'kbd', 'samp', 'var',
    'del', 'ins', 'q',
}


@dataclass
class TextNode:
    node: Any
    start: int
    end: int
    text: str


class TextRangeMapper:
    def __init__(self):
        self.full_text: str = ""
        self.text_nodes: List[TextNode] = []

    def build_from_block(self, block: Tag) -> None:
        self.full_text = ""
        self.text_nodes = []
        self._current_pos = 0
        self._collect_leaf_nodes(block)

    def _collect_leaf_nodes(self, element: Tag) -> None:
        for child in element.children:
            if isinstance(child, Tag) and child.name in BLOCK_ELEMENTS:
                continue

            if isinstance(child, NavigableString):
                text = str(child)
                if text and text.strip():
                    text_node = TextNode(
                        node=child,
                        start=self._current_pos,
                        end=self._current_pos + len(text),
                        text=text
                    )
                    self.text_nodes.append(text_node)
                    self.full_text += text
                    self._current_pos += len(text)

            elif isinstance(child, Tag):
                if child.name in INLINE_FORMAT_TAGS:
                    text = child.get_text()
                    has_content = (text and text.strip()) or len(list(child.children)) > 0
                    if has_content:
                        if not text or not text.strip():
                            text = " "
                        text_node = TextNode(
                            node=child,
                            start=self._current_pos,
                            end=self._current_pos + len(text),
                            text=text
                        )
                        self.text_nodes.append(text_node)
                        self.full_text += text
                        self._current_pos += len(text)
                    continue

                has_tag_children = any(isinstance(c, Tag) for c in child.children)
                if has_tag_children:
                    self._collect_leaf_nodes(child)
                else:
                    text = child.get_text()
                    if text and text.strip():
                        text_node = TextNode(
                            node=child,
                            start=self._current_pos,
                            end=self._current_pos + len(text),
                            text=text
                        )
                        self.text_nodes.append(text_node)
                        self.full_text += text
                        self._current_pos += len(text)

    def get_nodes_in_range(self, query_start: int, query_end: int) -> List[Any]:
        result = []
        for text_node in self.text_nodes:
            if text_node.end <= query_start:
                continue
            if text_node.start >= query_end:
                break
            result.append(text_node.node)
        return result


class SentenceAnnotator:
    def __init__(self, content_id: str, file_idx: int):
        self.content_id = content_id
        self.file_idx = file_idx
        self.sentence_count = 0

    def annotate(self, soup: BeautifulSoup) -> int:
        blocks = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'])

        paragraph_count = 0
        for block in blocks:
            has_block_children = any(
                isinstance(child, Tag) and child.name in BLOCK_ELEMENTS
                for child in block.children
            )

            paragraph_count += 1
            block_id = f"{self.content_id}-{self.file_idx}-p{paragraph_count}"
            block['id'] = block_id

            if has_block_children:
                self._annotate_mixed_block(soup, block, block_id)
            else:
                self._annotate_text_block(soup, block, block_id)

        return self.sentence_count

    def _annotate_text_block(self, soup: BeautifulSoup, block: Tag, block_id: str) -> None:
        mapper = TextRangeMapper()
        mapper.build_from_block(block)

        if not mapper.full_text.strip():
            return

        sentences = jio.split_sentence(mapper.full_text)

        sentence_spans = []
        current_pos = 0

        for i, sentence in enumerate(sentences, 1):
            sentence_start = mapper.full_text.find(sentence, current_pos)
            if sentence_start == -1:
                continue

            sentence_end = sentence_start + len(sentence)
            current_pos = sentence_end

            self.sentence_count += 1
            span_id = f"{block_id}-s{i}"
            span = soup.new_tag('span')
            span['id'] = span_id

            self._extract_nodes_for_range(soup, mapper, span, sentence_start, sentence_end)
            sentence_spans.append(span)

        block.clear()
        for span in sentence_spans:
            block.append(span)

    def _extract_nodes_for_range(self, soup, mapper, target_span, range_start, range_end):
        for text_node in mapper.text_nodes:
            if text_node.end <= range_start:
                continue
            if text_node.start >= range_end:
                break

            overlap_start = max(text_node.start, range_start)
            overlap_end = min(text_node.end, range_end)
            node_start_offset = overlap_start - text_node.start
            node_end_offset = overlap_end - text_node.start

            if node_start_offset == 0 and node_end_offset == len(text_node.text):
                if isinstance(text_node.node, NavigableString):
                    target_span.append(str(text_node.node))
                else:
                    target_span.append(text_node.node.__copy__())
            else:
                partial_text = text_node.text[node_start_offset:node_end_offset]
                if isinstance(text_node.node, NavigableString):
                    target_span.append(partial_text)
                else:
                    new_tag = soup.new_tag(text_node.node.name)
                    for attr, value in text_node.node.attrs.items():
                        new_tag[attr] = value
                    new_tag.string = partial_text
                    target_span.append(new_tag)

    def _annotate_mixed_block(self, soup: BeautifulSoup, block: Tag, block_id: str) -> None:
        children = list(block.children)
        block.clear()

        text_buffer = []
        span_counter = 1

        for child in children:
            if isinstance(child, Tag) and child.name in BLOCK_ELEMENTS:
                if text_buffer:
                    span = self._wrap_text_nodes(soup, text_buffer, f"{block_id}-s{span_counter}")
                    if span:
                        block.append(span)
                        span_counter += 1
                    text_buffer = []
                block.append(child)
            else:
                text_buffer.append(child)

        if text_buffer:
            span = self._wrap_text_nodes(soup, text_buffer, f"{block_id}-s{span_counter}")
            if span:
                block.append(span)

    def _wrap_text_nodes(self, soup, nodes, span_id) -> Optional[Tag]:
        combined_text = ''.join(
            str(node) if isinstance(node, NavigableString) else node.get_text()
            for node in nodes
        ).strip()

        if not combined_text:
            return None

        self.sentence_count += 1
        span = soup.new_tag('span')
        span['id'] = span_id

        for node in nodes:
            if isinstance(node, NavigableString):
                span.append(str(node))
            else:
                span.append(node)

        return span
