"""
HTMLProcessor - 三阶段 HTML 流水线处理器

Phase 1: Structure Normalization（结构规范化）
Phase 2: Rich Media Enhancement（富媒体增强）
Phase 3: Content Annotation（内容标注）

从 Resonote 复制，import 路径已调整。
"""
from bs4 import BeautifulSoup, NavigableString, Tag
from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProcessedHTML:
    """HTML处理结果"""
    html: str
    images: Dict[str, bytes]
    sentence_count: int


class HTMLProcessor:
    """一站式HTML处理器"""

    ALLOWED_TAGS = {
        'p', 'div', 'section', 'article',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'blockquote', 'pre', 'aside', 'nav', 'hr',
        'ul', 'ol', 'li', 'dl', 'dt', 'dd',
        'table', 'thead', 'tbody', 'tr', 'th', 'td', 'caption',
        'strong', 'em', 'mark', 'code', 'span',
        'a', 'br', 'small', 'cite', 'sup', 'sub',
        'img', 'figure', 'figcaption',
        'details', 'summary',  # 视频章节折叠
    }

    ALLOWED_ATTRS = {
        '*': {'id', 'class', 'epub:type', 'role', 'xml:lang'},
        'a': {'href', 'title', 'data-internal-link', 'data-target-span', 'data-ref-id', 'data-ref-content'},
        'img': {'src', 'alt', 'title'},
        'table': {'border', 'cellspacing', 'cellpadding', 'role'},
        'span': {'data-latex', 'data-time-start', 'data-time-end'},
        'div': {'data-table-id', 'data-figure-id'},
        'figure': {'data-figure-id'},
        'meta': {'name', 'content'},
    }

    def __init__(self, content_id: str, file_idx: int):
        self.content_id = content_id
        self.file_idx = file_idx
        self.span_id_prefix = f"{content_id}-{file_idx}"
        self.images = {}

    def process(self, raw_html: str, epub_images: Optional[Dict[str, bytes]] = None) -> ProcessedHTML:
        """三阶段流水线处理HTML"""
        if not raw_html or not raw_html.strip():
            return ProcessedHTML(html="", images={}, sentence_count=0)

        epub_images = epub_images or {}

        soup = self._smart_parse(raw_html)

        # Phase 1: Structure Normalization
        self._sanitize_tags(soup)
        self._remove_web_clutter(soup)
        self._convert_decorative_spans(soup)
        self._clean_attributes(soup)

        # Phase 2: Rich Media Enhancement
        from glynk.ingestion.processing.rich_media_enhancer import RichMediaEnhancer
        enhancer = RichMediaEnhancer()
        enhanced_html = enhancer.enhance(str(soup), self.content_id)
        soup = BeautifulSoup(enhanced_html, 'lxml')

        self._process_images(soup, epub_images)

        # Phase 3: Content Annotation
        from glynk.ingestion.processing.sentence_annotator import SentenceAnnotator
        annotator = SentenceAnnotator(self.content_id, self.file_idx)
        sentence_count = annotator.annotate(soup)

        # Cleanup
        self._remove_empty_tags(soup)
        self._rewrite_toc_links(soup)

        return ProcessedHTML(
            html=str(soup),
            images=self.images,
            sentence_count=sentence_count
        )

    def _smart_parse(self, raw_html: str) -> BeautifulSoup:
        head = raw_html[:500].lower()
        if any(marker in head for marker in ['<?xml', 'xmlns', 'epub:type']):
            try:
                return BeautifulSoup(raw_html, 'xml')
            except Exception:
                return BeautifulSoup(raw_html, 'lxml')
        return BeautifulSoup(raw_html, 'lxml')

    def _sanitize_tags(self, soup: BeautifulSoup) -> None:
        dangerous_tags = ['script', 'iframe', 'embed', 'object', 'style']
        danger_removed = 0
        for tag_name in dangerous_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()
                danger_removed += 1

        unwrapped = 0
        for tag in soup.find_all():
            if tag.name not in self.ALLOWED_TAGS:
                tag.unwrap()
                unwrapped += 1

        if danger_removed or unwrapped:
            logger.info(
                f"[{self.content_id}-{self.file_idx}] sanitize: "
                f"removed {danger_removed} dangerous tags, unwrapped {unwrapped} unknown tags"
            )

    def _remove_web_clutter(self, soup: BeautifulSoup) -> None:
        clutter_keywords = [
            'header', 'nav', 'navigation', 'navbar', 'menu', 'breadcrumb',
            'footer', 'copyright', 'legal', 'links-col',
            'sidebar', 'aside', 'widget',
            'ad', 'advertisement', 'promo', 'sponsor', 'banner',
            'share', 'social', 'follow',
            'modal', 'popup', 'subscribe', 'newsletter',
            'comment', 'disqus',
            'dropdown', 'dropdown-', 'login', 'right-menu', 'dialog',
        ]

        removed_count = 0
        for tag in list(soup.find_all()):
            if not isinstance(tag, Tag) or tag.parent is None:
                continue

            classes = tag.get('class', [])
            if isinstance(classes, list):
                removed = False
                for keyword in clutter_keywords:
                    if any(keyword in c.lower() for c in classes):
                        tag.decompose()
                        removed_count += 1
                        removed = True
                        break
                if removed:
                    continue

            tag_id = tag.get('id', '')
            if tag_id:
                for keyword in clutter_keywords:
                    if keyword in tag_id.lower():
                        tag.decompose()
                        removed_count += 1
                        break

        if removed_count > 0:
            logger.info(
                f"[{self.content_id}-{self.file_idx}] clutter: "
                f"removed {removed_count} elements by class/id keyword match"
            )

        link_heavy_removed = 0
        for div in list(soup.find_all('div')):
            links = div.find_all('a', recursive=True)
            if len(links) >= 3:
                total_text = div.get_text(strip=True)
                link_text = ' '.join(a.get_text(strip=True) for a in links)
                if total_text and len(link_text) / len(total_text) > 0.7:
                    div.decompose()
                    link_heavy_removed += 1
        if link_heavy_removed:
            logger.info(
                f"[{self.content_id}-{self.file_idx}] clutter: "
                f"removed {link_heavy_removed} link-heavy divs (>70% text in links)"
            )

    def _convert_decorative_spans(self, soup: BeautifulSoup) -> None:
        by_kind: dict[str, int] = {}
        for span in soup.find_all('span'):
            style = span.get('style', '')
            new_tag_name = self._get_semantic_tag_for_style(style)
            if new_tag_name:
                new_tag = soup.new_tag(new_tag_name)
                for attr, value in span.attrs.items():
                    if attr != 'style':
                        new_tag[attr] = value
                for child in list(span.children):
                    new_tag.append(child)
                span.replace_with(new_tag)
                by_kind[new_tag_name] = by_kind.get(new_tag_name, 0) + 1
        if by_kind:
            detail = ", ".join(f"{v} → <{k}>" for k, v in by_kind.items())
            logger.info(
                f"[{self.content_id}-{self.file_idx}] decorative spans: {detail}"
            )

    def _get_semantic_tag_for_style(self, style: str) -> Optional[str]:
        if not style:
            return None
        style_lower = style.lower().strip()
        if 'font-weight' in style_lower and 'bold' in style_lower:
            return 'strong'
        if 'font-style' in style_lower and 'italic' in style_lower:
            return 'em'
        if 'background-color' in style_lower or 'background:' in style_lower:
            return 'mark'
        return None

    def _clean_attributes(self, soup: BeautifulSoup) -> None:
        for tag in soup.find_all():
            if not isinstance(tag, Tag):
                continue
            allowed_attrs = self.ALLOWED_ATTRS.get(tag.name, set())
            allowed_attrs = allowed_attrs | self.ALLOWED_ATTRS.get('*', set())
            attrs_to_remove = [attr for attr in tag.attrs.keys() if attr not in allowed_attrs]
            for attr in attrs_to_remove:
                del tag[attr]

    def _remove_empty_tags(self, soup: BeautifulSoup) -> None:
        self_closing_tags = {'br', 'img', 'hr'}
        changed = True
        while changed:
            changed = False
            for tag in soup.find_all():
                if tag.name in self_closing_tags:
                    continue
                has_self_closing = any(
                    child.name in self_closing_tags for child in tag.find_all()
                )
                if not tag.get_text(strip=True) and not tag.find_all() and not has_self_closing:
                    tag.decompose()
                    changed = True

    def _process_images(self, soup: BeautifulSoup, epub_images: Dict[str, bytes]) -> None:
        for img in soup.find_all('img'):
            original_src = img.get('src', '')
            if not original_src:
                continue

            filename = original_src.split('/')[-1]
            if not filename:
                filename = f"img_{len(self.images)}.jpg"

            image_data = None
            for key in epub_images.keys():
                if key.endswith(filename) or key.endswith(original_src):
                    image_data = epub_images[key]
                    break

            if not image_data and original_src.startswith('http'):
                try:
                    import httpx
                    response = httpx.get(original_src, timeout=10, follow_redirects=True)
                    response.raise_for_status()
                    image_data = response.content
                except Exception as e:
                    logger.warning(f"Failed to download image {original_src}: {e}")

            if image_data:
                self.images[filename] = image_data

            img['src'] = f"/media/{self.content_id}/{filename}"

    def _rewrite_toc_links(self, soup: BeautifulSoup) -> None:
        for a in soup.find_all('a'):
            href = a.get('href', '')
            is_internal = href and (
                '.html' in href or '.xhtml' in href or href.startswith('#')
            )
            if is_internal:
                a['data-internal-link'] = href
                a['href'] = '#'

    @staticmethod
    def extract_text_from_spans(html: str, span_ids: List[str]) -> str:
        soup = BeautifulSoup(html, 'lxml')
        texts = []
        for span_id in span_ids:
            span = soup.find('span', id=span_id)
            if span:
                texts.append(span.get_text().strip())
        return ' '.join(texts)
