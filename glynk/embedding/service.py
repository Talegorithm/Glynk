"""
Embedding 生成服务

使用 Azure OpenAI text-embedding-3-large，3072维。
从 Resonote 简化，去掉 cache 依赖。
"""
import logging
from typing import List

from openai import AzureOpenAI

from glynk.config import EmbeddingConfig

logger = logging.getLogger(__name__)


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
