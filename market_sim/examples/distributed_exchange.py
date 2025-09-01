"""
Distributed exchange example.

Demonstrates running multiple blockchain nodes for distributed trading.
"""

import asyncio
from market_sim.blockchain.distributed import run_distributed_simulation, DistributedNetwork
from market_sim.blockchain.distributed_exchange import DistributedExchange


def run_distributed_exchange(num_nodes: int = 4):
    """Run a distributed exchange simulation."""
    print(f"=== Distributed Exchange Example ===")
    print(f"Starting {num_nodes} nodes...")
    
    # Run async simulation
    asyncio.run(run_distributed_simulation(num_nodes=num_nodes, duration=30))
    
    print("\nDistributed exchange simulation completed!")
    
    return {'num_nodes': num_nodes}


if __name__ == "__main__":
    run_distributed_exchange() 