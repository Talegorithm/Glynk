"""
Glynk 故事解析 Agent 启动脚本

用法:
    python -m glynk.agent.run_story_parser --unit-id f280a35784ab37e4    # 解析指定作品
    python -m glynk.agent.run_story_parser --unit-id xxx --model gpt-4o  # 指定模型

环境变量:
    GLYNK_TOKEN: Glynk API token（必需）
    OPEN_ROUTER_API_KEY: OpenRouter API key（LLM）
    QWEN_API_KEY: 可选，用 Qwen 更便宜
"""
import os
import sys
import asyncio
import argparse
from pathlib import Path

from dotenv import load_dotenv


async def main():
    parser = argparse.ArgumentParser(description="Glynk 故事解析 Agent")
    parser.add_argument("--unit-id", required=True, help="要解析的作品 Unit ID")
    parser.add_argument("--api-url", default=os.getenv("GLYNK_API_URL", "http://127.0.0.1:5000"))
    parser.add_argument("--model", default="qwen3.5-plus")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    token = os.getenv("GLYNK_TOKEN", "")
    if not token:
        print("Error: GLYNK_TOKEN environment variable required")
        sys.exit(1)

    from agent.core.runner import AgentRunner, RunConfig
    from agent.trace.store import FileSystemTraceStore
    from agent.llm import create_openrouter_llm_call, create_qwen_llm_call
    from agent.core.presets import load_presets_from_json

    # Register Glynk tools (shared with official-agent)
    import glynk.agent.tools  # noqa: F401

    agent_dir = Path(__file__).parent
    load_presets_from_json(str(agent_dir / "presets.json"))

    trace_dir = agent_dir / ".traces"
    trace_dir.mkdir(exist_ok=True)

    if os.getenv("QWEN_API_KEY"):
        llm_call = create_qwen_llm_call(model=args.model)
    else:
        llm_call = create_openrouter_llm_call(model=args.model)

    runner = AgentRunner(
        trace_store=FileSystemTraceStore(base_path=str(trace_dir)),
        llm_call=llm_call,
        debug=args.debug,
    )

    task = (
        f"请解析作品 {args.unit_id}：先用 read_unit 分页读完全文，"
        f"一边读一边提取 10 类素材，全书读完后做汇总层提取（character 画像、"
        f"relationship 动态、arc 弧线），最后按需求侧审计清单检查遗漏。"
    )

    config = RunConfig(
        model=args.model,
        agent_type="story_parser",
        tools=["list_units", "read_unit", "create_anchors", "search_units"],
        extra_llm_params={"extra_body": {"enable_thinking": True}},
        context={
            "glynk_base_url": args.api_url,
            "glynk_token": token,
        },
        knowledge=RunConfig().knowledge,
    )
    config.knowledge.enable_extraction = False
    config.knowledge.enable_completion_extraction = False
    config.knowledge.enable_injection = False
    config.enable_research_flow = False

    print(f"Glynk Story Parser")
    print(f"  API: {args.api_url}")
    print(f"  Model: {args.model}")
    print(f"  Target: {args.unit_id}")
    print()

    from agent.trace.models import Trace, Message

    async for item in runner.run(
        messages=[{"role": "user", "content": task}],
        config=config,
    ):
        if isinstance(item, Trace):
            if item.status == "completed":
                print(f"\nCompleted. Tokens: {item.total_tokens}, Cost: ${item.total_cost:.4f}")
            elif item.status == "failed":
                print(f"\nFailed.")
        elif isinstance(item, Message):
            if item.role == "assistant" and item.content:
                text = item.content if isinstance(item.content, str) else ""
                if text:
                    print(f"\n{text[:300]}{'...' if len(text) > 300 else ''}")


if __name__ == "__main__":
    load_dotenv(Path(__file__).parents[2] / ".env")
    load_dotenv(Path.home() / "Code" / "Agent" / ".env")
    asyncio.run(main())
