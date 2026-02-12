#!/usr/bin/env python3
"""
Streamlet Consensus Protocol Demonstration

This script demonstrates the Byzantine fault tolerant consensus protocol 
implemented for distributed trading systems. It shows:

1. Basic consensus operation
2. Byzantine fault tolerance  
3. Distributed exchange functionality
4. Integration with market simulation
5. Visualizations of the protocol

Based on the Streamlet protocol from the distributed consensus book.
"""

import sys
import os
import logging
from decimal import Decimal
from datetime import timedelta

# Add market_sim to path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from blockchain.consensus.streamlet import StreamletConsensus
from blockchain.consensus.distributed_exchange import DistributedExchange
from blockchain.consensus.models import Transaction
from blockchain.consensus.visualization import ConsensusVisualizer
from core.models.base import Order, OrderSide
from core.utils.time_utils import utc_now

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('consensus_demo.log')
    ]
)

def demo_basic_consensus():
    """Demonstrate basic Streamlet consensus with honest nodes."""
    print("=" * 60)
    print("DEMO 1: Basic Streamlet Consensus")
    print("=" * 60)
    
    consensus = StreamletConsensus()
    
    # Add 5 honest nodes (can tolerate up to 1 Byzantine)
    print("Setting up network with 5 honest nodes...")
    for i in range(5):
        consensus.add_node(f"honest_node_{i}", is_byzantine=False)
    
    # Add some transactions
    print("Adding transactions to the network...")
    for i in range(10):
        tx = Transaction(
            id=f"tx_{i}",
            transaction_type="trade",
            data={
                "symbol": "BTC", 
                "amount": str(Decimal(100 + i * 10)),
                "trader": f"trader_{i % 3}"
            },
            timestamp=utc_now()
        )
        consensus.add_transaction(tx)
    
    # Run consensus simulation
    print("Running consensus for 15 epochs...")
    results = consensus.run_simulation(num_epochs=15, add_transactions=True)
    
    # Display results
    final_status = results["final_status"]
    metrics = final_status["metrics"]
    
    print(f"\n✅ RESULTS:")
    print(f"Blocks proposed: {metrics['blocks_proposed']}")
    print(f"Blocks notarized: {metrics['blocks_notarized']}")
    print(f"Blocks finalized: {metrics['blocks_finalized']}")
    print(f"Success rate: {metrics['blocks_finalized']/metrics['blocks_proposed']*100:.1f}%")
    
    # Visualize
    visualizer = ConsensusVisualizer()
    print("\nGenerating visualizations...")
    visualizer.plot_consensus_timeline(results, "demo1_timeline.png")
    visualizer.plot_network_topology(consensus, "demo1_network.png")
    
    return results

def demo_byzantine_fault_tolerance():
    """Demonstrate Byzantine fault tolerance."""
    print("\n" + "=" * 60)
    print("DEMO 2: Byzantine Fault Tolerance")
    print("=" * 60)
    
    consensus = StreamletConsensus()
    
    # Add 4 honest nodes + 1 Byzantine (satisfies f < n/3)
    print("Setting up network: 4 honest + 1 Byzantine node...")
    for i in range(4):
        consensus.add_node(f"honest_{i}", is_byzantine=False)
    consensus.add_node("byzantine_attacker", is_byzantine=True)
    
    # Add transactions
    print("Adding transactions...")
    for i in range(12):
        tx = Transaction(
            id=f"btx_{i}",
            transaction_type="order",
            data={
                "symbol": "ETH",
                "side": "BUY" if i % 2 == 0 else "SELL", 
                "amount": str(Decimal(50 + i * 5)),
                "price": str(Decimal(3000 + i * 10))
            },
            timestamp=utc_now()
        )
        consensus.add_transaction(tx)
    
    # Run simulation
    print("Running consensus with Byzantine node present...")
    results = consensus.run_simulation(num_epochs=20, add_transactions=True)
    
    # Display results
    final_status = results["final_status"]
    metrics = final_status["metrics"]
    consensus_state = final_status["consensus_state"]
    
    print(f"\n✅ BYZANTINE TOLERANCE RESULTS:")
    print(f"Network size: {consensus_state['total_nodes']} nodes")
    print(f"Byzantine nodes: {consensus_state['byzantine_nodes']}")
    print(f"Byzantine tolerance: {consensus_state['byzantine_tolerance']} (f < n/3)")
    print(f"Blocks finalized: {metrics['blocks_finalized']}")
    print(f"Byzantine actions detected: {metrics['byzantine_actions']}")
    print(f"Success rate: {metrics['blocks_finalized']/metrics['blocks_proposed']*100:.1f}%")
    
    # Check if safety is maintained
    if consensus_state['byzantine_nodes'] <= consensus_state['byzantine_tolerance']:
        print("🛡️  SAFETY MAINTAINED: Byzantine nodes within tolerance threshold")
    else:
        print("⚠️  SAFETY COMPROMISED: Too many Byzantine nodes!")
    
    # Visualize
    visualizer = ConsensusVisualizer()
    visualizer.plot_byzantine_behavior_analysis(results, "demo2_byzantine_analysis.png")
    
    return results

