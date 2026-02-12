"""
pow_sim.py
A simple Proof-of-Work simulator inspired by Bitcoin (Nakamoto Consensus).
"""

# BY MOMINA KANWAL

import hashlib
import time


def mine(prefix: str, difficulty: int, max_iters: int = 1_000_000):
    """
    Try different nonces until sha256(prefix|nonce) has `difficulty` leading zeros in hex.

    Args:
        prefix (str): Data to include in the block (e.g., "Block1").
        difficulty (int): Number of leading zeros required.
        max_iters (int): Maximum number of attempts before giving up.

    Returns:
        dict: {'nonce': int, 'hash': str, 'time': float} if success, else None.
    """
    target = "0" * difficulty
    nonce = 0
    start_time = time.time()

    while nonce < max_iters:
        text = f"{prefix}|{nonce}"
        h = hashlib.sha256(text.encode()).hexdigest()
        if h.startswith(target):
            return {
                "nonce": nonce,
                "hash": h,
                "time": time.time() - start_time,
            }
        nonce += 1

    return None
