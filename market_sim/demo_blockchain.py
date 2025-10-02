from market_sim.core.blockchain import SimpleBlockchain
import matplotlib.pyplot as plt
import time

def run_demo():
    bc = SimpleBlockchain(difficulty=3)
    times = []
    for i in range(4):
        t0 = time.time()
        bc.add_block(f"txs batch {i}")
        t1 = time.time()
        times.append(t1 - t0)
        print(f"Mined block {i+1} in {times[-1]:.3f}s")

    plt.figure(figsize=(6,3))
    plt.plot(range(1,len(times)+1), times, marker='o')
    plt.title("Mining time per block (difficulty=3)")
    plt.xlabel("block number")
    plt.ylabel("seconds")
    plt.tight_layout()
    plt.savefig("market_sim/core/mining_times.png")
    print("Saved plot to market_sim/core/mining_times.png")

if __name__ == "__main__":
    run_demo()
