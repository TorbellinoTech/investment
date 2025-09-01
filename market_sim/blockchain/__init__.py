"""
Blockchain integration module for market simulation.

This module provides various consensus protocols and blockchain implementations
that can be integrated with the market simulation framework.
"""

from market_sim.blockchain import consensus
from market_sim.blockchain import contracts
from market_sim.blockchain import ethereum

__all__ = ["consensus", "contracts", "ethereum"] 