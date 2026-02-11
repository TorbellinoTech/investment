# Investment Market Simulator v0.1 (HR Test)

## Preliminary Notes

Some files have been added to the main branch with basic blockchain, cryptography and test logic.

## Preliminary Notes for the HR Test

This is an extension of the main branch with added folders and files, mainly placeholders that may serve you for inspiration or ideas of what can be done.

AS OF TODAY NOBODY HAS PASSED THE TEST. 

YOU DO NOT NEED TO DO EVERYTHING. YOU CAN CHOOSE ONE OBJECTIVE FROM THE LIST. IT IS BETTER TO SHOW A CONCEPT FROM THE BOOK CLEARLY AND NICELY THAN TO PROVIDE A MESSY AND BROKEN MIX.

YOU DO NOT NEED TO WATCH THE TIME ESTIMATES. THOSE ARE PURELY ORIENTATIVE.

SEE DISTRIBUTED_CHALLENGE_README for more details.

SEE CREDITS for more details.

## Instructions

1. Read this readme and all the docs.
2. Create a fork of this repo with your contribution.
3. Contact.

## Contact

juan.diez@torbellino.tech

## Further docs

test: https://drive.google.com/file/d/19vKu5HmRJWuzrDGBsTaEiHyJlznYUZKO/view?usp=drive_link
book: https://drive.google.com/file/d/1l9_uCBWikmX-XX5E15n3T65Nkh_cNnEW/view?usp=drive_link

## Overview

Investment v0.1 combines the some ideas of features from multiple proof-of-concept implementations to create a unified platform for:
- Stock market simulation with realistic trading dynamics
- Multiple blockchain consensus protocols (PoW, Raft, Streamlet, Byzantine fault-tolerant)
- Integration of blockchain with market operations
- Real-time distributed trading systems
- High-frequency trading strategies
- Machine learning-based trading algorithms

## Key Features

### 1. Market Simulation Core
- **Order Book Management**: Full limit order book with price-time priority matching
- **Multiple Asset Types**: Stocks, options, warrants, margin trading
- **Market Microstructure**: Latency simulation, various order types (IOC, FOK, etc.)
- **Agent-Based Modeling**: Extensible framework for trading strategies

### 2. Blockchain Protocols
- **Proof of Work (PoW)**: Classic blockchain consensus with adjustable difficulty
- **Raft Consensus**: Leader-based consensus for high-performance trading
- **Streamlet**: Byzantine fault-tolerant consensus for distributed exchanges
- **Dolev-Strong**: Byzantine agreement protocol for critical operations
- **Nakamoto Consensus**: Bitcoin-style longest chain consensus
- **Randomized Consensus**: Probabilistic consensus for scalability

### 3. Blockchain-Market Integration
- **Distributed Exchange**: Decentralized order matching with consensus
- **Trade Settlement**: Blockchain-based trade recording and settlement
- **Price Discovery**: Consensus-based price determination
- **Smart Contract Integration**: Ethereum compatibility (planned)

### 4. Real-Time Components
- **Distributed Nodes**: Multi-node blockchain network simulation
- **Network Communication**: Socket-based and async communication
- **Subprocess Management**: Node lifecycle management
- **Event-Driven Architecture**: Real-time market event processing

### 5. Trading Strategies
- **High-Frequency Trading (HFT)**: Market making, statistical arbitrage
- **Machine Learning**: Predictive models, reinforcement learning
- **Algorithmic Trading**: Technical indicators, portfolio optimization

## Architecture

```
investment_v0.1/
├── market_sim/              # Core simulation framework
│   ├── core/               # Data models and utilities
│   ├── market/             # Exchange and agent implementations
│   ├── strategies/         # Trading strategy implementations
│   ├── blockchain/         # Blockchain protocols and integration
│   ├── simulation/         # Simulation engine and scenarios
│   ├── analysis/           # Metrics and visualization
│   ├── api/               # REST/WebSocket APIs
│   ├── ui/                # User interfaces
│   └── tests/             # Comprehensive test suite
├── data/                   # Market data and blockchain data
├── metadata/              # Configuration and metadata
└── docs/                  # Documentation and tutorials
```

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd investment_v0.1

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

1. **Run a simple market simulation**:
```python
from market_sim.examples import run_basic_simulation
run_basic_simulation()
```

2. **Start a blockchain-integrated market**:
```python
from market_sim.examples import run_blockchain_market
run_blockchain_market(consensus='raft')
```

3. **Launch distributed exchange**:
```python
from market_sim.examples import run_distributed_exchange
run_distributed_exchange(num_nodes=4)
```

## Consensus Protocols

### Proof of Work (PoW)
- SHA-256 based mining
- Adjustable difficulty
- Trade recording on blockchain

### Raft Consensus
- Leader election and log replication
- Fast finality for trading operations
- Crash fault tolerance

### Streamlet
- Byzantine fault tolerance
- 2/3 honest assumption
- Suitable for adversarial environments

### Dolev-Strong
- Byzantine agreement
- Optimal message complexity
- Critical operation consensus

