"""Tool definitions: what Claude is told about each tool.

A definition is plain data sent to the API. It runs nothing. Claude reads it,
then asks for a call; our own code has to run the matching Python function.
"""

GET_TICKER_TOOL = {
    "name": "get_ticker",
    "description": (
        "Get the latest spot market snapshot for one trading pair on Bybit: "
        "last traded price, best bid, best ask, and Bybit's server time in "
        "Unix milliseconds. Call this whenever the user asks for a current "
        "price, bid, ask, or bid-ask spread; never answer those from memory. "
        "It covers one pair at a time on Bybit spot only. It does not return "
        "order book depth, recent trades, price history, or other exchanges. "
        "If the pair is not listed, it returns an error instead of a price."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": (
                    "Bybit spot pair: uppercase base and quote coin with no "
                    "separator, such as BTCUSDT or ETHUSDT. Bybit rejects "
                    "lowercase pairs and bare coin names, so send BTCUSDT, "
                    "not btcusdt or BTC."
                ),
            }
        },
        "required": ["symbol"],
    },
}
