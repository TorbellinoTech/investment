from market_sim.core.randomness import CommonCoin

def test_coin_basic():
    n, f = 10, 3
    coin = CommonCoin(n, f)
    outs = [coin.query(0, i) for i in range(n)]
    bit = next(b for b in outs if b is not None)
    assert all(coin.query(0, i) == bit for i in range(n))
