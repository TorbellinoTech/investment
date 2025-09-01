"""
Nakamoto's Blockchain Protocol Implementation

Based on Chapters 14, 16, and 17 of "Foundations of Distributed Consensus and Blockchains"
by Elaine Shi. Implements the proof-of-work based blockchain with formal security analysis.
"""

from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import random
import hashlib
import time
from threading import Lock
from decimal import Decimal


@dataclass
class PoWBlock:
    """
    A block in Nakamoto's blockchain.
    
    Format: (parent_hash, nonce, transactions, block_hash)
    """
    parent_hash: str
    nonce: int
    transactions: List[Any]
    miner_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    block_hash: str = ""
    
    def __post_init__(self):
        if not self.block_hash:
            self.block_hash = self.compute_hash()
    
    def compute_hash(self) -> str:
        """Compute the hash of this block."""
        data = {
            'parent_hash': self.parent_hash,
            'nonce': self.nonce,
            'transactions': self.transactions,
            'miner': self.miner_id,
            'timestamp': self.timestamp.isoformat()
        }
        content = json.dumps(data, sort_keys=True).encode('utf-8')
        return hashlib.sha256(content).hexdigest()
    
    def is_valid_pow(self, difficulty: int) -> bool:
        """Check if this block satisfies the proof-of-work difficulty."""
        target = 2 ** (256 - difficulty)
        return int(self.block_hash, 16) < target
    
    def get_height(self, blockchain: 'NakamotoBlockchain') -> int:
        """Get the height of this block in the blockchain."""
        if self.parent_hash == "":
            return 0
        
        parent = blockchain.get_block(self.parent_hash)
        if parent:
            return parent.get_height(blockchain) + 1
        return -1  # Invalid chain


class NakamotoBlockchain:
    """
    A blockchain following Nakamoto's protocol.
    
    Implements the longest chain rule with k-deep confirmation.
    """
    
    def __init__(self, confirmation_depth: int = 6):
        self.confirmation_depth = confirmation_depth
        
        # Genesis block
        self.genesis = PoWBlock(
            parent_hash="",
            nonce=0,
            transactions=[],
            miner_id="genesis"
        )
        
        # Storage
        self.blocks: Dict[str, PoWBlock] = {self.genesis.block_hash: self.genesis}
        self.longest_chain: List[PoWBlock] = [self.genesis]
        self.finalized_chain: List[PoWBlock] = [self.genesis]
        
        # Statistics
        self.honest_blocks: Set[str] = {self.genesis.block_hash}
        self.adversarial_blocks: Set[str] = set()
    
    def add_block(self, block: PoWBlock, is_honest: bool = True) -> bool:
        """Add a block to the blockchain."""
        # Verify parent exists
        if block.parent_hash not in self.blocks:
            return False
        
        # Add to storage
        self.blocks[block.block_hash] = block
        
        # Track honest vs adversarial
        if is_honest:
            self.honest_blocks.add(block.block_hash)
        else:
            self.adversarial_blocks.add(block.block_hash)
        
        # Update longest chain
        self._update_longest_chain()
        
        # Update finalized chain
        self._update_finalized_chain()
        
        return True
    
    def _update_longest_chain(self) -> None:
        """Update the longest chain based on current blocks."""
        # Find all chain tips (blocks with no children)
        tips = []
        for block_hash, block in self.blocks.items():
            has_child = any(
                b.parent_hash == block_hash 
                for b in self.blocks.values() 
                if b != block
            )
            if not has_child:
                tips.append(block)
        
        # Find the longest chain among all tips
        longest = None
        max_length = -1
        
        for tip in tips:
            chain = self._build_chain_to_genesis(tip)
            if len(chain) > max_length:
                max_length = len(chain)
                longest = chain
        
        if longest:
            self.longest_chain = longest
    
    def _build_chain_to_genesis(self, tip: PoWBlock) -> List[PoWBlock]:
        """Build chain from tip back to genesis."""
        chain = []
        current = tip
        
        while current:
            chain.append(current)
            if current.parent_hash == "":
                break
            current = self.blocks.get(current.parent_hash)
        
        return list(reversed(chain))
    
    def _update_finalized_chain(self) -> None:
        """Update finalized chain (longest chain minus last k blocks)."""
        if len(self.longest_chain) > self.confirmation_depth:
            self.finalized_chain = self.longest_chain[:-self.confirmation_depth]
        else:
            self.finalized_chain = [self.genesis]
    
    def get_block(self, block_hash: str) -> Optional[PoWBlock]:
        """Get block by hash."""
        return self.blocks.get(block_hash)
    
    def get_tip(self) -> PoWBlock:
        """Get the tip of the longest chain."""
        return self.longest_chain[-1]
    
    def get_chain_length(self) -> int:
        """Get the length of the longest chain."""
        return len(self.longest_chain)
    
    def get_finalized_length(self) -> int:
        """Get the length of the finalized chain."""
        return len(self.finalized_chain)
    
    def check_consistency(self, other: 'NakamotoBlockchain') -> bool:
        """
        Check consistency property with another blockchain.
        
        From Theorem 17: chainr[: −K] ⊆ chaint
        """
        # This blockchain's finalized chain should be prefix of other's longest chain
        if len(self.finalized_chain) > len(other.longest_chain):
            return False
        
        for i, block in enumerate(self.finalized_chain):
            if i >= len(other.longest_chain):
                return False
            if block.block_hash != other.longest_chain[i].block_hash:
                return False
        
        return True
    
    def get_chain_quality(self, window_size: int) -> float:
        """
        Calculate chain quality in a window.
        
        Returns fraction of honest blocks in the last window_size blocks.
        """
        if len(self.longest_chain) < window_size:
            window = self.longest_chain[1:]  # Exclude genesis
        else:
            window = self.longest_chain[-window_size:]
        
        if not window:
            return 1.0
        
        honest_count = sum(
            1 for block in window 
            if block.block_hash in self.honest_blocks
        )
        return honest_count / len(window)


