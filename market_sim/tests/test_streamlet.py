import random

from market_sim.streamlet import StreamletSim


def test_consistency_under_honest_majority():
    random.seed(0)
    sim = StreamletSim(n=10, corrupt_fraction=0.2, seed="seed0")
    sim.run(epochs=50)
    assert sim.consistency_holds()


def test_progress_eventually_finalizes_with_honest_majority():
    random.seed(1)
    sim = StreamletSim(n=10, corrupt_fraction=0.2, seed="seed1")
    sim.run(epochs=120)
    assert sim.finalized_prefix_hash is not None


def test_runs_under_high_corruption():
    random.seed(2)
    sim = StreamletSim(n=12, corrupt_fraction=0.5, seed="seed2")
    sim.run(epochs=150)
    # Just ensure the simulator completes and yields a boolean consistency status
    assert isinstance(sim.consistency_holds(), bool)


