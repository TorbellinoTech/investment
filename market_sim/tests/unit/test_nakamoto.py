import pytest

from blockchain.consensus.nakamoto import NakamotoNetwork, NetworkParams


def test_nakamoto_basic_convergence():
    params = NetworkParams(num_nodes=7, block_probability_per_tick=0.8, delay_probability=0.3, seed=7)
    net = NakamotoNetwork(params)
    net.run(num_ticks=200)

    # Common prefix should be at least genesis plus some progress
    cpl = net.common_prefix_length()
    assert cpl >= 1
    # finalized depth excludes genesis
    assert net.finalized_depth() >= 0


def test_nakamoto_progress():
    params = NetworkParams(num_nodes=3, block_probability_per_tick=0.5, delay_probability=0.2, seed=1)
    net = NakamotoNetwork(params)
    net.run(num_ticks=50)

    # Ensure chains have advanced beyond genesis
    heights = [n.head.index for n in net.nodes]
    assert min(heights) > 0 