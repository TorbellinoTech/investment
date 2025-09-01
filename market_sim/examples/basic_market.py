"""
Basic market simulation example.

Demonstrates core market functionality without blockchain integration.
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List
import matplotlib.pyplot as plt

from market_sim.core.models.base import Order, Trade, Asset, OrderType, OrderSide
from market_sim.market.exchange.matching_engine import MatchingEngine
from market_sim.market.agents.base_agent import BaseAgent
from market_sim.simulation.engine.simulation_engine import MarketSimulation


class RandomTrader(BaseAgent):
    """Simple random trading agent."""
    
    def __init__(self, agent_id: str, initial_cash: float, risk_tolerance: float = 0.5):
        super().__init__(agent_id, Decimal(str(initial_cash)))
        self.risk_tolerance = risk_tolerance
        
    def generate_orders(self, market_data: dict) -> list:
        """Generate random orders based on market data."""
        orders = []
        
        if random.random() < 0.3:  # 30% chance to place order
            current_price = market_data.get('last_price', 100)
            
            # Random side
            side = OrderSide.BUY if random.random() < 0.5 else OrderSide.SELL
            
            # Random quantity
            quantity = random.randint(10, 100)
            
            # Price based on current market
            if side == OrderSide.BUY:
                price = current_price * (1 - random.uniform(0, 0.02))  # 0-2% below market
            else:
                price = current_price * (1 + random.uniform(0, 0.02))  # 0-2% above market
                
            order = Order.create_limit_order(
                symbol="STOCK",
                side=side,
                quantity=Decimal(str(quantity)),
                price=Decimal(str(round(price, 2))),
                agent_id=self.agent_id
            )
            
            orders.append(order)
            self.orders.append(order)
            
        return orders
    
    def on_order_book_update(self, symbol: str, bids: List[tuple], asks: List[tuple]) -> None:
        """Handle order book updates."""
        pass  # Simple implementation - could use this for smarter trading
    
    def on_trade(self, trade) -> None:
        """Handle trade notifications."""
        pass  # Simple implementation - could track own trades
    
    def on_time_update(self, timestamp: datetime) -> None:
        """Handle time updates."""
        pass  # Simple implementation - could implement time-based strategies


def run_basic_simulation(num_agents: int = 10, simulation_steps: int = 100):
    """Run a basic market simulation."""
    print("=== Basic Market Simulation ===")
    print(f"Agents: {num_agents}, Steps: {simulation_steps}")
    
    # Create matching engine
    engine = MatchingEngine("STOCK")
    
    # Create agents
    agents = []
    for i in range(num_agents):
        agent = RandomTrader(f"trader_{i}", initial_cash=10000.0)
        agents.append(agent)
        
    # Initialize market with some orders
    print("\nInitializing market...")
    initial_price = 100.0
    
    # Add some initial limit orders to create a market
    for i in range(5):
        # Buy orders
        buy_order = Order.create_limit_order(
            symbol="STOCK",
            side=OrderSide.BUY,
            quantity=Decimal("100"),
            price=Decimal(str(initial_price - i)),
            agent_id="market_maker"
        )
        engine.add_order(buy_order)
        
        # Sell orders
        sell_order = Order.create_limit_order(
            symbol="STOCK",
            side=OrderSide.SELL,
            quantity=Decimal("100"),
            price=Decimal(str(initial_price + i + 1)),
            agent_id="market_maker"
        )
        engine.add_order(sell_order)
        
    # Run simulation
    print("\nRunning simulation...")
    prices = []
    volumes = []
    timestamps = []
    
    for step in range(simulation_steps):
        # Get current market data
        order_book = engine.get_order_book("STOCK")
        last_trade = engine.get_last_trade("STOCK")
        
        market_data = {
            'last_price': last_trade.price if last_trade else initial_price,
            'bid': order_book['bids'][0][0] if order_book['bids'] else 0,
            'ask': order_book['asks'][0][0] if order_book['asks'] else 0,
            'spread': (order_book['asks'][0][0] - order_book['bids'][0][0]) if order_book['bids'] and order_book['asks'] else 0
        }
        
        # Generate orders from agents
        step_trades = []
        for agent in agents:
            orders = agent.generate_orders(market_data)
            for order in orders:
                trades = engine.add_order(order)
                step_trades.extend(trades)
                
        # Record data
        if step_trades:
            avg_price = sum(t.price for t in step_trades) / len(step_trades)
            total_volume = sum(t.quantity for t in step_trades)
        else:
            avg_price = market_data['last_price']
            total_volume = 0
            
        prices.append(avg_price)
        volumes.append(total_volume)
        timestamps.append(datetime.now() + timedelta(minutes=step))
        
        if step % 20 == 0:
            print(f"Step {step}: Price=${avg_price:.2f}, Volume={total_volume}, "
                  f"Bid=${market_data['bid']:.2f}, Ask=${market_data['ask']:.2f}")
            
    # Print final statistics
    print("\n=== Simulation Results ===")
    print(f"Total trades: {len(engine.trades)}")
    print(f"Final price: ${prices[-1]:.2f}")
    print(f"Price range: ${min(prices):.2f} - ${max(prices):.2f}")
    print(f"Average volume: {sum(volumes) / len(volumes):.2f}")
    
    # Plot results
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # Price chart
    ax1.plot(range(len(prices)), prices, 'b-', label='Price')
    ax1.set_xlabel('Time Step')
    ax1.set_ylabel('Price ($)')
    ax1.set_title('Stock Price Over Time')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Volume chart
    ax2.bar(range(len(volumes)), volumes, color='green', alpha=0.6)
    ax2.set_xlabel('Time Step')
    ax2.set_ylabel('Volume')
    ax2.set_title('Trading Volume Over Time')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('basic_market_simulation.png', dpi=150, bbox_inches='tight')
    print("\nChart saved as 'basic_market_simulation.png'")
    
    return {
        'prices': prices,
        'volumes': volumes,
        'total_trades': len(engine.trades),
        'final_order_book': engine.get_order_book("STOCK")
    }


if __name__ == "__main__":
    # Run the simulation
    results = run_basic_simulation(num_agents=20, simulation_steps=200)
    print(f"\nSimulation completed with {results['total_trades']} trades") 