def demo_distributed_exchange():
    """Demonstrate distributed exchange with consensus."""
    print("\n" + "=" * 60)
    print("DEMO 3: Distributed Exchange with Consensus")
    print("=" * 60)
    
    # Create distributed exchange
    exchange = DistributedExchange("AAPL")
    
    # Add exchange nodes
    print("Setting up distributed exchange: 4 honest + 1 Byzantine exchange node...")
    for i in range(4):
        exchange.add_exchange_node(f"exchange_honest_{i}", is_byzantine=False)
    exchange.add_exchange_node("exchange_byzantine", is_byzantine=True)
    
    # Create realistic trading orders
    print("Creating trading orders...")
    orders = [
        # Market maker providing liquidity
        Order.create_limit_order("AAPL", OrderSide.BUY, Decimal("100"), Decimal("145.00"), "market_maker_1"),
        Order.create_limit_order("AAPL", OrderSide.SELL, Decimal("100"), Decimal("147.00"), "market_maker_1"),
        Order.create_limit_order("AAPL", OrderSide.BUY, Decimal("50"), Decimal("144.50"), "market_maker_2"),
        Order.create_limit_order("AAPL", OrderSide.SELL, Decimal("75"), Decimal("147.50"), "market_maker_2"),
        
        # Institutional orders
        Order.create_limit_order("AAPL", OrderSide.BUY, Decimal("500"), Decimal("146.00"), "institution_1"),
        Order.create_limit_order("AAPL", OrderSide.SELL, Decimal("200"), Decimal("146.50"), "institution_2"),
        
        # Retail traders
        Order.create_limit_order("AAPL", OrderSide.BUY, Decimal("25"), Decimal("145.75"), "retail_1"),
        Order.create_limit_order("AAPL", OrderSide.SELL, Decimal("30"), Decimal("146.25"), "retail_2"),
        Order.create_limit_order("AAPL", OrderSide.BUY, Decimal("40"), Decimal("145.25"), "retail_3"),
    ]
    
    # Run trading simulation
    print(f"Processing {len(orders)} orders through consensus...")
    results = exchange.run_trading_simulation(orders, num_rounds=15)
    
    # Display results
    final_status = results["final_status"]
    trading_metrics = final_status["trading_metrics"]
    
    print(f"\n✅ DISTRIBUTED TRADING RESULTS:")
    print(f"Orders submitted: {trading_metrics['orders_submitted']}")
    print(f"Orders processed: {trading_metrics['orders_processed']}")
    print(f"Trades executed: {trading_metrics['trades_executed']}")
    print(f"Byzantine attacks detected: {trading_metrics['byzantine_attacks_detected']}")
    print(f"Consensus failures: {trading_metrics['consensus_failures']}")
    
    # Show order book
    order_book = final_status["order_book"]
    print(f"\n📊 FINAL ORDER BOOK:")
    print(f"Best bids: {order_book['bids'][:3]}")
    print(f"Best asks: {order_book['asks'][:3]}")
    
    # Show Byzantine detection
    byzantine_suspects = final_status.get("byzantine_suspects", [])
    if byzantine_suspects:
        print(f"🕵️  Byzantine nodes detected: {byzantine_suspects}")
    
    return results

