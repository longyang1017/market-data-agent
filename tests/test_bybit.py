import pytest
from decimal import Decimal
from exchanges.bybit import parse_ticker


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
    assert ticker.response_time_ms == 1000

def test_parse_ticker_rejects_empty_list():
    response = {"time": 1000, "result": {"list": []}}

    with pytest.raises(ValueError, match="no ticker"):
        parse_ticker(response)