class PoWMiner:
    """
    A proof-of-work miner in Nakamoto's protocol.
    
    Implements the mining algorithm with difficulty adjustment.
    """
    
    def __init__(self, miner_id: str, hash_rate: float, is_honest: bool = True):
        self.miner_id = miner_id
        self.hash_rate = hash_rate  # Hashes per second
        self.is_honest = is_honest
        
        # Mining state
        self.blockchain = NakamotoBlockchain()
        self.pending_transactions: List[Any] = []
        self.mining_block: Optional[PoWBlock] = None
        
        # Statistics
        self.blocks_mined = 0
        self.total_hash_attempts = 0
    
    def receive_block(self, block: PoWBlock) -> bool:
        """Receive a block from the network."""
        # Only honest miners immediately adopt longer chains
        if self.is_honest or len(self._chain_from_block(block)) > self.blockchain.get_chain_length():
            return self.blockchain.add_block(block, is_honest=False)
        return False
    
    def _chain_from_block(self, block: PoWBlock) -> List[PoWBlock]:
        """Build chain from a block."""
        chain = []
        current = block
        
        while current:
            chain.append(current)
            if current.parent_hash == "":
                break
            if current.parent_hash in self.blockchain.blocks:
                parent_chain = self.blockchain._build_chain_to_genesis(
                    self.blockchain.blocks[current.parent_hash]
                )
                return list(reversed(chain)) + parent_chain[:-1]
            current = None
        
        return []
    
    def add_transaction(self, transaction: Any) -> None:
        """Add a transaction to pending pool."""
        self.pending_transactions.append(transaction)
    
    def attempt_mining(self, difficulty: int, max_attempts: int = 1000) -> Optional[PoWBlock]:
        """
        Attempt to mine a block.
        
        Returns a block if successful, None otherwise.
        """
        if not self.is_honest and self._should_selfish_mine():
            return self._selfish_mining_strategy(difficulty, max_attempts)
        
        return self._honest_mining(difficulty, max_attempts)
    
    def _honest_mining(self, difficulty: int, max_attempts: int) -> Optional[PoWBlock]:
        """Honest mining strategy - always mine on longest chain."""
        parent = self.blockchain.get_tip()
        
        for attempt in range(max_attempts):
            self.total_hash_attempts += 1
            
            block = PoWBlock(
                parent_hash=parent.block_hash,
                nonce=attempt,
                transactions=self.pending_transactions.copy(),
                miner_id=self.miner_id
            )
            
            if block.is_valid_pow(difficulty):
                self.blocks_mined += 1
                self.pending_transactions.clear()
                
                # Add to our blockchain
                self.blockchain.add_block(block, is_honest=self.is_honest)
                
                return block
        
        return None
    
    def _should_selfish_mine(self) -> bool:
        """Determine if adversarial miner should use selfish mining."""
        # Simple selfish mining: withhold blocks sometimes
        return random.random() < 0.3
    
    def _selfish_mining_strategy(self, difficulty: int, max_attempts: int) -> Optional[PoWBlock]:
        """
        Selfish mining strategy.
        
        Implements the attack from Chapter 15.
        """
        # For simplicity, mine on an older block to create a fork
        if len(self.blockchain.longest_chain) > 2:
            # Mine on a block that's not the tip
            parent = self.blockchain.longest_chain[-2]
        else:
            parent = self.blockchain.get_tip()
        
        for attempt in range(max_attempts):
            self.total_hash_attempts += 1
            
            block = PoWBlock(
                parent_hash=parent.block_hash,
                nonce=attempt,
                transactions=self.pending_transactions.copy(),
                miner_id=self.miner_id
            )
            
            if block.is_valid_pow(difficulty):
                self.blocks_mined += 1
                
                # Don't immediately add to blockchain (withhold)
                # In a real implementation, this would be released strategically
                return block
        
        return None


