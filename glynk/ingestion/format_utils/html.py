"""
HTML 格式工具 - 文件读取 + trafilatura 提取

从 Resonote HTMLParser 提取的格式工具部分。
"""
from pathlib import Path
from typing import Optional, Tuple, Dict
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False


def read_html_file(file_path: Path) -> str:
    """读取 HTML 文件并返回内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_with_trafilatura(html_content: str) -> Tuple[Optional[str], dict]:
    """
    使用 trafilatura 提取正文和元数据

    Returns:
        (extracted_html, metadata_dict)
    """
    if not TRAFILATURA_AVAILABLE:
        return None, {}

    try:
        extracted = trafilatura.extract(
            html_content,
            output_format='html',
            include_comments=False,
            include_tables=True,
            include_images=True,
            include_links=True,
            no_fallback=False,
        )

        if not extracted:
            return None, {}

        metadata = trafilatura.extract_metadata(html_content)
        metadata_dict = {}
        if metadata:
            metadata_dict = {
                'title': metadata.title,
                'author': metadata.author,
                'date': metadata.date,
                'url': metadata.url,
                'description': metadata.description,
                'sitename': metadata.sitename,
            }

        return extracted, metadata_dict

    except Exception as e:
        logger.warning(f"trafilatura extraction failed: {e}")
        return None, {}


def extract_basic_metadata(html_content: str) -> dict:
    """基础 HTML 元数据提取"""
    soup = BeautifulSoup(html_content, 'lxml')

    title = None
    if soup.title:
        title = soup.title.string
    if not title:
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()

    return {
        'title': title or "",
        'author': "Unknown",
    }


def download_url(url: str) -> bytes:
    """下载 URL 内容"""
    import httpx
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    response = httpx.get(url, timeout=30, follow_redirects=True, headers=headers)
    response.raise_for_status()
    return response.content
