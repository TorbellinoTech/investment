"""
Base trading agent class.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
from ...core.models.base import Order, Trade, Position, OrderSide, OrderType, OrderStatus
from ...core.utils.time_utils import utc_now

class BaseAgent(ABC):
    def __init__(self, agent_id: str, initial_balance: Decimal):
        self.agent_id = agent_id
        self.balance = initial_balance
        self.positions: Dict[str, Position] = {}  # symbol -> Position
        self.orders: Dict[str, Order] = {}  # order_id -> Order
        self.trades: List[Trade] = []
        self.last_update = utc_now()
        
    @abstractmethod
    def on_order_book_update(self, symbol: str, bids: List[tuple], asks: List[tuple]) -> None:
        """Called when order book is updated."""
        pass
    
    @abstractmethod
    def on_trade(self, trade: Trade) -> None:
        """Called when a trade occurs."""
        pass
    
    @abstractmethod
    def on_time_update(self, timestamp: datetime) -> None:
        """Called on each time step in the simulation."""
        pass
    
    def get_position(self, symbol: str) -> Position:
        """Get current position for a symbol."""
        if symbol not in self.positions:
            self.positions[symbol] = Position.create(self.agent_id, symbol)
        return self.positions[symbol]
    
    def update_position(self, trade: Trade, is_buyer: bool) -> None:
        """Update position based on a trade."""
        position = self.get_position(trade.symbol)
        side = OrderSide.BUY if is_buyer else OrderSide.SELL
        position.update(trade.quantity, trade.price, side)
        
        # Update cash balance
        trade_value = trade.price * trade.quantity
        if is_buyer:
            self.balance -= trade_value
        else:
            self.balance += trade_value
    
    def create_market_order(self, symbol: str, side: OrderSide, quantity: Decimal) -> Order:
        """Create a market order."""
        order = Order.create_market_order(symbol, side, quantity, self.agent_id)
        self.orders[str(order.id)] = order
        return order
    
    def create_limit_order(self, symbol: str, side: OrderSide, quantity: Decimal, 
                          price: Decimal) -> Order:
        """Create a limit order."""
        order = Order.create_limit_order(symbol, side, quantity, price, self.agent_id)
        self.orders[str(order.id)] = order
        return order
    
    def on_order_fill(self, order: Order, trade: Trade) -> None:
        """Called when one of agent's orders is filled."""
        self.trades.append(trade)
        is_buyer = trade.buyer_order_id == order.id
        self.update_position(trade, is_buyer)
        
        if order.status == OrderStatus.FILLED:
            del self.orders[str(order.id)]
    
    def get_portfolio_value(self, current_prices: Dict[str, Decimal]) -> Decimal:
        """Calculate total portfolio value including cash balance."""
        portfolio_value = self.balance
        
        for symbol, position in self.positions.items():
            if position.quantity != 0 and symbol in current_prices:
                market_value = position.quantity * current_prices[symbol]
                portfolio_value += market_value
        
        return portfolio_value
    
    def get_portfolio_summary(self, current_prices: Dict[str, Decimal]) -> Dict[str, Any]:
        """Get summary of current portfolio state."""
        total_value = self.get_portfolio_value(current_prices)
        positions_summary = {}
        
        for symbol, position in self.positions.items():
            if position.quantity != 0:
                current_price = current_prices.get(symbol)
                if current_price:
                    market_value = position.quantity * current_price
                    unrealized_pnl = (current_price - position.average_entry_price) * position.quantity
                    positions_summary[symbol] = {
                        'quantity': position.quantity,
                        'avg_entry_price': position.average_entry_price,
                        'current_price': current_price,
                        'market_value': market_value,
                        'unrealized_pnl': unrealized_pnl,
                        'realized_pnl': position.realized_pnl
                    }
        
        return {
            'timestamp': utc_now(),
            'agent_id': self.agent_id,
            'cash_balance': self.balance,
            'total_value': total_value,
            'positions': positions_summary,
            'open_orders': len(self.orders),
            'total_trades': len(self.trades)
        }
    
    def validate_order(self, order: Order, current_prices: Dict[str, Decimal]) -> bool:
        """Validate if order can be placed based on current portfolio state."""
        if order.side == OrderSide.SELL:
            position = self.get_position(order.symbol)
            return position.quantity >= order.quantity
        else:  # BUY
            if order.type == OrderType.MARKET:
                # For market orders, use last price as estimate
                estimated_price = current_prices.get(order.symbol)
                if not estimated_price:
                    return False
                estimated_cost = estimated_price * order.quantity
            else:
                estimated_cost = order.price * order.quantity
            
            return self.balance >= estimated_cost
    
    def cancel_all_orders(self) -> List[str]:
        """Cancel all open orders."""
        cancelled_orders = []
        for order_id, order in list(self.orders.items()):
            if order.status in [OrderStatus.PENDING, OrderStatus.PARTIAL]:
                order.status = OrderStatus.CANCELLED
                order.updated_at = utc_now()
                del self.orders[order_id]
                cancelled_orders.append(order_id)
        return cancelled_orders 