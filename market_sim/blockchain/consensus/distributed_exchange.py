"""
Distributed Exchange with Byzantine Fault Tolerant Consensus

Integrates the Streamlet consensus protocol with the market simulation to create
a distributed exchange where:

1. Orders are submitted to multiple exchange nodes
2. Trades must be validated through consensus before settlement
3. Byzantine nodes may attempt to manipulate the trading process
4. The system maintains consistency across all honest nodes

This demonstrates how distributed consensus can be applied to financial markets
to prevent manipulation and ensure fair trading.
"""

import logging
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Set, Any, Tuple
from uuid import UUID

from .streamlet import StreamletConsensus, ConsensusNode
from .models import Transaction, Block
from core.models.base import Order, Trade, OrderSide, OrderStatus, OrderType
from market.exchange.matching_engine import MatchingEngine
from market.agents.base_agent import BaseAgent
from core.utils.time_utils import utc_now


class DistributedExchangeNode(ConsensusNode):
    """
    Exchange node that participates in both trading and consensus.
    Extends ConsensusNode with trading functionality.
    """
    
    def __init__(self, node_id: str, symbol: str, is_byzantine: bool = False):
        super().__init__(node_id, is_byzantine)
        self.symbol = symbol
        self.matching_engine = MatchingEngine(symbol)
        self.pending_orders: List[Order] = []
        self.confirmed_trades: List[Trade] = []
        
        # Byzantine trading behavior
        self.byzantine_trading_strategy = "honest"  # "honest", "front_run", "fake_orders"
        
    def submit_order(self, order: Order) -> bool:
        """Submit an order to be processed through consensus."""
        if self.is_byzantine and self.byzantine_trading_strategy == "fake_orders":
            # Byzantine node creates fake orders
            fake_order = Order.create_limit_order(
                order.symbol, 
                order.side, 
                order.quantity * 10,  # Larger fake order
                order.price * Decimal('0.9') if order.side == OrderSide.BUY else order.price * Decimal('1.1'),
                f"fake_{self.node_id}"
            )
            self.pending_orders.append(fake_order)
            self.logger.info(f"Byzantine node {self.node_id} creating fake order")
            return False
        
        self.pending_orders.append(order)
        
        # Create transaction for consensus
        tx = Transaction.from_order(order)
        return True
    
    def process_consensus_block(self, block: Block) -> List[Trade]:
        """Process a finalized block and execute trades."""
        trades = []
        
        for transaction in block.transactions:
            if transaction.transaction_type == "order":
                # Reconstruct order from transaction
                order_data = transaction.data
                order = self._reconstruct_order(order_data)
                
                if order:
                    # Process order through matching engine
                    new_trades = self.matching_engine.process_order(order)
                    trades.extend(new_trades)
                    
                    # Record trades in blockchain
                    for trade in new_trades:
                        trade_tx = Transaction.from_trade(trade)
                        # In a real system, this would go through another consensus round
        
        self.confirmed_trades.extend(trades)
        return trades
    
    def _reconstruct_order(self, order_data: Dict[str, Any]) -> Optional[Order]:
        """Reconstruct an order from transaction data."""
        try:
            order = Order(
                id=UUID(order_data["order_id"]),
                symbol=order_data["symbol"],
                side=OrderSide(order_data["side"]),
                type=OrderType(order_data["type"]),
                quantity=Decimal(order_data["quantity"]),
                price=Decimal(order_data["price"]) if order_data["price"] else None,
                stop_price=None,
                status=OrderStatus.PENDING,
                filled_quantity=Decimal('0'),
                remaining_quantity=Decimal(order_data["quantity"]),
                created_at=utc_now(),
                updated_at=utc_now(),
                agent_id=order_data["agent_id"]
            )
            return order
        except Exception as e:
            self.logger.error(f"Failed to reconstruct order: {e}")
            return None
    
    def get_order_book_state(self) -> Tuple[List[Tuple[Decimal, Decimal]], List[Tuple[Decimal, Decimal]]]:
        """Get current order book state."""
        return self.matching_engine.get_order_book_snapshot()
    
    def simulate_byzantine_trading(self) -> None:
        """Simulate Byzantine behavior in trading."""
        if not self.is_byzantine:
            return
            
        strategies = ["honest", "front_run", "fake_orders"]
        if random.random() < 0.2:  # 20% chance to change strategy
            self.byzantine_trading_strategy = random.choice(strategies)
            self.logger.info(f"Byzantine node {self.node_id} switching to {self.byzantine_trading_strategy} trading")


