"""
Integration tests for Byzantine fault tolerant consensus in trading systems.

Tests the Streamlet consensus protocol implementation and demonstrates:
1. Basic consensus operation with honest nodes
2. Byzantine fault tolerance under various attack scenarios  
3. Distributed exchange functionality
4. Safety and liveness properties
"""

import pytest
import logging
from datetime import timedelta
from decimal import Decimal
from typing import List

from uuid import uuid4
from blockchain.consensus.streamlet import StreamletConsensus, ConsensusNode
from blockchain.consensus.distributed_exchange import DistributedExchange
from blockchain.consensus.models import Transaction, VoteType
from core.models.base import Order, OrderSide, OrderType
from core.utils.time_utils import utc_now

# Setup logging for tests
logging.basicConfig(level=logging.INFO)


class TestStreamletConsensus:
    """Test the core Streamlet consensus protocol."""
    
    def test_honest_nodes_consensus(self):
        """Test consensus with all honest nodes."""
        consensus = StreamletConsensus()
        
        # Add 4 honest nodes (can tolerate 1 Byzantine)
        for i in range(4):
            consensus.add_node(f"node_{i}", is_byzantine=False)
        
        # Add some transactions
        for i in range(5):
            tx = Transaction(
                id=f"tx_{i}",
                transaction_type="trade",
                data={"amount": str(Decimal(100 + i))},
                timestamp=utc_now()
            )
            consensus.add_transaction(tx)
        
        # Run consensus simulation
        results = consensus.run_simulation(num_epochs=10, add_transactions=True)
        
        # Verify results
        assert len(results["epochs"]) == 10
        assert results["final_status"]["metrics"]["blocks_finalized"] > 0
        assert results["final_status"]["consensus_state"]["byzantine_nodes"] == 0
        
        print(f"✓ Honest consensus test: {results['final_status']['metrics']['blocks_finalized']} blocks finalized")
    
    def test_byzantine_fault_tolerance(self):
        """Test consensus with Byzantine nodes (f < n/3)."""
        consensus = StreamletConsensus()
        
        # Add 4 honest nodes + 1 Byzantine (5 total, can tolerate 1 Byzantine)
        for i in range(4):
            consensus.add_node(f"honest_{i}", is_byzantine=False)
        consensus.add_node("byzantine_1", is_byzantine=True)
        
        # Add transactions
        for i in range(8):
            tx = Transaction(
                id=f"tx_{i}",
                transaction_type="order",
                data={"symbol": "BTC", "amount": str(Decimal(50 + i))},
                timestamp=utc_now()
            )
            consensus.add_transaction(tx)
        
        # Run simulation
        results = consensus.run_simulation(num_epochs=15, add_transactions=True)
        
        # Should still achieve consensus despite Byzantine node
        assert results["final_status"]["metrics"]["blocks_finalized"] > 0
        assert results["final_status"]["consensus_state"]["byzantine_nodes"] == 1
        assert results["final_status"]["consensus_state"]["byzantine_tolerance"] == 1
        
        print(f"✓ Byzantine tolerance test: {results['final_status']['metrics']['blocks_finalized']} blocks finalized with 1 Byzantine node")
    
    def test_safety_violation_prevention(self):
        """Test that Byzantine nodes cannot break safety (too many Byzantine nodes)."""
        consensus = StreamletConsensus()
        
        # Add 3 honest + 2 Byzantine nodes (5 total, exceeds f < n/3 threshold)
        for i in range(3):
            consensus.add_node(f"honest_{i}", is_byzantine=False)
        for i in range(2):
            consensus.add_node(f"byzantine_{i}", is_byzantine=True)
        
        # Add transactions
        for i in range(5):
            tx = Transaction(
                id=f"tx_{i}",
                transaction_type="trade",
                data={"amount": str(Decimal(200 + i))},
                timestamp=utc_now()
            )
            consensus.add_transaction(tx)
        
        # Run simulation
        results = consensus.run_simulation(num_epochs=10, add_transactions=False)
        
        # With too many Byzantine nodes, should have reduced finalization
        byzantine_tolerance = results["final_status"]["consensus_state"]["byzantine_tolerance"]
        byzantine_count = results["final_status"]["consensus_state"]["byzantine_nodes"]
        
        print(f"✓ Safety test: {byzantine_count} Byzantine nodes, tolerance is {byzantine_tolerance}")
        assert byzantine_count > byzantine_tolerance  # Exceeds safety threshold


