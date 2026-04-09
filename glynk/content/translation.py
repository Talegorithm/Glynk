"""
HTML 文件翻译服务

策略：原文 HTML → AI view（精简）→ 整块翻译 → 按 span id 回插到原 HTML
使用阿里云 DashScope qwen-turbo，追求速度。
"""
import logging
import os
import re
from pathlib import Path

from bs4 import BeautifulSoup
from openai import OpenAI

from glynk.content.ai_view import to_ai_view

logger = logging.getLogger(__name__)

TRANSLATE_MODEL = "qwen-turbo"
# 单次最大字符数（qwen-turbo context ~128K tokens，留足余量）
MAX_CHUNK_CHARS = 20000

SYSTEM_PROMPT = """你是一个专业翻译。将以下 HTML 内容翻译成{target_lang}。

规则：
- 保持所有 HTML 标签和属性不变（尤其是 id 属性）
- 只翻译标签内的文本内容
- 保持原文的语气和风格
- 专有名词可保留原文
- 直接输出翻译后的 HTML，不要加任何解释"""


def _get_client() -> OpenAI:
    return OpenAI(
        api_key=os.getenv("ALI_API_KEY"),
        base_url=os.getenv("ALI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        timeout=120.0,
        max_retries=2,
    )


def _detect_language(text: str) -> str:
    """简单检测：中文字符超过 30% 视为中文"""
    if not text:
        return "en"
    chinese = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return "zh" if chinese / max(len(text), 1) > 0.3 else "en"


def _target_lang(source: str) -> tuple[str, str]:
    """返回 (language_code, language_name)"""
    if source == "zh":
        return "en", "English"
    return "zh", "中文"


def _translate_html_chunk(client: OpenAI, html_chunk: str, target_lang_name: str) -> str:
    """翻译一块 AI view HTML，保留标签结构"""
    response = client.chat.completions.create(
        model=TRANSLATE_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(target_lang=target_lang_name)},
            {"role": "user", "content": html_chunk},
        ],
        temperature=0.3,
    )
    content = response.choices[0].message.content.strip()
    # 去掉可能的 markdown 代码块包裹
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
    return content


def _extract_span_texts(html: str) -> dict[str, str]:
    """从 HTML 中提取 {span_id: text} 映射"""
    soup = BeautifulSoup(html, 'html.parser')
    mapping = {}
    for span in soup.find_all('span', id=True):
        text = span.get_text()
        if text.strip():
            mapping[span['id']] = text
    return mapping


def _split_by_paragraphs(html: str, max_chars: int) -> list[str]:
    """将 AI view HTML 按段落标签切分为不超过 max_chars 的块"""
    # 按顶层段落标签分割
    soup = BeautifulSoup(html, 'html.parser')
    elements = soup.find_all(recursive=False)
    if not elements:
        return [html] if html.strip() else []

    chunks = []
    current = []
    current_len = 0

    for el in elements:
        el_str = str(el)
        if current_len + len(el_str) > max_chars and current:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(el_str)
        current_len += len(el_str)

    if current:
        chunks.append("\n".join(current))
    return chunks


def translate_file_on_disk(html_root: Path, content_id: str, file_idx: int) -> str:
    """
    翻译文件并保存到磁盘。已有翻译直接返回。

    流程：原文 HTML → AI view → 整块翻译 → 提取 span 文本映射 → 回插到原 HTML

    Returns: 目标语言代码
    """
    source_path = html_root / content_id / f"{file_idx}.html"
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    original_html = source_path.read_text(encoding="utf-8")
    source_lang = _detect_language(BeautifulSoup(original_html, 'html.parser').get_text()[:500])
    lang_code, lang_name = _target_lang(source_lang)

    target_path = html_root / content_id / f"{file_idx}.{lang_code}.html"
    if target_path.exists():
        return lang_code

    logger.info(f"Translating {content_id}/{file_idx}.html → {lang_code}")

    # Step 1: 生成 AI view（精简 HTML）
    ai_html = to_ai_view(original_html)

    # Step 2: 分块翻译 AI view
    client = _get_client()
    chunks = _split_by_paragraphs(ai_html, MAX_CHUNK_CHARS)
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        logger.info(f"Translating chunk {i + 1}/{len(chunks)} ({len(chunk)} chars)")
        translated = _translate_html_chunk(client, chunk, lang_name)
        translated_chunks.append(translated)

    translated_ai_html = "\n".join(translated_chunks)

    # Step 3: 提取翻译后的 span 文本映射
    translated_spans = _extract_span_texts(translated_ai_html)
    logger.info(f"Extracted {len(translated_spans)} translated spans")

    # Step 4: 回插到原 HTML
    original_soup = BeautifulSoup(original_html, 'html.parser')
    replaced = 0
    for span in original_soup.find_all('span', id=True):
        span_id = span['id']
        if span_id in translated_spans:
            span.string = translated_spans[span_id]
            replaced += 1

    logger.info(f"Replaced {replaced} spans in original HTML")

    # Step 5: 保存
    target_path.write_text(str(original_soup), encoding="utf-8")
    logger.info(f"Saved translation: {target_path}")
    return lang_code
