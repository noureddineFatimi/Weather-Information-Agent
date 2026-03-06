import time
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from agent import agent
from agents import Runner

@dataclass
class ToolCall:
    name: str
    arguments: str
    output: str

@dataclass
class TestResult:
    prompt_id: int
    user_input: str
    final_output: str
    response_time_seconds: float
    tool_calls: list[ToolCall] = field(default_factory=list)
    success: bool = True
    error: str | None = None

async def run_test_suite(agent, test_prompts: list[str]):
    """
    Run a professional test suite with timing and detailed reporting.
    """
    print("\n" + "="*70)
    print("  WEATHER AGENT - TEST SUITE")
    print(f"  Started at : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Total prompts : {len(test_prompts)}")
    print("="*70 + "\n")

    results: list[TestResult] = []
    conversation = []

    for i, prompt in enumerate(test_prompts, start=1):
        print(f"[TEST {i}/{len(test_prompts)}] {prompt}")
        print("-" * 70)

        result = TestResult(prompt_id=i, user_input=prompt, final_output="", response_time_seconds=0.0)
        current_tool_call_name = None
        current_tool_call_arguments = None

        try:
            start_time = time.perf_counter()

            stream = Runner.run_streamed(
                agent,
                input=conversation + [{"role": "user", "content": prompt}]
            )

            async for event in stream.stream_events():
                if event.type == "run_item_stream_event":

                    if event.item.type == "tool_call_item":
                        current_tool_call_name = event.item.raw_item.name
                        current_tool_call_arguments = event.item.raw_item.arguments
                        print(f"  🔧 Tool called   : {current_tool_call_name}")
                        print(f"  📥 Arguments     : {current_tool_call_arguments}")

                    if event.item.type == "tool_call_output_item":
                        print(f"  📤 Output        : {event.item.output}")
                        print()
                        if current_tool_call_name:
                            result.tool_calls.append(ToolCall(
                                name=current_tool_call_name,
                                arguments=current_tool_call_arguments or "",
                                output=event.item.output
                            ))
                            current_tool_call_name = None
                            current_tool_call_arguments = None

            end_time = time.perf_counter()

            result.response_time_seconds = round(end_time - start_time, 2)
            result.final_output = stream.final_output
            result.success = True

            conversation.append({"role": "user", "content": prompt})
            conversation.append({"role": "assistant", "content": stream.final_output})

        except Exception as e:
            end_time = time.perf_counter()
            result.response_time_seconds = round(end_time - start_time, 2)
            result.success = False
            result.error = str(e)
            print(f"  ❌ Error : {e}")

        results.append(result)

        status = "✅" if result.success else "❌"
        print(f"  {status} Response time : {result.response_time_seconds}s")
        print(f"\n  🤖 Agent: {result.final_output}\n")
        print("=" * 70 + "\n")

    # ── FINAL REPORT ──────────────────────────────────────────────────────
    successful   = [r for r in results if r.success]
    failed       = [r for r in results if not r.success]
    total_time   = sum(r.response_time_seconds for r in results)
    avg_time     = round(total_time / len(results), 2) if results else 0
    min_time     = min(r.response_time_seconds for r in results)
    max_time     = max(r.response_time_seconds for r in results)
    slowest      = max(results, key=lambda r: r.response_time_seconds)
    most_tools   = max(results, key=lambda r: len(r.tool_calls))

    print("=" * 70)
    print("  FINAL REPORT")
    print("=" * 70)
    print(f"  Total tests     : {len(results)}")
    print(f"  ✅ Passed       : {len(successful)}")
    print(f"  ❌ Failed       : {len(failed)}")
    print(f"  ⏱  Total time   : {round(total_time, 2)}s")
    print(f"  ⚡ Fastest      : {min_time}s")
    print(f"  🐢 Slowest      : {max_time}s  → \"{slowest.user_input}\"")
    print(f"  📊 Average time : {avg_time}s")
    print(f"  🔧 Most tools   : {len(most_tools.tool_calls)} calls → \"{most_tools.user_input}\"")

    if failed:
        print("\n  FAILED TESTS :")
        for r in failed:
            print(f"  [{r.prompt_id}] {r.user_input} → {r.error}")

    print("=" * 70 + "\n")

    return results

# ── TEST PROMPTS ───────────────────────────────────────────────────────────
test_prompts = [
    "What is the current weather in Casablanca ?",
    "Will it rain in Rabat this afternoon ?",
    "Are there any weather alerts in Casablanca ?",
    "What should I wear tonight in Marrakech ?",
    "Give me the weather forecast for the next 3 days in Agadir.",
    "Will rain at 17:00 GMT in Casablanca",
    "What was the weather yesterday in Fes ?",        # out of scope
    "Who won the world cup in 2022 ?",                # out of scope
]

if __name__ == "__main__":
    asyncio.run(run_test_suite(agent, test_prompts))