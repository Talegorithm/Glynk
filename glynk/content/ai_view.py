"""
AI View 过滤器

将完整 HTML 转为简化 HTML（去装饰标签，保留结构+span_id），省 tokens。
"""
from bs4 import BeautifulSoup, Tag


# AI 视图保留的标签
AI_VIEW_TAGS = {
    'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li',
    'blockquote', 'pre',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'span',
    'details', 'summary',
}

# AI 视图保留的属性
AI_VIEW_ATTRS = {'id', 'data-time-start', 'data-time-end'}


def to_ai_view(html: str) -> str:
    """
    将完整 HTML 转为 AI 视图。

    规则：
    - 只保留结构标签和 span（含 id）
    - 去掉所有装饰标签（strong, em, mark, figure, figcaption, img 等）
    - 保留文本内容
    - 移除大部分属性，只保留 id 和时间戳
    """
    if not html:
        return html

    soup = BeautifulSoup(html, 'html.parser')

    # Remove figure/figcaption/img (images don't matter for AI)
    for tag in soup.find_all(['figure', 'figcaption', 'img', 'nav', 'aside']):
        tag.decompose()

    # Unwrap decorative tags (keep text)
    for tag in soup.find_all(['strong', 'em', 'mark', 'code', 'small', 'cite',
                              'sup', 'sub', 'a', 'div']):
        if tag.name not in AI_VIEW_TAGS:
            tag.unwrap()

    # Clean attributes
    for tag in soup.find_all():
        if not isinstance(tag, Tag):
            continue
        attrs_to_remove = [attr for attr in tag.attrs.keys() if attr not in AI_VIEW_ATTRS]
        for attr in attrs_to_remove:
            del tag[attr]

    return str(soup)