class DistributedExchange:
    """
    A distributed exchange system using Streamlet consensus.
    
    Demonstrates Byzantine fault tolerance in financial markets by:
    1. Requiring consensus for order processing
    2. Preventing manipulation by Byzantine nodes
    3. Ensuring all honest nodes have consistent order books
    """
    
    def __init__(self, symbol: str, consensus_params: Optional[Dict] = None):
        self.symbol = symbol
        self.consensus = StreamletConsensus()
        self.exchange_nodes: Dict[str, DistributedExchangeNode] = {}
        
        # Trading metrics
        self.trading_metrics = {
            "orders_submitted": 0,
            "orders_processed": 0,
            "trades_executed": 0,
            "byzantine_attacks_detected": 0,
            "consensus_failures": 0
        }
        
        self.logger = logging.getLogger(f"DistributedExchange-{symbol}")
        self.logger.setLevel(logging.INFO)
    
    def add_exchange_node(self, node_id: str, is_byzantine: bool = False) -> None:
        """Add an exchange node to the distributed system."""
        node = DistributedExchangeNode(node_id, self.symbol, is_byzantine)
        self.exchange_nodes[node_id] = node
        self.consensus.add_node(node_id, is_byzantine)
        
        self.logger.info(f"Added {'Byzantine' if is_byzantine else 'honest'} exchange node {node_id}")
    
    def submit_order_to_network(self, order: Order) -> bool:
        """Submit an order to all exchange nodes."""
        success_count = 0
        
        for node in self.exchange_nodes.values():
            if node.submit_order(order):
                success_count += 1
        
        # Create consensus transaction
        order_tx = Transaction.from_order(order)
        self.consensus.add_transaction(order_tx)
        
        self.trading_metrics["orders_submitted"] += 1
        
        # Consider successful if majority of honest nodes accepted
        honest_nodes = len([n for n in self.exchange_nodes.values() if not n.is_byzantine])
        return success_count >= (honest_nodes + 1) // 2
    
    def run_consensus_round(self) -> Optional[Block]:
        """Run a single consensus round for order processing."""
        # Simulate Byzantine trading behavior
        for node in self.exchange_nodes.values():
            if hasattr(node, 'simulate_byzantine_trading'):
                node.simulate_byzantine_trading()
        
        # Run consensus epoch
        block = self.consensus.run_epoch()
        
        if block and block.finalized:
            # Process finalized block on all honest nodes
            all_trades = []
            for node in self.exchange_nodes.values():
                if not node.is_byzantine:
                    trades = node.process_consensus_block(block)
                    all_trades.extend(trades)
            
            self.trading_metrics["orders_processed"] += len(block.transactions)
            self.trading_metrics["trades_executed"] += len(all_trades)
            
            return block
        else:
            self.trading_metrics["consensus_failures"] += 1
            
        return None
    
    def get_consistent_order_book(self) -> Tuple[List[Tuple[Decimal, Decimal]], List[Tuple[Decimal, Decimal]]]:
        """Get order book from first honest node (should be consistent across all honest nodes)."""
        for node in self.exchange_nodes.values():
            if not node.is_byzantine:
                return node.get_order_book_state()
        return [], []
    
    def detect_byzantine_behavior(self) -> List[str]:
        """Detect potential Byzantine behavior by comparing node states."""
        byzantine_suspects = []
        
        if len(self.exchange_nodes) < 2:
            return byzantine_suspects
        
        # Get order book states from all nodes
        order_book_states = {}
        for node_id, node in self.exchange_nodes.items():
            order_book_states[node_id] = node.get_order_book_state()
        
        # Find nodes with significantly different states
        honest_nodes = [node_id for node_id, node in self.exchange_nodes.items() if not node.is_byzantine]
        if honest_nodes:
            reference_state = order_book_states[honest_nodes[0]]
            
            for node_id, state in order_book_states.items():
                if state != reference_state:
                    byzantine_suspects.append(node_id)
                    self.trading_metrics["byzantine_attacks_detected"] += 1
        
        return byzantine_suspects
    
    def get_exchange_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the distributed exchange."""
        consensus_status = self.consensus.get_consensus_status()
        
        # Get order book consistency
        bids, asks = self.get_consistent_order_book()
        
        return {
            "symbol": self.symbol,
            "consensus_status": consensus_status,
            "trading_metrics": self.trading_metrics,
            "order_book": {
                "bids": [(float(price), float(qty)) for price, qty in bids[:5]],
                "asks": [(float(price), float(qty)) for price, qty in asks[:5]]
            },
            "nodes": {
                node_id: {
                    "is_byzantine": node.is_byzantine,
                    "pending_orders": len(node.pending_orders),
                    "confirmed_trades": len(node.confirmed_trades)
                }
                for node_id, node in self.exchange_nodes.items()
            },
            "byzantine_suspects": self.detect_byzantine_behavior()
        }
    
    def run_trading_simulation(self, orders: List[Order], num_rounds: int = 10) -> Dict[str, Any]:
        """Run a complete trading simulation with consensus."""
        self.logger.info(f"Starting distributed trading simulation with {len(orders)} orders")
        
        results = {
            "rounds": [],
            "blocks": [],
            "trades": [],
            "final_status": None
        }
        
        # Submit all orders to the network
        for order in orders:
            self.submit_order_to_network(order)
        
        # Run consensus rounds
        for round_num in range(num_rounds):
            self.logger.info(f"=== Trading Round {round_num + 1} ===")
            
            block = self.run_consensus_round()
            
            round_result = {
                "round": round_num + 1,
                "block_finalized": block is not None,
                "orders_processed": len(block.transactions) if block else 0,
                "byzantine_suspects": self.detect_byzantine_behavior()
            }
            results["rounds"].append(round_result)
            
            if block:
                results["blocks"].append(block.to_dict())
                
                # Collect trades from honest nodes
                for node in self.exchange_nodes.values():
                    if not node.is_byzantine:
                        results["trades"].extend([
                            {
                                "id": str(trade.id),
                                "symbol": trade.symbol,
                                "price": float(trade.price),
                                "quantity": float(trade.quantity),
                                "timestamp": trade.timestamp.isoformat()
                            }
                            for trade in node.confirmed_trades[-10:]  # Last 10 trades
                        ])
                        break
        
        results["final_status"] = self.get_exchange_status()
        
        self.logger.info(f"Trading simulation completed: {self.trading_metrics['trades_executed']} trades executed")
        return results 