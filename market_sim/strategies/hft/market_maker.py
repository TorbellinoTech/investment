"""
Market Making Strategy

This module implements a basic market making strategy that:
1. Maintains a presence on both sides of the order book
2. Manages inventory risk
3. Adjusts spreads based on volatility
4. Uses position limits and risk controls
"""

from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from market_sim.market.agents.base_agent import BaseAgent
from market_sim.core.models.base import Order, Trade, OrderSide, OrderType
from market_sim.core.utils.time_utils import utc_now

class MarketMaker(BaseAgent):
    def __init__(self, agent_id: str, initial_balance: Decimal,
                 symbols: List[str],
                 max_position: Decimal = Decimal('1000'),
                 target_spread: Decimal = Decimal('0.02'),  # 2% spread
                 position_limit: Decimal = Decimal('5000'),
                 risk_factor: Decimal = Decimal('0.5'),
                 order_size: Decimal = Decimal('100'),
                 min_spread: Decimal = Decimal('0.001'),  # 0.1% minimum spread
                 max_spread: Decimal = Decimal('0.05'),   # 5% maximum spread
                 volatility_window: int = 100,            # Number of trades to calculate volatility
                 inventory_target: Decimal = Decimal('0')):
        
        super().__init__(agent_id, initial_balance)
        self.symbols = symbols
        self.max_position = max_position
        self.target_spread = target_spread
        self.position_limit = position_limit
        self.risk_factor = risk_factor
        self.order_size = order_size
        self.min_spread = min_spread
        self.max_spread = max_spread
        self.volatility_window = volatility_window
        self.inventory_target = inventory_target
        
        # State variables
        self.last_prices: Dict[str, List[Decimal]] = {symbol: [] for symbol in symbols}
        self.current_quotes: Dict[str, Dict[str, Order]] = {
            symbol: {'bid': None, 'ask': None} for symbol in symbols
        }
        self.last_order_update = utc_now()
        self.update_interval = timedelta(milliseconds=100)  # 100ms update frequency
        
    def calculate_volatility(self, symbol: str) -> Decimal:
        """Calculate recent price volatility."""
        prices = self.last_prices[symbol][-self.volatility_window:]
        if len(prices) < 2:
            return Decimal('0')
        
        returns = np.diff(np.log([float(p) for p in prices]))
        return Decimal(str(np.std(returns) * np.sqrt(252)))
    
    def calculate_spread(self, symbol: str, mid_price: Decimal) -> Tuple[Decimal, Decimal]:
        """Calculate bid-ask spread based on volatility and inventory."""
        # Base spread
        spread = self.target_spread
        
        # Adjust for volatility
        volatility = self.calculate_volatility(symbol)
        spread = spread * (1 + volatility)
        
        # Adjust for inventory risk
        position = self.get_position(symbol)
        inventory_ratio = position.quantity / self.position_limit
        inventory_skew = self.risk_factor * inventory_ratio
        
        # Calculate bid and ask prices
        half_spread = spread / 2
        bid_spread = half_spread * (1 - inventory_skew)
        ask_spread = half_spread * (1 + inventory_skew)
        
        # Apply minimum and maximum spreads
        bid_spread = max(min(bid_spread, self.max_spread), self.min_spread)
        ask_spread = max(min(ask_spread, self.max_spread), self.min_spread)
        
        bid_price = mid_price * (1 - bid_spread)
        ask_price = mid_price * (1 + ask_spread)
        
        return bid_price, ask_price
    
    def should_update_orders(self, symbol: str, bids: List[tuple], asks: List[tuple]) -> bool:
        """Determine if orders should be updated based on market conditions."""
        if not bids or not asks:
            return True
            
        current_quotes = self.current_quotes[symbol]
        if not current_quotes['bid'] or not current_quotes['ask']:
            return True
            
        # Check if our orders are still at the top of the book
        best_bid = Decimal(str(bids[0][0]))
        best_ask = Decimal(str(asks[0][0]))
        
        our_bid = current_quotes['bid'].price
        our_ask = current_quotes['ask'].price
        
        return (our_bid != best_bid or our_ask != best_ask or 
                utc_now() - self.last_order_update > self.update_interval)
    
    def on_order_book_update(self, symbol: str, bids: List[tuple], asks: List[tuple]) -> None:
        """Update quotes based on order book changes."""
        if symbol not in self.symbols or not bids or not asks:
            return
            
        if not self.should_update_orders(symbol, bids, asks):
            return
            
        # Calculate mid price
        mid_price = (Decimal(str(bids[0][0])) + Decimal(str(asks[0][0]))) / 2
        
        # Store price for volatility calculation
        self.last_prices[symbol].append(mid_price)
        if len(self.last_prices[symbol]) > self.volatility_window:
            self.last_prices[symbol].pop(0)
        
        # Calculate new bid and ask prices
        bid_price, ask_price = self.calculate_spread(symbol, mid_price)
        
        # Cancel existing orders
        self.cancel_current_quotes(symbol)
        
        # Place new orders
        position = self.get_position(symbol)
        
        # Adjust order sizes based on inventory
        bid_size = self.order_size
        ask_size = self.order_size
        
        if position.quantity > 0:
            # Reduce bid size and increase ask size when long
            adjustment = min(position.quantity / self.position_limit, Decimal('1'))
            bid_size *= (1 - adjustment)
            ask_size *= (1 + adjustment)
        elif position.quantity < 0:
            # Increase bid size and reduce ask size when short
            adjustment = min(abs(position.quantity) / self.position_limit, Decimal('1'))
            bid_size *= (1 + adjustment)
            ask_size *= (1 - adjustment)
        
        # Place new orders if within position limits
        if abs(position.quantity + bid_size) <= self.position_limit:
            bid_order = self.create_limit_order(symbol, OrderSide.BUY, bid_size, bid_price)
            self.current_quotes[symbol]['bid'] = bid_order
            
        if abs(position.quantity - ask_size) <= self.position_limit:
            ask_order = self.create_limit_order(symbol, OrderSide.SELL, ask_size, ask_price)
            self.current_quotes[symbol]['ask'] = ask_order
        
        self.last_order_update = utc_now()
    
    def on_trade(self, trade: Trade) -> None:
        """Handle trade updates."""
        if trade.symbol in self.symbols:
            # Store price for volatility calculation
            self.last_prices[trade.symbol].append(trade.price)
            if len(self.last_prices[trade.symbol]) > self.volatility_window:
                self.last_prices[trade.symbol].pop(0)
    
    def on_time_update(self, timestamp: datetime) -> None:
        """Handle time-based updates."""
        # Check for stale orders
        for symbol in self.symbols:
            quotes = self.current_quotes[symbol]
            for side, order in quotes.items():
                if order and (timestamp - order.created_at) > timedelta(seconds=5):
                    self.cancel_current_quotes(symbol)
                    break
    
    def cancel_current_quotes(self, symbol: str) -> None:
        """Cancel current quotes for a symbol."""
        quotes = self.current_quotes[symbol]
        for side in ['bid', 'ask']:
            if quotes[side]:
                self.cancel_all_orders()
                quotes[side] = None 
