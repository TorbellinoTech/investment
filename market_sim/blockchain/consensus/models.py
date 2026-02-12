"""
Blockchain models for Streamlet consensus protocol.

Based on the Streamlet protocol described in the distributed consensus book,
this implements a simple blockchain protocol with:
- Block structure with epochs and leader rotation
- Notarization through voting
- Chain finalization rules
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Set, Any
from uuid import UUID, uuid4
import hashlib
import json

from core.models.base import Order, Trade
from core.utils.time_utils import utc_now


class VoteType(Enum):
    """Types of votes in the consensus protocol."""
    PROPOSE = "propose"
    NOTARIZE = "notarize"
    FINALIZE = "finalize"


@dataclass
class Transaction:
    """Represents a transaction to be included in a block."""
    id: UUID
    transaction_type: str  # "order", "trade", "settlement"
    data: Dict[str, Any]
    timestamp: datetime
    signature: Optional[str] = None
    
    @classmethod
    def from_order(cls, order: Order) -> 'Transaction':
        """Create a transaction from an order."""
        return cls(
            id=uuid4(),
            transaction_type="order",
            data={
                "order_id": str(order.id),
                "symbol": order.symbol,
                "side": order.side.value,
                "type": order.type.value,
                "quantity": str(order.quantity),
                "price": str(order.price) if order.price else None,
                "agent_id": order.agent_id
            },
            timestamp=order.created_at
        )
    
    @classmethod
    def from_trade(cls, trade: Trade) -> 'Transaction':
        """Create a transaction from a trade."""
        return cls(
            id=uuid4(),
            transaction_type="trade",
            data={
                "trade_id": str(trade.id),
                "symbol": trade.symbol,
                "price": str(trade.price),
                "quantity": str(trade.quantity),
                "buyer_order_id": str(trade.buyer_order_id),
                "seller_order_id": str(trade.seller_order_id)
            },
            timestamp=trade.timestamp
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary for hashing."""
        return {
            "id": str(self.id),
            "type": self.transaction_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "signature": self.signature
        }
    
    def hash(self) -> str:
        """Compute hash of the transaction."""
        tx_dict = self.to_dict()
        tx_json = json.dumps(tx_dict, sort_keys=True)
        return hashlib.sha256(tx_json.encode()).hexdigest()


@dataclass
class Block:
    """Represents a block in the Streamlet blockchain."""
    epoch: int
    proposer_id: str
    parent_hash: str
    transactions: List[Transaction]
    timestamp: datetime
    nonce: int = 0
    hash: Optional[str] = None
    notarized: bool = False
    finalized: bool = False
    votes: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        """Compute hash after initialization."""
        if self.hash is None:
            self.hash = self.compute_hash()
    
    def compute_hash(self) -> str:
        """Compute the hash of this block."""
        block_dict = {
            "epoch": self.epoch,
            "proposer_id": self.proposer_id,
            "parent_hash": self.parent_hash,
            "transactions": [tx.hash() for tx in self.transactions],
            "timestamp": self.timestamp.isoformat(),
            "nonce": self.nonce
        }
        block_json = json.dumps(block_dict, sort_keys=True)
        return hashlib.sha256(block_json.encode()).hexdigest()
    
    def add_vote(self, node_id: str) -> None:
        """Add a vote from a node."""
        self.votes.add(node_id)
    
    def get_vote_count(self) -> int:
        """Get the number of votes for this block."""
        return len(self.votes)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary."""
        return {
            "epoch": self.epoch,
            "proposer_id": self.proposer_id,
            "parent_hash": self.parent_hash,
            "hash": self.hash,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "timestamp": self.timestamp.isoformat(),
            "nonce": self.nonce,
            "notarized": self.notarized,
            "finalized": self.finalized,
            "votes": list(self.votes)
        }


@dataclass
class Vote:
    """Represents a vote in the consensus protocol."""
    id: UUID
    vote_type: VoteType
    epoch: int
    block_hash: str
    voter_id: str
    timestamp: datetime
    signature: Optional[str] = None
    
    @classmethod
    def create(cls, vote_type: VoteType, epoch: int, block_hash: str, voter_id: str) -> 'Vote':
        """Create a new vote."""
        return cls(
            id=uuid4(),
            vote_type=vote_type,
            epoch=epoch,
            block_hash=block_hash,
            voter_id=voter_id,
            timestamp=utc_now()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert vote to dictionary."""
        return {
            "id": str(self.id),
            "vote_type": self.vote_type.value,
            "epoch": self.epoch,
            "block_hash": self.block_hash,
            "voter_id": self.voter_id,
            "timestamp": self.timestamp.isoformat(),
            "signature": self.signature
        }


