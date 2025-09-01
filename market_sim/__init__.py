"""
Investment Market Simulator v0.1

A comprehensive financial market simulation framework with integrated blockchain protocols.
"""

__version__ = "0.1.0"
__author__ = "Investment Simulator Contributors"

# Core imports
from market_sim.core.models.base import Order, Trade, Asset, OrderBook
from market_sim.market.agents.base_agent import BaseAgent
from market_sim.market.exchange.matching_engine import MatchingEngine
from market_sim.simulation.engine.simulation_engine import MarketSimulation

# Blockchain imports
from market_sim.blockchain.consensus import (
    ProofOfWork,
    RaftConsensus,
    StreamletConsensus,
    DolevStrongConsensus,
    NakamotoProtocol,
    RandomizedConsensus
)

__all__ = [
    "Order",
    "Trade", 
    "Asset",
    "OrderBook",
    "BaseAgent",
    "MatchingEngine",
    "MarketSimulation",
    "ProofOfWork",
    "RaftConsensus",
    "StreamletConsensus",
    "DolevStrongConsensus",
    "NakamotoProtocol", #NakamotoConsensus
    "RandomizedConsensus"
] 