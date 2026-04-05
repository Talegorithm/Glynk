"""
IngestionPipeline - 摄入流水线

结构化处理：parse → HTML标准化 → 保存。不跑LLM。
"""
import hashlib
import json
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from typing import Union
import logging

from glynk.config import AppConfig
from glynk.models import Content, IngestResult, ParsedContent
from glynk.ingestion.registry import HandlerRegistry
from glynk.ingestion.processing.html_processor import HTMLProcessor

logger = logging.getLogger(__name__)


class ContentAlreadyExistsError(Exception):
    def __init__(self, content: dict):
        self.content = content
        super().__init__(f"Content already exists: {content.get('content_id')}")


class IngestionPipeline:
    """结构化处理流水线。不跑LLM，只做确定性处理。"""

    def __init__(self, config: AppConfig, db):
        self.registry = HandlerRegistry()
        self.config = config
        self.db = db

    async def ingest(self, source: Union[str, Path], uid: str = None,
                     content_type: str = None,
                     source_hint: str = "") -> IngestResult:
        """
        摄入内容。

        Args:
            source: URL字符串 或 本地文件Path
            uid: 提交者uid
            content_type: 明确指定内容类型
            source_hint: 来源提示（如 'arxiv.org'）
        """
        # 1. 获取文件
        file_path = await self._resolve_source(source)
        if not source_hint and isinstance(source, str) and source.startswith('http'):
            source_hint = urlparse(source).netloc

        # 2. 计算 content_id + 去重检查
        file_hash = self._calculate_file_hash(file_path)
        content_id = file_hash[:16]
        existing = self.db.get_content(content_id)
        if existing:
            raise ContentAlreadyExistsError(existing)

        # 3. 选择 handler，解析
        handler = self.registry.resolve(file_path, content_type, source_hint)
        parsed = handler.parse(file_path)

        # 4. HTML 标准化
        processed_files = []
        total_chars = 0
        html_root = self.config.storage.html_root / content_id
        html_root.mkdir(parents=True, exist_ok=True)

        for file_idx, raw_html in enumerate(parsed.raw_html_parts):
            processor = HTMLProcessor(content_id, file_idx)
            result = processor.process(raw_html, parsed.images)
            processed_files.append(result)

            # 保存 HTML
            html_file = html_root / f"{file_idx}.html"
            html_file.write_text(result.html, encoding='utf-8')

            # 保存图片
            for img_name, img_data in result.images.items():
                img_path = html_root / img_name
                img_path.write_bytes(img_data)

            total_chars += result.sentence_count * 50  # 估算

        # 5. 保存 TOC
        toc_list = [item.to_dict() for item in parsed.toc] if parsed.toc else []

        # 6. 保存到数据库
        content = Content(
            content_id=content_id,
            title=parsed.title,
            author=parsed.author,
            source_type=parsed.content_type,
            source_url=source if isinstance(source, str) and source.startswith('http') else None,
            source_file_hash=file_hash,
            file_count=len(processed_files),
            toc_json=json.dumps(toc_list, ensure_ascii=False),
            abstract=parsed.abstract,
            uid=uid,
            status='ready',
            total_chars=total_chars,
        )
        self.db.create_content(content)

        return IngestResult(
            content_id=content_id,
            title=parsed.title,
            author=parsed.author,
            source_type=parsed.content_type,
            file_count=len(processed_files),
            total_chars=total_chars,
            toc=toc_list,
        )

    async def _resolve_source(self, source: Union[str, Path]) -> Path:
        """URL 则下载到临时目录，本地文件直接返回"""
        if isinstance(source, Path):
            return source
        if isinstance(source, str) and source.startswith('http'):
            from glynk.ingestion.format_utils.html import download_url
            content = download_url(source)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
            tmp.write(content)
            tmp.close()
            return Path(tmp.name)
        return Path(source)

    def _calculate_file_hash(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
