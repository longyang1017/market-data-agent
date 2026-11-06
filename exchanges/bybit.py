import httpx
from decimal import Decimal
from pydantic import BaseModel

#define the shape/type of ticker
class Ticker(BaseModel):
    symbol: str
    last_price: Decimal
    bid_price: Decimal
    ask_price: Decimal
    response_time_ms: int

def get_raw_ticker(symbol: str) -> dict:
    response = httpx.get(
        "https://api.bybit.com/v5/market/tickers",
        params={"category":"spot", "symbol":symbol},
        timeout=5.0,
    )
    response.raise_for_status()
    data = response.json()

    #retCode = 0 means request succeeded
    if data["retCode"] != 0:
            raise ValueError(data["retMsg"])
    return data

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
        response_time_ms=data["time"],
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
    response = httpx.get(
        "https://api.bybit.com/v5/market/orderbook",
        params={"category":"spot", "symbol":symbol, "limit": 5},
        timeout=5.0,
    )
    response.raise_for_status()
    data = response.json()

    #retCode = 0 means request succeeded
    if data["retCode"] != 0:
            raise ValueError(data["retMsg"])
    return data

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
    response = httpx.get(
        "https://api.bybit.com/v5/market/recent-trade",
        params={"category":"spot", "symbol":symbol, "limit": 5},
        timeout=5.0,
    )
    response.raise_for_status()
    data = response.json()

    #retCode = 0 means request succeeded
    if data["retCode"] != 0:
            raise ValueError(data["retMsg"])
    return data

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

