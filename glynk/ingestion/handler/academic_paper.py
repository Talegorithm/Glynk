"""
AcademicPaperHandler - 论文/PDF

内部调用 format_utils/pdf（MinerU 或基础模式），提取 abstract/作者/TOC。
"""
import os
from pathlib import Path

from glynk.models import ParsedContent
from glynk.ingestion.format_utils.pdf import parse_pdf_with_mineru, parse_pdf_basic


class AcademicPaperHandler:

    def supports(self, file_path: Path, source_hint: str = "") -> bool:
        if source_hint in ('arxiv.org',):
            return True
        return file_path.suffix.lower() == '.pdf'

    def parse(self, file_path: Path) -> ParsedContent:
        # Try MinerU first if configured
        mineru_url = os.getenv('MINERU_API_URL', '')
        if mineru_url:
            result = parse_pdf_with_mineru(file_path, mineru_url)
            if result:
                return self._from_mineru(result, file_path)

        # Fallback to basic extraction
        data = parse_pdf_basic(file_path)

        return ParsedContent(
            raw_html_parts=data['html_parts'],
            title=data['title'],
            author=data['author'],
            abstract=data.get('abstract', ''),
            content_type='pdf',
        )

    def _from_mineru(self, result: dict, file_path: Path) -> ParsedContent:
        """从 MinerU API 结果构建 ParsedContent"""
        markdown = result.get('markdown', '')
        images = result.get('images', {})

        # Convert markdown to HTML
        html = self._markdown_to_html(markdown)

        return ParsedContent(
            raw_html_parts=[html],
            images=images,
            title=file_path.stem,
            author='Unknown',
            content_type='pdf',
        )

    def _markdown_to_html(self, markdown: str) -> str:
        """Simple markdown to HTML conversion"""
        lines = markdown.split('\n')
        html_parts = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('# '):
                html_parts.append(f'<h1>{line[2:]}</h1>')
            elif line.startswith('## '):
                html_parts.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('### '):
                html_parts.append(f'<h3>{line[4:]}</h3>')
            else:
                html_parts.append(f'<p>{line}</p>')

        return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body>
{''.join(html_parts)}
</body>
</html>"""
