"""
Integration tests for Investment Market Simulator v0.1
"""

import pytest
from datetime import datetime
from decimal import Decimal

from market_sim.core.models.base import Order, OrderType, OrderSide
from market_sim.market.exchange.matching_engine import MatchingEngine
from market_sim.blockchain.consensus import ProofOfWork, RaftConsensus, StreamletConsensus
from market_sim.blockchain.market_ledger import MarketTransactionLedger


class TestMarketIntegration:
    """Test market components integration."""
    
    def test_basic_trading(self):
        """Test basic order matching."""
        engine = MatchingEngine("STOCK")

        # Create buy order
        buy_order = Order.create_limit_order(
            symbol="STOCK",
            side=OrderSide.BUY,
            quantity=Decimal("100"),
            price=Decimal("50.0"),
            agent_id="trader_1"
        )

        # Create sell order
        sell_order = Order.create_limit_order(
            symbol="STOCK",
            side=OrderSide.SELL,
            quantity=Decimal("100"),
            price=Decimal("50.0"),
            agent_id="trader_2"
        )

        # Process orders
        engine.process_order(buy_order)
        trades = engine.process_order(sell_order)

        # Verify trade occurred
        assert len(trades) == 1
        assert trades[0].price == Decimal("50.0")
        assert trades[0].quantity == Decimal("100")
        

class TestBlockchainIntegration:
    """Test blockchain integration."""
    
    def test_pow_consensus(self):
        """Test Proof of Work consensus."""
        pow = ProofOfWork(difficulty=2)
        
        # Add transaction
        pow.add_transaction({"data": "test_transaction"})
        
        # Mine block
        block = pow.mine_block()
        
        assert block is not None
        assert block.hash.startswith("00")
        assert len(pow.chain) == 2  # Genesis + new block
        
    def test_market_ledger_pow(self):
        """Test market ledger with PoW."""
        ledger = MarketTransactionLedger(consensus_type="pow", 
                                       consensus_params={"difficulty": 2})
        
        # Create dummy trade
        from market_sim.core.models.base import Trade
        from uuid import uuid4
        trade = Trade(
            id=uuid4(),
            symbol="STOCK",
            price=Decimal("50.0"),
            quantity=Decimal("100"),
            buyer_order_id=uuid4(),
            seller_order_id=uuid4(),
            timestamp=datetime.now()
        )
        
        # Record trade
        trade_id = ledger.record_trade(trade)
        
        # Mine block
        block_info = ledger.mine_block()
        
        assert block_info is not None
        assert block_info['trades_confirmed'] > 0
        

class TestConsensusProtocols:
    """Test different consensus protocols."""
    
    @pytest.mark.parametrize("consensus_type", ["pow", "raft", "streamlet"])
    def test_consensus_creation(self, consensus_type):
        """Test creating different consensus types."""
        ledger = MarketTransactionLedger(consensus_type=consensus_type)
        
        assert ledger.consensus_type == consensus_type
        assert ledger.consensus is not None
        

def test_full_integration():
    """Test full system integration."""
    # Create matching engine
    engine = MatchingEngine("STOCK")
    
    # Create ledger
    ledger = MarketTransactionLedger(consensus_type="pow", 
                                   consensus_params={"difficulty": 2})
    
    # Create and match orders
    buy_order = Order.create_limit_order(
        symbol="STOCK",
        side=OrderSide.BUY,
        quantity=Decimal("50"),
        price=Decimal("100.0"),
        agent_id="int_trader_1"
    )

    sell_order = Order.create_limit_order(
        symbol="STOCK",
        side=OrderSide.SELL,
        quantity=Decimal("50"),
        price=Decimal("100.0"),
        agent_id="int_trader_2"
    )

    # Execute trades
    engine.process_order(buy_order)
    trades = engine.process_order(sell_order)
    
    # Record on blockchain
    for trade in trades:
        ledger.record_trade(trade)
        
    # Mine block
    block_info = ledger.mine_block()
    
    # Verify
    assert len(trades) == 1
    assert block_info is not None
    assert ledger.verify_ledger_integrity()
    print(ledger.get_ledger_stats())

def test_full_integration_2():
    """Test full system integration."""
    # Create matching engine
    N = 10

    engine = MatchingEngine("STOCK")
    
    # Create ledger
    ledger = MarketTransactionLedger(consensus_type="pow", 
                                   consensus_params={"difficulty": 2})
    
    for i in range(N):
        # Create and match orders
        buy_order = Order.create_limit_order(
            symbol="STOCK",
            side=OrderSide.BUY,
            quantity=Decimal("50"),
            price=Decimal("100.0"),
            agent_id=f"int_trader_{i}"
        )

        sell_order = Order.create_limit_order(
            symbol="STOCK",
            side=OrderSide.SELL,
            quantity=Decimal("50"),
            price=Decimal("100.0"),
            agent_id=f"int_trader_{i}"
        )

        # Execute trades
        engine.process_order(buy_order)
        trades = engine.process_order(sell_order)
    
        # Record on blockchain
        for trade in trades:
            ledger.record_trade(trade)
        
        # Mine block
        block_info = ledger.mine_block()
    
    # Verify
    assert block_info is not None
    assert ledger.verify_ledger_integrity()
    print(ledger.get_ledger_stats())

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 