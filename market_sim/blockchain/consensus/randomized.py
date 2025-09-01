"""
Randomized Asynchronous Consensus Protocol Implementation

Based on Chapter 13 of "Foundations of Distributed Consensus and Blockchains"
by Elaine Shi. Implements a randomized protocol that overcomes the FLP impossibility
using a common coin oracle.
"""

from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import random
import time
from threading import Lock
from market_sim.blockchain.consensus.crypto import SigningKey, DigitalSignature


class ConsensusPhase(Enum):
    """Phases of the randomized consensus protocol."""
    PRE_VOTE = "pre_vote"
    MAIN_VOTE = "main_vote"
    COIN_QUERY = "coin_query"


@dataclass
class ConsensusMessage:
    """A message in the randomized consensus protocol."""
    epoch: int
    phase: ConsensusPhase
    value: Optional[int]  # 0, 1, or None for abstain
    sender_id: str
    justification: List[Dict] = field(default_factory=list)
    signature: Optional[DigitalSignature] = None
    
    def serialize(self) -> bytes:
        """Serialize message for signing."""
        data = {
            'epoch': self.epoch,
            'phase': self.phase.value,
            'value': self.value,
            'sender': self.sender_id,
            'justification_count': len(self.justification)
        }
        return json.dumps(data, sort_keys=True).encode('utf-8')


class CommonCoinOracle:
    """
    Common Coin Oracle for randomized consensus.
    
    From Chapter 13: "Once at least 2n/3 nodes have queried CommonCoin(e),
    the oracle flips a random coin b and returns b to every CommonCoin(e) query."
    """
    
    def __init__(self, total_nodes: int):
        self.total_nodes = total_nodes
        self.required_queries = (2 * total_nodes + 2) // 3  # Ceiling of 2n/3
        self.epoch_queries: Dict[int, Set[str]] = {}
        self.epoch_results: Dict[int, int] = {}
        self.lock = Lock()
    
    def query_coin(self, epoch: int, node_id: str) -> Optional[int]:
        """
        Query the common coin for a specific epoch.
        Returns None if not enough queries received yet.
        """
        with self.lock:
            if epoch not in self.epoch_queries:
                self.epoch_queries[epoch] = set()
            
            self.epoch_queries[epoch].add(node_id)
            
            # If we have enough queries and haven't flipped yet
            if (len(self.epoch_queries[epoch]) >= self.required_queries and 
                epoch not in self.epoch_results):
                # Flip the coin (deterministic based on epoch for reproducibility)
                random.seed(epoch)
                self.epoch_results[epoch] = random.randint(0, 1)
            
            return self.epoch_results.get(epoch)


