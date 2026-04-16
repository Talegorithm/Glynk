"""
Glynk 配置

所有配置从环境变量读取，dataclass提供默认值和类型安全。
"""
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StorageConfig:
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "glynk"
    postgres_password: str = "glynk"
    postgres_db: str = "glynk"
    data_root: Path = field(default_factory=lambda: Path("/data/glynk"))

    @property
    def html_root(self) -> Path:
        return self.data_root / "html"

    @property
    def uploads_root(self) -> Path:
        return self.data_root / "uploads"

    @property
    def dsn(self) -> str:
        return (
            f"host={self.postgres_host} port={self.postgres_port} "
            f"user={self.postgres_user} password={self.postgres_password} "
            f"dbname={self.postgres_db}"
        )


@dataclass
class EmbeddingConfig:
    api_key: str = ""
    endpoint: str = ""
    api_version: str = "2024-02-01"
    model: str = "text-embedding-3-large"
    dimension: int = 3072
    batch_size: int = 100


@dataclass
class TranslationConfig:
    enabled: bool = True
    model: str = "gpt-4o-mini"
    batch_size: int = 20
    supported_languages: list = field(default_factory=lambda: ["zh", "en"])


@dataclass
class AppConfig:
    storage: StorageConfig = field(default_factory=StorageConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    translation: TranslationConfig = field(default_factory=TranslationConfig)
    rss_check_interval_hours: int = 24
    remote_file_base: str = ""  # 非空时用 RemoteFileStore 从远程读文件（本地开发用）

    def create_file_store(self):
        """根据配置创建 FileStore。REMOTE_FILE_BASE 非空时用远程，否则用本地。"""
        from glynk.storage.file_store import LocalFileStore, RemoteFileStore
        if self.remote_file_base:
            token = os.getenv("GLYNK_TOKEN") or None
            return RemoteFileStore(self.remote_file_base, token=token)
        return LocalFileStore(self.storage.html_root)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """从环境变量创建配置"""
        storage = StorageConfig(
            postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
            postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
            postgres_user=os.getenv("POSTGRES_USER", "glynk"),
            postgres_password=os.getenv("POSTGRES_PASSWORD", "glynk"),
            postgres_db=os.getenv("POSTGRES_DB", "glynk"),
            data_root=Path(os.getenv("DATA_ROOT", "/data/glynk")),
        )

        embedding = EmbeddingConfig(
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"),
        )

        translation = TranslationConfig(
            enabled=os.getenv("TRANSLATION_ENABLED", "true").lower() == "true",
        )

        return cls(
            storage=storage,
            embedding=embedding,
            translation=translation,
            rss_check_interval_hours=int(os.getenv("RSS_CHECK_INTERVAL_HOURS", "24")),
            remote_file_base=os.getenv("REMOTE_FILE_BASE", ""),
        )
