"""
Blockchain-integrated trading example.

Demonstrates how to record trades on different blockchain consensus mechanisms.
"""

import time
from datetime import datetime
from decimal import Decimal
from typing import List
import matplotlib.pyplot as plt

from market_sim.core.models.base import Order, Trade, OrderType, OrderSide
from market_sim.market.exchange.matching_engine import MatchingEngine
from market_sim.market.agents.base_agent import BaseAgent
from market_sim.blockchain.market_ledger import MarketTransactionLedger, TradeStatus


class BlockchainTrader(BaseAgent):
    """Trader that records trades on blockchain."""
    
    def __init__(self, agent_id: str, initial_cash: float, ledger: MarketTransactionLedger):
        super().__init__(agent_id, Decimal(str(initial_cash)))
        self.ledger = ledger
    
    def on_order_book_update(self, symbol: str, bids: List[tuple], asks: List[tuple]) -> None:
        """Handle order book updates."""
        pass
    
    def on_trade(self, trade) -> None:
        """Handle trade notifications."""
        pass
    
    def on_time_update(self, timestamp: datetime) -> None:
        """Handle time updates."""
        pass


def run_blockchain_market(consensus: str = "pow", num_trades: int = 50):
    """Run a market simulation with blockchain integration."""
    print(f"=== Blockchain Trading Example ({consensus.upper()}) ===")
    
    # Create market ledger with specified consensus
    consensus_params = {
        "pow": {"difficulty": 3},  # Lower difficulty for faster demo
        "raft": {"num_nodes": 5},
        "streamlet": {}
    }
    
    ledger = MarketTransactionLedger(
        consensus_type=consensus,
        consensus_params=consensus_params.get(consensus, {})
    )
    
    # Create matching engine
    engine = MatchingEngine("STOCK")
    
    # Create traders
    traders = []
    for i in range(5):
        trader = BlockchainTrader(f"blockchain_trader_{i}", 10000.0, ledger)
        traders.append(trader)
        
    # Simulate trading
    print("\nSimulating trades...")
    recorded_trades = []
    consensus_times = []
    
    for i in range(num_trades):
        # Create random buy and sell orders
        buy_trader = traders[i % len(traders)]
        sell_trader = traders[(i + 1) % len(traders)]
        
        price = 100 + (i % 10) - 5  # Price oscillates around 100
        quantity = 10 + (i % 5) * 10
        
        # Create orders
        buy_order = Order.create_limit_order(
            symbol="STOCK",
            side=OrderSide.BUY,
            quantity=Decimal(str(quantity)),
            price=Decimal(str(price)),
            agent_id=buy_trader.agent_id
        )
        
        sell_order = Order.create_limit_order(
            symbol="STOCK",
            side=OrderSide.SELL,
            quantity=Decimal(str(quantity)),
            price=Decimal(str(price)),
            agent_id=sell_trader.agent_id
        )
        
        # Add orders to engine
        engine.add_order(buy_order)
        trades = engine.add_order(sell_order)
        
        # Record trades on blockchain
        for trade in trades:
            trade_id = ledger.record_trade(trade)
            recorded_trades.append((trade_id, trade))
            print(f"Trade {i}: {trade.quantity} @ ${trade.price} - Recorded as {trade_id}")
            
        # Run consensus every 5 trades or at the end
        if (i + 1) % 5 == 0 or i == num_trades - 1:
            start_time = time.time()
            
            if consensus == "pow":
                # Mine a block
                block_info = ledger.mine_block()
                if block_info:
                    print(f"\nMined block {block_info['block_index']} with {block_info['trades_confirmed']} trades")
                    print(f"Block hash: {block_info['block_hash'][:16]}...")
            else:
                # Run consensus round
                result = ledger.run_consensus_round()
                print(f"\nConsensus round completed: {result}")
                
            consensus_time = time.time() - start_time
            consensus_times.append(consensus_time)
            
    # Check trade statuses
    print("\n=== Trade Status Summary ===")
    confirmed_count = 0
    pending_count = 0
    
    for trade_id, trade in recorded_trades:
        status = ledger.get_trade_status(trade_id)
        if status == TradeStatus.CONFIRMED:
            confirmed_count += 1
        elif status == TradeStatus.PENDING:
            pending_count += 1
            
    print(f"Total trades: {len(recorded_trades)}")
    print(f"Confirmed: {confirmed_count}")
    print(f"Pending: {pending_count}")
    
    # Get ledger statistics
    stats = ledger.get_ledger_stats()
    print(f"\n=== Ledger Statistics ===")
    for key, value in stats.items():
        print(f"{key}: {value}")
        
    # Verify ledger integrity
    if consensus == "pow":
        is_valid = ledger.verify_ledger_integrity()
        print(f"\nBlockchain integrity check: {'PASSED' if is_valid else 'FAILED'}")
        
    # Plot consensus times
    if consensus_times:
        plt.figure(figsize=(10, 6))
        plt.bar(range(len(consensus_times)), consensus_times, color='blue', alpha=0.7)
        plt.xlabel('Consensus Round')
        plt.ylabel('Time (seconds)')
        plt.title(f'{consensus.upper()} Consensus Performance')
        plt.grid(True, alpha=0.3)
        
        avg_time = sum(consensus_times) / len(consensus_times)
        plt.axhline(y=avg_time, color='red', linestyle='--', 
                   label=f'Average: {avg_time:.3f}s')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(f'blockchain_{consensus}_performance.png', dpi=150, bbox_inches='tight')
        print(f"\nPerformance chart saved as 'blockchain_{consensus}_performance.png'")
        
    return {
        'ledger': ledger,
        'trades': recorded_trades,
        'confirmed': confirmed_count,
        'consensus_times': consensus_times
    }


def compare_blockchain_consensus():
    """Compare different consensus mechanisms."""
    print("=== Comparing Blockchain Consensus Mechanisms ===\n")
    
    results = {}
    consensus_types = ["pow", "raft", "streamlet"]
    
    for consensus in consensus_types:
        print(f"\nTesting {consensus.upper()}...")
        start_time = time.time()
        
        result = run_blockchain_market(consensus=consensus, num_trades=30)
        
        total_time = time.time() - start_time
        results[consensus] = {
            'total_time': total_time,
            'confirmed_trades': result['confirmed'],
            'avg_consensus_time': sum(result['consensus_times']) / len(result['consensus_times']) if result['consensus_times'] else 0
        }
        
    # Print comparison
    print("\n=== Consensus Comparison Results ===")
    print(f"{'Consensus':<12} {'Total Time':<12} {'Confirmed':<12} {'Avg Consensus':<15}")
    print("-" * 50)
    
    for consensus, metrics in results.items():
        print(f"{consensus.upper():<12} {metrics['total_time']:<12.2f} "
              f"{metrics['confirmed_trades']:<12} {metrics['avg_consensus_time']:<15.3f}")
        
    return results


if __name__ == "__main__":
    # Run individual consensus examples
    for consensus_type in ["pow", "raft", "streamlet"]:
        print(f"\n{'='*60}")
        run_blockchain_market(consensus=consensus_type, num_trades=20)
        print(f"{'='*60}\n")
        
    # Compare all consensus mechanisms
    print("\n" + "="*60)
    comparison = compare_blockchain_consensus()
    print("="*60) 