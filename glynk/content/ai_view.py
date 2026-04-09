"""
AI View 过滤器

将完整 HTML 转为简化 HTML（去装饰标签，保留结构+span_id），省 tokens。
- 去掉图片、装饰标签
- span 标签简化为 <s>，ID 去掉 content_id 前缀
- 去掉无 id 的 span（噪声）
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


def to_ai_view(html: str, content_id: str = None) -> str:
    """
    将完整 HTML 转为 AI 视图。

    规则：
    - 去掉图片、figure、nav、aside
    - 去掉装饰标签（strong, em, mark 等），保留文本
    - 有 id 的 span → <s id="短ID">，去掉 content_id 前缀
    - 无 id 的 span → unwrap（只保留文本）
    - 移除所有非 id 属性
    """
    if not html:
        return html

    soup = BeautifulSoup(html, 'html.parser')

    # Remove images and non-content elements
    for tag in soup.find_all(['figure', 'figcaption', 'img', 'nav', 'aside']):
        tag.decompose()

    # Unwrap decorative tags (keep text)
    for tag in soup.find_all(['strong', 'em', 'mark', 'code', 'small', 'cite',
                              'sup', 'sub', 'a', 'div']):
        if tag.name not in AI_VIEW_TAGS:
            tag.unwrap()

    # Simplify spans: keep only those with id, shorten tag and id
    prefix = f"{content_id}-" if content_id else None
    for span in soup.find_all('span'):
        span_id = span.get('id')
        if span_id:
            # Shorten: <span id="abc123-0-p6-s2"> → <s id="0-p6-s2">
            short_id = span_id[len(prefix):] if prefix and span_id.startswith(prefix) else span_id
            span.name = 's'
            span.attrs = {'id': short_id}
        else:
            # No id → unwrap (remove tag, keep text)
            span.unwrap()

    # Clean remaining tags: remove all attributes except id
    for tag in soup.find_all():
        if not isinstance(tag, Tag):
            continue
        if tag.name == 's':
            continue  # already cleaned
        attrs_to_remove = [attr for attr in tag.attrs.keys() if attr != 'id']
        for attr in attrs_to_remove:
            del tag[attr]
        # Remove id from non-span block tags (p, h1 etc)
        if tag.name != 's' and 'id' in tag.attrs:
            del tag['id']

    return str(soup)
