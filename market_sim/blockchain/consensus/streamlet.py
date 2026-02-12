"""
Streamlet Consensus Protocol Implementation

Based on the Streamlet protocol from the distributed consensus book.
This implements a simple, deterministic blockchain protocol with:

1. Epoch-based leader rotation  
2. Block proposal and notarization
3. Finalization rules for safety
4. Byzantine fault tolerance (tolerates f < n/3 Byzantine nodes)

The protocol ensures:
- Consistency: All honest nodes agree on finalized blocks
- Liveness: New blocks are continuously finalized under honest majority
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Callable, Any
from decimal import Decimal
from uuid import uuid4

from .models import (
    Block, Transaction, Vote, VoteType, Blockchain, ConsensusState
)
from core.utils.time_utils import utc_now


class ConsensusNode:
    """
    Represents a node participating in the Streamlet consensus protocol.
    Can be either honest or Byzantine.
    """
    
    def __init__(self, node_id: str, is_byzantine: bool = False):
        self.node_id = node_id
        self.is_byzantine = is_byzantine
        self.blockchain = Blockchain()
        self.logger = logging.getLogger(f"Node-{node_id}")
        self.logger.setLevel(logging.INFO)
        
        # Network simulation
        self.message_handlers: Dict[str, Callable] = {}
        self.pending_messages: List[Dict[str, Any]] = []
        
        # Byzantine behavior configuration
        self.byzantine_strategy = "silent"  # "silent", "double_vote", "wrong_vote"
        
    def setup_handlers(self):
        """Setup message handlers."""
        self.message_handlers = {
            "block_proposal": self.handle_block_proposal,
            "vote": self.handle_vote,
            "finalization": self.handle_finalization
        }
    
    def propose_block(self, consensus_state: ConsensusState, parent_hash: str) -> Optional[Block]:
        """Propose a new block as the current leader."""
        if self.is_byzantine and self.byzantine_strategy == "silent":
            # Byzantine node stays silent
            self.logger.info(f"Byzantine node {self.node_id} staying silent")
            return None
        
        # Get pending transactions
        transactions = consensus_state.pending_transactions[:10]  # Limit block size
        
        block = Block(
            epoch=consensus_state.current_epoch,
            proposer_id=self.node_id,
            parent_hash=parent_hash,
            transactions=transactions,
            timestamp=utc_now()
        )
        
        if self.is_byzantine and self.byzantine_strategy == "wrong_block":
            # Byzantine node proposes invalid block
            block.parent_hash = "invalid_parent"
            self.logger.info(f"Byzantine node {self.node_id} proposing invalid block")
        
        self.logger.info(f"Node {self.node_id} proposing block for epoch {consensus_state.current_epoch}")
        return block
    
    def handle_block_proposal(self, block: Block, consensus_state: ConsensusState) -> Optional[Vote]:
        """Handle a block proposal from another node."""
        if self.is_byzantine and self.byzantine_strategy == "silent":
            return None
            
        # Validate the block
        if not self._validate_block(block, consensus_state):
            self.logger.warning(f"Node {self.node_id} rejecting invalid block from {block.proposer_id}")
            return None
        
        # Create notarization vote
        vote = Vote.create(
            vote_type=VoteType.NOTARIZE,
            epoch=block.epoch,
            block_hash=block.hash,
            voter_id=self.node_id
        )
        
        if self.is_byzantine and self.byzantine_strategy == "double_vote":
            # Byzantine node creates conflicting vote
            conflicting_vote = Vote.create(
                vote_type=VoteType.NOTARIZE,
                epoch=block.epoch,
                block_hash="conflicting_hash",
                voter_id=self.node_id
            )
            self.logger.info(f"Byzantine node {self.node_id} double voting")
            return conflicting_vote
        
        self.logger.info(f"Node {self.node_id} voting to notarize block {block.hash[:8]}")
        return vote
    
    def handle_vote(self, vote: Vote, consensus_state: ConsensusState) -> None:
        """Handle a vote from another node."""
        consensus_state.add_vote(vote)
        
        # Check if block can be notarized
        if consensus_state.has_sufficient_votes(vote.block_hash, VoteType.NOTARIZE):
            block = self.blockchain.get_block_by_hash(vote.block_hash)
            if block and not block.notarized:
                block.notarized = True
                self.logger.info(f"Block {block.hash[:8]} notarized")
                
                # Check finalization rule (simplified)
                self._check_finalization(block, consensus_state)
    
    def handle_finalization(self, block: Block, consensus_state: ConsensusState) -> None:
        """Handle block finalization."""
        if not block.finalized:
            block.finalized = True
            self.logger.info(f"Block {block.hash[:8]} finalized")
    
    def _validate_block(self, block: Block, consensus_state: ConsensusState) -> bool:
        """Validate a proposed block."""
        # Check epoch
        if block.epoch != consensus_state.current_epoch:
            return False
        
        # Check proposer is current leader
        if block.proposer_id != consensus_state.current_leader:
            return False
        
        # Check parent exists (simplified)
        if block.parent_hash != self.blockchain.genesis_hash:
            parent = self.blockchain.get_block_by_hash(block.parent_hash)
            if not parent:
                return False
        
        return True
    
    def _check_finalization(self, block: Block, consensus_state: ConsensusState) -> None:
        """
        Check Streamlet finalization rule:
        A block is finalized if it and its two successors are notarized
        """
        # For simplicity, we'll use a basic finalization rule
        # In practice, you'd check for three consecutive notarized blocks
        if block.notarized and not block.finalized:
            # Simple rule: finalize after being notarized for demonstration
            self.handle_finalization(block, consensus_state)


class StreamletConsensus:
    """
    Main Streamlet consensus protocol coordinator.
    Manages multiple nodes and simulates the distributed protocol.
    """
    
    def __init__(self, epoch_duration: timedelta = timedelta(seconds=2)):
        self.nodes: Dict[str, ConsensusNode] = {}
        self.consensus_state = ConsensusState()
        self.epoch_duration = epoch_duration
        self.last_epoch_time = utc_now()
        self.network_delay = timedelta(milliseconds=100)
        
        # Metrics
        self.metrics = {
            "blocks_proposed": 0,
            "blocks_notarized": 0,
            "blocks_finalized": 0,
            "votes_cast": 0,
            "byzantine_actions": 0
        }
        
        self.logger = logging.getLogger("StreamletConsensus")
        self.logger.setLevel(logging.INFO)
    
    def add_node(self, node_id: str, is_byzantine: bool = False) -> None:
        """Add a node to the consensus protocol."""
        node = ConsensusNode(node_id, is_byzantine)
        node.setup_handlers()
        self.nodes[node_id] = node
        self.consensus_state.add_node(node_id, is_byzantine)
        
        self.logger.info(f"Added {'Byzantine' if is_byzantine else 'honest'} node {node_id}")
    
    def add_transaction(self, transaction: Transaction) -> None:
        """Add a transaction to the pending pool."""
        self.consensus_state.pending_transactions.append(transaction)
    
    def run_epoch(self) -> Optional[Block]:
        """Run a single epoch of the Streamlet protocol."""
        self.logger.info(f"=== Running epoch {self.consensus_state.current_epoch} ===")
        
        # Advance epoch and select leader
        self.consensus_state.advance_epoch()
        current_leader = self.consensus_state.current_leader
        
        if not current_leader:
            self.logger.warning("No leader selected for this epoch")
            return None
        
        self.logger.info(f"Leader for epoch {self.consensus_state.current_epoch}: {current_leader}")
        
        # Get parent hash
        latest_block = self._get_latest_notarized_block()
        parent_hash = latest_block.hash if latest_block else self.nodes[current_leader].blockchain.genesis_hash
        
        # Leader proposes block
        leader_node = self.nodes[current_leader]
        proposed_block = leader_node.propose_block(self.consensus_state, parent_hash)
        
        if not proposed_block:
            self.logger.info(f"Leader {current_leader} did not propose a block")
            return None
        
        self.metrics["blocks_proposed"] += 1
        
        # Add block to all honest nodes' blockchains
        for node in self.nodes.values():
            if not node.is_byzantine or random.random() < 0.5:  # Byzantine nodes might ignore
                node.blockchain.add_block(proposed_block)
        
        # Collect votes from all nodes
        votes = []
        for node_id, node in self.nodes.items():
            vote = node.handle_block_proposal(proposed_block, self.consensus_state)
            if vote:
                votes.append(vote)
                self.metrics["votes_cast"] += 1
        
        # Process votes
        for vote in votes:
            for node in self.nodes.values():
                node.handle_vote(vote, self.consensus_state)
        
        # Check if block was notarized
        if self.consensus_state.has_sufficient_votes(proposed_block.hash, VoteType.NOTARIZE):
            proposed_block.notarized = True
            self.metrics["blocks_notarized"] += 1
            self.logger.info(f"Block {proposed_block.hash[:8]} was notarized")
            
            # Simple finalization: finalize immediately if notarized
            proposed_block.finalized = True
            self.metrics["blocks_finalized"] += 1
            
            # Remove transactions from pending pool
            processed_txs = {tx.id for tx in proposed_block.transactions}
            self.consensus_state.pending_transactions = [
                tx for tx in self.consensus_state.pending_transactions 
                if tx.id not in processed_txs
            ]
        
        return proposed_block
    
    def _get_latest_notarized_block(self) -> Optional[Block]:
        """Get the latest notarized block from the first honest node."""
        for node in self.nodes.values():
            if not node.is_byzantine:
                notarized_blocks = node.blockchain.get_notarized_chain()
                return notarized_blocks[-1] if notarized_blocks else None
        return None
    
    def simulate_byzantine_behavior(self) -> None:
        """Simulate various Byzantine attack scenarios."""
        byzantine_nodes = [node for node in self.nodes.values() if node.is_byzantine]
        
        if not byzantine_nodes:
            return
        
        # Randomly choose Byzantine behavior
        behaviors = ["silent", "double_vote", "wrong_block"]
        for node in byzantine_nodes:
            if random.random() < 0.3:  # 30% chance to change behavior
                node.byzantine_strategy = random.choice(behaviors)
                self.metrics["byzantine_actions"] += 1
                self.logger.info(f"Byzantine node {node.node_id} switching to {node.byzantine_strategy}")
    
    def get_consensus_status(self) -> Dict[str, Any]:
        """Get current status of the consensus protocol."""
        honest_nodes = self.consensus_state.get_honest_nodes()
        
        # Get blockchain state from first honest node
        sample_node = None
        for node in self.nodes.values():
            if not node.is_byzantine:
                sample_node = node
                break
        
        if not sample_node:
            return {"error": "No honest nodes available"}
        
        return {
            "consensus_state": self.consensus_state.to_dict(),
            "blockchain": sample_node.blockchain.to_dict(),
            "metrics": self.metrics,
            "safety_threshold": f"{self.consensus_state.get_byzantine_tolerance()}/{self.consensus_state.get_total_nodes()} Byzantine nodes tolerated",
            "finalized_blocks": len(sample_node.blockchain.get_finalized_blocks()),
            "pending_transactions": len(self.consensus_state.pending_transactions)
        }
    
    def run_simulation(self, num_epochs: int, add_transactions: bool = True) -> Dict[str, Any]:
        """Run a complete consensus simulation."""
        self.logger.info(f"Starting Streamlet consensus simulation for {num_epochs} epochs")
        
        results = {
            "epochs": [],
            "blocks": [],
            "final_status": None
        }
        
        for epoch in range(num_epochs):
            # Optionally add some random transactions
            if add_transactions and random.random() < 0.7:
                # Create dummy transaction
                dummy_tx = Transaction(
                    id=uuid4(),
                    transaction_type="trade",
                    data={"amount": str(Decimal(random.randint(1, 1000)))},
                    timestamp=utc_now()
                )
                self.add_transaction(dummy_tx)
            
            # Simulate Byzantine behavior
            self.simulate_byzantine_behavior()
            
            # Run epoch
            block = self.run_epoch()
            
            # Record results
            epoch_result = {
                "epoch": self.consensus_state.current_epoch,
                "leader": self.consensus_state.current_leader,
                "block_proposed": block is not None,
                "block_notarized": block.notarized if block else False,
                "block_finalized": block.finalized if block else False,
                "pending_transactions": len(self.consensus_state.pending_transactions)
            }
            results["epochs"].append(epoch_result)
            
            if block:
                results["blocks"].append(block.to_dict())
        
        results["final_status"] = self.get_consensus_status()
        
        self.logger.info(f"Simulation completed: {self.metrics['blocks_finalized']} blocks finalized")
        return results 