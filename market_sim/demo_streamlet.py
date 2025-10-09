import argparse

from market_sim.streamlet import StreamletSim


def main() -> None:
    parser = argparse.ArgumentParser(description="Streamlet protocol demo")
    parser.add_argument("--nodes", type=int, default=15, help="number of nodes")
    parser.add_argument("--corrupt", type=float, default=0.2, help="fraction [0,1) corrupt")
    parser.add_argument("--epochs", type=int, default=150, help="epochs to simulate")
    parser.add_argument("--seed", type=str, default="viz", help="PRNG seed")
    args = parser.parse_args()

    sim = StreamletSim(n=args.nodes, corrupt_fraction=args.corrupt, seed=args.seed)
    sim.run(epochs=args.epochs)
    print("Finalized:", sim.finalized_prefix_hash)
    print("Consistency:", sim.consistency_holds())
    lengths = [len(node.chain) for node in sim.nodes]
    print("Chain lengths:", lengths)
    print("Avg length:", sum(lengths) / len(lengths))
    # Optional mini visualization: show notarized epochs seen by first node
    first = sim.nodes[0]
    notarized_epochs = [blk.epoch for blk in first.chain if blk.hash in first.notarized_hashes]
    print("Node 0 notarized epochs:", notarized_epochs)


if __name__ == "__main__":
    main()


