from typing import List, Dict
from dataclasses import dataclass
import argparse
import sys

import plotly.graph_objects as go
import pandas as pd

from ...blockchain.consensus.nakamoto import NakamotoNetwork, NetworkParams


@dataclass
class RunConfig:
    num_ticks: int = 300
    num_nodes: int = 5
    block_probability_per_tick: float = 0.7
    delay_probability: float = 0.2
    seed: int = 1


def run_simulation_series(cfg: RunConfig) -> pd.DataFrame:
    net = NakamotoNetwork(NetworkParams(
        num_nodes=cfg.num_nodes,
        block_probability_per_tick=cfg.block_probability_per_tick,
        delay_probability=cfg.delay_probability,
        seed=cfg.seed,
    ))

    records: List[Dict] = []
    for t in range(cfg.num_ticks):
        net.step()
        heights = [n.head.index for n in net.nodes]
        records.append({
            'tick': t,
            'common_prefix': net.common_prefix_length(),
            'finalized_depth': net.finalized_depth(),
            'min_height': min(heights),
            'max_height': max(heights),
            'avg_height': sum(heights) / len(heights)
        })

    return pd.DataFrame.from_records(records)


def plot_series(df: pd.DataFrame, title: str = "Nakamoto consensus dynamics") -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['tick'], y=df['common_prefix'], mode='lines', name='common_prefix'))
    fig.add_trace(go.Scatter(x=df['tick'], y=df['finalized_depth'], mode='lines', name='finalized_depth'))
    fig.add_trace(go.Scatter(x=df['tick'], y=df['min_height'], mode='lines', name='min_height'))
    fig.add_trace(go.Scatter(x=df['tick'], y=df['avg_height'], mode='lines', name='avg_height'))
    fig.add_trace(go.Scatter(x=df['tick'], y=df['max_height'], mode='lines', name='max_height'))

    fig.update_layout(
        title=title,
        xaxis_title='tick',
        yaxis_title='blocks',
        legend_title='series',
        template='plotly_white',
        height=500,
    )
    return fig


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Visualize Nakamoto consensus dynamics")
    p.add_argument('--ticks', type=int, default=300, help='number of ticks to simulate')
    p.add_argument('--nodes', type=int, default=5, help='number of nodes')
    p.add_argument('--bp', type=float, default=0.7, help='block probability per tick')
    p.add_argument('--delay', type=float, default=0.2, help='message delay probability')
    p.add_argument('--seed', type=int, default=1, help='random seed')
    p.add_argument('--save', type=str, default='', help='optional path to save HTML plot instead of opening')
    p.add_argument('--no-show', action='store_true', help='do not open an interactive window')
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    cfg = RunConfig(
        num_ticks=args.ticks,
        num_nodes=args.nodes,
        block_probability_per_tick=args.bp,
        delay_probability=args.delay,
        seed=args.seed,
    )
    df = run_simulation_series(cfg)
    fig = plot_series(df)
    if args.save:
        fig.write_html(args.save, include_plotlyjs='cdn')
        print(f"Saved: {args.save}")
        sys.exit(0)
    if not args.no_show:
        fig.show() 