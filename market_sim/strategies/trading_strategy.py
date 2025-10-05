import random

class TradingStrategy:
    def __init__(self, symbol):
        self.symbol = symbol

    def generate_signal(self, prices):
        # Simple random strategy for testing
        if not prices:
            return "hold"
        return random.choice(["buy", "sell", "hold"])
