"""
Market Transaction Ledger - Blockchain-based trade recording system.

Integrates market operations with blockchain consensus for:
- Immutable trade recording
- Distributed trade validation
- Consensus-based settlement
"""

import hashlib
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from market_sim.core.models.base import Order, Trade
from market_sim.blockchain.consensus import ProofOfWork, RaftConsensus, StreamletConsensus


class TradeStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SETTLED = "settled"
    REJECTED = "rejected"


@dataclass
class BlockchainTrade:
    """Trade record for blockchain storage."""
    trade_id: str
    buyer: str
    seller: str
    asset: str
    quantity: float
    price: float
    timestamp: float
    status: TradeStatus
    block_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        return data
        
    @classmethod
    def from_trade(cls, trade: Trade) -> 'BlockchainTrade':
        """Create from a market Trade object."""
        return cls(
            trade_id=str(trade.id),
            buyer=str(trade.buyer_order_id),
            seller=str(trade.seller_order_id),
            asset=trade.symbol,
            quantity=float(trade.quantity),
            price=float(trade.price),
            timestamp=trade.timestamp.timestamp(),
            status=TradeStatus.PENDING
        )


class MarketTransactionLedger:
    """
    Blockchain-based ledger for recording market transactions.
    """
    
    def __init__(self, consensus_type: str = "pow", consensus_params: Dict[str, Any] = None):
        self.consensus_type = consensus_type
        self.consensus = self._init_consensus(consensus_type, consensus_params or {})
        self.pending_trades: List[BlockchainTrade] = []
        self.confirmed_trades: Dict[str, BlockchainTrade] = {}
        self.trade_blocks: Dict[str, str] = {}  # trade_id -> block_hash
        
    def _init_consensus(self, consensus_type: str, params: Dict[str, Any]):
        """Initialize the consensus mechanism."""
        if consensus_type == "pow":
            return ProofOfWork(difficulty=params.get("difficulty", 4))
        elif consensus_type == "raft":
            return RaftConsensus(num_nodes=params.get("num_nodes", 5))
        elif consensus_type == "streamlet":
            return StreamletConsensus()
        else:
            raise ValueError(f"Unknown consensus type: {consensus_type}")
            
    def record_trade(self, trade: Trade) -> str:
        """Record a new trade in the ledger."""
        blockchain_trade = BlockchainTrade.from_trade(trade)
        self.pending_trades.append(blockchain_trade)
        
        # For PoW, add to pending transactions
        if isinstance(self.consensus, ProofOfWork):
            self.consensus.add_transaction(blockchain_trade.to_dict())
            
        # For other consensus, submit as command
        elif hasattr(self.consensus, 'submit_command'):
            self.consensus.submit_command(blockchain_trade.to_dict())
            
        return blockchain_trade.trade_id
        
    def mine_block(self) -> Optional[Dict[str, Any]]:
        """Mine a new block containing pending trades (for PoW)."""
        if not isinstance(self.consensus, ProofOfWork):
            return None
            
        if not self.pending_trades:
            return None
            
        # Mine the block
        block = self.consensus.mine_block()
        if block:
            # Update trade statuses
            for trade_data in block.transactions:
                trade_id = trade_data.get('trade_id')
                if trade_id:
                    # Find and update the trade
                    for pending_trade in self.pending_trades[:]:
                        if pending_trade.trade_id == trade_id:
                            pending_trade.status = TradeStatus.CONFIRMED
                            pending_trade.block_hash = block.hash
                            self.confirmed_trades[trade_id] = pending_trade
                            self.trade_blocks[trade_id] = block.hash
                            self.pending_trades.remove(pending_trade)
                            break
                            
            return {
                'block_hash': block.hash,
                'block_index': block.index,
                'trades_confirmed': len(block.transactions),
                'timestamp': block.timestamp.isoformat()
            }
            
        return None
        
    def run_consensus_round(self) -> Dict[str, Any]:
        """Run a consensus round for non-PoW consensus mechanisms."""
        if isinstance(self.consensus, ProofOfWork):
            return self.mine_block() or {'status': 'no_pending_trades'}
            
        # For Raft/Streamlet, run consensus round
        if hasattr(self.consensus, 'run_consensus_round'):
            self.consensus.run_consensus_round()
            
            # Process confirmed trades
            confirmed_count = 0
            for trade in self.pending_trades[:]:
                # Check if trade was confirmed by consensus
                if self._is_trade_confirmed(trade):
                    trade.status = TradeStatus.CONFIRMED
                    self.confirmed_trades[trade.trade_id] = trade
                    self.pending_trades.remove(trade)
                    confirmed_count += 1
                    
            return {
                'consensus_type': self.consensus_type,
                'trades_confirmed': confirmed_count,
                'pending_trades': len(self.pending_trades)
            }
            
        return {'status': 'consensus_not_available'}
        
    def _is_trade_confirmed(self, trade: BlockchainTrade) -> bool:
        """Check if a trade has been confirmed by consensus."""
        # This would be implemented based on the specific consensus mechanism
        # For now, we'll use a simple confirmation after consensus round
        return True
        
    def get_trade_status(self, trade_id: str) -> Optional[TradeStatus]:
        """Get the status of a specific trade."""
        # Check confirmed trades
        if trade_id in self.confirmed_trades:
            return self.confirmed_trades[trade_id].status
            
        # Check pending trades
        for trade in self.pending_trades:
            if trade.trade_id == trade_id:
                return trade.status
                
        return None
        
    def get_trade_block(self, trade_id: str) -> Optional[str]:
        """Get the block hash containing a specific trade."""
        return self.trade_blocks.get(trade_id)
        
    def settle_trade(self, trade_id: str) -> bool:
        """Mark a confirmed trade as settled."""
        if trade_id in self.confirmed_trades:
            self.confirmed_trades[trade_id].status = TradeStatus.SETTLED
            return True
        return False
        
    def get_ledger_stats(self) -> Dict[str, Any]:
        """Get statistics about the ledger."""
        stats = {
            'consensus_type': self.consensus_type,
            'pending_trades': len(self.pending_trades),
            'confirmed_trades': len(self.confirmed_trades),
            'settled_trades': sum(1 for t in self.confirmed_trades.values() 
                                if t.status == TradeStatus.SETTLED),
        }
        
        # Add consensus-specific stats
        if isinstance(self.consensus, ProofOfWork):
            stats['blockchain_length'] = len(self.consensus.chain)
            stats['mining_difficulty'] = self.consensus.difficulty
        elif hasattr(self.consensus, 'get_status'):
            stats['consensus_status'] = self.consensus.get_status()
            
        return stats
        
    def verify_ledger_integrity(self) -> bool:
        """Verify the integrity of the entire ledger."""
        if isinstance(self.consensus, ProofOfWork):
            return self.consensus.is_valid_chain()
        # For other consensus types, implement appropriate verification
        return True


