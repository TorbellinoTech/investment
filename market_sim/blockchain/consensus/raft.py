# -- raft_simulator.py --------------------------------------------------------
"""
Raft consensus simulator with log replication + commit callbacks
(Phase 1-A: no network delay, no crash/restart yet)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Deque, Protocol
from collections import deque
import random

# --------------------------------------------------------------------------- #
# Public callback interface
# --------------------------------------------------------------------------- #
class CommitListener(Protocol):
    def on_commit(self, term: int, index: int, command: Any) -> None: ...

# --------------------------------------------------------------------------- #
# Message / log primitives
# --------------------------------------------------------------------------- #
class RPC(Enum):
    REQUEST_VOTE    = auto()
    VOTE_RESPONSE   = auto()
    APPEND_ENTRIES  = auto()
    APPEND_RESPONSE = auto()
    HEARTBEAT       = auto()

@dataclass
class Message:
    term: int
    rpc: RPC
    sender: str
    receiver: str            # "*" means broadcast
    payload: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LogEntry:
    term: int
    command: Any

class NodeState(Enum):
    FOLLOWER  = auto()
    CANDIDATE = auto()
    LEADER    = auto()

_ELECTION_TIMEOUT_MS = (150, 300)
_HEARTBEAT_INTERVAL  = 50

# --------------------------------------------------------------------------- #
# RaftConsensus - Main wrapper class
# --------------------------------------------------------------------------- #
class RaftConsensus:
    """
    Main Raft consensus wrapper for integration with market simulation.
    """
    def __init__(self, num_nodes: int = 5):
        self.cluster = RaftCluster.make_demo_cluster(num_nodes)
        self.listener = None
        
    def set_commit_listener(self, listener: CommitListener):
        """Set a listener for committed commands."""
        self.listener = listener
        self.cluster.commit_listener = listener
        
    def submit_command(self, command: Any) -> bool:
        """Submit a command to the Raft consensus."""
        leader = self.cluster.get_leader()
        if leader:
            leader.append_entry(command)
            return True
        return False
        
    def run_consensus_round(self, duration_ms: int = 1000):
        """Run consensus for specified duration."""
        elapsed = 0
        tick_size = 10  # 10ms ticks
        
        while elapsed < duration_ms:
            self.cluster.tick(tick_size)
            elapsed += tick_size
            
    def get_status(self) -> Dict[str, Any]:
        """Get current consensus status."""
        leader = self.cluster.get_leader()
        return {
            "leader": leader.id if leader else None,
            "term": max(node.current_term for node in self.cluster.nodes.values()) if self.cluster.nodes else 0,
            "committed_entries": sum(node.commit_index + 1 for node in self.cluster.nodes.values())
        }

# --------------------------------------------------------------------------- #
# RaftNode
# --------------------------------------------------------------------------- #
class RaftNode:
    def __init__(self, node_id: str, cluster: "RaftCluster") -> None:
        self.id = node_id
        self.cluster = cluster

        # Persistent
        self.current_term: int = 0
        self.voted_for: Optional[str] = None
        self.log: List[LogEntry] = []

        # Volatile
        self.commit_index = -1
        self.last_applied = -1

        # Leader-only
        self.next_index: Dict[str, int] = {}
        self.match_index: Dict[str, int] = {}

        # State & timers
        self.state = NodeState.FOLLOWER
        self.election_timeout = self._new_election_timeout()
        self.heartbeat_due = _HEARTBEAT_INTERVAL

        # Candidate votes
        self.votes_granted: set[str] = set()

    # ------------------------------------------------------------------ tick #
    def tick(self, ms: int) -> None:
        if self.state is NodeState.LEADER:
            self.heartbeat_due -= ms
            if self.heartbeat_due <= 0:
                self._broadcast_append_entries()
                self.heartbeat_due = _HEARTBEAT_INTERVAL
        else:
            self.election_timeout -= ms
            if self.election_timeout <= 0:
                self._start_election()

    # --------------------------------------------------------- message entry #
    def on_message(self, msg: Message) -> None:
        if msg.term > self.current_term:
            self._become_follower(msg.term)

        match msg.rpc:
            case RPC.REQUEST_VOTE:    self._rv_request(msg)
            case RPC.VOTE_RESPONSE:   self._rv_response(msg)
            case RPC.APPEND_ENTRIES | RPC.HEARTBEAT: self._ae_request(msg)
            case RPC.APPEND_RESPONSE: self._ae_response(msg)

    # ---------------------------------------------------- RequestVote (send) #
    def _start_election(self) -> None:
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.id
        self.votes_granted = {self.id}
        self.election_timeout = self._new_election_timeout()

        last_index = len(self.log) - 1
        last_term  = self.log[last_index].term if self.log else 0
        self.cluster.broadcast(Message(
            term=self.current_term,
            rpc=RPC.REQUEST_VOTE,
            sender=self.id,
            receiver="*",
            payload={"last_index": last_index, "last_term": last_term},
        ))

    # -------------------------------------------------- RequestVote (handle) #
    def _rv_request(self, msg: Message) -> None:
        grant = False
        if msg.term < self.current_term:
            grant = False
        else:
            up_to_date = True   # simplified (log comparison later)
            if (self.voted_for in (None, msg.sender)) and up_to_date:
                grant = True
                self.voted_for = msg.sender
                self._reset_election_timer()

        self.cluster.send(Message(
            term=self.current_term,
            rpc=RPC.VOTE_RESPONSE,
            sender=self.id,
            receiver=msg.sender,
            payload={"granted": grant},
        ))

    # ------------------------------------------------ VoteResponse (handle) #
    def _rv_response(self, msg: Message) -> None:
        if self.state is not NodeState.CANDIDATE or msg.term != self.current_term:
            return
        if msg.payload["granted"]:
            self.votes_granted.add(msg.sender)
            if len(self.votes_granted) > len(self.cluster.nodes) // 2:
                self._become_leader()

    # ----------------------------------------- AppendEntries / Heartbeat in #
    def _ae_request(self, msg: Message) -> None:
        if msg.term < self.current_term:
            # ignore old term
            return
        self._become_follower(msg.term)
        self._reset_election_timer()

        # *Simplified replication:* trust leader’s prev_index checks
        prev_index = msg.payload["prev_index"]
        if prev_index >= 0 and prev_index < len(self.log):
            if self.log[prev_index].term != msg.payload["prev_term"]:
                # conflict – delete Stale suffix
                self.log = self.log[:prev_index]
        # append new entries
        for entry in msg.payload["entries"]:
            self.log.append(entry)
        # commit index
        leader_commit = msg.payload["leader_commit"]
        if leader_commit > self.commit_index:
            self.commit_index = min(leader_commit, len(self.log)-1)
            self._apply_commits()

        # reply OK
        self.cluster.send(Message(
            term=self.current_term,
            rpc=RPC.APPEND_RESPONSE,
            sender=self.id,
            receiver=msg.sender,
            payload={"success": True, "match_index": len(self.log)-1},
        ))

    # --------------------------------------------- AppendResponse (leader) #
    def _ae_response(self, msg: Message) -> None:
        if self.state is not NodeState.LEADER or msg.term != self.current_term:
            return
        if not msg.payload["success"]:
            return  # future: decrement next_index
        follower = msg.sender
        match_idx = msg.payload["match_index"]
        self.match_index[follower] = match_idx
        self.next_index[follower]  = match_idx + 1

        # advance commit index if majority replicated
        for N in range(len(self.log)-1, self.commit_index, -1):
            if self.log[N].term != self.current_term:
                continue
            replicated = 1 + sum(1 for m in self.match_index.values() if m >= N)
            if replicated > len(self.cluster.nodes)//2:
                self.commit_index = N
                self._apply_commits()
                break

    # ---------------------------------------------------- leader transition #
    def _become_leader(self) -> None:
        self.state = NodeState.LEADER
        last_index = len(self.log)
        for peer in self.cluster.nodes:
            if peer != self.id:
                self.next_index[peer]  = last_index
                self.match_index[peer] = -1
        self.cluster.notify_new_leader(self.id, self.current_term)
        self.heartbeat_due = 0  # send immediately

    def _become_follower(self, term: int) -> None:
        self.state = NodeState.FOLLOWER
        self.current_term = term
        self.voted_for = None
        self._reset_election_timer()

    # ------------------------------------------------------ heartbeat/AE tx #
    def _broadcast_append_entries(self) -> None:
        for peer in self.cluster.nodes:
            if peer == self.id:
                continue
            prev_index = self.next_index.get(peer, 0) - 1
            prev_term  = self.log[prev_index].term if prev_index >= 0 else 0
            entries    = self.log[self.next_index.get(peer, 0):]
            self.cluster.send(Message(
                term=self.current_term,
                rpc=RPC.APPEND_ENTRIES,
                sender=self.id,
                receiver=peer,
                payload={
                    "prev_index": prev_index,
                    "prev_term": prev_term,
                    "entries": entries,
                    "leader_commit": self.commit_index,
                },
            ))

    # ----------------------------------------------------------- commits  #
    def _apply_commits(self) -> None:
        while self.last_applied < self.commit_index:
            self.last_applied += 1
            entry = self.log[self.last_applied]
            self.cluster._notify_listeners(entry, self.current_term, self.last_applied)

    # ------------------------------------------------------------ helpers #
    def _new_election_timeout(self) -> int:
        return random.randint(*_ELECTION_TIMEOUT_MS)

    def _reset_election_timer(self) -> None:
        self.election_timeout = self._new_election_timeout()

# --------------------------------------------------------------------------- #
# Cluster / transport
# --------------------------------------------------------------------------- #
class RaftCluster:
    def __init__(self) -> None:
        self.nodes: Dict[str, RaftNode] = {}
        self.msg_queue: Deque[Message] = deque()
        self.listeners: List[CommitListener] = []
        self.leader_id: Optional[str] = None
        self.term = 0
        self.current_time_ms = 0
        self.down: set[str] = set()  # crashed node IDs

    # ---- API ------------------------------------------------------------- #
    @classmethod
    def make_demo_cluster(cls, n: int) -> "RaftCluster":
        c = cls()
        for i in range(1, n+1):
            nid = f"N{i}"
            c.nodes[nid] = RaftNode(nid, c)
        return c
    
    def get_leader(self) -> Optional[RaftNode]:
        """Get the current leader node."""
        for node in self.nodes.values():
            if node.state == NodeState.LEADER:
                return node
        return None

    def tick(self, ms: int = 1) -> None:
        self.current_time_ms += ms
        while self.msg_queue:
            msg = self.msg_queue.popleft()
            targets = self.nodes.values() if msg.receiver == "*" else [self.nodes[msg.receiver]]
            for node in targets:
                if node.id in self.down:
                    continue
                node.on_message(msg)
        for node in self.nodes.values():
            if node.id not in self.down:
                node.tick(ms)

    # ---- message helpers ------------------------------------------------- #
    def send(self, msg: Message) -> None:       self.msg_queue.append(msg)
    def broadcast(self, msg: Message) -> None:  self.msg_queue.append(msg)

    # ---- leader / commit notifications ---------------------------------- #
    def notify_new_leader(self, leader_id: str, term: int) -> None:
        self.leader_id, self.term = leader_id, term

    def _notify_listeners(self, entry: LogEntry, term: int, index: int) -> None:
        for l in self.listeners:
            if callable(l):
                # plain function/lambda
                l(term, index, entry.command)
            else:
                l.on_commit(term, index, entry.command)

    def register_listener(self, listener: CommitListener) -> None:
        self.listeners.append(listener)

    # ---- client API ------------------------------------------------------ #
    def commit_command(self, command: Any) -> None:
        """Called by application code (must be on leader)."""
        if self.leader_id is None:
            raise RuntimeError("No leader yet")
        leader = self.nodes[self.leader_id]
        leader.log.append(LogEntry(term=leader.current_term, command=command))
        # trigger immediate AppendEntries
        leader._broadcast_append_entries()

    # ---------------------------- failure injection --------------------------- #
    def crash_node(self, node_id: str) -> None:
        """Simulate crash: stop delivering messages & ticking."""
        self.down.add(node_id)
        if self.leader_id == node_id:
            self.leader_id = None  # force re-election

    def restart_node(self, node_id: str) -> None:
        """Bring node back; keeps its previous state."""
        self.down.discard(node_id)

