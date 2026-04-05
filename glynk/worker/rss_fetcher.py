"""
RSSFetcher - RSS 定时拉取

唯一的后台任务。由 APScheduler 定时调用。
"""
import logging
from datetime import datetime, timedelta

import feedparser

from glynk.ingestion.pipeline import IngestionPipeline, ContentAlreadyExistsError
from glynk.storage.postgres import PostgresStore

logger = logging.getLogger(__name__)


class RSSFetcher:

    def __init__(self, db: PostgresStore, pipeline: IngestionPipeline):
        self.db = db
        self.pipeline = pipeline

    async def fetch_all(self):
        """拉取所有启用的 RSS 源。"""
        sources = self.db.list_sources(enabled_only=True)
        for source in sources:
            if self._should_fetch(source):
                await self._fetch_source(source)

    async def _fetch_source(self, source: dict):
        """拉取单个 RSS 源的新条目"""
        logger.info(f"Fetching RSS source: {source['name']} ({source['url']})")

        try:
            feed = feedparser.parse(source['url'])
        except Exception as e:
            logger.error(f"Failed to parse RSS feed {source['url']}: {e}")
            return

        new_entries = feed.entries[:source.get('max_items', 5)]

        for entry in new_entries:
            url = entry.get('link')
            if not url:
                continue
            try:
                await self.pipeline.ingest(
                    url,
                    content_type=source.get('content_type'),
                )
                logger.info(f"RSS ingest success: {url}")
            except ContentAlreadyExistsError:
                continue
            except Exception as e:
                logger.error(f"RSS ingest failed: {url} - {e}")

        self.db.update_source_last_fetched(source['id'])

    def _should_fetch(self, source: dict) -> bool:
        """根据 schedule 判断是否该拉取"""
        last_fetched = source.get('last_fetched_at')
        if not last_fetched:
            return True

        schedule = source.get('schedule', 'daily')
        now = datetime.utcnow()

        intervals = {
            'hourly': timedelta(hours=1),
            'daily': timedelta(days=1),
            'weekly': timedelta(weeks=1),
        }

        interval = intervals.get(schedule, timedelta(days=1))
        return now - last_fetched >= interval
