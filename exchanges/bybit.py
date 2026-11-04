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

# only runs when this code is ran by this file (for testing)
# won't run if get_raw_ticker is called by others
if __name__ == "__main__":
    print(get_ticker("BTCUSDT"))
