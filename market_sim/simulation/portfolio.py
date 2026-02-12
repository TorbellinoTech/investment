class Portfolio:
    def __init__(self, initial_cash=0):
        self.cash = initial_cash
        self.holdings = {}

    def buy(self, symbol, quantity, price):
        cost = quantity * price
        if cost <= self.cash:
            self.cash -= cost
            self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity

    def sell(self, symbol, quantity, price):
        if symbol in self.holdings and self.holdings[symbol] >= quantity:
            self.holdings[symbol] -= quantity
            self.cash += quantity * price