class DistributedMarketLedger(MarketTransactionLedger):
    """
    Extended ledger with distributed node support.
    """
    
    def __init__(self, node_id: str, consensus_type: str = "raft", 
                 consensus_params: Dict[str, Any] = None):
        super().__init__(consensus_type, consensus_params)
        self.node_id = node_id
        self.peer_nodes: List[str] = []
        
    def add_peer(self, peer_url: str):
        """Add a peer node for distributed consensus."""
        self.peer_nodes.append(peer_url)
        
    def broadcast_trade(self, trade: Trade) -> Dict[str, Any]:
        """Broadcast a trade to all peer nodes."""
        results = {'success': [], 'failed': []}
        
        # Record locally first
        trade_id = self.record_trade(trade)
        results['success'].append({'node': self.node_id, 'trade_id': trade_id})
        
        # Broadcast to peers
        import requests
        for peer in self.peer_nodes:
            try:
                response = requests.post(
                    f"{peer}/ledger/trade",
                    json=trade.to_dict(),
                    timeout=5
                )
                if response.status_code == 200:
                    results['success'].append({'node': peer, 'response': response.json()})
                else:
                    results['failed'].append({'node': peer, 'error': f"Status {response.status_code}"})
            except Exception as e:
                results['failed'].append({'node': peer, 'error': str(e)})
                
        return results 