@dataclass
class Blockchain:
    """Represents the blockchain state."""
    blocks: List[Block] = field(default_factory=list)
    genesis_hash: str = "0" * 64
    
    def add_block(self, block: Block) -> bool:
        """Add a block to the chain if it's valid."""
        if self.is_valid_block(block):
            self.blocks.append(block)
            return True
        return False
    
    def is_valid_block(self, block: Block) -> bool:
        """Check if a block is valid to add to the chain."""
        if not self.blocks:
            # Genesis block
            return block.parent_hash == self.genesis_hash
        
        # Check if parent exists
        parent_block = self.get_block_by_hash(block.parent_hash)
        if not parent_block:
            return False
        
        # Check epoch progression
        if block.epoch != parent_block.epoch + 1:
            return False
        
        return True
    
    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        """Get a block by its hash."""
        for block in self.blocks:
            if block.hash == block_hash:
                return block
        return None
    
    def get_latest_block(self) -> Optional[Block]:
        """Get the latest block in the chain."""
        return self.blocks[-1] if self.blocks else None
    
    def get_finalized_blocks(self) -> List[Block]:
        """Get all finalized blocks."""
        return [block for block in self.blocks if block.finalized]
    
    def get_notarized_chain(self) -> List[Block]:
        """Get the longest notarized chain."""
        # For simplicity, return all notarized blocks in order
        return [block for block in self.blocks if block.notarized]
    
    def get_chain_length(self) -> int:
        """Get the length of the blockchain."""
        return len(self.blocks)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert blockchain to dictionary."""
        return {
            "blocks": [block.to_dict() for block in self.blocks],
            "genesis_hash": self.genesis_hash,
            "chain_length": self.get_chain_length()
        }


@dataclass
class ConsensusState:
    """Maintains the state of the consensus protocol."""
    current_epoch: int = 0
    current_leader: Optional[str] = None
    pending_transactions: List[Transaction] = field(default_factory=list)
    votes: Dict[str, List[Vote]] = field(default_factory=dict)  # block_hash -> votes
    nodes: Set[str] = field(default_factory=set)
    byzantine_nodes: Set[str] = field(default_factory=set)
    
    def add_node(self, node_id: str, is_byzantine: bool = False) -> None:
        """Add a node to the consensus."""
        self.nodes.add(node_id)
        if is_byzantine:
            self.byzantine_nodes.add(node_id)
    
    def get_honest_nodes(self) -> Set[str]:
        """Get all honest nodes."""
        return self.nodes - self.byzantine_nodes
    
    def get_total_nodes(self) -> int:
        """Get total number of nodes."""
        return len(self.nodes)
    
    def get_byzantine_tolerance(self) -> int:
        """Get the maximum number of Byzantine nodes tolerated (f)."""
        return (len(self.nodes) - 1) // 3
    
    def get_required_votes(self) -> int:
        """Get the number of votes required for consensus (2f + 1)."""
        f = self.get_byzantine_tolerance()
        return 2 * f + 1
    
    def add_vote(self, vote: Vote) -> None:
        """Add a vote to the consensus state."""
        if vote.block_hash not in self.votes:
            self.votes[vote.block_hash] = []
        self.votes[vote.block_hash].append(vote)
    
    def get_votes_for_block(self, block_hash: str) -> List[Vote]:
        """Get all votes for a specific block."""
        return self.votes.get(block_hash, [])
    
    def has_sufficient_votes(self, block_hash: str, vote_type: VoteType) -> bool:
        """Check if a block has sufficient votes of a specific type."""
        votes = self.get_votes_for_block(block_hash)
        type_votes = [v for v in votes if v.vote_type == vote_type]
        return len(type_votes) >= self.get_required_votes()
    
    def advance_epoch(self) -> None:
        """Advance to the next epoch."""
        self.current_epoch += 1
        # Simple round-robin leader selection
        if self.nodes:
            node_list = sorted(list(self.get_honest_nodes()))
            if node_list:
                self.current_leader = node_list[self.current_epoch % len(node_list)]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert consensus state to dictionary."""
        return {
            "current_epoch": self.current_epoch,
            "current_leader": self.current_leader,
            "pending_transactions": len(self.pending_transactions),
            "total_nodes": self.get_total_nodes(),
            "byzantine_nodes": len(self.byzantine_nodes),
            "byzantine_tolerance": self.get_byzantine_tolerance(),
            "required_votes": self.get_required_votes()
        } 