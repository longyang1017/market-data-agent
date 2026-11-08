import json
from pathlib import Path

from agent import run_agent
from exchanges.bybit import BybitError, Ticker, parse_ticker

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"

def replay_ticker(symbol: str) -> Ticker:
    path = SNAPSHOT_DIR / f"ticker_{symbol}.json"
    print("replaying", symbol)
    if not path.exists():
        raise BybitError(f"Bybit error 10001 for {symbol}: Not supported symbols")
    return parse_ticker(json.loads(path.read_text()))
    # json.loads turn json object into dict

REPLAY_FUNCTIONS = {"get_ticker": replay_ticker}

if __name__ == "__main__":
    question = "What's the BTC price on Bybit?"
    expected = replay_ticker("BTCUSDT").last_price

    answer = run_agent(question, tool_functions=REPLAY_FUNCTIONS)
    passed = str(expected) in answer.replace(",", "")

    print(answer)
    print("expected:", expected, "->", "PASS" if passed else "FAIL")