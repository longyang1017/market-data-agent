import json
from pathlib import Path

# need to run from project root to see this file (.venv/bin/python -m evals.record_snapshots)
from exchanges.bybit import get_raw_ticker

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


def save(name: str, data: dict) -> None:
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    path = SNAPSHOT_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2))
    print("saved", path)


if __name__ == "__main__":
    save("ticker_BTCUSDT", get_raw_ticker("BTCUSDT"))
