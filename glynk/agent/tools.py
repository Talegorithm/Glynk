"""
Glynk 官方 Agent 的工具集

通过 Glynk REST API 读取内容、提交大纲和标注。
"""
import json
import httpx
from typing import Optional
from agent.tools import tool, ToolResult


def _get_client(context: dict) -> httpx.Client:
    """从 context dict 获取 httpx client"""
    base_url = context.get("glynk_base_url", "http://127.0.0.1:5000") if context else "http://127.0.0.1:5000"
    token = context.get("glynk_token", "") if context else ""
    return httpx.Client(
        base_url=base_url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )


@tool(description="列出 Glynk 平台上的所有内容", hidden_params=["context"])
async def list_contents(
    limit: int = 50,
    context: Optional[dict] = None,
) -> ToolResult:
    """列出平台上的内容。

    Args:
        limit: 返回数量上限
    """
    client = _get_client(context)
    r = client.get("/contents", params={"limit": limit})
    r.raise_for_status()
    contents = r.json()["contents"]
    lines = []
    for c in contents:
        lines.append(f"- [{c['content_id']}] {c['title']} ({c['source_type']}, {c['file_count']} files, {c.get('total_chars', 0)} chars)")
    return ToolResult(
        title=f"{len(contents)} contents",
        output="\n".join(lines),
    )


@tool(description="读取 Glynk 内容的一页（AI 视图，简化 HTML）", hidden_params=["context"])
async def read_content(
    content_id: str,
    from_span: str = "",
    size: int = 8000,
    context: Optional[dict] = None,
) -> ToolResult:
    """读取内容的一段文本，返回 AI 视图的简化 HTML。

    Args:
        content_id: 内容 ID
        from_span: 起始 span_id（空则从头开始）
        size: 读取字符数
    """
    client = _get_client(context)
    params = {"view": "ai", "size": size}
    if from_span:
        params["from"] = from_span
    r = client.get(f"/content/{content_id}/read", params=params)
    r.raise_for_status()
    data = r.json()

    summary = f"from={data['from']} to={data['to']} chars={data['char_count']} has_more={data['has_more']}"
    if data.get("next_from"):
        summary += f" next_from={data['next_from']}"

    return ToolResult(
        title=f"Read {data['char_count']} chars",
        output=data["content"],
        long_term_memory=summary,
        metadata={
            "from": data["from"],
            "to": data["to"],
            "next_from": data.get("next_from"),
            "has_more": data["has_more"],
            "char_count": data["char_count"],
        },
    )


@tool(description="提交内容的 AI 大纲（覆盖式写入）", hidden_params=["context"])
async def submit_outline(
    content_id: str,
    outline_json: str,
    context: Optional[dict] = None,
) -> ToolResult:
    """提交 AI 生成的大纲。

    Args:
        content_id: 内容 ID
        outline_json: 大纲 JSON 字符串，格式 [{"title":"...","description":"...","span_id":"...","children":[]}]
    """
    client = _get_client(context)
    outline = json.loads(outline_json)
    r = client.put(f"/content/{content_id}/outline", json={"outline": outline})
    r.raise_for_status()
    return ToolResult(
        title=f"Outline submitted ({len(outline)} top-level items)",
        output=f"Successfully submitted outline for {content_id}",
    )


@tool(description="批量提交标注（hooks/highlights）到 Glynk", hidden_params=["context"])
async def submit_annotations(
    annotations_json: str,
    context: Optional[dict] = None,
) -> ToolResult:
    """批量提交标注。

    Args:
        annotations_json: 标注 JSON 数组字符串，每项包含 content_id, anchor, type, text, tags, contextuality
    """
    client = _get_client(context)
    annotations = json.loads(annotations_json)
    r = client.post("/annotate/batch", json={"annotations": annotations})
    r.raise_for_status()
    data = r.json()
    return ToolResult(
        title=f"Submitted {data['created']} annotations",
        output=f"Created {data['created']} annotations: {data['ids']}",
    )
