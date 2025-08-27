from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib
import random


@dataclass(frozen=True)
class Block:
    index: int
    parent_hash: Optional[str]
    proposer_id: str
    timestamp: float
    payload: str
    hash: str

    @staticmethod
    def compute_hash(index: int, parent_hash: Optional[str], proposer_id: str, timestamp: float, payload: str) -> str:
        h = hashlib.sha256()
        h.update(str(index).encode())
        h.update((parent_hash or "GENESIS").encode())
        h.update(proposer_id.encode())
        h.update(str(timestamp).encode())
        h.update(payload.encode())
        return h.hexdigest()

    @classmethod
    def create_genesis(cls) -> Block:
        ts = 0.0
        payload = "genesis"
        digest = cls.compute_hash(0, None, "GENESIS", ts, payload)
        return cls(index=0, parent_hash=None, proposer_id="GENESIS", timestamp=ts, payload=payload, hash=digest)

    @classmethod
    def create_child(cls, parent: Block, proposer_id: str, timestamp: float, payload: str) -> Block:
        index = parent.index + 1
        digest = cls.compute_hash(index, parent.hash, proposer_id, timestamp, payload)
        return cls(index=index, parent_hash=parent.hash, proposer_id=proposer_id, timestamp=timestamp, payload=payload, hash=digest)


class ChainStore:
    def __init__(self) -> None:
        self.hash_to_block: Dict[str, Block] = {}
        self.children: Dict[str, List[str]] = {}
        self.genesis = Block.create_genesis()
        self.add_block(self.genesis)

    def add_block(self, block: Block) -> None:
        if block.hash in self.hash_to_block:
            return
        self.hash_to_block[block.hash] = block
        if block.parent_hash is not None:
            self.children.setdefault(block.parent_hash, []).append(block.hash)

    def has_block(self, block_hash: str) -> bool:
        return block_hash in self.hash_to_block

    def get_block(self, block_hash: str) -> Optional[Block]:
        return self.hash_to_block.get(block_hash)

    def find_longest_chain_tip(self) -> Block:
        # Simple DFS from genesis to find the deepest tip; tie-breaker = lowest hash (deterministic)
        stack: List[Tuple[Block, int]] = [(self.genesis, 0)]
        best_depth = 0
        best_tip = self.genesis
        while stack:
            block, depth = stack.pop()
            if depth > best_depth or (depth == best_depth and block.hash < best_tip.hash):
                best_depth = depth
                best_tip = block
            for child_hash in self.children.get(block.hash, []):
                child = self.hash_to_block[child_hash]
                stack.append((child, depth + 1))
        return best_tip

    def get_chain_to(self, tip: Block) -> List[Block]:
        chain: List[Block] = []
        cur: Optional[Block] = tip
        while cur is not None:
            chain.append(cur)
            cur = self.hash_to_block.get(cur.parent_hash) if cur.parent_hash else None
        chain.reverse()
        return chain


class Node:
    def __init__(self, node_id: str, rng: random.Random) -> None:
        self.node_id = node_id
        self.store = ChainStore()
        self.head: Block = self.store.genesis
        self.rng = rng

    def on_block(self, block: Block) -> None:
        # Basic parent-availability rule: only add if parent known (or it's genesis)
        if block.parent_hash is None or self.store.has_block(block.parent_hash):
            self.store.add_block(block)
            # Recompute head if this extends or ties best chain
            current_best = self.store.find_longest_chain_tip()
            self.head = current_best

    def produce_block(self, timestamp: float, payload: str = "txs") -> Block:
        parent = self.head
        block = Block.create_child(parent=parent, proposer_id=self.node_id, timestamp=timestamp, payload=payload)
        # Add locally immediately
        self.on_block(block)
        return block


@dataclass
class NetworkParams:
    num_nodes: int = 5
    block_probability_per_tick: float = 0.6  # probability that exactly one leader is chosen
    delay_probability: float = 0.2           # per message, probability to delay by one tick
    seed: int = 42


class NakamotoNetwork:
    def __init__(self, params: NetworkParams) -> None:
        self.params = params
        self.rng = random.Random(params.seed)
        self.nodes: List[Node] = [Node(f"N{i}", self.rng) for i in range(params.num_nodes)]
        # message_queue[tick] = list of (recipient_index, Block)
        self.message_queue: Dict[int, List[Tuple[int, Block]]] = {}
        self.tick: int = 0

    def step(self) -> None:
        # Deliver queued messages for this tick
        deliveries = self.message_queue.pop(self.tick, [])
        for recipient_idx, block in deliveries:
            self.nodes[recipient_idx].on_block(block)

        # Leader election and block production (at most one block per tick on average)
        if self.rng.random() < self.params.block_probability_per_tick:
            leader_idx = self.rng.randrange(len(self.nodes))
            leader = self.nodes[leader_idx]
            new_block = leader.produce_block(timestamp=float(self.tick))

            # Gossip to all other nodes with potential one-tick delay
            for i, node in enumerate(self.nodes):
                if i == leader_idx:
                    continue
                deliver_at = self.tick + (1 if self.rng.random() < self.params.delay_probability else 0)
                self.message_queue.setdefault(deliver_at, []).append((i, new_block))

        self.tick += 1

    def run(self, num_ticks: int) -> None:
        for _ in range(num_ticks):
            self.step()

    def heads(self) -> List[str]:
        return [n.head.hash for n in self.nodes]

    def common_prefix_length(self) -> int:
        # Compute common prefix length among all node heads
        chains: List[List[Block]] = [n.store.get_chain_to(n.head) for n in self.nodes]
        min_len = min(len(c) for c in chains)
        k = 0
        for i in range(min_len):
            h0 = chains[0][i].hash
            if all(chain[i].hash == h0 for chain in chains):
                k += 1
            else:
                break
        return k

    def finalized_depth(self) -> int:
        # In longest-chain style with simple temporary forks, assume confirmations = depth of common prefix - 1 (discount genesis)
        return max(0, self.common_prefix_length() - 1) 