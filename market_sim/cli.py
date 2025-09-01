"""
Command Line Interface for Investment Market Simulator v0.1
"""

import argparse
import sys
from typing import Optional

from market_sim.examples.basic_market import run_basic_simulation
from market_sim.examples.blockchain_trading import run_blockchain_market
from market_sim.examples.distributed_exchange import run_distributed_exchange
from market_sim.examples.hft_simulation import run_hft_simulation
from market_sim.examples.consensus_comparison import compare_consensus_protocols


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Investment Market Simulator v0.1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  market-sim basic           # Run basic market simulation
  market-sim blockchain      # Run blockchain-integrated market
  market-sim distributed     # Run distributed exchange simulation
  market-sim hft             # Run high-frequency trading simulation
  market-sim consensus       # Compare consensus protocols
        """
    )

    parser.add_argument(
        'command',
        choices=['basic', 'blockchain', 'distributed', 'hft', 'consensus'],
        help='Simulation type to run'
    )

    parser.add_argument(
        '--nodes', '-n',
        type=int,
        default=4,
        help='Number of nodes for distributed simulations (default: 4)'
    )

    parser.add_argument(
        '--consensus', '-c',
        choices=['pow', 'raft', 'streamlet'],
        default='pow',
        help='Consensus protocol to use (default: pow)'
    )

    parser.add_argument(
        '--duration', '-d',
        type=int,
        default=1000,
        help='Simulation duration in milliseconds (default: 1000)'
    )

    args = parser.parse_args()

    try:
        if args.command == 'basic':
            print("Running basic market simulation...")
            run_basic_simulation()

        elif args.command == 'blockchain':
            print(f"Running blockchain-integrated market with {args.consensus} consensus...")
            run_blockchain_market(consensus=args.consensus)

        elif args.command == 'distributed':
            print(f"Running distributed exchange with {args.nodes} nodes...")
            run_distributed_exchange(num_nodes=args.nodes)

        elif args.command == 'hft':
            print("Running high-frequency trading simulation...")
            run_hft_simulation()

        elif args.command == 'consensus':
            print("Running consensus protocol comparison...")
            compare_consensus_protocols()

        print("Simulation completed successfully!")

    except Exception as e:
        print(f"Error running simulation: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
