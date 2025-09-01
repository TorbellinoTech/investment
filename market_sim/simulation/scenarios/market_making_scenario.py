"""
Market Making Scenario

This scenario simulates a market with:
1. One market maker providing liquidity
2. Multiple random traders creating market pressure
3. Periodic market events to test strategy robustness
"""

from datetime import datetime, timedelta
from decimal import Decimal
import random
from typing import List, Dict
import numpy as np

from market_sim.core.models.base import Asset, OrderSide, OrderType, Trade
from market_sim.market.agents.base_agent import BaseAgent
from market_sim.strategies.hft.market_maker import MarketMaker
from market_sim.simulation.engine.simulation_engine import MarketSimulation
from market_sim.core.utils.time_utils import utc_now

class RandomTrader(BaseAgent):
    """Simple trader that randomly places market orders."""
    def __init__(self, agent_id: str, initial_balance: Decimal,
                 symbols: List[str],
                 trade_frequency: float = 0.1,  # Probability of trading each update
                 min_trade_size: Decimal = Decimal('1'),
                 max_trade_size: Decimal = Decimal('1000')):
        super().__init__(agent_id, initial_balance)
        self.symbols = symbols
        self.trade_frequency = trade_frequency
        self.min_trade_size = min_trade_size
        self.max_trade_size = max_trade_size
        self.last_prices: Dict[str, Decimal] = {}
    
    def on_order_book_update(self, symbol: str, bids: List[tuple], asks: List[tuple]) -> None:
        """Possibly place a random trade."""
        if symbol not in self.symbols or not bids or not asks:
            return
            
        if random.random() > self.trade_frequency:
            return
            
        # Update last known price
        mid_price = (Decimal(str(bids[0][0])) + Decimal(str(asks[0][0]))) / 2
        self.last_prices[symbol] = mid_price
        
        # Randomly choose direction and size
        side = random.choice([OrderSide.BUY, OrderSide.SELL])
        size = Decimal(str(random.uniform(
            float(self.min_trade_size),
            float(self.max_trade_size)
        )))
        
        # Create and validate order
        order = self.create_market_order(symbol, side, size)
        if self.validate_order(order, self.last_prices):
            return order
    
    def on_trade(self, trade: Trade) -> None:
        """Update last known price on trades."""
        if trade.symbol in self.symbols:
            self.last_prices[trade.symbol] = trade.price
    
    def on_time_update(self, timestamp: datetime) -> None:
        """No time-based actions needed."""
        pass

def create_market_making_scenario(
    start_time: datetime = None,
    duration: timedelta = timedelta(hours=1),
    symbols: List[str] = None,
    num_random_traders: int = 10,
    include_market_events: bool = True
) -> MarketSimulation:
    """Create a market making scenario."""
    
    # Set default values
    if start_time is None:
        start_time = utc_now()
    if symbols is None:
        symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    # Create simulation
    sim = MarketSimulation(
        start_time=start_time,
        end_time=start_time + duration,
        time_step=timedelta(milliseconds=100)
    )
    
    # Add assets
    for symbol in symbols:
        asset = Asset(
            symbol=symbol,
            name=f"Stock {symbol}",
            asset_type="stock",
            decimals=2,
            min_trade_size=Decimal('1'),
            max_trade_size=Decimal('1000000'),
            tick_size=Decimal('0.01')
        )
        sim.add_asset(asset)
        sim.add_exchange(symbol)
    
    # Add market maker
    market_maker = MarketMaker(
        agent_id="MM_001",
        initial_balance=Decimal('1000000'),
        symbols=symbols,
        max_position=Decimal('10000'),
        target_spread=Decimal('0.002'),  # 0.2% spread
        position_limit=Decimal('50000'),
        risk_factor=Decimal('0.5'),
        order_size=Decimal('100'),
        min_spread=Decimal('0.001'),
        max_spread=Decimal('0.005'),
        volatility_window=100
    )
    sim.add_agent(market_maker)
    
    # Add random traders
    for i in range(num_random_traders):
        trader = RandomTrader(
            agent_id=f"TRADER_{i+1:03d}",
            initial_balance=Decimal('10000000'),
            symbols=symbols,
            trade_frequency=1,
            min_trade_size=Decimal('1'),
            max_trade_size=Decimal('1000')
        )
        sim.add_agent(trader)

    # Schedule initial market orders to seed trading
    for symbol in symbols:
        # Schedule some initial trades spread out in the first few seconds
        for i in range(3):  # Create 3 initial trades per symbol
            order_time = start_time + timedelta(seconds=i*2)  # Space them out every 2 seconds
            
            # Schedule a buy and sell order
            sim.schedule_event(
                timestamp=order_time,
                event_type='order',
                data=sim.agents['TRADER_001'].create_market_order(
                    symbol, OrderSide.BUY, Decimal('110')
                )
            )
            sim.schedule_event(
                timestamp=order_time + timedelta(milliseconds=100),
                event_type='order',
                data=sim.agents['TRADER_002'].create_market_order(
                    symbol, OrderSide.SELL, Decimal('90')
                )
            )

    # Add market events if requested
    #if include_market_events:
    #    _add_market_events(sim, start_time, duration, symbols)
    
    return sim

def _add_market_events(
    sim: MarketSimulation,
    start_time: datetime,
    duration: timedelta,
    symbols: List[str]
) -> None:
    """Add various market events to the simulation."""
    
    # Add some price shocks
    for symbol in symbols:
        # Add 2-3 price shocks per symbol
        num_shocks = random.randint(2, 3)
        for _ in range(num_shocks):
            shock_time = start_time + timedelta(
                seconds=random.uniform(0, duration.total_seconds())
            )
            magnitude = random.uniform(-5, 5)  # -5% to +5% price shock
            
            sim.schedule_event(
                timestamp=shock_time,
                event_type='market_event',
                data={
                    'type': 'price_shock',
                    'symbol': symbol,
                    'magnitude': magnitude
                }
            )
    
    # Add volatility regime changes
    for symbol in symbols:
        # Add 1-2 volatility changes per symbol
        num_changes = random.randint(1, 2)
        for _ in range(num_changes):
            change_time = start_time + timedelta(
                seconds=random.uniform(0, duration.total_seconds())
            )
            new_volatility = random.uniform(0.1, 0.4)  # 10% to 40% annualized volatility
            
            sim.schedule_event(
                timestamp=change_time,
                event_type='market_event',
                data={
                    'type': 'volatility_change',
                    'symbol': symbol,
                    'new_volatility': new_volatility
                }
            )

if __name__ == '__main__':
    # Run a sample simulation
    start_time = utc_now()
    duration = timedelta(hours=1)
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    print(f"Creating market making scenario...")
    sim = create_market_making_scenario(
        start_time=start_time,
        duration=duration,
        symbols=symbols,
        num_random_traders=10,
        include_market_events=True
    )
    
    print(f"Running simulation...")
    results = sim.run()
    
    print("\nSimulation completed!")
    print(f"Total trades: {len(results['trades'])}")
    print(f"Number of market events: {len([e for e in sim.event_queue if e.event_type == 'market_event'])}")
    
    # Print some basic statistics
    for symbol in symbols:
        symbol_trades = [t for t in results['trades'] if t.symbol == symbol]
        if symbol_trades:
            prices = [float(t.price) for t in symbol_trades]
            print(f"\n{symbol} Statistics:")
            print(f"Number of trades: {len(symbol_trades)}")
            print(f"Average price: ${np.mean(prices):.2f}")
            print(f"Price range: ${min(prices):.2f} - ${max(prices):.2f}")
            print(f"Price volatility: {np.std(prices):.4f}") 
