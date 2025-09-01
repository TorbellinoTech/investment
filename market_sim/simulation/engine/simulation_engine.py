"""
Market Simulation Engine

This module provides the core simulation engine that:
1. Manages time progression
2. Coordinates multiple exchanges and agents
3. Handles event processing and scheduling
4. Collects and records simulation results
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import heapq
import logging
from market_sim.core.models.base import Order, Trade, Asset
from market_sim.market.exchange.matching_engine import MatchingEngine
from market_sim.market.agents.base_agent import BaseAgent

class SimulationEvent:
    def __init__(self, timestamp: datetime, event_type: str, data: Any):
        self.timestamp = timestamp
        self.event_type = event_type
        self.data = data
    
    def __lt__(self, other):
        return self.timestamp < other.timestamp

class MarketSimulation:
    def __init__(self, 
                 start_time: datetime,
                 end_time: datetime,
                 time_step: timedelta = timedelta(milliseconds=100)):
        self.start_time = start_time
        self.end_time = end_time
        self.time_step = time_step
        self.current_time = start_time
        
        # Components
        self.exchanges: Dict[str, MatchingEngine] = {}
        self.agents: Dict[str, BaseAgent] = {}
        self.assets: Dict[str, Asset] = {}
        
        # Event queue
        self.event_queue = []
        
        # Results collection
        self.trades: List[Trade] = []
        self.metrics: Dict[str, List[Dict]] = {
            'order_book_snapshots': [],
            'agent_metrics': [],
            'market_metrics': []
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
    
    def add_exchange(self, symbol: str) -> None:
        """Add a new exchange for a symbol."""
        self.exchanges[symbol] = MatchingEngine(symbol)
    
    def add_agent(self, agent: BaseAgent) -> None:
        """Add a trading agent to the simulation."""
        self.agents[agent.agent_id] = agent
    
    def add_asset(self, asset: Asset) -> None:
        """Add an asset to the simulation."""
        self.assets[asset.symbol] = asset
    
    def schedule_event(self, timestamp: datetime, event_type: str, data: Any) -> None:
        """Schedule an event for future processing."""
        event = SimulationEvent(timestamp, event_type, data)
        heapq.heappush(self.event_queue, event)
    
    def process_order(self, order: Order) -> List[Trade]:
        """Process an order through the appropriate exchange."""
        if order.symbol not in self.exchanges:
            self.logger.warning(f"No exchange found for symbol {order.symbol}")
            return []
            
        exchange = self.exchanges[order.symbol]
        trades = exchange.process_order(order)
        
        # Record trades and notify agents
        for trade in trades:
            self.trades.append(trade)
            self._notify_agents_of_trade(trade)
        
        return trades
    
    def _notify_agents_of_trade(self, trade: Trade) -> None:
        """Notify all agents of a trade."""
        for agent in self.agents.values():
            agent.on_trade(trade)
    
    def _update_order_books(self) -> None:
        """Update order book snapshots and notify agents."""
        for symbol, exchange in self.exchanges.items():
            bids, asks = exchange.get_order_book_snapshot()
            
            # Record snapshot
            self.metrics['order_book_snapshots'].append({
                'timestamp': self.current_time,
                'symbol': symbol,
                'bids': bids,
                'asks': asks
            })
            
            # Notify agents
            for agent in self.agents.values():
                agent.on_order_book_update(symbol, bids, asks)
    
    def _collect_metrics(self) -> None:
        """Collect various simulation metrics."""
        # Get current prices for portfolio calculations
        current_prices = {}
        for symbol, exchange in self.exchanges.items():
            bids, asks = exchange.get_order_book_snapshot()
            if bids and asks:  # Use mid price if available
                current_prices[symbol] = (Decimal(str(bids[0][0])) + Decimal(str(asks[0][0]))) / 2
        
        # Collect agent metrics
        for agent in self.agents.values():
            portfolio_summary = agent.get_portfolio_summary(current_prices)
            self.metrics['agent_metrics'].append({
                'timestamp': self.current_time,
                **portfolio_summary
            })
        
        # Collect market metrics
        for symbol, exchange in self.exchanges.items():
            bids, asks = exchange.get_order_book_snapshot()
            if bids and asks:
                spread = Decimal(str(asks[0][0])) - Decimal(str(bids[0][0]))
                spread_pct = spread / Decimal(str(bids[0][0])) * 100
                
                self.metrics['market_metrics'].append({
                    'timestamp': self.current_time,
                    'symbol': symbol,
                    'bid': bids[0][0],
                    'ask': asks[0][0],
                    'spread': float(spread),
                    'spread_pct': float(spread_pct),
                    'bid_volume': sum(qty for _, qty in bids),
                    'ask_volume': sum(qty for _, qty in asks)
                })
    
    def run(self) -> Dict[str, Any]:
        """Run the simulation."""
        self.logger.info(f"Starting simulation from {self.start_time} to {self.end_time}")
        
        while self.current_time <= self.end_time:
            # Process scheduled events
            while self.event_queue and self.event_queue[0].timestamp <= self.current_time:
                event = heapq.heappop(self.event_queue)
                self._process_event(event)
            
            # Update agents
            for agent in self.agents.values():
                agent.on_time_update(self.current_time)
            
            # Update order books and collect metrics
            self._update_order_books()
            self._collect_metrics()
            
            # Advance time
            self.current_time += self.time_step
        
        self.logger.info("Simulation completed")
        return self._get_simulation_results()
    
    def _process_event(self, event: SimulationEvent) -> None:
        """Process a simulation event."""
        if event.event_type == 'order':
            self.process_order(event.data)
        elif event.event_type == 'market_event':
            self._handle_market_event(event.data)
        # Add more event types as needed
    
    def _handle_market_event(self, event_data: Dict) -> None:
        """Handle various market events."""
        event_type = event_data.get('type')
        if event_type == 'price_shock':
            self._handle_price_shock(event_data)
        elif event_type == 'volatility_change':
            self._handle_volatility_change(event_data)
        # Add more market event handlers as needed
    
    def _handle_price_shock(self, event_data: Dict) -> None:
        """Handle a price shock event."""
        symbol = event_data['symbol']
        magnitude = event_data['magnitude']
        self.logger.info(f"Price shock of {magnitude}% for {symbol}")
        # Implement price shock logic
    
    def _handle_volatility_change(self, event_data: Dict) -> None:
        """Handle a volatility change event."""
        symbol = event_data['symbol']
        new_volatility = event_data['new_volatility']
        self.logger.info(f"Volatility change to {new_volatility} for {symbol}")
        # Implement volatility change logic
    
    def _get_simulation_results(self) -> Dict[str, Any]:
        """Compile and return simulation results."""
        return {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'trades': self.trades,
            'metrics': self.metrics,
            'final_state': {
                'agents': {
                    agent_id: agent.get_portfolio_summary({})
                    for agent_id, agent in self.agents.items()
                }
            }
        } 
