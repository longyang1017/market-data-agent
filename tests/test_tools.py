import inspect

import pytest

from exchanges.bybit import get_orderbook, get_recent_trades, get_ticker
from tools import GET_ORDERBOOK_TOOL, GET_RECENT_TRADES_TOOL, GET_TICKER_TOOL


@pytest.mark.parametrize(
    ("tool", "function"),
    [
        (GET_TICKER_TOOL, get_ticker),
        (GET_ORDERBOOK_TOOL, get_orderbook),
        (GET_RECENT_TRADES_TOOL, get_recent_trades),
    ],
)
def test_tool_definition_matches_the_python_function(tool, function):
    # The definition and the function are separate, so they can drift apart.
    schema = tool["input_schema"]
    parameters = inspect.signature(function).parameters
    required_parameters = [
        name
        for name, parameter in parameters.items()
        if parameter.default is inspect.Parameter.empty
    ]

    assert tool["name"] == function.__name__
    assert sorted(schema["properties"]) == sorted(parameters)
    assert sorted(schema["required"]) == sorted(required_parameters)
