from datetime import datetime, timedelta
from .simulation_engine import MarketSimulation


def main() -> None:
    sim = MarketSimulation(
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(seconds=1),
        time_step=timedelta(milliseconds=100),
    )
    sim.add_consensus_network({
        'num_nodes': 5,
        'block_probability_per_tick': 0.7,
        'delay_probability': 0.2,
        'seed': 1,
    })
    results = sim.run()
    print('consensus ticks:', len(results['metrics']['consensus_metrics']))


if __name__ == '__main__':
    main() 