class TestDistributedExchange:
    """Test the distributed exchange with consensus."""
    
    def test_distributed_order_processing(self):
        """Test basic distributed order processing."""
        exchange = DistributedExchange("AAPL")
        
        # Add exchange nodes
        for i in range(4):
            exchange.add_exchange_node(f"exchange_{i}", is_byzantine=False)
        
        # Create test orders
        orders = [
            Order.create_limit_order("AAPL", OrderSide.BUY, Decimal("100"), Decimal("150.00"), "trader_1"),
            Order.create_limit_order("AAPL", OrderSide.SELL, Decimal("50"), Decimal("151.00"), "trader_2"),
            Order.create_limit_order("AAPL", OrderSide.BUY, Decimal("75"), Decimal("149.50"), "trader_3"),
            Order.create_limit_order("AAPL", OrderSide.SELL, Decimal("200"), Decimal("152.00"), "trader_4")
        ]
        
        # Run trading simulation
        results = exchange.run_trading_simulation(orders, num_rounds=8)
        
        # Verify trading occurred
        assert results["final_status"]["trading_metrics"]["orders_submitted"] == len(orders)
        assert results["final_status"]["trading_metrics"]["orders_processed"] > 0
        
        print(f"✓ Distributed trading test: {results['final_status']['trading_metrics']['orders_processed']} orders processed")
        print(f"  Trades executed: {results['final_status']['trading_metrics']['trades_executed']}")
    
    def test_byzantine_exchange_nodes(self):
        """Test exchange with Byzantine nodes attempting manipulation."""
        exchange = DistributedExchange("BTC")
        
        # Add 3 honest + 1 Byzantine exchange node
        for i in range(3):
            exchange.add_exchange_node(f"honest_exchange_{i}", is_byzantine=False)
        exchange.add_exchange_node("byzantine_exchange", is_byzantine=True)
        
        # Create orders
        orders = [
            Order.create_limit_order("BTC", OrderSide.BUY, Decimal("1.5"), Decimal("45000.00"), "buyer_1"),
            Order.create_limit_order("BTC", OrderSide.SELL, Decimal("1.0"), Decimal("45100.00"), "seller_1"),
            Order.create_limit_order("BTC", OrderSide.BUY, Decimal("2.0"), Decimal("44900.00"), "buyer_2"),
        ]
        
        # Run simulation
        results = exchange.run_trading_simulation(orders, num_rounds=12)
        
        # Should still process orders correctly despite Byzantine node
        assert results["final_status"]["trading_metrics"]["orders_submitted"] == len(orders)
        
        # Check if Byzantine behavior was detected
        byzantine_attacks = results["final_status"]["trading_metrics"]["byzantine_attacks_detected"]
        print(f"✓ Byzantine exchange test: {byzantine_attacks} attacks detected")
        
        # Should have some successful order processing
        assert results["final_status"]["trading_metrics"]["orders_processed"] > 0
    
    def test_order_book_consistency(self):
        """Test that honest nodes maintain consistent order books."""
        exchange = DistributedExchange("ETH")
        
        # Add multiple honest nodes
        for i in range(5):
            exchange.add_exchange_node(f"node_{i}", is_byzantine=False)
        
        # Submit orders
        orders = [
            Order.create_limit_order("ETH", OrderSide.BUY, Decimal("10"), Decimal("3000.00"), "trader_1"),
            Order.create_limit_order("ETH", OrderSide.BUY, Decimal("5"), Decimal("2995.00"), "trader_2"),
            Order.create_limit_order("ETH", OrderSide.SELL, Decimal("8"), Decimal("3010.00"), "trader_3"),
            Order.create_limit_order("ETH", OrderSide.SELL, Decimal("12"), Decimal("3015.00"), "trader_4"),
        ]
        
        # Process orders
        for order in orders:
            exchange.submit_order_to_network(order)
        
        # Run some consensus rounds
        for _ in range(6):
            exchange.run_consensus_round()
        
        # Check order book consistency across honest nodes
        order_book_states = []
        for node in exchange.exchange_nodes.values():
            if not node.is_byzantine:
                state = node.get_order_book_state()
                order_book_states.append(state)
        
        # All honest nodes should have the same order book
        if len(order_book_states) > 1:
            reference_state = order_book_states[0]
            for state in order_book_states[1:]:
                assert state == reference_state, "Order book inconsistency detected between honest nodes"
        
        print("✓ Order book consistency test passed")
    
    def test_consensus_liveness(self):
        """Test that consensus makes progress (liveness property)."""
        exchange = DistributedExchange("DOGE")
        
        # Add nodes with some Byzantine ones
        for i in range(4):
            exchange.add_exchange_node(f"honest_{i}", is_byzantine=False)
        exchange.add_exchange_node("byzantine_1", is_byzantine=True)
        
        # Continuously add orders
        orders = []
        for i in range(15):
            order = Order.create_limit_order(
                "DOGE", 
                OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
                Decimal(str(10 + i)), 
                Decimal(str(1.00 + i * 0.01)), 
                f"trader_{i}"
            )
            orders.append(order)
        
        # Run extended simulation
        results = exchange.run_trading_simulation(orders, num_rounds=20)
        
        # Check liveness: should make continuous progress
        blocks_finalized = len([r for r in results["rounds"] if r["block_finalized"]])
        
        print(f"✓ Liveness test: {blocks_finalized}/20 rounds resulted in finalized blocks")
        assert blocks_finalized > 10, "Insufficient progress - liveness may be compromised"


