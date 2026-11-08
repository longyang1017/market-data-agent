import json
from pathlib import Path

# need to run from project root to see this file (.venv/bin/python -m evals.record_snapshots)
from exchanges.bybit import get_raw_ticker, get_raw_orderbook, get_raw_recent_trades

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


def save(name: str, data: dict) -> None:
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    path = SNAPSHOT_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2))
    print("saved", path)


if __name__ == "__main__":
    for symbol in ["BTCUSDT", "ETHUSDT"]:
        save(f"ticker_{symbol}", get_raw_ticker(symbol))
        save(f"orderbook_{symbol}", get_raw_orderbook(symbol))
        save(f"trades_{symbol}", get_raw_recent_trades(symbol))