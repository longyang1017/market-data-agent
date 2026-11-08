import anthropic
from datetime import datetime, timezone
from dotenv import load_dotenv
import json

from exchanges.bybit import get_orderbook, get_recent_trades, get_ticker, BybitError
from tools import GET_ORDERBOOK_TOOL, GET_RECENT_TRADES_TOOL, GET_TICKER_TOOL

load_dotenv()
client = anthropic.Anthropic()

MODEL = "claude-haiku-5-5"
MAX_STEPS = 5

TOOLS = [GET_TICKER_TOOL, GET_ORDERBOOK_TOOL, GET_RECENT_TRADES_TOOL]

TOOL_FUNCTIONS = {
    "get_ticker": get_ticker,
    "get_orderbook": get_orderbook,
    "get_recent_trades": get_recent_trades,
}

def run_tool(name: str, tool_input: dict, tool_functions: dict) -> str:
    function = tool_functions[name]
    result = function(**tool_input)

    if isinstance(result, list):
        return json.dumps([item.model_dump(mode="json") for item in result])
    return result.model_dump_json()

def build_tool_result(block, tool_functions: dict) -> dict:
    try:
        content = run_tool(block.name, block.input, tool_functions)
    except (BybitError, ValueError, KeyError, TypeError) as exc:
        return {
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": f"Error: {exc}",
            "is_error": True,
        }

    return {
        "type": "tool_result",
        "tool_use_id": block.id,
        "content": content,
    }

def run_agent(question: str, tool_functions: dict = TOOL_FUNCTIONS) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    system_prompt = f"""You answer questions about crypto spot markets using live Bybit data from your tools.
    The current time is {now}.

    Rules:
    - Take every market figure from a tool result in this conversation. Never use memory or estimate one.
    - If a tool fails, or the data can't answer the question, say so plainly instead of guessing.
    - When you report market data, include its timestamp in UTC.
    - Do not give investment advice or predict prices. If asked whether to buy, sell or hold, briefly decline. You may still offer factual market data.
    """


    messages = [{"role": "user", "content": question}]

    for step in range(MAX_STEPS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )
        print(f"step {step + 1}: {response.stop_reason}")
        print("tokens:", response.usage.input_tokens, "in,", response.usage.output_tokens, "out")

        if response.stop_reason != "tool_use":
            return "".join(
                block.text for block in response.content if block.type == "text"
            )

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_results.append(build_tool_result(block, tool_functions))

        messages.append({"role": "user", "content": tool_results})

    return f"Stopped: no final answer after {MAX_STEPS} steps."


if __name__ == "__main__":
    print(run_agent("What is an orderbook?"))