"""
Ethereum integration module for market simulation.

This module provides integration with Ethereum blockchain for:
- Smart contract deployment and interaction
- Web3.py integration
- ERC20 token support
- DeFi protocol integration

Note: This module requires web3.py to be installed.
"""

# Check if web3 is available
try:
    import web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False

if WEB3_AVAILABLE:
    from market_sim.blockchain.ethereum.eth_integration import EthereumIntegration
    from market_sim.blockchain.ethereum.smart_contracts import TradingContract, SettlementContract
    from market_sim.blockchain.ethereum.defi_adapter import DeFiAdapter
    
    __all__ = [
        "EthereumIntegration",
        "TradingContract", 
        "SettlementContract",
        "DeFiAdapter"
    ]
else:
    __all__ = []
    
    class EthereumIntegration:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "Web3.py is not installed. Install it with: pip install web3"
            ) 