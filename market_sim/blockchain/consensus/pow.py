"""
Proof of Work consensus mechanism for market simulation.
"""

import hashlib
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from market_sim.core.utils.time_utils import utc_now

@dataclass
class Block:
    """Represents a block in the blockchain."""
    index: int
    timestamp: datetime
    transactions: List[Dict]
    previous_hash: str
    nonce: int = 0
    hash: str = ""

    def compute_hash(self) -> str:
        """Compute the hash of the block."""
        block_string = (
            f"{self.index}{self.timestamp}{self.transactions}"
            f"{self.previous_hash}{self.nonce}"
        ).encode()
        return hashlib.sha256(block_string).hexdigest()

class ProofOfWork:
    def __init__(self, difficulty: int = 4):
        self.difficulty = difficulty
        self.chain: List[Block] = []
        self.pending_transactions: List[Dict] = []
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        """Create and mine the genesis block."""
        genesis_block = Block(
            index=0,
            timestamp=utc_now(),
            transactions=[{"data": "Genesis Block"}],
            previous_hash="0" * 64
        )
        
        # Mine the genesis block
        while True:
            genesis_block.hash = genesis_block.compute_hash()
            if genesis_block.hash.startswith("0" * self.difficulty):
                break
            genesis_block.nonce += 1
            
        self.chain.append(genesis_block)

    def mine_block(self) -> Optional[Block]:
        """Mine a new block with current pending transactions."""
        if not self.pending_transactions:
            return None

        last_block = self.chain[-1]
        new_block = Block(
            index=last_block.index + 1,
            timestamp=utc_now(),
            transactions=self.pending_transactions.copy(),
            previous_hash=last_block.hash
        )

        # Proof of Work
        while True:
            new_block.hash = new_block.compute_hash()
            if new_block.hash.startswith("0" * self.difficulty):
                break
            new_block.nonce += 1

        self.chain.append(new_block)
        self.pending_transactions = []
        return new_block

    def add_transaction(self, transaction: Dict) -> None:
        """Add a new transaction to pending transactions."""
        self.pending_transactions.append(transaction)

    def is_valid_chain(self) -> bool:
        """Validate the entire blockchain."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Verify current block's hash
            if current.hash != current.compute_hash():
                return False

            # Verify chain linkage
            if current.previous_hash != previous.hash:
                return False

            # Verify proof of work
            if not current.hash.startswith("0" * self.difficulty):
                return False

        return True

    def get_chain_metrics(self) -> Dict:
        """Get metrics about the blockchain."""
        return {
            "length": len(self.chain),
            "last_block_time": self.chain[-1].timestamp if self.chain else None,
            "total_transactions": sum(len(block.transactions) for block in self.chain),
            "pending_transactions": len(self.pending_transactions)
        }
