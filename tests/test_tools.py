import inspect

from exchanges.bybit import get_ticker
from tools import GET_TICKER_TOOL


def test_ticker_tool_has_the_fields_the_api_requires():
    assert GET_TICKER_TOOL["name"] == "get_ticker"
    assert GET_TICKER_TOOL["description"]
    assert GET_TICKER_TOOL["input_schema"]["type"] == "object"


def test_ticker_schema_matches_the_python_function():
    # The definition and the function are separate, so they can drift apart.
    schema = GET_TICKER_TOOL["input_schema"]
    assert list(schema["properties"]) == list(inspect.signature(get_ticker).parameters)
    assert schema["required"] == ["symbol"]
