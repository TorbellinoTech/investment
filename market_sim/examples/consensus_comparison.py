"""
Consensus protocol comparison example.

Compares different blockchain consensus mechanisms for trading.
"""

from market_sim.examples.blockchain_trading import compare_blockchain_consensus


def compare_consensus_protocols():
    """Compare different consensus protocols."""
    print("=== Consensus Protocol Comparison ===")
    
    results = compare_blockchain_consensus()
    
    print("\nConsensus comparison completed!")
    
    return results


if __name__ == "__main__":
    compare_consensus_protocols() 