"""
ContentTypeHandler 接口 + ParsedContent 数据类
"""
from typing import Protocol
from pathlib import Path

from glynk.models import ParsedContent


class ContentTypeHandler(Protocol):
    """
    内容类型handler。每个handler知道怎么最好地处理该类型的内容。
    内部调用format_utils完成格式转换，在原始格式上提取元数据。
    """

    def supports(self, file_path: Path, source_hint: str = "") -> bool:
        """是否能处理这个文件"""
        ...

    def parse(self, file_path: Path) -> ParsedContent:
        """解析文件，返回HTML + 元数据"""
        ...
