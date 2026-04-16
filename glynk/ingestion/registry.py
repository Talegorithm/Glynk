"""
HandlerRegistry - 内容类型选择

优先级：来源指定 > 来源提示匹配 > handler自己判断 > 兜底
"""
from pathlib import Path
from typing import Optional

from glynk.ingestion.handler.base import ContentTypeHandler
from glynk.ingestion.handler.academic_paper import AcademicPaperHandler
from glynk.ingestion.handler.book import BookHandler
from glynk.ingestion.handler.wechat_article import WeChatArticleHandler
from glynk.ingestion.handler.markdown import MarkdownHandler
from glynk.ingestion.handler.generic_article import GenericArticleHandler
from glynk.ingestion.handler.fallback import FallbackHandler


class HandlerRegistry:

    def __init__(self):
        self.handlers: list[ContentTypeHandler] = [
            AcademicPaperHandler(),
            BookHandler(),
            WeChatArticleHandler(),
            MarkdownHandler(),
            GenericArticleHandler(),
            FallbackHandler(),
        ]

        self.source_map: dict[str, str] = {
            'mp.weixin.qq.com': 'wechat_article',
            'arxiv.org': 'academic_paper',
        }

        self._name_map: dict[str, ContentTypeHandler] = {
            'academic_paper': AcademicPaperHandler(),
            'book': BookHandler(),
            'wechat_article': WeChatArticleHandler(),
            'markdown': MarkdownHandler(),
            'generic': GenericArticleHandler(),
        }

    def resolve(self, file_path: Path,
                content_type: str = None,
                source_hint: str = "") -> ContentTypeHandler:
        # 1. 明确指定
        if content_type and content_type in self._name_map:
            return self._name_map[content_type]

        # 2. 来源提示快速映射
        if source_hint in self.source_map:
            return self._name_map[self.source_map[source_hint]]

        # 3. handler 自己判断
        for handler in self.handlers:
            if handler.supports(file_path, source_hint):
                return handler

        # 4. 不会到这里（FallbackHandler 永远返回 True）
        return FallbackHandler()
