"""
Unit tests for Proof-of-Work simulator.
"""
# BY MOMINA KANWAL
from market_sim.pow_sim import mine


def test_mine_easy():
    res = mine("testprefix", difficulty=2, max_iters=200000)
    assert res is not None
    assert "nonce" in res
    assert res["hash"].startswith("00")  # 2 leading zeros
