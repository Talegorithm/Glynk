"""
BookHandler - 书籍（EPUB）

内部调用 format_utils/epub，直接从 EPUB package 读元数据。
"""
from pathlib import Path

from glynk.models import ParsedContent
from glynk.ingestion.format_utils.epub import read_epub


class BookHandler:

    def supports(self, file_path: Path, source_hint: str = "") -> bool:
        return file_path.suffix.lower() == '.epub'

    def parse(self, file_path: Path) -> ParsedContent:
        data = read_epub(file_path)

        return ParsedContent(
            raw_html_parts=data['html_parts'],
            file_names=data['file_names'],
            images=data['images'],
            title=data['title'],
            author=data['author'],
            abstract=data['abstract'],
            toc=data['toc'],
            cover_image=data['cover_path'],
            content_type='book',
        )
