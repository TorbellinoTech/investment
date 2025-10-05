class MarketEnvironment:
    def __init__(self, initial_balance=0):
        self.balance = initial_balance
        self.portfolio = {}

    def step(self, symbol, action, price, quantity):
        if action == "buy":
            cost = price * quantity
            if cost <= self.balance:
                self.balance -= cost
                self.portfolio[symbol] = self.portfolio.get(symbol, 0) + quantity
        elif action == "sell":
            if symbol in self.portfolio and self.portfolio[symbol] >= quantity:
                self.portfolio[symbol] -= quantity
                self.balance += price * quantity
