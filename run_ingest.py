import asyncio
from glynk.storage.postgres import PostgresStore
from glynk.ingestion.pipeline import IngestionPipeline

async def main():
    PostgresStore.get_instance()
    p = IngestionPipeline()
    res = await p.ingest("/Users/sunlit/Downloads/从优秀到卓越 ([美]吉姆·柯林斯) .epub", "system")
    print(f"Ingested as {res.unit_id}")

asyncio.run(main())