class RandomizedConsensusNode:
    """
    A node in the randomized asynchronous consensus protocol.
    
    Implements the algorithm from Chapter 13 that achieves consensus
    with probability 1 - (2/3)^E where E is the number of epochs.
    """
    
    def __init__(self, node_id: str, total_nodes: int, input_value: int):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.input_value = input_value
        self.signing_key = SigningKey(node_id)
        
        # Protocol state
        self.sticky_bit: Optional[int] = None
        self.current_epoch = 0
        self.max_epochs = 40  # For 1 - (2/3)^40 ≈ 9×10^-8 failure probability
        
        # Message storage
        self.pre_votes: Dict[int, List[ConsensusMessage]] = {}
        self.main_votes: Dict[int, List[ConsensusMessage]] = {}
        self.output_value: Optional[int] = None
        self.terminated = False
        
        # Common coin
        self.coin_oracle: Optional[CommonCoinOracle] = None
        
    def set_coin_oracle(self, oracle: CommonCoinOracle) -> None:
        """Set the common coin oracle."""
        self.coin_oracle = oracle
    
    def start_consensus(self) -> List[ConsensusMessage]:
        """
        Start the consensus protocol by sending epoch-0 pre-vote.
        
        From Chapter 13: "Initially, every node i does the following: 
        send an epoch-0 pre-vote of the form {pre, 0, b}pk^{-1}_i to everyone"
        """
        if self.current_epoch != 0:
            raise ValueError("Consensus already started")
        
        message = ConsensusMessage(
            epoch=0,
            phase=ConsensusPhase.PRE_VOTE,
            value=self.input_value,
            sender_id=self.node_id
        )
        message.signature = self.signing_key.sign(message.serialize())
        
        self.current_epoch = 1
        return [message]
    
    def process_message(self, message: ConsensusMessage) -> List[ConsensusMessage]:
        """
        Process an incoming consensus message.
        
        Returns list of messages to send in response.
        """
        if self.terminated:
            return []
        
        if not self._verify_message(message):
            return []
        
        # Store the message
        if message.phase == ConsensusPhase.PRE_VOTE:
            if message.epoch not in self.pre_votes:
                self.pre_votes[message.epoch] = []
            self.pre_votes[message.epoch].append(message)
        elif message.phase == ConsensusPhase.MAIN_VOTE:
            if message.epoch not in self.main_votes:
                self.main_votes[message.epoch] = []
            self.main_votes[message.epoch].append(message)
        
        # Check if we can advance the protocol
        return self._try_advance_protocol()
    
    def _verify_message(self, message: ConsensusMessage) -> bool:
        """Verify message signature and format."""
        if message.signature is None:
            return False
        
        return message.signature.verify()
    
    def _try_advance_protocol(self) -> List[ConsensusMessage]:
        """Try to advance the protocol based on current state."""
        messages_to_send = []
        
        # Process each epoch
        for epoch in range(max(1, self.current_epoch - 1), self.current_epoch + 1):
            if epoch > self.max_epochs:
                break
            
            # Try to send pre-vote
            pre_vote = self._try_send_pre_vote(epoch)
            if pre_vote:
                messages_to_send.extend(pre_vote)
            
            # Try to send main-vote
            main_vote = self._try_send_main_vote(epoch)
            if main_vote:
                messages_to_send.extend(main_vote)
            
            # Check for termination
            if self._check_termination(epoch):
                break
        
        return messages_to_send
    
    def _try_send_pre_vote(self, epoch: int) -> List[ConsensusMessage]:
        """Try to send a pre-vote for the given epoch."""
        if epoch == 1:
            return self._handle_epoch_1_pre_vote()
        else:
            return self._handle_later_epoch_pre_vote(epoch)
    
    def _handle_epoch_1_pre_vote(self) -> List[ConsensusMessage]:
        """Handle pre-vote for epoch 1."""
        # Wait for 2n/3 epoch-0 pre-votes
        epoch_0_votes = self.pre_votes.get(0, [])
        required_votes = (2 * self.total_nodes + 2) // 3
        
        if len(epoch_0_votes) < required_votes:
            return []
        
        # Find most common bit
        bit_counts = {0: 0, 1: 0}
        for vote in epoch_0_votes:
            if vote.value in bit_counts:
                bit_counts[vote.value] += 1
        
        # Choose bit with more than n/3 votes
        chosen_bit = None
        for bit, count in bit_counts.items():
            if count > self.total_nodes // 3:
                chosen_bit = bit
                break
        
        if chosen_bit is not None:
            message = ConsensusMessage(
                epoch=1,
                phase=ConsensusPhase.PRE_VOTE,
                value=chosen_bit,
                sender_id=self.node_id,
                justification=[{'type': 'epoch_0_prevotes', 'count': len(epoch_0_votes)}]
            )
            message.signature = self.signing_key.sign(message.serialize())
            return [message]
        
        return []
    
    def _handle_later_epoch_pre_vote(self, epoch: int) -> List[ConsensusMessage]:
        """Handle pre-vote for epochs > 1."""
        prev_epoch = epoch - 1
        prev_main_votes = self.main_votes.get(prev_epoch, [])
        required_votes = (2 * self.total_nodes + 2) // 3
        
        if len(prev_main_votes) < required_votes:
            return []
        
        # Get common coin
        if self.coin_oracle is None:
            return []
        
        coin_result = self.coin_oracle.query_coin(epoch, self.node_id)
        if coin_result is None:
            return []
        
        # Check if there's a main-vote for a bit
        bit_votes = {0: 0, 1: 0, None: 0}  # None represents abstain
        for vote in prev_main_votes:
            if vote.value in bit_votes:
                bit_votes[vote.value] += 1
        
        chosen_bit = coin_result  # Default to coin result
        
        # If there's a main-vote for a specific bit, use that
        for bit in [0, 1]:
            if bit_votes[bit] > 0:
                chosen_bit = bit
                break
        
        message = ConsensusMessage(
            epoch=epoch,
            phase=ConsensusPhase.PRE_VOTE,
            value=chosen_bit,
            sender_id=self.node_id,
            justification=[{'type': 'prev_main_votes', 'count': len(prev_main_votes)}]
        )
        message.signature = self.signing_key.sign(message.serialize())
        return [message]
    
    def _try_send_main_vote(self, epoch: int) -> List[ConsensusMessage]:
        """Try to send a main-vote for the given epoch."""
        pre_votes = self.pre_votes.get(epoch, [])
        required_votes = (2 * self.total_nodes + 2) // 3
        
        if len(pre_votes) < required_votes:
            return []
        
        # Count pre-votes
        bit_counts = {0: 0, 1: 0}
        for vote in pre_votes:
            if vote.value in bit_counts:
                bit_counts[vote.value] += 1
        
        # Determine main-vote value
        if bit_counts[0] == len(pre_votes):
            vote_value = 0
        elif bit_counts[1] == len(pre_votes):
            vote_value = 1
        else:
            vote_value = None  # Abstain
        
        message = ConsensusMessage(
            epoch=epoch,
            phase=ConsensusPhase.MAIN_VOTE,
            value=vote_value,
            sender_id=self.node_id,
            justification=[{'type': 'prevotes', 'count': len(pre_votes)}]
        )
        message.signature = self.signing_key.sign(message.serialize())
        return [message]
    
    def _check_termination(self, epoch: int) -> bool:
        """Check if we can terminate with an output."""
        main_votes = self.main_votes.get(epoch, [])
        required_votes = (2 * self.total_nodes + 2) // 3
        
        if len(main_votes) < required_votes:
            return False
        
        # Count main-votes for each value
        bit_counts = {0: 0, 1: 0, None: 0}
        for vote in main_votes:
            if vote.value in bit_counts:
                bit_counts[vote.value] += 1
        
        # Check if we have 2n/3 votes for the same bit
        for bit in [0, 1]:
            if bit_counts[bit] >= required_votes:
                self.output_value = bit
                self.terminated = True
                return True
        
        return False
    
    def get_output(self) -> Optional[int]:
        """Get the consensus output if available."""
        return self.output_value


