"""
批量回填 annotation embedding

读取所有 embedding IS NULL 的标注，调用 Azure OpenAI 生成向量，写回 pgvector。

用法（在 glynk-api 容器内运行）：
    python3 /app/scripts/backfill_embeddings.py

环境变量：
    AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT（从容器环境继承）
"""
import os
import sys
import time
import logging

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import AzureOpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# --- 配置 ---
BATCH_SIZE = 100          # Azure OpenAI 每批最多 2048，100 比较稳
DB_BATCH_SIZE = 500       # 每次从 DB 取多少条
MODEL = "text-embedding-3-large"
DIMENSION = 3072

def get_db_conn():
    import psycopg2
    import psycopg2.extras
    psycopg2.extras.register_default_jsonb(loads=lambda x: x)
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "glynk"),
        password=os.getenv("POSTGRES_PASSWORD", "glynk"),
        dbname=os.getenv("POSTGRES_DB", "glynk"),
    )
    return conn

def get_openai_client():
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        timeout=120.0,
        max_retries=3,
    )

def generate_embeddings(client, texts):
    """调用 Azure OpenAI 批量生成 embedding"""
    response = client.embeddings.create(
        model=MODEL,
        input=texts,
        encoding_format="float",
    )
    return [item.embedding for item in response.data]

def main():
    conn = get_db_conn()
    client = get_openai_client()

    # 统计
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM annotations WHERE embedding IS NULL")
        total = cur.fetchone()[0]

    if total == 0:
        logger.info("所有标注都已有 embedding，无需处理")
        return

    logger.info(f"需要生成 embedding 的标注: {total}")

    processed = 0
    errors = 0
    start_time = time.time()

    while True:
        # 取一批没有 embedding 的标注
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, text FROM annotations
                WHERE embedding IS NULL AND text IS NOT NULL AND text != ''
                LIMIT %s
            """, (DB_BATCH_SIZE,))
            rows = cur.fetchall()

        if not rows:
            break

        # 按 BATCH_SIZE 分批调 API
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            ids = [r[0] for r in batch]
            texts = [r[1] for r in batch]

            # 截断过长文本（Azure OpenAI 限制 8191 tokens，中文约 1字≈2token，保守取 3500 字）
            texts = [t[:3500] for t in texts]

            try:
                embeddings = generate_embeddings(client, texts)

                # 批量写回
                with conn.cursor() as cur:
                    for ann_id, emb in zip(ids, embeddings):
                        cur.execute(
                            "UPDATE annotations SET embedding = %s WHERE id = %s",
                            (str(emb), ann_id),
                        )
                conn.commit()

                processed += len(batch)
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                logger.info(
                    f"进度: {processed}/{total} ({processed*100//total}%) "
                    f"| {rate:.1f} 条/秒 "
                    f"| 预计剩余: {(total - processed) / rate / 60:.1f} 分钟"
                    if rate > 0 else f"进度: {processed}/{total}"
                )

            except Exception as e:
                conn.rollback()
                errors += 1
                logger.error(f"批次失败 ({len(batch)} 条): {e}")
                if errors > 10:
                    logger.error("错误过多，停止")
                    break
                time.sleep(5)
                continue

        if errors > 10:
            break

    elapsed = time.time() - start_time
    logger.info(f"完成: 处理 {processed} 条, 错误 {errors} 次, 耗时 {elapsed/60:.1f} 分钟")
    conn.close()

if __name__ == "__main__":
    main()
