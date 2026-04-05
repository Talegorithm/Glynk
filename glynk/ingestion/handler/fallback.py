"""
FallbackHandler - 兜底

按文件扩展名选 format_util，h1取标题，meta取作者。
"""
from pathlib import Path
from bs4 import BeautifulSoup

from glynk.models import ParsedContent


class FallbackHandler:

    def supports(self, file_path: Path, source_hint: str = "") -> bool:
        return True  # 永远兜底

    def parse(self, file_path: Path) -> ParsedContent:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Try to parse as HTML
        soup = BeautifulSoup(content, 'lxml')

        title = ""
        if soup.title:
            title = soup.title.string or ""
        if not title:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text().strip()

        author = "Unknown"
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author:
            author = meta_author.get('content', 'Unknown')

        return ParsedContent(
            raw_html_parts=[content],
            title=title,
            author=author,
            content_type='generic',
        )
