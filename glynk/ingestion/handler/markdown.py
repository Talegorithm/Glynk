"""
MarkdownHandler - 用户 Markdown 内容

支持 .md 直传和 .zip（md + 图片）打包上传。
Frontmatter 提取 title/author，本地图片引用自动收集。
"""
import re
import tempfile
import zipfile
from pathlib import Path

import markdown

from glynk.models import ParsedContent


class MarkdownHandler:

    def supports(self, file_path: Path, source_hint: str = "") -> bool:
        if file_path.suffix.lower() == '.md':
            return True
        if file_path.suffix.lower() == '.zip':
            try:
                with zipfile.ZipFile(file_path) as zf:
                    return any(n.endswith('.md') for n in zf.namelist())
            except zipfile.BadZipFile:
                return False
        return False

    def parse(self, file_path: Path) -> ParsedContent:
        if file_path.suffix.lower() == '.zip':
            return self._parse_zip(file_path)
        return self._parse_md(file_path)

    def _parse_md(self, file_path: Path, images_dir: Path | None = None) -> ParsedContent:
        md_text = file_path.read_text(encoding='utf-8')

        title, author, md_body = self._extract_frontmatter(md_text)

        # Collect local images
        images: dict[str, bytes] = {}
        if images_dir is None:
            images_dir = file_path.parent

        for img_ref in self._find_image_refs(md_body):
            img_path = images_dir / img_ref
            if img_path.exists():
                images[img_ref] = img_path.read_bytes()

        # Markdown → HTML
        html_body = markdown.markdown(
            md_body,
            extensions=['fenced_code', 'tables'],
        )

        if not title:
            title = self._extract_first_heading(html_body) or file_path.stem

        full_html = (
            '<!DOCTYPE html>\n<html>\n'
            f'<head><meta charset="UTF-8"><title>{title}</title></head>\n'
            f'<body>\n{html_body}\n</body>\n</html>'
        )

        return ParsedContent(
            raw_html_parts=[full_html],
            images=images,
            title=title,
            author=author,
            content_type='markdown',
        )

    def _parse_zip(self, zip_path: Path) -> ParsedContent:
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(tmpdir)

            tmp = Path(tmpdir)
            md_files = list(tmp.rglob('*.md'))
            if not md_files:
                raise ValueError("No .md file found in zip")

            md_file = md_files[0]
            return self._parse_md(md_file, images_dir=md_file.parent)

    @staticmethod
    def _extract_frontmatter(text: str) -> tuple[str, str, str]:
        """Extract YAML frontmatter. Returns (title, author, body)."""
        if not text.startswith('---'):
            return "", "", text

        end = text.find('---', 3)
        if end == -1:
            return "", "", text

        frontmatter = text[3:end].strip()
        body = text[end + 3:].strip()

        title = ""
        author = ""
        for line in frontmatter.split('\n'):
            line = line.strip()
            if line.lower().startswith('title:'):
                title = line[6:].strip().strip('"').strip("'")
            elif line.lower().startswith('author:'):
                author = line[7:].strip().strip('"').strip("'")

        return title, author, body

    @staticmethod
    def _find_image_refs(md_text: str) -> list[str]:
        """Find local image references in Markdown."""
        refs = []
        for match in re.finditer(r'!\[.*?\]\(([^)]+)\)', md_text):
            path = match.group(1).split(' ')[0]  # strip optional title
            if not path.startswith(('http://', 'https://', '/')):
                refs.append(path)
        return refs

    @staticmethod
    def _extract_first_heading(html: str) -> str:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        h = soup.find(re.compile(r'^h[1-6]$'))
        return h.get_text(strip=True) if h else ""
