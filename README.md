# Investment

Code related to the investment section of the website.

See [market_sim](market_sim/README.md) for more details on the market simulation framework

## Usage

```
python3 test_db_operations.py
```

## Market Dynamics and Trading Simulation

Implements a framework for simulating, analyzing, and learning about financial markets, trading strategies, and blockchain integration.

Currently v0.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

The MIT License was chosen to:
- Encourage wide adoption and collaboration
- Allow commercial and academic use
- Keep compliance simple
- Protect contributors from liability
- Maintain compatibility with most open-source projects

## Notes

Project log reinitialized on 2025-01-19.

## New: Blockchain consensus simulator
- See `market_sim/README.md` for a minimal Nakamoto-style longest-chain simulator (`market_sim/blockchain/consensus/nakamoto.py`) and how to run its tests.

## Quick demo
Generate a headless consensus plot (HTML):
```bash
python -m market_sim.analysis.visualization.consensus_viz --ticks 50 --no-show --save consensus.html
```
Then open `consensus.html` in your browser.