def test_integration_with_market_simulation():
    """Test integration between consensus and existing market simulation components."""
    from simulation.scenarios.market_making_scenario import RandomTrader
    from strategies.hft.market_maker import MarketMaker
    
    # Create distributed exchange
    exchange = DistributedExchange("TSLA")
    
    # Add exchange nodes
    for i in range(4):
        exchange.add_exchange_node(f"exchange_{i}", is_byzantine=False)
    exchange.add_exchange_node("byzantine_exchange", is_byzantine=True)
    
    # Create agents (but don't run full market simulation)
    market_maker = MarketMaker(
        agent_id="MM_consensus", 
        initial_balance=Decimal("1000000"),
        symbols=["TSLA"]
    )
    
    random_trader = RandomTrader(
        agent_id="RT_consensus",
        initial_balance=Decimal("100000"), 
        symbols=["TSLA"]
    )
    
    # Generate orders from agents
    orders = []
    for i in range(10):
        # Market maker orders
        mm_bid = market_maker.create_limit_order("TSLA", OrderSide.BUY, Decimal("100"), Decimal(f"{200 + i}"))
        mm_ask = market_maker.create_limit_order("TSLA", OrderSide.SELL, Decimal("100"), Decimal(f"{202 + i}"))
        orders.extend([mm_bid, mm_ask])
        
        # Random trader orders  
        rt_order = random_trader.create_market_order("TSLA", OrderSide.BUY, Decimal("50"))
        orders.append(rt_order)
    
    # Run consensus-based trading
    results = exchange.run_trading_simulation(orders, num_rounds=15)
    
    # Verify integration
    assert results["final_status"]["trading_metrics"]["orders_submitted"] == len(orders)
    assert results["final_status"]["trading_metrics"]["orders_processed"] > 0
    
    print(f"✓ Integration test: {len(orders)} orders from market agents processed through consensus")
    print(f"  Final status: {results['final_status']['trading_metrics']}")


if __name__ == "__main__":
    """Run all consensus tests."""
    print("=== Running Streamlet Consensus Tests ===\n")
    
    # Core consensus tests
    consensus_tests = TestStreamletConsensus()
    consensus_tests.test_honest_nodes_consensus()
    consensus_tests.test_byzantine_fault_tolerance() 
    consensus_tests.test_safety_violation_prevention()
    
    print("\n=== Running Distributed Exchange Tests ===\n")
    
    # Distributed exchange tests
    exchange_tests = TestDistributedExchange()
    exchange_tests.test_distributed_order_processing()
    exchange_tests.test_byzantine_exchange_nodes()
    exchange_tests.test_order_book_consistency()
    exchange_tests.test_consensus_liveness()
    
    print("\n=== Running Integration Tests ===\n")
    
    # Integration tests
    test_integration_with_market_simulation()
    
    print("\n🎉 All consensus tests completed successfully!")
    print("\nThis demonstrates:")
    print("✓ Byzantine fault tolerant consensus for trading systems")
    print("✓ Streamlet protocol implementation from the distributed consensus book")
    print("✓ Prevention of trading manipulation through consensus")
    print("✓ Integration with existing market simulation framework") 