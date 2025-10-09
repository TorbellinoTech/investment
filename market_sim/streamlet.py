"""Streamlet consensus simulation.

Leader per epoch (hash-based), notarization at ≥ 2n/3 votes,
finalization on three adjacent notarized epochs.
"""
import hashlib
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


def _rand_oracle(seed: str, epoch: int, n: int) -> int:
    """Deterministic leader selection H(epoch) → [0, n)."""
    material = f"{seed}:{epoch}".encode()
    h = hashlib.sha256(material).digest()
    return int.from_bytes(h, "big") % n


@dataclass
class Block:
    parent_hash: Optional[str]
    epoch: int
    txs: Tuple[str, ...] = field(default_factory=tuple)
    hash: str = field(init=False)

    def __post_init__(self) -> None:
        s = f"{self.parent_hash}|{self.epoch}|{','.join(self.txs)}"
        self.hash = hashlib.sha256(s.encode()).hexdigest()


@dataclass
class Node:
    node_id: int
    n: int
    seed: str
    is_corrupt: bool = False
    # local view
    chain: List[Block] = field(default_factory=list)
    notarized_hashes: Set[str] = field(default_factory=set)


class StreamletSim:
    """Small Streamlet simulator derived from the textbook.

    - Leader per epoch via a random-oracle model
    - Notarization at ≥ 2n/3 votes
    - Finalize on three adjacent notarized epochs (finalize middle)
    """

    def __init__(
        self,
        n: int,
        corrupt_fraction: float = 0.0,
        seed: Optional[str] = None,
    ) -> None:
        assert n >= 4
        self.n = n
        self.seed = seed or str(random.getrandbits(64))
        num_corrupt = int(corrupt_fraction * n)
        self.nodes: List[Node] = [
            Node(i, n, self.seed, is_corrupt=(i < num_corrupt)) for i in range(n)
        ]
        # genesis
        self.genesis = Block(None, 0, tuple())
        for node in self.nodes:
            node.chain = [self.genesis]
        self._votes: Dict[str, Set[int]] = {}
        self.finalized_prefix_hash: Optional[str] = None

    def leader(self, epoch: int) -> int:
        return _rand_oracle(self.seed, epoch, self.n)

    def _longest_chain(self) -> List[Block]:
        # tie-break: higher epoch, then lexicographic hash
        best = self.nodes[0].chain
        for node in self.nodes[1:]:
            c = node.chain
            if len(c) > len(best):
                best = c
            elif len(c) == len(best):
                if (c[-1].epoch, c[-1].hash) > (best[-1].epoch, best[-1].hash):
                    best = c
        return best

    def _broadcast_block(self, block: Block) -> None:
        for node in self.nodes:
            # adopt if extends tip or yields longer chain from known prefix
            if not node.chain:
                node.chain = [block]
                continue
            tip = node.chain[-1]
            if block.parent_hash == tip.hash:
                node.chain = node.chain + [block]
            elif len(self._locate(block.parent_hash, node.chain)) + 1 > len(node.chain):
                # switch if strictly longer from a prefix
                prefix = self._locate(block.parent_hash, node.chain)
                node.chain = prefix + [block]

    @staticmethod
    def _locate(target_hash: Optional[str], chain: List[Block]) -> List[Block]:
        if target_hash is None:
            return []
        for idx, blk in enumerate(chain):
            if blk.hash == target_hash:
                return chain[: idx + 1]
        return chain[:]  # if unknown, treat as current

    def _update_notarized(self) -> None:
        for node in self.nodes:
            for blk in node.chain:
                if self._is_notarized(blk.hash):
                    node.notarized_hashes.add(blk.hash)

    def _try_finalize(self) -> None:
        # finalize the middle block of three consecutive notarized epochs
        for node in self.nodes:
            chain = node.chain
            for i in range(2, len(chain)):
                a, b, c = chain[i - 2 : i + 1]
                if (
                    a.hash in node.notarized_hashes
                    and b.hash in node.notarized_hashes
                    and c.hash in node.notarized_hashes
                    and a.epoch + 1 == b.epoch
                    and b.epoch + 1 == c.epoch
                ):
                    self.finalized_prefix_hash = b.hash

    def run(self, epochs: int) -> None:
        for e in range(1, epochs + 1):
            leader_id = self.leader(e)
            parent = self._longest_chain()[-1]
            proposed = Block(parent.hash, e, tuple())

            # votes (corrupt nodes may abstain)
            for node in self.nodes:
                if node.is_corrupt:
                    # abstain randomly with 50% chance
                    if random.random() < 0.5:
                        continue
                self._vote(node.node_id, proposed.hash)

            # notarization and chain update
            if self._is_notarized(proposed.hash):
                self._broadcast_block(proposed)
            self._update_notarized()
            self._try_finalize()

    def consistency_holds(self) -> bool:
        # check finalized tips are prefix-compatible
        finalized_hashes = []
        for node in self.nodes:
            idx = self._finalized_index(node)
            finalized_hashes.append(node.chain[idx].hash if idx is not None else None)
        non_null = [h for h in finalized_hashes if h is not None]
        return len(set(non_null)) <= 1

    def _finalized_index(self, node: Node) -> Optional[int]:
        # rightmost occurrence matching global finalized hash
        if self.finalized_prefix_hash is None:
            return None
        for idx, blk in enumerate(node.chain):
            if blk.hash == self.finalized_prefix_hash:
                return idx
        return None

    # voting helpers (inlined NotaryBook)
    def _vote(self, node_id: int, block_hash: str) -> None:
        voters = self._votes.setdefault(block_hash, set())
        voters.add(node_id)

    def _is_notarized(self, block_hash: str) -> bool:
        voters = self._votes.get(block_hash, set())
        return len(voters) >= (2 * self.n) // 3


