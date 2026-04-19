"""
OSS client wrapper — 媒体摄入用。

- presigned PUT：agent 直接上传
- presigned GET：DashScope 拉取
- download_bytes / delete：本地持久化 + 清理临时对象
"""
import logging
from dataclasses import dataclass

import oss2

from glynk.config import OSSConfig

logger = logging.getLogger(__name__)


@dataclass
class OSSClient:
    config: OSSConfig

    def __post_init__(self):
        if not self.config.enabled:
            raise RuntimeError(
                "OSS not configured; need ALI_ACCESS_KEY_ID / ALI_ACCESS_KEY_SECRET "
                "(ALI_OSS_ENDPOINT / ALI_OSS_BUCKET have defaults)"
            )
        auth = oss2.Auth(self.config.access_key_id, self.config.access_key_secret)
        endpoint = self.config.endpoint
        if not endpoint.startswith(("http://", "https://")):
            endpoint = f"https://{endpoint}"
        self._bucket = oss2.Bucket(auth, endpoint, self.config.bucket)

    def presigned_put(self, key: str, expires_seconds: int = 1800) -> str:
        return self._bucket.sign_url("PUT", key, expires_seconds, slash_safe=True)

    def presigned_get(self, key: str, expires_seconds: int = 3 * 3600) -> str:
        return self._bucket.sign_url("GET", key, expires_seconds, slash_safe=True)

    def exists(self, key: str) -> bool:
        return self._bucket.object_exists(key)

    def download_bytes(self, key: str) -> bytes:
        return self._bucket.get_object(key).read()

    def delete(self, key: str) -> None:
        self._bucket.delete_object(key)
