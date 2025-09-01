#!/usr/bin/env python3
"""
Quick start script to run various examples of the Investment Market Simulator.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from market_sim.examples import (
    run_basic_simulation,
    run_blockchain_market,
    run_distributed_exchange,
    run_hft_simulation,
    compare_consensus_protocols
)


def main():
    """Run examples based on user selection."""
    print("=== Investment Market Simulator v0.1 - Examples ===")
    print("\nAvailable examples:")
    print("1. Basic Market Simulation")
    print("2. Blockchain Trading (PoW)")
    print("3. Blockchain Trading (Raft)")
    print("4. Blockchain Trading (Streamlet)")
    print("5. Distributed Exchange")
    print("6. HFT Simulation")
    print("7. Compare All Consensus Protocols")
    print("8. Run All Examples")
    print("0. Exit")
    
    while True:
        try:
            choice = input("\nSelect an example to run (0-8): ")
            
            if choice == "0":
                print("Exiting...")
                break
            elif choice == "1":
                print("\n" + "="*60)
                run_basic_simulation(num_agents=10, simulation_steps=100)
            elif choice == "2":
                print("\n" + "="*60)
                run_blockchain_market(consensus="pow", num_trades=20)
            elif choice == "3":
                print("\n" + "="*60)
                run_blockchain_market(consensus="raft", num_trades=20)
            elif choice == "4":
                print("\n" + "="*60)
                run_blockchain_market(consensus="streamlet", num_trades=20)
            elif choice == "5":
                print("\n" + "="*60)
                run_distributed_exchange(num_nodes=4)
            elif choice == "6":
                print("\n" + "="*60)
                run_hft_simulation()
            elif choice == "7":
                print("\n" + "="*60)
                compare_consensus_protocols()
            elif choice == "8":
                print("\nRunning all examples...")
                print("\n" + "="*60)
                run_basic_simulation(num_agents=5, simulation_steps=50)
                print("\n" + "="*60)
                run_blockchain_market(consensus="pow", num_trades=10)
                print("\n" + "="*60)
                run_blockchain_market(consensus="raft", num_trades=10)
                print("\n" + "="*60)
                run_blockchain_market(consensus="streamlet", num_trades=10)
                print("\n" + "="*60)
                compare_consensus_protocols()
            else:
                print("Invalid choice. Please select 0-8.")
                
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"\nError running example: {e}")
            print("Some examples may require additional dependencies.")
            

if __name__ == "__main__":
    main() 