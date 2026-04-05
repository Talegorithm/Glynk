"""
GenericArticleHandler - 通用网页文章

内部调用 format_utils/html + trafilatura。
"""
from pathlib import Path

from glynk.models import ParsedContent
from glynk.ingestion.format_utils.html import (
    read_html_file,
    extract_with_trafilatura,
    extract_basic_metadata,
)


class GenericArticleHandler:

    def supports(self, file_path: Path, source_hint: str = "") -> bool:
        return file_path.suffix.lower() in ('.html', '.htm')

    def parse(self, file_path: Path) -> ParsedContent:
        html_content = read_html_file(file_path)

        # Try trafilatura first
        extracted, metadata = extract_with_trafilatura(html_content)

        if extracted:
            title = metadata.get('title') or ""
            author = metadata.get('author') or "Unknown"

            clean_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>{title}</title></head>
<body>
{extracted}
</body>
</html>"""
            return ParsedContent(
                raw_html_parts=[clean_html],
                title=title,
                author=author,
                content_type='generic',
            )

        # Fallback to basic parsing
        meta = extract_basic_metadata(html_content)
        return ParsedContent(
            raw_html_parts=[html_content],
            title=meta['title'],
            author=meta['author'],
            content_type='generic',
        )