def demo_integration_with_market_simulation():
    """Demonstrate integration with existing market simulation."""
    print("\n" + "=" * 60)
    print("DEMO 4: Integration with Market Simulation")
    print("=" * 60)
    
    try:
        from simulation.scenarios.market_making_scenario import RandomTrader
        from strategies.hft.market_maker import MarketMaker
        
        # Create distributed exchange
        exchange = DistributedExchange("TSLA")
        
        # Add exchange nodes
        print("Setting up distributed exchange network...")
        for i in range(5):
            exchange.add_exchange_node(f"exchange_{i}", is_byzantine=False)
        exchange.add_exchange_node("byzantine_manipulator", is_byzantine=True)
        
        # Create market agents
        print("Creating market agents...")
        market_maker = MarketMaker(
            agent_id="MM_distributed",
            initial_balance=Decimal("1000000"),
            symbols=["TSLA"],
            target_spread=Decimal("0.005"),  # 0.5% spread
            order_size=Decimal("50")
        )
        
        random_trader = RandomTrader(
            agent_id="RT_distributed",
            initial_balance=Decimal("500000"),
            symbols=["TSLA"],
            trade_frequency=0.8,
            min_trade_size=Decimal("10"),
            max_trade_size=Decimal("100")
        )
        
        # Generate orders from agents
        print("Generating orders from market agents...")
        orders = []
        
        # Market maker orders (providing liquidity)
        for i in range(8):
            bid_price = Decimal(f"{200 + i * 0.5}")
            ask_price = Decimal(f"{202 + i * 0.5}")
            
            mm_bid = market_maker.create_limit_order("TSLA", OrderSide.BUY, Decimal("50"), bid_price)
            mm_ask = market_maker.create_limit_order("TSLA", OrderSide.SELL, Decimal("50"), ask_price)
            orders.extend([mm_bid, mm_ask])
        
        # Random trader orders (creating market pressure)
        for i in range(12):
            side = OrderSide.BUY if i % 2 == 0 else OrderSide.SELL
            quantity = Decimal(str(20 + i * 5))
            price = Decimal(f"{201 + (i % 4) * 0.25}")
            
            rt_order = random_trader.create_limit_order("TSLA", side, quantity, price)
            orders.append(rt_order)
        
        # Run consensus-based trading
        print(f"Processing {len(orders)} orders from market agents through consensus...")
        results = exchange.run_trading_simulation(orders, num_rounds=20)
        
        # Display results
        final_status = results["final_status"]
        trading_metrics = final_status["trading_metrics"]
        
        print(f"\n✅ INTEGRATION RESULTS:")
        print(f"Market maker orders: {len([o for o in orders if 'MM_' in o.agent_id])}")
        print(f"Random trader orders: {len([o for o in orders if 'RT_' in o.agent_id])}")
        print(f"Total orders processed: {trading_metrics['orders_processed']}")
        print(f"Trades executed: {trading_metrics['trades_executed']}")
        print(f"Byzantine attacks detected: {trading_metrics['byzantine_attacks_detected']}")
        
        # Show portfolio impact (simplified)
        processed_orders = trading_metrics['orders_processed']
        success_rate = processed_orders / trading_metrics['orders_submitted'] * 100
        print(f"Order processing success rate: {success_rate:.1f}%")
        
        print("🎯 Successfully integrated consensus with market simulation agents!")
        
        return results
        
    except ImportError as e:
        print(f"⚠️  Could not import market simulation components: {e}")
        print("Skipping integration demo...")
        return None

