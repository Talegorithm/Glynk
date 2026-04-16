"""
FileStore - 文件读取抽象层

LocalFileStore: 从本地磁盘读（生产环境）
RemoteFileStore: 从远程 HTTP 读（本地开发连远程数据）
"""
import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)


class FileStore(ABC):
    """文件读取接口。只抽象读操作；写操作（ingestion）仍直接用本地磁盘。"""

    @abstractmethod
    def read_html(self, unit_id: str, filename: str) -> str | None:
        """读取 HTML 文件内容。文件不存在返回 None。"""

    @abstractmethod
    def html_exists(self, unit_id: str, filename: str) -> bool:
        """检查 HTML 文件是否存在。"""


class LocalFileStore(FileStore):
    """从本地磁盘读取。"""

    def __init__(self, html_root: Path):
        self.html_root = html_root

    def read_html(self, unit_id: str, filename: str) -> str | None:
        path = self.html_root / unit_id / filename
        if not path.exists():
            return None
        return path.read_text(encoding='utf-8')

    def html_exists(self, unit_id: str, filename: str) -> bool:
        return (self.html_root / unit_id / filename).exists()


class RemoteFileStore(FileStore):
    """从远程 HTTP 读取（通过线上的 /media/ 端点）。带 LRU 缓存——文件是静态的。"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self._client = httpx.Client(timeout=30.0, follow_redirects=True)

    @lru_cache(maxsize=500)
    def read_html(self, unit_id: str, filename: str) -> str | None:
        url = f"{self.base_url}/media/{unit_id}/{filename}"
        try:
            resp = self._client.get(url)
            if resp.status_code == 200:
                return resp.text
            return None
        except httpx.HTTPError as e:
            logger.warning(f"RemoteFileStore: failed to fetch {url}: {e}")
            return None

    def html_exists(self, unit_id: str, filename: str) -> bool:
        return self.read_html(unit_id, filename) is not None
