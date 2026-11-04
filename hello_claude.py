"""Step 1 smoke test: one call to Claude Haiku 5.5."""
from dotenv import load_dotenv
import anthropic

load_dotenv()  # reads ANTHROPIC_API_KEY from .env into the environment

client = anthropic.Anthropic()  # picks up ANTHROPIC_API_KEY automatically

response = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "In one sentence, what is an order book?"}],
)

# The response is a list of content blocks; we only want the text ones.
for block in response.content:
    if block.type == "text":
        print(block.text)

print("---")
print("stop_reason:", response.stop_reason)
print("input tokens:", response.usage.input_tokens)
print("output tokens:", response.usage.output_tokens)
