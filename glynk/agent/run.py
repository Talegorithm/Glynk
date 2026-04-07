"""
Glynk 官方 Agent 启动脚本

用法:
    python -m glynk.agent.run                                    # 处理所有内容
    python -m glynk.agent.run --content-id f280a35784ab37e4      # 处理指定内容

环境变量:
    GLYNK_TOKEN: Glynk API token（必需）
    OPEN_ROUTER_API_KEY: OpenRouter API key（用于 LLM）
"""
import os
import sys
import asyncio
import argparse
from pathlib import Path

from dotenv import load_dotenv


async def main():
    parser = argparse.ArgumentParser(description="Glynk 官方标注 Agent")
    parser.add_argument("--content-id", help="处理指定内容（不指定则处理全部）")
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

    # Register Glynk tools
    import glynk.agent.tools  # noqa: F401

    # Load presets
    agent_dir = Path(__file__).parent
    load_presets_from_json(str(agent_dir / "presets.json"))

    # Setup runner
    trace_dir = agent_dir / ".traces"
    trace_dir.mkdir(exist_ok=True)

    # Use Qwen directly (cheaper) or OpenRouter as fallback
    if os.getenv("QWEN_API_KEY"):
        llm_call = create_qwen_llm_call(model=args.model)
    else:
        llm_call = create_openrouter_llm_call(model=args.model)

    runner = AgentRunner(
        trace_store=FileSystemTraceStore(base_path=str(trace_dir)),
        llm_call=llm_call,
        debug=args.debug,
    )

    # Build task
    if args.content_id:
        task = f"请处理内容 {args.content_id}：通读全文，生成 AI 大纲和 hooks。"
    else:
        task = "请处理 Glynk 平台上所有内容。先用 list_contents 查看有哪些，然后逐个通读并生成 AI 大纲和 hooks。"

    config = RunConfig(
        model=args.model,
        agent_type="annotator",
        tools=["list_contents", "read_content", "submit_outline", "submit_annotations", "goal"],
        extra_llm_params={"extra_body": {"enable_thinking": True}},
        context={
            "glynk_base_url": args.api_url,
            "glynk_token": token,
        },
        knowledge=RunConfig().knowledge,  # disable knowledge
    )
    config.knowledge.enable_extraction = False
    config.knowledge.enable_completion_extraction = False
    config.knowledge.enable_injection = False
    config.enable_research_flow = False

    print(f"Glynk Official Agent")
    print(f"  API: {args.api_url}")
    print(f"  Model: {args.model}")
    print(f"  Content: {args.content_id or 'all'}")
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
