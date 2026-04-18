"""
Glynk Agent 工具集

通过 REST API 读取 Units、提交大纲和标注。
"""
import json
import httpx
from typing import Optional
from agent.tools import tool, ToolResult


def _get_client(context: dict) -> httpx.Client:
    base_url = context.get("glynk_base_url", "http://127.0.0.1:5000") if context else "http://127.0.0.1:5000"
    token = context.get("glynk_token", "") if context else ""
    return httpx.Client(
        base_url=base_url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )


@tool(description="列出 Glynk 平台上的所有 Units", hidden_params=["context"])
async def list_units(
    limit: int = 50,
    origin: str = "",
    context: Optional[dict] = None,
) -> ToolResult:
    """列出平台上的内容。

    Args:
        limit: 返回数量上限
        origin: 过滤来源类型（ingested / authored），空则全部
    """
    client = _get_client(context)
    params = {"limit": limit}
    if origin:
        params["origin"] = origin
    r = client.get("/units", params=params)
    r.raise_for_status()
    contents = r.json()["contents"]
    lines = []
    for c in contents:
        lines.append(f"- [{c['content_id']}] {c['title']} ({c.get('source_type', '')}, {c.get('file_count', 0)} files, {c.get('total_chars', 0)} chars)")
    return ToolResult(
        title=f"{len(contents)} units",
        output="\n".join(lines),
    )


@tool(description="读取 Glynk Unit 的一页（AI 视图，简化 HTML）", hidden_params=["context"])
async def read_unit(
    unit_id: str,
    from_span: str = "",
    size: int = 8000,
    context: Optional[dict] = None,
) -> ToolResult:
    """读取 Unit 的一段文本，返回 AI 视图的简化 HTML。

    Args:
        unit_id: Unit ID
        from_span: 起始 span_id（空则从头开始）
        size: 读取字符数
    """
    client = _get_client(context)
    params = {"size": size}
    if from_span:
        params["from"] = from_span
    r = client.get(f"/units/{unit_id}/read", params=params)
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


@tool(description="提交 Unit 的 AI 大纲（覆盖式写入）", hidden_params=["context"])
async def submit_outline(
    unit_id: str,
    outline_json: str,
    context: Optional[dict] = None,
) -> ToolResult:
    """提交 AI 生成的大纲。

    Args:
        unit_id: Unit ID
        outline_json: 大纲 JSON [{"title":"...","description":"...","span_id":"...","children":[]}]
    """
    client = _get_client(context)
    outline = json.loads(outline_json)
    r = client.put(f"/units/{unit_id}/outline", json={"outline": outline})
    r.raise_for_status()
    return ToolResult(
        title=f"Outline submitted ({len(outline)} top-level items)",
        output=f"Successfully submitted outline for {unit_id}",
    )


@tool(description="批量创建 Anchors（标注）到 Glynk", hidden_params=["context"])
async def create_anchors(
    unit_id: str,
    anchors_json: str,
    context: Optional[dict] = None,
) -> ToolResult:
    """批量创建标注。

    Args:
        unit_id: 目标 Unit ID
        anchors_json: JSON 数组，每项: {text, spans, tags, role?, metadata?}
                      示例: [{"text":"问题","spans":["xxx-1-p3-s1"],"tags":["关键词"],"role":"hook"}]
    """
    client = _get_client(context)
    hooks = json.loads(anchors_json)

    anchors = []
    for hook in hooks:
        role = hook.get("role", "hook")
        spans = hook.get("spans", [])
        anchors.append({
            "target_unit": unit_id,
            "target_span": spans[0] if spans else None,
            "role": role,
            "metadata": {
                "type": "text",
                "spans": spans,
                "color": "ghost",
                **(hook.get("metadata") or {}),
            },
            "text": hook["text"],
            "tags": hook.get("tags", []),
        })

    r = client.post("/anchors/batch", json={"anchors": anchors})
    r.raise_for_status()
    data = r.json()
    return ToolResult(
        title=f"Created {data['created']} anchors",
        output=f"Created {data['created']} anchors: {data['ids']}",
    )


@tool(description="语义搜索 Glynk Units", hidden_params=["context"])
async def search_units(
    query: str,
    limit: int = 10,
    context: Optional[dict] = None,
) -> ToolResult:
    """语义搜索 Units。

    Args:
        query: 搜索文本
        limit: 返回数量上限
    """
    client = _get_client(context)
    r = client.post("/units/search", json={"text": query, "top_k": limit})
    r.raise_for_status()
    data = r.json()
    results = data.get("results", [])
    lines = []
    for res in results:
        lines.append(f"- [{res.get('content_id', '')}] {res.get('content_title', '')} | {res.get('type', '')}: {res.get('text', '')[:100]}")
    return ToolResult(
        title=f"{len(results)} results",
        output="\n".join(lines) if lines else "No results found.",
    )


@tool(description="将 Agent 产出存为 Glynk thought（authored flat Unit）", hidden_params=["context"])
async def save_thought(
    text: str,
    metadata: str = "{}",
    context: Optional[dict] = None,
) -> ToolResult:
    """把一段文本保存为 thought（= authored flat Unit，"放下一个想法"）。

    想让内容被精细标注 / 供人阅读，请用 publication 相关工具而不是这个。

    Args:
        text: 文本内容
        metadata: 元数据 JSON，如 {"title": "...", "tags": ["..."]}
    """
    client = _get_client(context)
    meta = json.loads(metadata)
    r = client.post("/thoughts", json={"text": text, "metadata": meta})
    r.raise_for_status()
    data = r.json()
    return ToolResult(
        title=f"Thought saved: {data['id']}",
        output=f"Created thought {data['id']}",
    )
