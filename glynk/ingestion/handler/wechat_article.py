"""
WeChatArticleHandler - 微信公众号文章

内部调用 format_utils/html，用 WeChat 专属 CSS 选择器提取。
"""
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import logging

from glynk.models import ParsedContent, TOCItem

logger = logging.getLogger(__name__)


class WeChatArticleHandler:

    def supports(self, file_path: Path, source_hint: str = "") -> bool:
        if source_hint == 'mp.weixin.qq.com':
            return True
        if file_path.suffix.lower() in ('.html', '.htm'):
            return self._detect_wechat_html(file_path)
        return False

    def _detect_wechat_html(self, file_path: Path) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                head = f.read(2000)
            return 'rich_media_content' in head or 'js_content' in head
        except Exception:
            return False

    def parse(self, file_path: Path) -> ParsedContent:
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()

        soup = BeautifulSoup(html, 'lxml')

        title = self._extract_title(soup)
        author = self._extract_author(soup)
        content_html = self._extract_content(soup)
        cleaned_html = self._clean_wechat_elements(content_html)
        toc = self._generate_toc(cleaned_html)

        return ParsedContent(
            raw_html_parts=[str(cleaned_html)],
            title=title,
            author=author,
            toc=toc,
            content_type='wechat_article',
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_elem = soup.find('h1', class_='rich_media_title')
        if title_elem:
            return title_elem.get_text().strip()
        title_elem = soup.find('h1', id='activity-name')
        if title_elem:
            return title_elem.get_text().strip()
        if soup.title:
            t = soup.title.get_text().strip()
            if t and t.lower() != 'untitled':
                return t
        return ""

    def _extract_author(self, soup: BeautifulSoup) -> str:
        author_elem = soup.find('a', class_='rich_media_meta_nickname')
        if author_elem:
            return author_elem.get_text().strip()
        author_elem = soup.find(id='js_name')
        if author_elem:
            return author_elem.get_text().strip()
        return "Unknown"

    def _extract_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        content_div = soup.find('div', class_='rich_media_content')
        if content_div:
            return content_div
        content_div = soup.find('div', id='js_content')
        if content_div:
            return content_div
        return soup.find('body') or soup

    def _clean_wechat_elements(self, content_soup) -> BeautifulSoup:
        for tag in content_soup.find_all(['script', 'style']):
            tag.decompose()
        for tag in content_soup.find_all(class_=lambda x: x and 'js_' in x):
            tag.decompose()
        for tag in content_soup.find_all(class_='qr_code_pc'):
            tag.decompose()
        for tag in content_soup.find_all(id='js_pc_qr_code'):
            tag.decompose()
        return content_soup

    def _generate_toc(self, content_soup) -> List[TOCItem]:
        for level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            headings = content_soup.find_all(level)
            if headings:
                toc = []
                for idx, heading in enumerate(headings):
                    title_text = heading.get_text(strip=True)
                    if not title_text:
                        continue
                    heading_id = heading.get('id') or f"heading-{idx}"
                    heading['id'] = heading_id
                    toc.append(TOCItem(title=title_text, href=f"0.html#{heading_id}"))
                return toc
        return []
