"""One question, one tool: show what Claude asks for. No tool is executed."""
import sys

import anthropic
from dotenv import load_dotenv

from tools import GET_TICKER_TOOL, GET_ORDERBOOK_TOOL, GET_RECENT_TRADES_TOOL

load_dotenv()
client = anthropic.Anthropic()

question = sys.argv[1] if len(sys.argv) > 1 else "What's the BTC price on Bybit?"
response = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=1024,
    tools=[GET_TICKER_TOOL, GET_ORDERBOOK_TOOL, GET_RECENT_TRADES_TOOL],
    messages=[{"role": "user", "content": question}],
)

print("stop_reason:", response.stop_reason)
for block in response.content:
    if block.type == "tool_use":
        print("tool_use:", block.name, block.input)
    elif block.type == "text":
        print("text:", block.text)
print("tokens:", response.usage.input_tokens, "in,", response.usage.output_tokens, "out")
