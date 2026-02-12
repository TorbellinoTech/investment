""""
plot_chain.py
Visualize Proof-of-Work mining times for multiple runs.
"""
# BY MOMINA KANWAL

import matplotlib.pyplot as plt
from market_sim.pow_sim import mine


def run_and_plot(prefix="Block", difficulty=2, runs=5):
    times = []
    for i in range(runs):
        res = mine(f"{prefix}{i}", difficulty)
        if res:
            times.append(res["time"])
        else:
            times.append(None)

    plt.plot(times, marker="o", label=f"Difficulty={difficulty}")
    plt.title("Proof-of-Work Mining Times")
    plt.xlabel("Run #")
    plt.ylabel("Seconds")
    plt.legend()
    plt.show()
