"""
Examples demonstrating various features of the Investment Market Simulator v0.1
"""

from market_sim.examples.basic_market import run_basic_simulation
from market_sim.examples.blockchain_trading import run_blockchain_market
from market_sim.examples.distributed_exchange import run_distributed_exchange
from market_sim.examples.hft_simulation import run_hft_simulation
from market_sim.examples.consensus_comparison import compare_consensus_protocols

__all__ = [
    "run_basic_simulation",
    "run_blockchain_market",
    "run_distributed_exchange", 
    "run_hft_simulation",
    "compare_consensus_protocols"
] 