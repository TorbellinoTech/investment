# Market Dynamics and Trading Simulation Framework

Implements a framework for simulating, analyzing, and learning about financial markets, trading strategies, and blockchain integration.

Currently v0.

## Project Structure

```
market_sim/
├── core/                      # Core functionality and base classes
│   ├── data/                 # Data management and storage
│   ├── models/              # Core market models and entities
│   └── utils/               # Utility functions and helpers
│
├── market/                   # Market simulation components
│   ├── exchange/            # Exchange mechanisms and matching engines
│   ├── agents/              # Trading agents and strategies
│   ├── mechanisms/          # Trading mechanisms (options, warrants, etc.)
│   └── dynamics/            # Market dynamics and price formation
│
├── strategies/               # Trading strategies implementation
│   ├── traditional/         # Classical trading strategies
│   ├── hft/                 # High-frequency trading strategies
│   └── ml/                  # Machine learning based strategies
│
├── simulation/              # Simulation framework
│   ├── engine/             # Simulation engine and time management
│   ├── scenarios/          # Pre-defined simulation scenarios
│   └── results/            # Results analysis and visualization
│
├── blockchain/              # Blockchain integration
│   ├── ethereum/           # Ethereum specific implementations
│   ├── consensus/          # Consensus mechanisms
│   └── contracts/          # Smart contracts
│
├── analysis/                # Analysis tools and utilities
│   ├── metrics/            # Performance and risk metrics
│   ├── visualization/      # Data visualization tools
│   └── reports/            # Report generation
│
├── api/                     # API interfaces
│   ├── rest/               # REST API
│   └── websocket/          # WebSocket API
│
├── ui/                      # User interfaces
│   ├── web/                # Web interface
│   ├── cli/                # Command-line interface
│   └── desktop/            # Desktop application
│
└── tests/                   # Test suite
    ├── unit/               # Unit tests
    ├── integration/        # Integration tests
    └── performance/        # Performance tests
```

## Features

### Market Simulation
- Real-time market simulation with configurable parameters
- Multiple asset types and trading mechanisms
- Price formation and order book management
- Trading agent framework with customizable strategies

### Trading Mechanisms
- Stock trading with various order types
- Options and warrants simulation
- Short selling and margin trading
- Custom mechanism creation framework

### High-Frequency Trading
- Ultra-low latency framework
- Order execution optimization
- Market making strategies
- Statistical arbitrage

### Blockchain Integration
- Ethereum smart contract integration
- Consensus mechanism simulation
- Cross-chain trading strategies
- DeFi protocol integration

### Learning Environment
- Interactive tutorials and scenarios
- Strategy backtesting framework
- Performance analytics
- Risk management tools

### Visualization (consensus)
- Script: `analysis/visualization/consensus_viz.py`
- Run:
```bash
python market_sim/analysis/visualization/consensus_viz.py
```
This opens an interactive Plotly chart showing over time: common prefix, finalized depth, and min/avg/max chain heights across nodes.

## Getting Started

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run tests:
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/

# Run with coverage
pytest --cov=market_sim

# Run specific test file
pytest tests/integration/test_market_making.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Blockchain Consensus (new)

A minimal longest-chain (Nakamoto-style) consensus simulator has been added:
- Code: `blockchain/consensus/nakamoto.py`
- Tests: `tests/unit/test_nakamoto.py`

Run the unit tests:
```bash
pytest market_sim/tests/unit/test_nakamoto.py -q
```

Quick usage example (Python REPL):
```python
from blockchain.consensus.nakamoto import NakamotoNetwork, NetworkParams
net = NakamotoNetwork(NetworkParams(num_nodes=5, block_probability_per_tick=0.7, delay_probability=0.2, seed=1))
net.run(num_ticks=200)
print("common_prefix_length:", net.common_prefix_length())
print("finalized_depth:", net.finalized_depth())
```