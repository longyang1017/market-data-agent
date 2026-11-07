import httpx
from decimal import Decimal
from pydantic import BaseModel


class BybitError(Exception):
    pass


BASE_URL = "https://api.bybit.com"


def _get_market_data(path: str, params: dict[str, str | int]) -> dict:
    """Fetch a public Bybit endpoint and turn request failures into BybitError."""
    symbol = params["symbol"]
    try:
        response = httpx.get(f"{BASE_URL}{path}", params=params, timeout=5)
        response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise BybitError(f"Bybit request timed out for {symbol}") from exc
    except httpx.HTTPStatusError as exc:
        raise BybitError(f"Bybit HTTP {exc.response.status_code} for {symbol}") from exc
    except httpx.RequestError as exc:
        raise BybitError(f"Could not reach Bybit for {symbol}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise BybitError(f"Bybit returned invalid JSON for {symbol}") from exc

    if not isinstance(data, dict) or "retCode" not in data:
        raise BybitError(f"Bybit returned an unexpected response for {symbol}")
    if data["retCode"] != 0:
        message = data.get("retMsg", "unknown error")
        raise BybitError(f"Bybit error {data['retCode']} for {symbol}: {message}")
    return data

#define the shape/type of ticker
class Ticker(BaseModel):
    symbol: str
    last_price: Decimal
    bid_price: Decimal
    ask_price: Decimal
    server_time_ms: int

def get_raw_ticker(symbol: str) -> dict:
    return _get_market_data(
        "/v5/market/tickers", {"category": "spot", "symbol": symbol}
    )

def parse_ticker(data:dict) -> Ticker:
    tickers = data["result"]["list"]
    if not tickers:
        raise ValueError("Bybit returned no ticker")

    ticker = tickers[0]
    clean_ticker = Ticker(
        symbol=ticker["symbol"],
        last_price=ticker["lastPrice"],
        bid_price=ticker["bid1Price"],
        ask_price=ticker["ask1Price"],
        server_time_ms=data["time"],
    )
    return clean_ticker

def get_ticker(symbol:str) -> Ticker:
    data = get_raw_ticker(symbol)
    return parse_ticker(data)

class OrderLevel(BaseModel):
    price: Decimal
    size: Decimal

class Orderbook(BaseModel):
    symbol: str
    bids: list[OrderLevel]
    asks: list[OrderLevel]
    ts: int

def get_raw_orderbook(symbol: str) -> dict:
    return _get_market_data(
        "/v5/market/orderbook",
        {"category": "spot", "symbol": symbol, "limit": 200},
    )

def parse_orderbook(data:dict) -> Orderbook:
    orderbooks = data["result"]

    if not orderbooks:
        raise ValueError("Bybit returned no orderbook")
    if not orderbooks["b"] or not orderbooks["a"]:
        raise ValueError("Bybit returned an empty orderbook side")
         

    bids = []
    for price, size in orderbooks["b"]:
        bids.append(OrderLevel(price=price, size=size))

    asks = []
    for price, size in orderbooks["a"]:
        asks.append(OrderLevel(price=price, size=size))

    clean_orderbook = Orderbook(
        symbol=orderbooks["s"],
        bids=bids,
        asks=asks,
        ts=orderbooks["ts"],
    )
    return clean_orderbook

def get_orderbook(symbol:str) -> Orderbook:
    data = get_raw_orderbook(symbol)
    return parse_orderbook(data)

class Trade(BaseModel):
    trade_id: str
    symbol: str
    price: Decimal
    size: Decimal
    side: str
    trade_time_ms: int

def get_raw_recent_trades(symbol: str) -> dict:
    return _get_market_data(
        "/v5/market/recent-trade",
        {"category": "spot", "symbol": symbol, "limit": 5},
    )

def parse_recent_trades(data:dict) -> list[Trade]:
    recent_trades = data["result"]["list"]
    if not recent_trades:
        raise ValueError("Bybit returned no recent trades")
    clean_trades = []
    for trade in recent_trades:
        clean_trades.append(
            Trade(
                trade_id= trade["execId"],
                symbol= trade["symbol"],
                price= trade["price"],
                size= trade["size"],
                side= trade["side"],
                trade_time_ms= trade["time"]
            )
        )
    return clean_trades

def get_recent_trades(symbol:str) -> list[Trade]:
    data = get_raw_recent_trades(symbol)
    return parse_recent_trades(data)

# only runs when this code is ran by this file (for testing)
# won't run if get_raw_ticker is called by others
if __name__ == "__main__":
    print(get_recent_trades("BTCUSDT"))

