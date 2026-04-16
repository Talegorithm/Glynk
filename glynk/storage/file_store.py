"""
FileStore - 文件读写抽象层

LocalFileStore: 读写本地磁盘（生产环境 / 纯本地 dev）
RemoteFileStore: 通过 HTTP 读写远程（本地开发连远程数据）

读操作：GET /media/{unit_id}/{filename}
写操作：PUT /api/internal/files/{unit_id}/{filename}（需 token 在服务器白名单内）
       DELETE /api/internal/files/{unit_id}
"""
import logging
import shutil
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)


class FileStore(ABC):
    """文件读写接口。"""

    @abstractmethod
    def read_html(self, unit_id: str, filename: str) -> str | None:
        """读取 HTML 文件内容。文件不存在返回 None。"""

    @abstractmethod
    def html_exists(self, unit_id: str, filename: str) -> bool:
        """检查 HTML 文件是否存在。"""

    @abstractmethod
    def write_html(self, unit_id: str, filename: str, content: str) -> None:
        """写 HTML 文件。自动建目录。"""

    @abstractmethod
    def write_bytes(self, unit_id: str, filename: str, data: bytes) -> None:
        """写二进制文件（图片等）。自动建目录。"""

    @abstractmethod
    def delete_unit_dir(self, unit_id: str) -> None:
        """删除整个 unit 目录。目录不存在则 no-op。"""


class LocalFileStore(FileStore):
    """本地磁盘。"""

    def __init__(self, html_root: Path):
        self.html_root = html_root

    def read_html(self, unit_id: str, filename: str) -> str | None:
        path = self.html_root / unit_id / filename
        if not path.exists():
            return None
        return path.read_text(encoding='utf-8')

    def html_exists(self, unit_id: str, filename: str) -> bool:
        return (self.html_root / unit_id / filename).exists()

    def write_html(self, unit_id: str, filename: str, content: str) -> None:
        unit_dir = self.html_root / unit_id
        unit_dir.mkdir(parents=True, exist_ok=True)
        (unit_dir / filename).write_text(content, encoding='utf-8')

    def write_bytes(self, unit_id: str, filename: str, data: bytes) -> None:
        unit_dir = self.html_root / unit_id
        unit_dir.mkdir(parents=True, exist_ok=True)
        (unit_dir / filename).write_bytes(data)

    def delete_unit_dir(self, unit_id: str) -> None:
        unit_dir = self.html_root / unit_id
        if unit_dir.exists():
            shutil.rmtree(unit_dir, ignore_errors=True)


class RemoteFileStore(FileStore):
    """通过 HTTP 操作远程文件。读走 /media/，写走 /api/internal/files/。读有 LRU 缓存。"""

    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self._client = httpx.Client(timeout=30.0, follow_redirects=True)

    def _write_headers(self, content_type: str) -> dict:
        if not self.token:
            raise RuntimeError(
                "REMOTE_FILE_BASE set but GLYNK_TOKEN not provided; "
                "ingestion writes are disabled. Set GLYNK_TOKEN env to a bearer "
                "token that is allowlisted in the server's GLYNK_WRITE_ALLOWED_TOKENS."
            )
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": content_type,
        }

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

    def write_html(self, unit_id: str, filename: str, content: str) -> None:
        url = f"{self.base_url}/api/internal/files/{unit_id}/{filename}"
        resp = self._client.put(
            url,
            content=content.encode('utf-8'),
            headers=self._write_headers("text/html; charset=utf-8"),
        )
        if resp.status_code >= 400:
            raise RuntimeError(
                f"RemoteFileStore.write_html failed: {resp.status_code} {resp.text}"
            )
        # 写成功后清读缓存（简单起见清整个 LRU）
        self.read_html.cache_clear()

    def write_bytes(self, unit_id: str, filename: str, data: bytes) -> None:
        url = f"{self.base_url}/api/internal/files/{unit_id}/{filename}"
        resp = self._client.put(
            url,
            content=data,
            headers=self._write_headers("application/octet-stream"),
        )
        if resp.status_code >= 400:
            raise RuntimeError(
                f"RemoteFileStore.write_bytes failed: {resp.status_code} {resp.text}"
            )
        self.read_html.cache_clear()

    def delete_unit_dir(self, unit_id: str) -> None:
        url = f"{self.base_url}/api/internal/files/{unit_id}"
        if not self.token:
            raise RuntimeError(
                "REMOTE_FILE_BASE set but GLYNK_TOKEN not provided; "
                "ingestion writes are disabled."
            )
        resp = self._client.delete(
            url,
            headers={"Authorization": f"Bearer {self.token}"},
        )
        # 404 视作 no-op（目录本来就不存在）
        if resp.status_code not in (200, 204, 404):
            raise RuntimeError(
                f"RemoteFileStore.delete_unit_dir failed: {resp.status_code} {resp.text}"
            )
        self.read_html.cache_clear()
