# market_sim/tests/test_blockchain_sim.py
import pytest
from market_sim.blockchain_sim import Blockchain

def test_blockchain_creation():
    """Test that a new blockchain has a genesis block"""
    bc = Blockchain()
    assert len(bc.chain) == 1  # Genesis block

def test_block_mining():
    """Test that mining a block increases the chain length and keeps it valid"""
    bc = Blockchain()
    
    # Mine a block with 2 transactions
    bc.add_transaction("tx1")
    bc.add_transaction("tx2")
    bc.mine_pending_transactions()

    # Check that the chain has 2 blocks now
    assert len(bc.chain) == 2
    
    # Check that the blockchain is still valid
    assert bc.is_chain_valid()
