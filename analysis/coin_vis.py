from market_sim.core.randomness import CommonCoin
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

n, f = 10, 3
coin = CommonCoin(n, f)
trials = 1000

# collect one flip per epoch by having every node press
bits = []
for epoch in range(trials):
    for node_id in range(n):
        b = coin.query(epoch, node_id)
        if b is not None:
            bits.append(b)
            break

plt.figure()
plt.hist(bits, bins=[-0.5, 0.5, 1.5])
plt.xticks([0, 1])
plt.xlabel("Coin value")
plt.ylabel(f"Frequency over {trials} epochs")
plt.title(f"Common-Coin distribution (n={n},f={f})")
plt.show()   