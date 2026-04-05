"""
PDF 格式工具

支持两种模式：
1. MinerU API（如果配置了 MINERU_API_URL）：高质量解析，保留结构
2. 基础模式：使用 pymupdf 提取文本，生成简单 HTML
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def parse_pdf_with_mineru(file_path: Path, mineru_url: str) -> Optional[dict]:
    """
    调用 MinerU API 解析 PDF

    Returns:
        {'markdown': str, 'images': dict} 或 None（失败时）
    """
    import httpx

    try:
        with open(file_path, 'rb') as f:
            response = httpx.post(
                f"{mineru_url}/predict",
                files={"file": (file_path.name, f, "application/pdf")},
                timeout=300,
            )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"MinerU API failed: {e}")
        return None


def parse_pdf_basic(file_path: Path) -> dict:
    """
    基础 PDF 解析：提取文本 → 生成 HTML

    Returns:
        {'title': str, 'author': str, 'html_parts': list[str], 'abstract': str}
    """
    try:
        import fitz  # pymupdf
    except ImportError:
        # Fallback: try reading as binary and extract what we can
        logger.warning("pymupdf not installed, trying minimal extraction")
        return _extract_minimal(file_path)

    doc = fitz.open(str(file_path))

    title = doc.metadata.get('title', '') or ''
    author = doc.metadata.get('author', '') or 'Unknown'

    # Extract text page by page → single HTML file
    paragraphs = []
    abstract = ''

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        if not text.strip():
            continue

        # Split into paragraphs
        for para in text.split('\n\n'):
            para = para.strip()
            if not para:
                continue

            # Detect headings (short lines, often all caps or numbered)
            if len(para) < 80 and (para.isupper() or para[0].isdigit()):
                paragraphs.append(f'<h2>{para}</h2>')
            else:
                paragraphs.append(f'<p>{para}</p>')

            # Try to find abstract
            if not abstract and 'abstract' in para.lower()[:20]:
                abstract = para

    if not title and paragraphs:
        # Use first heading-like element as title
        from bs4 import BeautifulSoup
        for p in paragraphs[:5]:
            soup = BeautifulSoup(p, 'html.parser')
            h = soup.find(['h1', 'h2'])
            if h:
                title = h.get_text().strip()
                break

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>{title}</title></head>
<body>
{''.join(paragraphs)}
</body>
</html>"""

    doc.close()

    return {
        'title': title,
        'author': author,
        'html_parts': [html],
        'abstract': abstract,
    }


def _extract_minimal(file_path: Path) -> dict:
    """最小化提取——在没有 pymupdf 时使用"""
    return {
        'title': file_path.stem,
        'author': 'Unknown',
        'html_parts': [f'<html><body><p>PDF parsing requires pymupdf. File: {file_path.name}</p></body></html>'],
        'abstract': '',
    }
