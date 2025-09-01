"""
Cryptographic primitives for consensus protocols.

Implements digital signatures, collision-resistant hash functions, 
and random oracles as described in Chapter 2 of the textbook.

Note: This is a simplified implementation for educational purposes.
In production, use proper cryptographic libraries.
"""

import hashlib
import time
import hmac
import secrets
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class DigitalSignature:
    """Represents a digital signature on a message (simplified implementation)."""
    signature: bytes
    public_key: str  # Simplified as string identifier
    message: bytes
    
    def verify(self) -> bool:
        """Verify the signature (simplified implementation)."""
        # In real implementation, this would use public key cryptography
        # For demo, we derive the same key from public_key as used in signing
        private_key = hashlib.sha256(self.public_key.encode('utf-8')).digest()
        expected_sig = hmac.new(
            private_key, 
            self.message, 
            hashlib.sha256
        ).digest()
        return hmac.compare_digest(self.signature, expected_sig)


class SigningKey:
    """Digital signature key pair for a node (simplified implementation)."""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        # In real implementation, this would generate RSA/ECDSA keys
        # For demo, we use the node_id as the private key material
        self.private_key = hashlib.sha256(node_id.encode('utf-8')).digest()
        self.public_key = node_id  # Simplified public key
        
    def sign(self, message: bytes) -> DigitalSignature:
        """Sign a message and return the signature (simplified implementation)."""
        # In real implementation, this would use RSA/ECDSA signing
        # For demo, we use HMAC
        signature = hmac.new(
            self.private_key,
            message,
            hashlib.sha256
        ).digest()
        
        return DigitalSignature(
            signature=signature,
            public_key=self.public_key,
            message=message
        )
    
    def get_public_key_pem(self) -> bytes:
        """Get the public key in PEM format (simplified)."""
        return self.public_key.encode('utf-8')


class CollisionResistantHash:
    """Collision-resistant hash function (SHA-256)."""
    
    @staticmethod
    def hash(data: bytes) -> bytes:
        """Hash data using SHA-256."""
        return hashlib.sha256(data).digest()
    
    @staticmethod
    def hash_string(data: str) -> str:
        """Hash string data and return hex digest."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()


class RandomOracle:
    """
    Random oracle model for hash functions.
    
    Models H: {0,1}* -> {0,1}^λ as described in Section 2.3.
    Used for proof-of-work and leader election.
    """
    
    def __init__(self, output_length: int = 32):
        self.output_length = output_length
        self._cache: Dict[bytes, bytes] = {}
    
    def query(self, input_data: bytes) -> bytes:
        """Query the random oracle."""
        if input_data not in self._cache:
            # Generate "random" output deterministically
            self._cache[input_data] = hashlib.sha256(input_data).digest()[:self.output_length]
        return self._cache[input_data]
    
    def query_int(self, input_data: bytes, modulus: int) -> int:
        """Query the random oracle and return integer in [0, modulus)."""
        hash_output = self.query(input_data)
        return int.from_bytes(hash_output, 'big') % modulus


class ProofOfWork:
    """
    Proof-of-Work implementation using random oracle.
    
    Used for consensus mechanisms like Nakamoto's blockchain.
    """
    
    def __init__(self, difficulty: int = 4):
        self.difficulty = difficulty
        self.oracle = RandomOracle()
    
    def mine(self, block_data: bytes, max_nonce: int = 1000000) -> Optional[Tuple[int, bytes]]:
        """
        Mine a block by finding a nonce that satisfies the difficulty requirement.
        
        Returns (nonce, hash) if solution found, None otherwise.
        """
        target = (1 << (256 - self.difficulty))
        
        for nonce in range(max_nonce):
            nonce_bytes = nonce.to_bytes(8, 'big')
            candidate = block_data + nonce_bytes
            hash_output = self.oracle.query(candidate)
            hash_int = int.from_bytes(hash_output, 'big')
            
            if hash_int < target:
                return nonce, hash_output
        
        return None
    
    def verify(self, block_data: bytes, nonce: int, claimed_hash: bytes) -> bool:
        """Verify a proof-of-work solution."""
        nonce_bytes = nonce.to_bytes(8, 'big')
        candidate = block_data + nonce_bytes
        actual_hash = self.oracle.query(candidate)
        
        if actual_hash != claimed_hash:
            return False
        
        target = (1 << (256 - self.difficulty))
        hash_int = int.from_bytes(actual_hash, 'big')
        return hash_int < target


# Global random oracle for leader election
LEADER_ELECTION_ORACLE = RandomOracle()

def elect_leader(epoch: int, num_nodes: int, seed: str = "market_consensus") -> int:
    """
    Elect a leader for a given epoch using a random oracle.
    
    Implements H(epoch || seed) mod n as described in Chapter 7.
    """
    input_data = f"{epoch}:{seed}".encode('utf-8')
    return LEADER_ELECTION_ORACLE.query_int(input_data, num_nodes)
