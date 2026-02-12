import hashlib
import time
import json
from typing import List, Dict, Any, Optional

class Block:
    def __init__(self, index: int, transactions: List[Dict[str, Any]], prev_hash: str):
        self.index = index
        self.timestamp = time.time()
        self.transactions = list(transactions)
        self.prev_hash = prev_hash
        self.nonce = 0
        self.hash = self.compute_hash()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "prev_hash": self.prev_hash,
            "nonce": self.nonce
        }

    def compute_hash(self) -> str:
        block_string = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def __repr__(self):
        return f"<Block index={self.index} hash={self.hash[:8]} prev={self.prev_hash[:8]}>"

class Blockchain:
    def __init__(self, difficulty: int = 3):
        self.difficulty = difficulty
        self.chain: List[Block] = [self.create_genesis_block()]
        self.pending_tx: List[Dict[str, Any]] = []

    def create_genesis_block(self) -> Block:
        genesis = Block(0, [{"genesis": True}], "0")
        genesis.hash = genesis.compute_hash()
        return genesis

    def add_transaction(self, tx: Dict[str, Any]) -> None:
        self.pending_tx.append(tx)

    def mine_pending_transactions(self) -> Optional[Block]:
        if not self.pending_tx:
            return None
        prev_hash = self.chain[-1].hash
        new_block = Block(len(self.chain), self.pending_tx, prev_hash)
        self.proof_of_work(new_block)
        self.chain.append(new_block)
        self.pending_tx = []
        return new_block

    def proof_of_work(self, block: Block) -> str:
        target = "0" * self.difficulty
        while not block.hash.startswith(target):
            block.nonce += 1
            block.hash = block.compute_hash()
        return block.hash

    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]
            if curr.hash != curr.compute_hash():
                return False
            if curr.prev_hash != prev.hash:
                return False
            if not curr.hash.startswith("0" * self.difficulty):
                return False
        return True

if __name__ == "__main__":
    bc = Blockchain(difficulty=2)
    bc.add_transaction({"buyer": "Alice", "seller": "Bob", "asset": "AAPL", "amount": 5})
    print("Mining block...")
    block = bc.mine_pending_transactions()
    print("Mined:", block)
    print("Chain valid?", bc.is_chain_valid())