class RandomizedConsensusProtocol:
    """
    Orchestrates randomized asynchronous consensus among multiple nodes.
    
    Implements the full protocol from Chapter 13 with common coin oracle.
    """
    
    def __init__(self, node_ids: List[str], input_values: Dict[str, int]):
        self.node_ids = node_ids
        self.total_nodes = len(node_ids)
        self.input_values = input_values
        
        # Validate inputs
        for value in input_values.values():
            if value not in [0, 1]:
                raise ValueError("Input values must be 0 or 1")
        
        # Create nodes
        self.nodes: Dict[str, RandomizedConsensusNode] = {}
        for node_id in node_ids:
            input_val = input_values.get(node_id, 0)
            self.nodes[node_id] = RandomizedConsensusNode(
                node_id, self.total_nodes, input_val
            )
        
        # Create common coin oracle
        self.coin_oracle = CommonCoinOracle(self.total_nodes)
        for node in self.nodes.values():
            node.set_coin_oracle(self.coin_oracle)
        
        # Network simulation
        self.message_queue: List[Tuple[str, ConsensusMessage]] = []
        self.round_count = 0
        self.max_rounds = 1000  # Safety limit
    
    def run_consensus(self) -> Dict[str, int]:
        """
        Run the randomized consensus protocol.
        
        Returns the outputs of all nodes.
        """
        print(f"Starting randomized consensus with {self.total_nodes} nodes")
        print(f"Input values: {self.input_values}")
        
        # Start consensus on all nodes
        for node_id, node in self.nodes.items():
            initial_messages = node.start_consensus()
            for message in initial_messages:
                # Broadcast to all other nodes
                for recipient_id in self.node_ids:
                    if recipient_id != node_id:
                        self.message_queue.append((recipient_id, message))
        
        print(f"Initial messages sent, queue size: {len(self.message_queue)}")
        
        # Run message processing rounds
        while self.message_queue and self.round_count < self.max_rounds:
            self._process_round()
            self.round_count += 1
            
            # Check if all nodes have terminated
            if all(node.terminated for node in self.nodes.values()):
                print(f"All nodes terminated after {self.round_count} rounds")
                break
        
        # Collect outputs
        outputs = {}
        for node_id, node in self.nodes.items():
            outputs[node_id] = node.get_output()
        
        return outputs
    
    def _process_round(self) -> None:
        """Process one round of message delivery."""
        current_messages = self.message_queue.copy()
        self.message_queue.clear()
        
        for recipient_id, message in current_messages:
            if recipient_id in self.nodes:
                node = self.nodes[recipient_id]
                responses = node.process_message(message)
                
                # Broadcast responses
                for response in responses:
                    for node_id in self.node_ids:
                        if node_id != recipient_id:
                            self.message_queue.append((node_id, response))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get protocol execution statistics."""
        outputs = [node.get_output() for node in self.nodes.values()]
        terminated_count = sum(1 for node in self.nodes.values() if node.terminated)
        
        # Check validity
        all_same_input = len(set(self.input_values.values())) == 1
        validity_satisfied = True
        if all_same_input:
            expected_output = list(self.input_values.values())[0]
            validity_satisfied = all(output == expected_output for output in outputs if output is not None)
        
        # Check consistency
        non_none_outputs = [output for output in outputs if output is not None]
        consistency_satisfied = len(set(non_none_outputs)) <= 1
        
        return {
            "round_count": self.round_count,
            "terminated_nodes": terminated_count,
            "total_nodes": self.total_nodes,
            "outputs": {node_id: node.get_output() for node_id, node in self.nodes.items()},
            "consistency_satisfied": consistency_satisfied,
            "validity_satisfied": validity_satisfied,
            "common_output": non_none_outputs[0] if non_none_outputs else None,
            "coin_queries_per_epoch": {
                epoch: len(queries) 
                for epoch, queries in self.coin_oracle.epoch_queries.items()
            }
        }


class RandomizedConsensus:
    """
    Wrapper class for Randomized Consensus protocol integration.
    """
    def __init__(self, num_nodes: int = 7, byzantine_nodes: int = 2):
        self.protocol = RandomizedConsensusProtocol(num_nodes, byzantine_nodes)
        
    def run_consensus(self, value: int = None) -> Dict[str, int]:
        """Run the randomized consensus protocol."""
        if value is not None:
            # Set initial value for nodes
            for node in self.protocol.nodes.values():
                node.value = value
                
        return self.protocol.run_consensus()
        
    def get_consensus_value(self) -> Optional[int]:
        """Get the consensus value if agreement was reached."""
        decisions = set(node.decision for node in self.protocol.nodes.values() 
                       if node.decision is not None)
        return decisions.pop() if len(decisions) == 1 else None
