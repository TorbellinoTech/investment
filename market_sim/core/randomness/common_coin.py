from __future__ import annotations
import hashlib, secrets, threading

class CommonCoin:
    def __init__(self, n: int, f: int, seed: bytes | None = None):
        self.n, self.f = n, f
        self.threshold = 2 * n // 3          # need 2/3 presses
        self._seed = seed or secrets.token_bytes(32)   # secret salt
        self._queries: dict[int, set[int]] = {}
        self._bits: dict[int, int] = {}
        self._lock = threading.Lock()

    def query(self, epoch: int, node_id: int) -> int | None:
        with self._lock:
            if epoch in self._bits:          # already flipped
                return self._bits[epoch]

            self._queries.setdefault(epoch, set()).add(node_id)

            if len(self._queries[epoch]) >= self.threshold:
                h = hashlib.sha256(self._seed + str(epoch).encode()).digest()
                self._bits[epoch] = h[-1] & 1   # last bit is our coin
                return self._bits[epoch]

            return None                       # not enough presses yet
