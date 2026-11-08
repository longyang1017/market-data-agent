import json
import re
from decimal import Decimal
from pathlib import Path

from agent import run_agent
from exchanges.bybit import BybitError, Ticker, Orderbook, Trade, parse_ticker, parse_orderbook, parse_recent_trades

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"

def load_snapshot(kind: str, symbol: str) -> dict:
    path = SNAPSHOT_DIR / f"{kind}_{symbol}.json"
    if not path.exists():
        raise BybitError(f"Bybit error 10001 for {symbol}: Not supported symbols")
    return json.loads(path.read_text())

def replay_ticker(symbol: str) -> Ticker:
    return parse_ticker(load_snapshot("ticker", symbol))

def replay_orderbook(symbol: str) -> Orderbook:
    return parse_orderbook(load_snapshot("orderbook", symbol))

def replay_recent_trades(symbol: str) -> list[Trade]:
    return parse_recent_trades(load_snapshot("trades", symbol))

def numbers_in(text: str) -> list[Decimal]:
    return [Decimal(n) for n in re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))]

def mentions(text: str, expected: Decimal, tolerance: Decimal) -> bool:
    return any(abs(n - expected) <= abs(expected) * tolerance for n in numbers_in(text))

REPLAY_FUNCTIONS = {
    "get_ticker": replay_ticker,
    "get_orderbook": replay_orderbook,
    "get_recent_trades": replay_recent_trades,
}

def ask_depth(book: Orderbook, pct: Decimal) -> Decimal:
    limit = book.asks[0].price * (1 + pct / 100)
    return sum(level.size for level in book.asks if level.price <= limit)

def bid_depth(book: Orderbook, pct: Decimal) -> Decimal:
    limit = book.bids[0].price * (1 - pct / 100)
    return sum(level.size for level in book.bids if level.price >= limit)

btc = replay_ticker("BTCUSDT")
eth = replay_ticker("ETHUSDT")
eth_book = replay_orderbook("ETHUSDT")
btc_book = replay_orderbook("BTCUSDT")
btc_trades = replay_recent_trades("BTCUSDT")
latest_btc_trade = max(btc_trades, key=lambda trade: trade.trade_time_ms)

EXACT = Decimal("0")
DEPTH = Decimal("0.005")

QUESTIONS = [
    {"id": "btc_price",
     "question": "What's the BTC price on Bybit?",
     "tools": [["get_ticker"]], "numbers": [btc.last_price], "tolerance": EXACT},
    {"id": "eth_spread",
     "question": "What are the best bid and ask for ETH on Bybit?",
     "tools": [["get_ticker"]], "numbers": [eth.bid_price, eth.ask_price], "tolerance": EXACT},
    {"id": "eth_ask_depth",
     "question": "How much ETH is offered on Bybit at prices within 0.1% above the best ask?",
     "tools": [["get_orderbook"]], "numbers": [ask_depth(eth_book, Decimal("0.1"))], "tolerance": DEPTH},
    {"id": "fake_coin",
     "question": "What's the price of FAKECOIN on Bybit?",
     "tools": [["get_ticker"]], "numbers": [], "tolerance": EXACT, "manual": True},
    {"id": "advice",
     "question": "Should I buy BTC right now?",
     "tools": [[], ["get_ticker"]], "numbers": [], "tolerance": EXACT, "manual": True},
    {"id": "btc_eth_prices",
     "question": "What are the current BTC and ETH prices on Bybit?",
     "tools": [["get_ticker"]], "numbers": [btc.last_price, eth.last_price], "tolerance": EXACT},
    {"id": "btc_bid_depth",
     "question": "How much BTC is bid on Bybit at prices within 0.1% below the best bid?",
     "tools": [["get_orderbook"]], "numbers": [bid_depth(btc_book, Decimal("0.1"))], "tolerance": DEPTH},
    {"id": "btc_last_trade",
     "question": "What was the most recent BTC trade on Bybit? Give its price and side.",
     "tools": [["get_recent_trades"]], "numbers": [latest_btc_trade.price], "tolerance": EXACT},
    {"id": "prediction",
     "question": "Where will the ETH price be tomorrow?",
     "tools": [[], ["get_ticker"]], "numbers": [], "tolerance": EXACT, "manual": True},
    {"id": "concept",
     "question": "What is an order book?",
     "tools": [[]], "numbers": [], "tolerance": EXACT},
]

def grade(case: dict, result: dict) -> tuple[bool, bool]:
    called = sorted({call["name"] for call in result["tool_calls"]})
    tools_ok = called in [sorted(t) for t in case["tools"]]
    numbers_ok = result["completed"] and all(
        mentions(result["answer"], n, case["tolerance"]) for n in case["numbers"]
    )
    return tools_ok, numbers_ok

if __name__ == "__main__":
    rows = []
    for case in QUESTIONS:
        result = run_agent(case["question"], tool_functions=REPLAY_FUNCTIONS)
        tools_ok, numbers_ok = grade(case, result)
        rows.append((case, result, tools_ok, numbers_ok))

    total_in = total_out = 0
    for case, result, tools_ok, numbers_ok in rows:
        total_in += result["input_tokens"]
        total_out += result["output_tokens"]
        print(f"{case['id']:15} tools={'PASS' if tools_ok else 'FAIL'} "
              f"numbers={'PASS' if numbers_ok else 'FAIL'}")
        if case.get("manual") or not (tools_ok and numbers_ok):
            print("   answer:", result["answer"][:300].replace("\n", " "))
            if case["numbers"]:
                print("   expected:", [str(n) for n in case["numbers"]])

    cost = total_in * 0.10 / 1_000_000 + total_out * 0.50 / 1_000_000
    print(f"tokens: {total_in} in, {total_out} out, est. cost ${cost:.4f}")