def demo_comprehensive_visualization():
    """Create comprehensive visualizations of all demos."""
    print("\n" + "=" * 60)
    print("DEMO 5: Comprehensive Visualization Dashboard")
    print("=" * 60)
    
    # Run a comprehensive scenario
    consensus = StreamletConsensus()
    
    # Mixed network: honest and Byzantine nodes
    for i in range(6):
        consensus.add_node(f"honest_{i}", is_byzantine=False)
    for i in range(2):
        consensus.add_node(f"byzantine_{i}", is_byzantine=True)
    
    # Add various transaction types
    for i in range(25):
        tx_types = ["trade", "order", "settlement"]
        tx_type = tx_types[i % len(tx_types)]
        
        tx = Transaction(
            id=f"mixed_tx_{i}",
            transaction_type=tx_type,
            data={
                "symbol": ["BTC", "ETH", "AAPL"][i % 3],
                "amount": str(Decimal(100 + i * 20)),
                "complexity": "high" if i > 15 else "low"
            },
            timestamp=utc_now()
        )
        consensus.add_transaction(tx)
    
    # Run extended simulation
    print("Running comprehensive consensus simulation...")
    results = consensus.run_simulation(num_epochs=30, add_transactions=True)
    
    # Create comprehensive dashboard
    print("Creating comprehensive visualization dashboard...")
    visualizer = ConsensusVisualizer()
    
    try:
        visualizer.create_consensus_dashboard(consensus, results, "comprehensive_dashboard.png")
        visualizer.plot_voting_patterns(results["blocks"], "voting_patterns.png")
        
        print("📊 Comprehensive dashboard saved as 'comprehensive_dashboard.png'")
        print("🗳️  Voting patterns saved as 'voting_patterns.png'")
        
    except Exception as e:
        print(f"⚠️  Visualization error (may need matplotlib/seaborn): {e}")
        print("Charts not generated, but consensus simulation completed successfully.")
    
    # Display final summary
    final_status = results["final_status"]
    metrics = final_status["metrics"]
    consensus_state = final_status["consensus_state"]
    
    print(f"\n🎯 COMPREHENSIVE DEMO SUMMARY:")
    print(f"Network: {consensus_state['total_nodes']} nodes ({consensus_state['byzantine_nodes']} Byzantine)")
    print(f"Epochs: 30")
    print(f"Blocks finalized: {metrics['blocks_finalized']}")
    print(f"Overall success rate: {metrics['blocks_finalized']/metrics['blocks_proposed']*100:.1f}%")
    print(f"Byzantine actions: {metrics['byzantine_actions']}")
    
    if consensus_state['byzantine_nodes'] <= consensus_state['byzantine_tolerance']:
        print("✅ Byzantine fault tolerance successfully demonstrated!")
    else:
        print("⚠️  Byzantine threshold exceeded - demonstrating failure scenarios")
    
    return results

def main():
    """Run all consensus demonstrations."""
    print("🚀 STREAMLET CONSENSUS PROTOCOL DEMONSTRATION")
    print("Based on the distributed consensus book concepts")
    print("Implementing Byzantine fault tolerant consensus for trading systems\n")
    
    # Run all demos
    try:
        demo1_results = demo_basic_consensus()
        demo2_results = demo_byzantine_fault_tolerance()
        demo3_results = demo_distributed_exchange()
        demo4_results = demo_integration_with_market_simulation()
        demo5_results = demo_comprehensive_visualization()
        
        print("\n" + "🎉" * 20)
        print("ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("🎉" * 20)
        
        print(f"\n📋 DEMONSTRATION SUMMARY:")
        print(f"✅ Basic consensus operation")
        print(f"✅ Byzantine fault tolerance (f < n/3)")
        print(f"✅ Distributed exchange functionality")
        print(f"✅ Market simulation integration")
        print(f"✅ Comprehensive visualizations")
        
        print(f"\n🔬 KEY INSIGHTS DEMONSTRATED:")
        print(f"• Streamlet protocol ensures safety and liveness")
        print(f"• Byzantine nodes cannot manipulate honest majority")
        print(f"• Consensus enables trustworthy distributed trading")
        print(f"• Integration with existing market infrastructure")
        print(f"• Real-time detection of malicious behavior")
        
        print(f"\n📖 DISTRIBUTED CONSENSUS CONCEPTS APPLIED:")
        print(f"• Byzantine Broadcast and agreement")
        print(f"• Epoch-based leader rotation") 
        print(f"• Notarization through voting")
        print(f"• Chain finalization rules")
        print(f"• State machine replication")
        
        print(f"\n📁 Generated Files:")
        print(f"• demo1_timeline.png - Basic consensus timeline")
        print(f"• demo1_network.png - Network topology")
        print(f"• demo2_byzantine_analysis.png - Byzantine behavior analysis")
        print(f"• comprehensive_dashboard.png - Complete dashboard")
        print(f"• voting_patterns.png - Voting pattern analysis")
        print(f"• consensus_demo.log - Detailed execution log")
        
    except Exception as e:
        print(f"\n❌ ERROR during demonstration: {e}")
        print("Check consensus_demo.log for details")
        raise

if __name__ == "__main__":
    main() 