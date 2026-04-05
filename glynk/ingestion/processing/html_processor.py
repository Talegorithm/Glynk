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
        self._remove_embedded_toc(soup)

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
        for tag_name in dangerous_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        for tag in soup.find_all():
            if tag.name not in self.ALLOWED_TAGS:
                tag.unwrap()

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
            logger.info(f"Removed {removed_count} clutter elements")

        for div in list(soup.find_all('div')):
            links = div.find_all('a', recursive=True)
            if len(links) >= 3:
                total_text = div.get_text(strip=True)
                link_text = ' '.join(a.get_text(strip=True) for a in links)
                if total_text and len(link_text) / len(total_text) > 0.7:
                    div.decompose()

    def _convert_decorative_spans(self, soup: BeautifulSoup) -> None:
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

    def _remove_embedded_toc(self, soup: BeautifulSoup) -> None:
        toc_keywords = [
            'table of contents', 'contents', 'index',
            '目录', '目次', '索引', '內容',
            'chapters', '章节列表',
        ]
        chapter_keywords = [
            'chapter', 'part', 'section',
            '第', '章', 'preface', 'appendix', '附录', '序', '后记',
        ]

        for elem in soup.find_all(string=lambda text: text and any(
            keyword in text.lower() for keyword in toc_keywords
        )):
            parent = elem.parent
            if not parent:
                continue

            siblings = []
            current = parent
            for _ in range(15):
                current = current.find_next_sibling()
                if not current:
                    break
                siblings.append(current)

            if len(siblings) < 5:
                continue

            links_count = 0
            internal_links_count = 0
            chapter_links_count = 0
            for sibling in siblings:
                links = sibling.find_all('a')
                for link in links:
                    links_count += 1
                    href = link.get('href', '')
                    text = link.get_text().strip().lower()
                    if href and (href.startswith('#') or not href.startswith('http')):
                        internal_links_count += 1
                    if any(keyword in text for keyword in chapter_keywords):
                        chapter_links_count += 1

            elements_with_links = sum(1 for s in siblings if s.find('a'))
            link_density = elements_with_links / len(siblings) if siblings else 0

            is_toc = (
                links_count >= 5
                and link_density > 0.5
                and internal_links_count / links_count > 0.8
                and chapter_links_count >= 3
            )

            if is_toc:
                to_remove = [parent]
                for sibling in siblings:
                    if sibling.find('a') or len(sibling.get_text().strip()) < 100:
                        to_remove.append(sibling)
                    else:
                        break
                for tag in to_remove:
                    tag.decompose()
                break

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

            img['src'] = f"/api/media/{self.content_id}/{filename}"

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
