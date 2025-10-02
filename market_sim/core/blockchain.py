import time
import hashlib
from typing import List, Optional

class Block:
    def __init__(self, index:int, prev_hash:str, data:str, timestamp:Optional[float]=None, nonce:int=0):
        self.index = index
        self.prev_hash = prev_hash
        self.data = data
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        s = f"{self.index}|{self.prev_hash}|{self.data}|{self.timestamp}|{self.nonce}"
        return hashlib.sha256(s.encode()).hexdigest()

    def __repr__(self):
        return f"Block(index={self.index}, hash={self.hash[:8]}, prev={self.prev_hash[:8]}, nonce={self.nonce})"

class SimpleBlockchain:
    def __init__(self, difficulty:int=2):
        if difficulty < 1:
            raise ValueError("difficulty must be >=1")
        self.difficulty = difficulty
        self.chain:List[Block] = [self._create_genesis()]

    def _create_genesis(self) -> Block:
        return Block(0, "0"*64, "genesis", time.time(), 0)

    def latest(self) -> Block:
        return self.chain[-1]

    def proof_of_work(self, block:Block, max_nonce:int=1000000) -> Block:
        target = "0"*self.difficulty
        nonce = 0
        while nonce < max_nonce:
            block.nonce = nonce
            h = block.compute_hash()
            if h.startswith(target):
                block.hash = h
                return block
            nonce += 1
        raise RuntimeError("Failed to find proof within max_nonce")

    def add_block(self, data:str) -> Block:
        index = len(self.chain)
        prev_hash = self.latest().hash
        block = Block(index, prev_hash, data)
        mined = self.proof_of_work(block)
        self.chain.append(mined)
        return mined

    def is_valid(self) -> bool:
        target = "0"*self.difficulty
        for i in range(1, len(self.chain)):
            cur = self.chain[i]
            prev = self.chain[i-1]
            if cur.prev_hash != prev.hash:
                return False
            if not cur.hash.startswith(target):
                return False
            if cur.compute_hash() != cur.hash:
                return False
        return True

    def tamper(self, index:int, new_data:str):
        if index==0:
            raise ValueError("Cannot tamper genesis")
        self.chain[index].data = new_data
        self.chain[index].hash = self.chain[index].compute_hash()
