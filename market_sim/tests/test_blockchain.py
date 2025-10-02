from market_sim.core.blockchain import SimpleBlockchain

def test_blockchain_mining_and_validation():
    bc = SimpleBlockchain(difficulty=2)
    bc.add_block("first")
    bc.add_block("second")
    assert len(bc.chain) == 3  # genesis + 2
    assert bc.is_valid()

def test_tamper_detection():
    bc = SimpleBlockchain(difficulty=2)
    bc.add_block("a")
    bc.add_block("b")
    bc.tamper(1, "malicious")
    assert not bc.is_valid()
