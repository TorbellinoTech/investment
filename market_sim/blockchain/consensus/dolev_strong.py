from typing import List, Set, Dict, Optional


class Message:
    def __init__(self, bit: int, signatures: List[int]):
        self.bit = bit
        self.signatures = signatures

    def __repr__(self):
        return f"<Message bit={self.bit} sigs={self.signatures}>"

    def has_signature(self, node_id: int) -> bool:
        return node_id in self.signatures

    def add_signature(self, node_id: int) -> 'Message':
        # Return a new message with the additional signature
        return Message(self.bit, self.signatures + [node_id])


class Node:
    def __init__(self, node_id: int, is_corrupt=False):
        self.node_id = node_id
        self.is_corrupt = is_corrupt
        self.extracted_bits: Set[int] = set()
        self.inbox: List[Message] = []

    def receive(self, message: Message):
        # Accept and store the bit if it's new
        if message.bit not in self.extracted_bits:
            self.extracted_bits.add(message.bit)
            self.inbox.append(message)

    def send_messages(self) -> List[Message]:
        # Honest nodes forward signed messages
        if self.is_corrupt:
            return []  # corrupt nodes don't forward messages (basic model)

        outgoing = []
        for msg in self.inbox:
            if not msg.has_signature(self.node_id):
                signed_msg = msg.add_signature(self.node_id)
                outgoing.append(signed_msg)

        self.inbox.clear()
        return outgoing


class DolevStrongSimulator:
    def __init__(self, num_nodes: int, num_corrupt: int, sender_input: int):
        self.num_nodes = num_nodes
        self.num_corrupt = num_corrupt
        self.sender_input = sender_input
        self.nodes = self._create_nodes()
        self.rounds = num_corrupt + 1  # f + 1 rounds required

    def _create_nodes(self) -> List[Node]:
        # First `f` nodes are corrupt
        nodes = []
        for i in range(self.num_nodes):
            is_corrupt = i < self.num_corrupt
            nodes.append(Node(node_id=i, is_corrupt=is_corrupt))
        return nodes

    def run_protocol(self) -> None:
        # Round 0: sender sends ⟨b⟩₁ to everyone
        sender = self.nodes[0]
        initial_msg = Message(bit=self.sender_input, signatures=[sender.node_id])
        for node in self.nodes[1:]:
            node.receive(initial_msg)

        # Rounds 1 to f+1: message forwarding
        for r in range(1, self.rounds + 1):
            all_messages = []

            for node in self.nodes:
                outgoing = node.send_messages()
                all_messages.extend(outgoing)

            for msg in all_messages:
                for node in self.nodes:
                    # Forward to all nodes that haven't signed this message
                    if node.node_id not in msg.signatures:
                        node.receive(msg)

        # Final Output
        for node in self.nodes:
            if not node.is_corrupt:
                print(f"\nNode {node.node_id} final extracted bits: {node.extracted_bits}")
                if len(node.extracted_bits) == 1:
                    print(f"Node {node.node_id} OUTPUT: {list(node.extracted_bits)[0]}")
                else:
                    print(f"Node {node.node_id} OUTPUT: 0 (default due to multiple bits)")


class DolevStrongConsensus:
    """
    Wrapper class for Dolev-Strong Byzantine Agreement protocol.
    """
    def __init__(self, num_nodes: int = 7, num_corrupt: int = 2):
        self.num_nodes = num_nodes
        self.num_corrupt = num_corrupt
        self.simulator = None
        
    def run_agreement(self, sender_input: int) -> Dict[int, Set[int]]:
        """Run the Dolev-Strong protocol and return results."""
        self.simulator = DolevStrongSimulator(
            self.num_nodes, 
            self.num_corrupt, 
            sender_input
        )
        self.simulator.run_protocol()
        
        # Collect results
        results = {}
        for node in self.simulator.nodes:
            if not node.is_corrupt:
                results[node.node_id] = node.extracted_bits
                
        return results
        
    def get_consensus_value(self) -> Optional[int]:
        """Get the consensus value if agreement was reached."""
        if not self.simulator:
            return None
            
        consensus_values = set()
        for node in self.simulator.nodes:
            if not node.is_corrupt and len(node.extracted_bits) == 1:
                consensus_values.add(list(node.extracted_bits)[0])
                
        return consensus_values.pop() if len(consensus_values) == 1 else None
