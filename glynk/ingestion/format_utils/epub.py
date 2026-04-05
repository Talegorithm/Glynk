"""
EPUB 格式工具 - ebooklib 读取

从 Resonote EPUBParser 提取的格式工具部分。
"""
import ebooklib
from ebooklib import epub
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

from glynk.models import TOCItem

import logging

logger = logging.getLogger(__name__)


def read_epub(file_path: Path) -> dict:
    """
    读取 EPUB 文件，返回所有数据。

    Returns:
        {
            'title': str,
            'author': str,
            'html_parts': List[str],
            'file_names': List[str],
            'toc': List[TOCItem],
            'images': Dict[str, bytes],
            'cover_path': str | None,
            'abstract': str,
        }
    """
    book = epub.read_epub(str(file_path))

    title = _get_metadata(book, 'title') or ""
    author = _get_metadata(book, 'creator') or "Unknown"

    toc = _extract_toc(book)
    toc_filenames = _get_toc_filenames(book)

    html_parts = []
    file_names = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            item_name = item.get_name()
            if any(toc_name in item_name for toc_name in toc_filenames):
                continue

            try:
                html_content = item.get_content().decode('utf-8')

                if _is_toc_document(html_content):
                    continue

                base_name = item_name.split('/')[-1]
                html_parts.append(html_content)
                file_names.append(base_name)
            except Exception as e:
                logger.warning(f"Skipping unreadable chapter: {e}")

    if not html_parts:
        raise ValueError(f"No HTML content found in EPUB: {file_path}")

    images, cover_path = _extract_images_with_cover(book, html_parts)

    return {
        'title': title,
        'author': author,
        'html_parts': html_parts,
        'file_names': file_names,
        'toc': toc,
        'images': images,
        'cover_path': cover_path,
        'abstract': '',
    }


def _get_metadata(book: epub.EpubBook, key: str) -> Optional[str]:
    try:
        metadata = book.get_metadata('DC', key)
        if metadata and len(metadata) > 0:
            return metadata[0][0]
    except Exception:
        pass
    return None


def _extract_toc(book: epub.EpubBook) -> List[TOCItem]:
    toc_items = []

    def parse_toc_item(item) -> Optional[TOCItem]:
        if isinstance(item, epub.Link):
            return TOCItem(title=item.title, href=item.href)
        elif isinstance(item, tuple):
            section, children = item
            if isinstance(section, epub.Link):
                return TOCItem(
                    title=section.title,
                    href=section.href,
                    children=[parse_toc_item(child) for child in children if parse_toc_item(child)],
                )
            elif isinstance(section, epub.Section):
                return TOCItem(
                    title=section.title,
                    href="",
                    children=[parse_toc_item(child) for child in children if parse_toc_item(child)],
                )
        return None

    try:
        for item in book.toc:
            parsed = parse_toc_item(item)
            if parsed:
                toc_items.append(parsed)
    except Exception as e:
        logger.warning(f"Failed to extract TOC: {e}")

    return toc_items


def _get_toc_filenames(book: epub.EpubBook) -> List[str]:
    filenames = ['toc.xhtml', 'toc.html', 'nav.xhtml', 'nav.html', 'toc.ncx']
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_NAVIGATION:
            filenames.append(item.get_name())
    return filenames


def _is_toc_document(html_content: str) -> bool:
    try:
        soup = BeautifulSoup(html_content, 'lxml-xml')
        nav_toc = soup.find('nav', attrs={'epub:type': 'toc'})
        if nav_toc:
            return True
        links = soup.find_all('a')
        total_text = soup.get_text().strip()
        if len(links) > 10 and len(total_text) < 1000:
            return True
    except Exception:
        pass
    return False


def _extract_images_with_cover(book: epub.EpubBook, html_parts: List[str]) -> Tuple[Dict[str, bytes], Optional[str]]:
    images = {}
    cover_path = None

    try:
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_IMAGE:
                image_path = item.get_name()
                images[image_path] = item.get_content()

        # Priority 1: EPUB metadata
        try:
            cover_meta = book.get_metadata('OPF', 'cover')
            if cover_meta:
                cover_id = cover_meta[0][0]
                cover_item = book.get_item_with_id(cover_id)
                if cover_item:
                    cover_path = cover_item.get_name()
                    if cover_path not in images:
                        images[cover_path] = cover_item.get_content()
        except Exception:
            pass

        # Priority 2: HTML alt attribute
        if not cover_path:
            for html_content in html_parts:
                soup = BeautifulSoup(html_content, 'lxml')
                for img in soup.find_all('img'):
                    alt = img.get('alt', '').lower()
                    src = img.get('src', '')
                    if '封面' in alt or 'cover' in alt:
                        img_filename = src.split('/')[-1]
                        for img_path in images.keys():
                            if img_filename in img_path:
                                cover_path = img_path
                                break
                    if cover_path:
                        break
                if cover_path:
                    break

        # Priority 3: Filename heuristic
        if not cover_path:
            for path in images.keys():
                if 'cover' in path.lower():
                    cover_path = path
                    break

        # Priority 4: First image
        if not cover_path and images:
            cover_path = next(iter(images.keys()))

    except Exception as e:
        logger.warning(f"Image extraction failed: {e}")

    return images, cover_path
