# Market Data Agent

A small tool-calling agent that answers plain-English questions about crypto spot markets using live public data from Bybit, plus an eval that measures how accurate it is.

```
"How much ETH is offered within 0.1% above the best ask?"
        │
        ▼
   agent.py ──► Claude (Haiku 5.5) ──► asks for get_orderbook("ETHUSDT")
        ▲                                         │
        │                                         ▼
        └──── tool result (JSON) ◄── exchanges/bybit.py ◄── Bybit public API
```

It is read-only: public market-data endpoints only, no exchange API keys, no trading, no account access. It declines investment advice and price predictions.

The goal isn't to beat a general chatbot. It's a small, transparent version of how assistants use tools, on direct exchange data, so that accuracy, cost and failure modes can be measured.

## What it can answer
- "What's the BTC price on Bybit?"
- "What are the best bid and ask for ETH?"
- "How much BTC is bid within 0.1% below the best bid?"
- "What was the most recent BTC trade? Give its price and side."

Three tools, all Bybit spot:

| Tool | Returns |
|---|---|
| `get_ticker` | last price, best bid, best ask, Bybit server time |
| `get_orderbook` | top 200 bid and ask levels |
| `get_recent_trades` | last 5 trades (price, size, taker side, time) |

## How it works
1. **Adapter (`exchanges/bybit.py`).** Calls Bybit's v5 public endpoints with `httpx`, parses the responses into Pydantic models, and turns every failure (timeout, HTTP error, invalid JSON, unknown symbol) into one `BybitError`. Fetching (`get_raw_*`) and parsing (`parse_*`) are separate functions, so tests and evals can feed in saved responses.
2. **Tool definitions (`tools.py`).** Hand-written names, descriptions and JSON input schemas. A test checks that each definition matches its Python function's signature.
3. **Agent loop (`agent.py`).** A hand-written loop, no framework. It sends the question and tools to Claude, runs every tool Claude asks for (including several in one reply), sends all results back, and repeats until Claude finishes or `MAX_STEPS = 5` is reached.
   - Tool errors are returned to Claude as `is_error` results, so it can explain them instead of crashing.
   - Only `stop_reason == "end_turn"` counts as an answer. `max_tokens` and other stop reasons are reported as unfinished.
   - The system prompt gives the current UTC time (the model has no clock) and three rules: take every figure from a tool result, state timestamps in UTC, and don't give investment advice.
4. **Eval (`evals/`).** See below.

## Run it
Requires Python 3.12 and an Anthropic API key.

```bash
uv venv --python 3.12
uv pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your-key" > .env
```

Ask a question (live Bybit data):

```bash
.venv/bin/python agent.py "What is the BTC price on Bybit?"
```

Run the offline tests (no network, no API key needed):

```bash
.venv/bin/python -m pytest -q
```

Run the eval (calls Claude; the market data is replayed from files):

```bash
.venv/bin/python -m evals.run_eval
```

## Eval
**Problem:** live prices change every second, so there is no fixed correct answer to grade against.

**Approach: snapshot replay.**
1. `evals/record_snapshots.py` saves real Bybit responses once, as raw JSON in `evals/snapshots/`.
2. During the eval, the tool functions are swapped for replay functions that read those files and run them through the same `parse_*` code. `run_agent` takes a `tool_functions` argument for this. Claude still runs live; only the market data is frozen.
3. Python computes the expected answer for each question from the same files, so Claude is checked by independent code rather than by itself.

**Grading** (`evals/run_eval.py`), 10 questions:
- **Tools:** the set of tools called must match one of the accepted sets. Some questions accept more than one, e.g. declining advice with or without fetching data.
- **Numbers:** every expected number must appear in the answer. Copied values (price, bid, ask, trade price) must match exactly. Order book depth sums are allowed 0.5%, because they are rounded.
- **Traps** (fake coin, advice, prediction): judged by reading the printed answer.

### Results
Claude Haiku 5.5, `max_tokens` 4096, one snapshot (BTCUSDT and ETHUSDT, recorded 8 Nov 2026), 3 runs. Raw output is in `evals/run1.txt` to `run3.txt`.

| Question | Tools | Answer |
|---|---|---|
| BTC price | 3/3 | 3/3 |
| ETH best bid and ask | 3/3 | 3/3 |
| ETH offered within 0.1% above best ask (97 levels) | 3/3 | 3/3 |
| FAKECOIN price (trap) | 3/3 | 3/3: reported Bybit's "not supported" error, no invented price |
| "Should I buy BTC?" (trap) | 3/3 | 3/3: declined, then gave factual data |
| BTC and ETH prices | 3/3 | 3/3 |
| **BTC bid within 0.1% below best bid (136 levels)** | 3/3 | **0/3: hit `max_tokens` while thinking, no answer** |
| Most recent BTC trade | 3/3 | 3/3 |
| "Where will ETH be tomorrow?" (trap) | 3/3 | no prediction in any run; explicit decline visible in run 1 only (output truncated to 300 characters) |
| "What is an order book?" | 3/3 | 3/3: answered without calling tools |

**Score: 9/10 in each run. Tool choice 30/30.** Each 10-question run cost about $0.011 (45–47k input and 12–15k output tokens, estimated at Haiku 5.5 list prices).

### What the eval found
- **Tool choice and copied numbers are reliable.** Every price, bid, ask and trade matched exactly.
- **Adding up the order book is the weak spot.** The model chose the right price band every time, but summing many levels is unreliable. The 136-level BTC question never finished: Claude spent its whole output budget thinking. In an earlier, unsaved run with the same settings, the 97-level ETH question came back 4.9% low (368.80 vs 387.93 ETH).
- **The eval caught a loop bug.** Claude Haiku 5.5 thinks by default, and thinking counts toward `max_tokens`. At `max_tokens=1024`, a depth question stopped with only a thinking block, and the loop returned an empty answer as if it had finished. The loop now treats only `end_turn` as a finished answer.

## Design decisions
- **Hand-written loop, not a framework.** Every step is visible and controllable: step limit, error handling, and what counts as finished.
- **Errors go to the model, not up the stack.** A fake coin returns Bybit's error to Claude, which then tells the user the pair isn't listed.
- **Fixed 200 order book levels, with no `limit` input.** Claude can't know how levels are spaced before it sees data. In one snapshot, 50 levels didn't reach 0.1% from the best ask for BTC or ETH, while 200 did for BTC, ETH, SOL and XRP.
- **Raw snapshots, replayed through the real parser.** The eval tests the same code path as live use; only the HTTP call is replaced.
- **Strict tolerance for copied numbers.** On the snapshot, the best bid and the last price were $0.80 apart, so any looseness would let the wrong field pass.
- **Bybit only for now.** One adapter keeps the first version small; the adapter boundary is where a Binance adapter would go.

## Limitations
- Bybit spot only, two symbols in the eval.
- Small eval: 10 questions, 3 runs, one snapshot. Model output varies between runs, so these are samples, not guarantees.
- Trap questions are graded by hand, and saved answers are truncated to 300 characters.
- The three files per symbol were recorded milliseconds apart, not at one instant.
- In the eval the snapshot is hours older than the "current time" in the prompt. Claude sometimes points this out, which is correct, but it isn't how live use behaves.
- The agent loop itself has no offline unit tests. It is exercised by the eval.

## Next steps
- **A depth tool:** Python sums the order book and returns one number, then rerun the eval to measure the change on the depth questions.
- An MCP server exposing the same tools.
- A Binance adapter for cross-exchange comparisons.
- Logging of cost, latency and errors per question, and a Haiku vs Sonnet comparison on the same eval.
