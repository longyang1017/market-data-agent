# Tool definitions: what Claude is told about each tool.

SYMBOL_INPUT_SCHEMA = {
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
}

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
    "input_schema": SYMBOL_INPUT_SCHEMA
}

GET_ORDERBOOK_TOOL = {
    "name": "get_orderbook",
    "description": (
        "Get the current order book for one trading pair on Bybit spot: the "
        "200 best bid levels and 200 best ask levels, each with a price and "
        "a size in the base coin, plus Bybit's timestamp in Unix "
        "milliseconds. Call this when the user asks about liquidity, market "
        "depth, or how much is bid or offered near the price. For only the "
        "current price or best bid and ask, use get_ticker instead. For a "
        "depth question, add the sizes of the levels inside the requested "
        "range. If the levels stop before the end of that range, say the "
        "total is a minimum, not a complete figure. It does not return "
        "executed trades, price history, or other exchanges. If the pair is "
        "not listed, it returns an error."
    ),
    "input_schema": SYMBOL_INPUT_SCHEMA,
}

GET_RECENT_TRADES_TOOL = {
    "name": "get_recent_trades",
    "description": (
        "Get the 5 most recent executed trades for one trading pair on Bybit "
        "spot. Each trade has a trade ID, price, size in the base coin, the "
        "taker's side (Buy or Sell), and trade time in Unix milliseconds. "
        "Call this when the user asks what just traded or how large recent "
        "trades were. For the current bid or ask, use get_ticker; for orders "
        "waiting in the book, use get_orderbook. Five trades cover only a "
        "brief moment, so do not present them as a market trend. If the pair "
        "is not listed, it returns an error."
    ),
    "input_schema": SYMBOL_INPUT_SCHEMA,
}