## Examples

See the `market_sim/examples/` directory for:
- `basic_market.py`: Simple market simulation
- `blockchain_trading.py`: Blockchain-integrated trading
- `distributed_exchange.py`: Multi-node exchange
- `hft_simulation.py`: High-frequency trading scenarios
- `consensus_comparison.py`: Compare different consensus protocols

## Development

### Running Tests
```bash
# Unit tests
pytest market_sim/tests/unit/

# Integration tests
pytest market_sim/tests/integration/

# All tests
pytest
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Push to your repo
5. Contact
6. Submit a pull request (optional)

## Performance Metrics

- Order processing: < 1ms latency
- Blockchain consensus: 100-1000 TPS (varies by protocol)
- Concurrent agents: 1000+ supported
- Real-time visualization: 60 FPS

## Future Roadmap

- [ ] Ethereum smart contract integration
- [ ] WebSocket real-time data feeds
- [ ] Advanced ML trading strategies
- [ ] Cross-chain trading capabilities
- [ ] Production-ready deployment tools

## License

MIT License - see LICENSE file for details

## Credits

AS OF TODAY NOBODY HAS PASSED THE TEST.
 
This project integrates some contributions from multiple contributors who explored various blockchain-market integration concepts. Special thanks to all who tried the test and shared their attempts.


### GitHub Usernames (Comma-separated)
Absentation,AnandMNambiar,Ansh2610,Atulsingh1155,Benaia7,JohnPerson05,MEHDI615,MrGranday,NAVEENKUMARKR777,NikhilSingh07,Nikhileshgawhale,Tejas356,abhinavashish15,adlaedorazio,alienx5499,amartya116,domin191013,dominguezz05,eonben,gambhirsharma,maxwrrn,modelpath,mominakanwal,ouss01,patilharsh03,prakharjain3,priyanshu0463,pushkar,sajet4819,shivanshvashisth,shreybm26,thesyzling,ubaidullah,ujjwallsrivastavaa,ultrasage,vidushijhunjhunwala,wesamabed,yatharth

### GitHub Usernames (One per line)
Absentation
AnandMNambiar
Ansh2610
Atulsingh1155
Benaia7
JohnPerson05
MEHDI615
MrGranday
NAVEENKUMARKR777
NikhilSingh07
Nikhileshgawhale
Tejas356
abhinavashish15
adlaedorazio
alienx5499
amartya116
domin191013
dominguezz05
eonben
gambhirsharma
maxwrrn
modelpath
mominakanwal
ouss01
patilharsh03
prakharjain3
priyanshu0463
pushkar
sajet4819
shivanshvashisth
shreybm26
thesyzling
ubaidullah
ujjwallsrivastavaa
ultrasage
vidushijhunjhunwala
wesamabed
yatharth

### Markdown Format for README
[@Absentation](https://github.com/Absentation),
[@AnandMNambiar](https://github.com/AnandMNambiar),
[@Ansh2610](https://github.com/Ansh2610),
[@Atulsingh1155](https://github.com/Atulsingh1155),
[@Benaia7](https://github.com/Benaia7),
[@JohnPerson05](https://github.com/JohnPerson05),
[@MEHDI615](https://github.com/MEHDI615),
[@MrGranday](https://github.com/MrGranday),
[@NAVEENKUMARKR777](https://github.com/NAVEENKUMARKR777),
[@NikhilSingh07](https://github.com/NikhilSingh07),
[@Nikhileshgawhale](https://github.com/Nikhileshgawhale),
[@Tejas356](https://github.com/Tejas356),
[@abhinavashish15](https://github.com/abhinavashish15),
[@adlaedorazio](https://github.com/adlaedorazio),
[@alienx5499](https://github.com/alienx5499),
[@amartya116](https://github.com/amartya116),
[@domin191013](https://github.com/domin191013),
[@dominguezz05](https://github.com/dominguezz05),
[@eonben](https://github.com/eonben),
[@gambhirsharma](https://github.com/gambhirsharma),
[@maxwrrn](https://github.com/maxwrrn),
[@modelpath](https://github.com/modelpath),
[@mominakanwal](https://github.com/mominakanwal),
[@ouss01](https://github.com/ouss01),
[@patilharsh03](https://github.com/patilharsh03),
[@prakharjain3](https://github.com/prakharjain3),
[@priyanshu0463](https://github.com/priyanshu0463),
[@pushkar](https://github.com/pushkar),
[@sajet4819](https://github.com/sajet4819),
[@shivanshvashisth](https://github.com/shivanshvashisth),
[@shreybm26](https://github.com/shreybm26),
[@thesyzling](https://github.com/thesyzling),
[@ubaidullah](https://github.com/ubaidullah),
[@ujjwallsrivastavaa](https://github.com/ujjwallsrivastavaa),
[@ultrasage](https://github.com/ultrasage),
[@vidushijhunjhunwala](https://github.com/vidushijhunjhunwala),
[@wesamabed](https://github.com/wesamabed),
[@yatharth](https://github.com/yatharth)

