"""
RichMediaEnhancer - 富媒体统一增强器

从 Resonote 复制，import 路径已调整。
"""
from bs4 import BeautifulSoup, NavigableString, Tag
import re
from typing import Optional, Tuple, Union


class RichMediaEnhancer:

    FIGURE_CONTENT_PATTERN = r'^(?:Figure|Fig\.?|Image|Diagram|Chart|Graph|Photo|Illustration|图|示意|示例|照片|截图|图例)\s*\d*\s*[:\：\.\-\|—]?'
    TABLE_CONTENT_PATTERN = r'^(?:Table|Tab\.?|表)\s*\d*\s*[:\：\.\-\|—]?'

    def enhance(self, html: str, content_id: str) -> str:
        if not html or not html.strip():
            return html

        soup = BeautifulSoup(html, 'lxml')

        self._enhance_formulas(soup)
        self._enhance_figures(soup, content_id)
        self._enhance_tables(soup)
        self._enhance_references(soup)

        return str(soup)

    def _has_caption_style(self, elem: Tag) -> bool:
        classes = elem.get('class', [])
        caption_keywords = ['caption', 'title', 'label', 'fig', 'table', 'center', 'grey', 'gray']
        if any(kw in str(classes).lower() for kw in caption_keywords):
            return True

        style = elem.get('style', '').lower()
        if 'font-size' in style and any(s in style for s in ['0.8', '0.9', 'small', '12px', '13px', '14px']):
            return True
        if 'color' in style and any(c in style for c in ['gray', 'grey', '#666', '#999', '#888']):
            return True
        if 'text-align' in style and 'center' in style:
            return True
        if 'font-style' in style and 'italic' in style:
            return True

        return False

    def _is_short_standalone_paragraph(self, elem: Tag, target_type: str = 'figure') -> bool:
        text = elem.get_text().strip()
        if len(text) > 100:
            return False
        next_sibling = elem.find_next_sibling()
        if target_type == 'figure':
            return next_sibling is not None and next_sibling.name == 'img'
        return next_sibling is not None and next_sibling.name == 'table'

    def _calculate_caption_score(self, elem: Tag, target_type: str = 'both') -> int:
        if elem.find(['img', 'figure', 'table']):
            return -100

        score = 0
        text = elem.get_text().strip()
        
        if target_type in ('figure', 'both') and re.match(self.FIGURE_CONTENT_PATTERN, text, re.IGNORECASE):
            score += 50
        if target_type in ('table', 'both') and re.match(self.TABLE_CONTENT_PATTERN, text, re.IGNORECASE):
            score += 50
        if self._has_caption_style(elem):
            score += 30
        if self._is_short_standalone_paragraph(elem, target_type):
            score += 20
        return score

    def _is_likely_caption(self, elem: Tag, target_type: str = 'both') -> bool:
        return self._calculate_caption_score(elem, target_type) >= 50

    def _is_footnote_marker_image(self, img: Tag) -> bool:
        parent_a = img.find_parent('a')
        if parent_a:
            epub_type = parent_a.get('epub:type', '')
            if 'noteref' in epub_type:
                return True
        img_classes = img.get('class', [])
        if isinstance(img_classes, list):
            for cls in img_classes:
                if 'footnote' in cls.lower():
                    return True
        if img.get('zy-footnote'):
            return True
        return False

    def _enhance_formulas(self, soup: BeautifulSoup) -> None:
        inline_pattern = r'\$([^\$]+)\$'
        block_pattern = r'\$\$([^\$]+)\$\$'

        def replace_inline_formula(match):
            latex = match.group(1).strip()
            span = soup.new_tag('span')
            span['class'] = 'formula formula-inline'
            span['role'] = 'math'
            span['data-latex'] = latex
            span.string = f'${latex}$'
            return str(span)

        def replace_block_formula(match):
            latex = match.group(1).strip()
            div = soup.new_tag('div')
            div['class'] = 'formula formula-block'
            div['role'] = 'math'
            div['data-latex'] = latex
            div.string = f'$${latex}$$'
            return str(div)

        for element in soup.find_all(string=True):
            if element.parent.name in ['script', 'style', 'code', 'pre']:
                continue
            new_text = str(element)
            new_text = re.sub(block_pattern, replace_block_formula, new_text)
            new_text = re.sub(inline_pattern, replace_inline_formula, new_text)
            if new_text != str(element):
                element.replace_with(BeautifulSoup(new_text, 'lxml'))

    def _enhance_figures(self, soup: BeautifulSoup, content_id: str) -> None:
        figure_counter = 1
        all_images = soup.find_all('img')

        for img in all_images:
            if self._is_footnote_marker_image(img):
                continue

            existing_figure = img.parent if img.parent and img.parent.name == 'figure' else None

            if existing_figure:
                caption_text, elem_to_remove = self._find_caption_for_img(img, content_id)
                if caption_text:
                    old_caption = existing_figure.find('figcaption')
                    if old_caption:
                        old_caption.string = caption_text
                        old_caption.clear()
                        if isinstance(caption_elem_or_text, Tag):
                            figcaption.append(caption_elem_or_text)
                        else:
                            old_caption.string = caption_elem_or_text
                    else:
                        figcaption = soup.new_tag('figcaption')
                        if isinstance(caption_elem_or_text, Tag):
                            figcaption.append(caption_elem_or_text)
                        else:
                            figcaption.string = caption_elem_or_text
                        existing_figure.append(figcaption)
                    if elem_to_remove:
                        elem_to_remove.extract()
            else:
                caption_elem_or_text, elem_to_remove = self._find_caption_for_img(img, content_id)

                figure = soup.new_tag('figure')
                figure['class'] = 'content-figure'
                figure['data-figure-id'] = f'fig-{figure_counter}'

                img_copy = img
                img.replace_with(figure)
                figure.append(img_copy)

                if caption_elem_or_text:
                    figcaption = soup.new_tag('figcaption')
                    if isinstance(caption_elem_or_text, Tag):
                        figcaption.append(caption_elem_or_text)
                    else:
                        figcaption.string = caption_elem_or_text
                    figure.append(figcaption)

                if elem_to_remove:
                    elem_to_remove.extract()

                figure_counter += 1

    def _find_caption_for_img(self, img: Tag, content_id: str) -> Tuple[Optional[Union[str, Tag]], Optional[Tag]]:
        # 1. Identify anchors: the img itself, and its structural parents (up to 3 levels)
        anchors = [img]
        current = img.parent
        for _ in range(3):
            if not current or current.name in ['body', 'html', 'article', 'main']:
                break
            anchors.append(current)
            current = current.parent

        target_tags = ['p', 'div', 'figcaption', 'h5', 'h6', 'h4', 'caption']

        # 2. Helper to scan immediate siblings (handling empty white space nodes naturally)
        def _scan_siblings(anchor: Tag, forwards: bool):
            generator = anchor.next_siblings if forwards else anchor.previous_siblings
            for sibling in generator:
                if not isinstance(sibling, Tag):
                    if sibling.strip():  # non-empty text node
                        return None, None
                    continue
                
                # We found a tag
                if not sibling.get_text(strip=True):
                    continue # Skip empty tags like <br> or empty <p>
                
                # Does the sibling match our criteria?
                if sibling.name in target_tags:
                    if self._is_likely_caption(sibling, target_type='both'):
                        return sibling, sibling
                    return None, None
                
                if sibling.name == 'div':
                    child = sibling.find(target_tags)
                    if child and child.get_text(strip=True):
                        if self._is_likely_caption(child, target_type='both'):
                            # remove the whole wrapper or just the child? Remove the whole wrapper
                            return child, sibling
                
                # Stop at the first significant block tag
                if sibling.name in ['p', 'div', 'table', 'section', 'h1', 'h2', 'h3', 'h4']:
                    break
            return None, None

        # Try scanning front and back around the anchors from innermost to outermost
        for anchor in anchors:
            caption, elem = _scan_siblings(anchor, forwards=False)
            if caption: return caption, elem
            
            caption, elem = _scan_siblings(anchor, forwards=True)
            if caption: return caption, elem

        # 3. Check if any anchor itself contains the caption text (e.g. <p><img/> Figure 1.2</p>)
        for anchor in anchors:
            if anchor.name in target_tags and anchor != img:
                text = anchor.get_text(separator=' ', strip=True)
                if text and self._calculate_caption_score(anchor, target_type='both') >= 50:
                    # Return anchor as the "element" to be used as content, but None to extract so we don't delete it
                    return anchor, None

        return None, None

    def _enhance_tables(self, soup: BeautifulSoup) -> None:
        table_counter = 1
        tables_to_process = []
        for table in soup.find_all('table'):
            if table.parent.name == 'div' and 'table-wrapper' in table.parent.get('class', []):
                continue
            tables_to_process.append(table)

        for table in tables_to_process:
            wrapper = soup.new_tag('div')
            wrapper['class'] = 'table-wrapper'
            wrapper['data-table-id'] = f'table-{table_counter}'
            table['role'] = 'table'

            prev_sibling = table.find_previous_sibling()
            if prev_sibling and prev_sibling.name == 'p':
                if self._is_likely_caption(prev_sibling, target_type='table'):
                    caption = soup.new_tag('caption')
                    caption.append(prev_sibling)
                    table.insert(0, caption)

            table.replace_with(wrapper)
            wrapper.append(table)
            table_counter += 1

    def _enhance_references(self, soup: BeautifulSoup) -> None:
        for link in soup.find_all('a'):
            epub_type = link.get('epub:type', '')

            if 'noteref' not in epub_type and 'toc' not in epub_type:
                if 'reference-link' in link.get('class', []):
                    continue
                text = link.get_text().strip()
                if not re.match(r'^\[?\d+\]?$', text):
                    continue
                href = link.get('href', '')
                if not (href and ('#' in href or href == '#')):
                    continue

            existing_classes = link.get('class', [])
            if 'reference-link' not in existing_classes:
                existing_classes.append('reference-link')
            link['class'] = existing_classes

            if not link.get('role'):
                if 'noteref' in epub_type:
                    link['role'] = 'doc-noteref'
                elif 'toc' in epub_type:
                    link['role'] = 'navigation'
                else:
                    link['role'] = 'doc-noteref'