class NakamotoProtocol:
    """
    Orchestrates Nakamoto's blockchain protocol among multiple miners.
    
    Implements the security analysis from Chapter 17.
    """
    
    def __init__(self, miner_configs: List[Dict[str, Any]], difficulty: int = 20):
        self.difficulty = difficulty
        self.network_delay = 1  # Rounds
        self.total_hash_rate = sum(config['hash_rate'] for config in miner_configs)
        
        # Create miners
        self.miners: Dict[str, PoWMiner] = {}
        self.honest_miners: Set[str] = set()
        self.adversarial_miners: Set[str] = set()
        
        for config in miner_configs:
            miner = PoWMiner(
                miner_id=config['id'],
                hash_rate=config['hash_rate'],
                is_honest=config.get('is_honest', True)
            )
            self.miners[miner.id] = miner
            
            if miner.is_honest:
                self.honest_miners.add(miner.id)
            else:
                self.adversarial_miners.add(miner.id)
        
        # Network simulation
        self.message_queue: List[Tuple[str, PoWBlock, int]] = []  # (recipient, block, delivery_round)
        self.current_round = 0
        self.blocks_by_round: Dict[int, List[PoWBlock]] = {}
        
        # Protocol parameters (from Chapter 14)
        self.alpha = self._calculate_honest_mining_rate()
        self.beta = self._calculate_adversarial_mining_rate()
        
    def _calculate_honest_mining_rate(self) -> float:
        """Calculate expected honest blocks per round (α)."""
        honest_hash_rate = sum(
            self.miners[miner_id].hash_rate 
            for miner_id in self.honest_miners
        )
        return honest_hash_rate / self.total_hash_rate
    
    def _calculate_adversarial_mining_rate(self) -> float:
        """Calculate expected adversarial blocks per round (β)."""
        adversarial_hash_rate = sum(
            self.miners[miner_id].hash_rate 
            for miner_id in self.adversarial_miners
        )
        return adversarial_hash_rate / self.total_hash_rate
    
    def run_simulation(self, rounds: int) -> Dict[str, Any]:
        """
        Run the Nakamoto protocol simulation.
        
        Returns statistics about the execution.
        """
        print(f"Running Nakamoto simulation for {rounds} rounds")
        print(f"Honest mining rate (α): {self.alpha:.3f}")
        print(f"Adversarial mining rate (β): {self.beta:.3f}")
        print(f"Honest majority: {self.alpha > self.beta}")
        
        for round_num in range(rounds):
            self.current_round = round_num
            self._execute_round()
            
            if round_num % 100 == 0:
                print(f"Completed round {round_num}")
        
        return self._collect_statistics()
    
    def _execute_round(self) -> None:
        """Execute one round of the protocol."""
        # Deliver pending messages
        self._deliver_messages()
        
        # Each miner attempts mining
        for miner_id, miner in self.miners.items():
            # Mining success probability based on hash rate
            mining_probability = miner.hash_rate / self.total_hash_rate
            
            if random.random() < mining_probability:
                block = miner.attempt_mining(self.difficulty, max_attempts=1000)
                if block:
                    # Broadcast to all other miners with delay
                    self._broadcast_block(block, miner_id)
                    
                    # Record block
                    if self.current_round not in self.blocks_by_round:
                        self.blocks_by_round[self.current_round] = []
                    self.blocks_by_round[self.current_round].append(block)
    
    def _deliver_messages(self) -> None:
        """Deliver messages scheduled for this round."""
        delivered = []
        remaining = []
        
        for recipient_id, block, delivery_round in self.message_queue:
            if delivery_round <= self.current_round:
                if recipient_id in self.miners:
                    self.miners[recipient_id].receive_block(block)
                delivered.append((recipient_id, block, delivery_round))
            else:
                remaining.append((recipient_id, block, delivery_round))
        
        self.message_queue = remaining
    
    def _broadcast_block(self, block: PoWBlock, sender_id: str) -> None:
        """Broadcast a block to all other miners with network delay."""
        delivery_round = self.current_round + self.network_delay
        
        for miner_id in self.miners:
            if miner_id != sender_id:
                self.message_queue.append((miner_id, block, delivery_round))
    
    def _collect_statistics(self) -> Dict[str, Any]:
        """Collect protocol execution statistics."""
        # Chain growth analysis
        chain_lengths = [miner.blockchain.get_chain_length() for miner in self.miners.values()]
        finalized_lengths = [miner.blockchain.get_finalized_length() for miner in self.miners.values()]
        
        # Consistency check
        honest_blockchains = [
            self.miners[miner_id].blockchain 
            for miner_id in self.honest_miners
        ]
        
        consistency_violations = 0
        for i, bc1 in enumerate(honest_blockchains):
            for j, bc2 in enumerate(honest_blockchains[i+1:], i+1):
                if not bc1.check_consistency(bc2) and not bc2.check_consistency(bc1):
                    consistency_violations += 1
        
        # Chain quality analysis
        chain_qualities = []
        for miner_id in self.honest_miners:
            quality = self.miners[miner_id].blockchain.get_chain_quality(50)
            chain_qualities.append(quality)
        
        # Mining statistics
        total_blocks_mined = sum(len(blocks) for blocks in self.blocks_by_round.values())
        honest_blocks_mined = sum(
            self.miners[miner_id].blocks_mined 
            for miner_id in self.honest_miners
        )
        
        return {
            "total_rounds": self.current_round,
            "total_miners": len(self.miners),
            "honest_miners": len(self.honest_miners),
            "adversarial_miners": len(self.adversarial_miners),
            "alpha": self.alpha,
            "beta": self.beta,
            "chain_lengths": {
                "min": min(chain_lengths),
                "max": max(chain_lengths),
                "avg": sum(chain_lengths) / len(chain_lengths)
            },
            "finalized_lengths": {
                "min": min(finalized_lengths),
                "max": max(finalized_lengths),
                "avg": sum(finalized_lengths) / len(finalized_lengths)
            },
            "consistency_violations": consistency_violations,
            "chain_quality": {
                "min": min(chain_qualities) if chain_qualities else 0,
                "max": max(chain_qualities) if chain_qualities else 0,
                "avg": sum(chain_qualities) / len(chain_qualities) if chain_qualities else 0
            },
            "total_blocks_mined": total_blocks_mined,
            "honest_blocks_mined": honest_blocks_mined,
            "adversarial_blocks_mined": total_blocks_mined - honest_blocks_mined,
            "honest_fraction": honest_blocks_mined / total_blocks_mined if total_blocks_mined > 0 else 0
        }


def create_nakamoto_simulation(honest_miners: int = 6, adversarial_miners: int = 2, 
                             base_hash_rate: float = 1.0) -> NakamotoProtocol:
    """Create a Nakamoto protocol simulation with specified parameters."""
    miner_configs = []
    
    # Create honest miners
    for i in range(honest_miners):
        miner_configs.append({
            'id': f'honest_{i}',
            'hash_rate': base_hash_rate * (0.8 + 0.4 * random.random()),
            'is_honest': True
        })
    
    # Create adversarial miners
    for i in range(adversarial_miners):
        miner_configs.append({
            'id': f'adversary_{i}',
            'hash_rate': base_hash_rate * (0.8 + 0.4 * random.random()),
            'is_honest': False
        })
    
    return NakamotoProtocol(miner_configs, difficulty=20)
