"""
IngestionPipeline - 摄入流水线

结构化处理：parse -> HTML标准化 -> 保存为 Unit。不跑LLM。
"""
import hashlib
import json
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from typing import Union
from uuid import uuid4
import logging

from bs4 import BeautifulSoup

from glynk.config import AppConfig
from glynk.models import IngestResult, ParsedContent, TOCItem
from glynk.ingestion.registry import HandlerRegistry
from glynk.ingestion.processing.html_processor import HTMLProcessor
from glynk.storage.file_store import FileStore

logger = logging.getLogger(__name__)


class ContentAlreadyExistsError(Exception):
    def __init__(self, unit: dict):
        self.unit = unit
        super().__init__(f"Content already exists: {unit.get('id')}")


class IngestionPipeline:
    """结构化处理流水线。不跑LLM，只做确定性处理。"""

    def __init__(self, config: AppConfig, db, file_store: FileStore):
        self.registry = HandlerRegistry()
        self.config = config
        self.db = db
        self.file_store = file_store

    @staticmethod
    def _normalize_url(url: str) -> str:
        """归一化 URL"""
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=False)
        tracking_keys = {
            'mpshare', 'scene', 'srcid', 'sharer_shareinfo',
            'sharer_shareinfo_first', 'share_token', 'from', 'isappinstalled',
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
            'fbclid', 'gclid', 'ref', 'source',
        }
        cleaned = {k: v for k, v in params.items() if k.lower() not in tracking_keys}
        sorted_query = urlencode(cleaned, doseq=True)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', sorted_query, ''))

    def _get_or_create_author_entity(self, author_name: str) -> str:
        """为内容作者创建 dormant Entity（去重：同名复用同一个）"""
        if not author_name:
            author_name = "Unknown"

        existing = self.db.find_entity_by_name(author_name, state='dormant')
        if existing:
            return existing['id']

        entity_id = f"ent-{uuid4().hex[:12]}"
        self.db.create_entity(
            entity_id=entity_id,
            kind='human',
            state='dormant',
            display_name=author_name,
        )
        return entity_id

    async def ingest(self, source: Union[str, Path], entity_id: str = None,
                     content_type: str = None,
                     source_hint: str = "") -> IngestResult:
        """
        摄入内容，产出 Unit(origin=ingested, shape=structured)。

        Args:
            source: URL字符串 或 本地文件Path
            entity_id: 提交者 entity_id（imported_by）
            content_type: 明确指定内容类型
            source_hint: 来源提示
        """
        # 1. URL 去重
        source_url = None
        if isinstance(source, str) and source.startswith('http'):
            source_url = source
            normalized = self._normalize_url(source)
            existing_by_url = self.db.get_unit_by_source_url(normalized)
            if existing_by_url:
                raise ContentAlreadyExistsError(existing_by_url)

        # 2. 获取文件
        file_path = await self._resolve_source(source)
        if not source_hint and source_url:
            source_hint = urlparse(source_url).netloc

        # 3. 计算 unit_id + 去重
        file_hash = self._calculate_file_hash(file_path)
        unit_id = file_hash[:16]
        existing = self.db.get_unit(unit_id)
        if existing:
            old_chars = (existing.get('metadata') or {}).get('total_chars', 0) or 0
            old_imported_by = (existing.get('metadata') or {}).get('imported_by', '')
            if old_chars < 3000 and (not old_imported_by or old_imported_by == entity_id):
                logger.info(f"Overwriting unit {unit_id} (old chars={old_chars})")
                self.db.delete_unit(unit_id)
                self.file_store.delete_unit_dir(unit_id)
            else:
                raise ContentAlreadyExistsError(existing)

        # 4. 选择 handler，解析
        handler = self.registry.resolve(file_path, content_type, source_hint)
        parsed = handler.parse(file_path)

        # 5. HTML 标准化
        processed_files = []
        total_chars = 0

        for file_idx, raw_html in enumerate(parsed.raw_html_parts):
            processor = HTMLProcessor(unit_id, file_idx)
            result = processor.process(raw_html, parsed.images)
            processed_files.append(result)

            self.file_store.write_html(unit_id, f"{file_idx}.html", result.html)

            for img_name, img_data in result.images.items():
                self.file_store.write_bytes(unit_id, img_name, img_data)

            total_chars += result.sentence_count * 50

        # 6. TOC mapping
        toc_list = [item.to_dict() for item in parsed.toc] if parsed.toc else []
        if toc_list and parsed.file_names:
            self._map_toc_to_span_ids(toc_list, parsed.file_names, unit_id)

        # 7. 创建作者 Entity（dormant）
        author_entity_id = self._get_or_create_author_entity(parsed.author)

        # 8. 保存 Unit
        self.db.create_unit(
            unit_id=unit_id,
            author_id=author_entity_id,
            origin='ingested',
            shape='structured',
            body={
                "toc": toc_list,
                "file_count": len(processed_files),
            },
            metadata={
                "title": parsed.title,
                "abstract": parsed.abstract,
                "source_type": parsed.content_type,
                "source_url": source if isinstance(source, str) and source.startswith('http') else None,
                "source_file_hash": file_hash,
                "total_chars": total_chars,
                "imported_by": entity_id,
                "status": "ready",
            },
        )

        return IngestResult(
            unit_id=unit_id,
            title=parsed.title,
            author=parsed.author,
            author_entity_id=author_entity_id,
            source_type=parsed.content_type,
            file_count=len(processed_files),
            total_chars=total_chars,
            toc=toc_list,
        )

    async def _resolve_source(self, source: Union[str, Path]) -> Path:
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

    def _map_toc_to_span_ids(self, toc_list: list[dict], file_names: list[str],
                              unit_id: str):
        """将 TOC EPUB href 映射为 span_id"""
        name_to_idx = {}
        for idx, name in enumerate(file_names):
            name_to_idx[name] = idx
            base = name.split('/')[-1]
            name_to_idx[base] = idx

        file_first_span = {}
        for idx in range(len(file_names)):
            html = self.file_store.read_html(unit_id, f"{idx}.html")
            if html is None:
                continue
            soup = BeautifulSoup(html, 'html.parser')
            first = soup.find('span', id=True)
            if first:
                file_first_span[idx] = first.get('id')

        def resolve_href(href: str) -> str:
            if not href:
                return ""
            parts = href.split('#', 1)
            file_ref = parts[0]
            anchor = parts[1] if len(parts) > 1 else None

            file_idx = None
            base_ref = file_ref.split('/')[-1]
            if file_ref in name_to_idx:
                file_idx = name_to_idx[file_ref]
            elif base_ref in name_to_idx:
                file_idx = name_to_idx[base_ref]

            if file_idx is None:
                return ""

            if anchor:
                html = self.file_store.read_html(unit_id, f"{file_idx}.html")
                if html is not None:
                    soup = BeautifulSoup(html, 'html.parser')
                    target = soup.find(id=anchor)
                    if target:
                        span = target.find('span', id=True) if target.name != 'span' else target
                        if not span and target.get('id'):
                            span = target.find_next('span', id=True)
                        if span and span.get('id'):
                            return span.get('id')

            return file_first_span.get(file_idx, "")

        def process_toc_items(items: list[dict], depth: int = 1):
            for item in items:
                item['level'] = depth
                item['href'] = resolve_href(item.get('href', ''))
                if not item['href'] and item.get('children'):
                    for child in item['children']:
                        child_href = resolve_href(child.get('href', ''))
                        if child_href:
                            item['href'] = child_href
                            break
                if item.get('children'):
                    process_toc_items(item['children'], depth + 1)

        process_toc_items(toc_list)
        stats = {'mapped': 0, 'failed': 0}
        def count(items):
            for i in items:
                if i.get('href'): stats['mapped'] += 1
                else: stats['failed'] += 1
                if i.get('children'): count(i['children'])
        count(toc_list)
        logger.info(f"TOC mapping: {stats['mapped']} mapped, {stats['failed']} failed")

    def _calculate_file_hash(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
