import pytest
import httpx
from decimal import Decimal
from exchanges.bybit import (
    BybitError,
    get_raw_orderbook,
    get_raw_recent_trades,
    get_raw_ticker,
    parse_orderbook,
    parse_recent_trades,
    parse_ticker,
)


def test_parse_ticker():
    response = {
        "time": 1000,
        "result": {
            "list": [{
                "symbol": "BTCUSDT",
                "lastPrice": "100.50",
                "bid1Price": "100.40",
                "ask1Price": "100.60",
            }]
        },
    }

    ticker = parse_ticker(response)

    assert ticker.symbol == "BTCUSDT"
    assert ticker.last_price == Decimal("100.50")
    assert ticker.server_time_ms == 1000

def test_parse_ticker_rejects_empty_list():
    response = {"time": 1000, "result": {"list": []}}

    with pytest.raises(ValueError, match="no ticker"):
        parse_ticker(response)

def test_parse_orderbook():
    response = {"result":{
        "s": "BTCUSDT",
        "ts": 1000,
        "a": [['80217.8', '0.902349'], ['80219.3', '0.022534'], ['80220.5', '0.015026']],
        "b": [['80217.7', '0.370004'], ['80217.6', '0.001326'], ['80216.8', '0.001833']]
        }
    }

    orderbook = parse_orderbook(response)

    assert orderbook.symbol == "BTCUSDT"
    assert orderbook.ts == 1000
    assert orderbook.asks[0].price == Decimal("80217.8")
    assert orderbook.asks[0].size == Decimal("0.902349")
    assert orderbook.bids[0].price == Decimal("80217.7")
    assert orderbook.bids[0].size == Decimal("0.370004")

def test_parse_orderbook_rejects_empty_side():
    response = {
        "result":{
        "s": "BTCUSDT",
        "ts": 1000,
        "a": [],
        "b": [['80217.7', '0.370004'], ['80217.6', '0.001326'], ['80216.8', '0.001833']]
        }
    }

    with pytest.raises(ValueError, match="empty orderbook side"):
        parse_orderbook(response)

def test_parse_recent_trades():
    response = {
        "result": {
            "list": [
                {
                "execId": "2290000001259057332",
                "symbol": "BTCUSDT",
                "price": "75873.4",
                "size": "0.02775",
                "side": "Sell",
                "time": "1793980739100",
            },
            {
                "execId": "2290000001259057331",
                "symbol": "BTCUSDT",
                "price": "0.000066",
                "size": "0.02775",
                "side": "Sell",
                "time": "1793980739100" ,
            }
            ]
        },
    }

    trades = parse_recent_trades(response)

    assert len(trades) == 2
    assert trades[0].trade_id == "2290000001259057332"
    assert trades[0].symbol == "BTCUSDT"
    assert trades[0].price == Decimal("75873.4")
    assert trades[0].size == Decimal("0.02775")
    assert trades[0].side == "Sell"
    assert trades[0].trade_time_ms == 1793980739100
    assert trades[1].trade_id == "2290000001259057331"
    assert trades[1].price == Decimal("0.000066")

@pytest.mark.parametrize(
    "fetch",
    [get_raw_ticker, get_raw_orderbook, get_raw_recent_trades],
)
def test_market_data_timeout(monkeypatch, fetch):
    def fake_get(*args, **kwargs):
        raise httpx.ReadTimeout("simulated timeout")

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(BybitError, match="timed out"):
        fetch("BTCUSDT")


@pytest.mark.parametrize(
    ("fetch", "path", "expected_params"),
    [
        (get_raw_ticker, "/v5/market/tickers", {"category": "spot", "symbol": "BTCUSDT"}),
        (get_raw_orderbook, "/v5/market/orderbook", {"category": "spot", "symbol": "BTCUSDT", "limit": 200}),
        (get_raw_recent_trades, "/v5/market/recent-trade", {"category": "spot", "symbol": "BTCUSDT", "limit": 5}),
    ],
)
def test_market_data_request(monkeypatch, fetch, path, expected_params):
    def fake_get(url, *, params, timeout):
        assert url == f"https://api.bybit.com{path}"
        assert params == expected_params
        assert timeout == 5.0
        return httpx.Response(
            200,
            json={"retCode": 0, "result": {}},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)
    assert fetch("BTCUSDT")["retCode"] == 0


def test_market_data_http_error(monkeypatch):
    def fake_get(url, **kwargs):
        return httpx.Response(503, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    with pytest.raises(BybitError, match="HTTP 503") as error:
        get_raw_ticker("BTCUSDT")
    assert isinstance(error.value.__cause__, httpx.HTTPStatusError)


def test_market_data_connection_error(monkeypatch):
    def fake_get(*args, **kwargs):
        raise httpx.ConnectError("simulated connection failure")

    monkeypatch.setattr(httpx, "get", fake_get)
    with pytest.raises(BybitError, match="Could not reach Bybit"):
        get_raw_ticker("BTCUSDT")


def test_market_data_bybit_error(monkeypatch):
    def fake_get(url, **kwargs):
        return httpx.Response(
            200,
            json={"retCode": 10001, "retMsg": "Not supported symbols"},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)
    with pytest.raises(BybitError, match="10001.*Not supported symbols"):
        get_raw_ticker("NOTAREALCOINUSDT")


def test_market_data_invalid_json(monkeypatch):
    def fake_get(url, **kwargs):
        return httpx.Response(200, text="not JSON", request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    with pytest.raises(BybitError, match="invalid JSON"):
        get_raw_ticker("BTCUSDT")
