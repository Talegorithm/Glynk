"""
Embedding 生成服务

使用 Azure OpenAI text-embedding-3-large，3072维。
从 Resonote 简化，去掉 cache 依赖。
"""
import logging
import unicodedata
from typing import List

from openai import AzureOpenAI

from glynk.config import EmbeddingConfig

logger = logging.getLogger(__name__)

# 有效字符（字母/数字/CJK）长度阈值
MIN_EMBED_CHARS = 30
# 上限：超过跳过 embed 而不截断。8192 token 的 Azure 硬上限对 CJK ≈ 8k 字，这里
# 留 4x margin，避免因少量 token 超限整批失败，也避免单向量语义被稀释。
MAX_EMBED_CHARS = 2000


def _meaningful_length(text: str) -> int:
    """剔除标点 / 空白 / emoji 后的字符数（字母 + 数字 + CJK 等 L 类）。"""
    return sum(
        1 for c in text
        if c.isalnum() or unicodedata.category(c).startswith("L")
    )


def should_embed(text: str, metadata: dict | None = None) -> bool:
    """
    判断一段文本是否值得 embed。

    不 embed 的条件：
    - metadata.skip_embedding = True（显式标记）
    - 文本为空
    - 有效字符数 < MIN_EMBED_CHARS（太短，召回意义不大）
    - 有效字符数 > MAX_EMBED_CHARS（太长，单向量会语义糊掉；也避免踩 Azure token 上限）

    短反应 / emoji 串 / 长篇 essay 都会被跳过。vector 留 null，
    前者用户不在乎，后者用户想被搜要自己拆成多段 authored Unit。
    """
    if metadata and metadata.get("skip_embedding"):
        return False
    if not text or not text.strip():
        return False

    n = _meaningful_length(text)
    if n < MIN_EMBED_CHARS:
        return False
    if n > MAX_EMBED_CHARS:
        logger.warning(
            f"Text too long for single embedding ({n} meaningful chars > "
            f"{MAX_EMBED_CHARS}); skipping. Split into shorter Units if you "
            f"want it searchable."
        )
        return False
    return True


def _create_client(config: EmbeddingConfig) -> AzureOpenAI:
    return AzureOpenAI(
        api_key=config.api_key,
        api_version=config.api_version,
        azure_endpoint=config.endpoint,
        timeout=60.0,
        max_retries=3,
    )


async def generate_embedding(text: str, config: EmbeddingConfig) -> List[float] | None:
    """生成单个文本的 embedding 向量，未配置时返回 None"""
    embeddings = await generate_embeddings([text], config)
    return embeddings[0] if embeddings else None


async def maybe_embed(text: str, config: EmbeddingConfig,
                      metadata: dict | None = None) -> List[float] | None:
    """
    统一的 "该不该 embed + 要的话去 embed" 决策点。

    callers 不再自己做 should_embed 判断 —— 只要想把一段文本关联到一个 Unit 的
    vector 上，都走这里。返回 None 表示不合适 embed（太短 / skip 标记 / 未配置）。
    """
    if not should_embed(text, metadata):
        return None
    return await generate_embedding(text, config)


async def generate_embeddings(texts: List[str], config: EmbeddingConfig) -> List[List[float]]:
    """
    批量生成 embedding 向量

    Args:
        texts: 文本列表
        config: Embedding 配置

    Returns:
        向量列表，每个向量是 List[float]
    """
    if not texts:
        return []

    # 未配置 embedding 时返回 None（标注仍可创建，只是不参与语义检索）
    if not config.api_key or not config.endpoint:
        logger.warning("Embedding not configured, skipping vector generation")
        return [None] * len(texts)

    # Filter out empty texts
    empty_indices = [i for i, t in enumerate(texts) if not t or not t.strip()]
    if empty_indices:
        raise ValueError(f"Found {len(empty_indices)} empty texts at indices: {empty_indices[:10]}")

    client = _create_client(config)

    all_embeddings = []
    batch_size = config.batch_size

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        response = client.embeddings.create(
            model=config.model,
            input=batch,
            encoding_format="float",
        )

        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)

        logger.debug(f"Generated batch {i // batch_size + 1}, {len(batch_embeddings)} embeddings")

    logger.info(f"Generated {len(all_embeddings)} embeddings total")
    return all_embeddings
