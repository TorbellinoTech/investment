"""
Distributed blockchain node implementation for market simulation.

Combines concepts from multiple implementations to provide:
- Socket-based communication
- Subprocess node management  
- Async operations
- REST API endpoints
"""

import socket
import subprocess
import time
import asyncio
import requests
import threading
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from flask import Flask, request, jsonify
import logging

logger = logging.getLogger(__name__)


@dataclass
class NodeConfig:
    """Configuration for a blockchain node."""
    node_id: str
    host: str = "127.0.0.1"
    port: int = 0  # 0 means auto-assign
    consensus_type: str = "raft"
    is_validator: bool = True


class DistributedNode:
    """A distributed blockchain node with networking capabilities."""
    
    def __init__(self, config: NodeConfig):
        self.config = config
        self.app = Flask(f"node_{config.node_id}")
        self.peers: List[str] = []
        self.consensus = None
        self.is_running = False
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup REST API routes."""
        
        @self.app.route('/status', methods=['GET'])
        def status():
            return jsonify({
                'node_id': self.config.node_id,
                'is_running': self.is_running,
                'peers': self.peers,
                'consensus_type': self.config.consensus_type
            })
            
        @self.app.route('/peers/register', methods=['POST'])
        def register_peers():
            data = request.get_json()
            new_peers = data.get('peers', [])
            self.peers.extend(new_peers)
            self.peers = list(set(self.peers))  # Remove duplicates
            return jsonify({'success': True, 'total_peers': len(self.peers)})
            
        @self.app.route('/transaction', methods=['POST'])
        def submit_transaction():
            data = request.get_json()
            # Process transaction through consensus
            result = self._process_transaction(data)
            return jsonify(result)
            
        @self.app.route('/consensus/sync', methods=['GET'])
        def sync_consensus():
            # Trigger consensus synchronization
            sync_result = self._sync_with_peers()
            return jsonify(sync_result)
            
    def _process_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Process a transaction through the consensus mechanism."""
        if not self.consensus:
            return {'success': False, 'error': 'No consensus mechanism initialized'}
            
        # Submit to consensus
        try:
            if hasattr(self.consensus, 'submit_command'):
                success = self.consensus.submit_command(transaction)
            else:
                success = False
                
            return {
                'success': success,
                'transaction_id': transaction.get('id', 'unknown'),
                'node_id': self.config.node_id
            }
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            return {'success': False, 'error': str(e)}
            
    def _sync_with_peers(self) -> Dict[str, Any]:
        """Synchronize state with peer nodes."""
        sync_results = []
        
        for peer in self.peers:
            try:
                response = requests.get(f"{peer}/status", timeout=2)
                if response.status_code == 200:
                    sync_results.append({
                        'peer': peer,
                        'status': 'connected',
                        'data': response.json()
                    })
            except Exception as e:
                sync_results.append({
                    'peer': peer,
                    'status': 'error',
                    'error': str(e)
                })
                
        return {
            'node_id': self.config.node_id,
            'sync_results': sync_results,
            'timestamp': time.time()
        }
        
    def start(self):
        """Start the node."""
        self.is_running = True
        
        # Initialize consensus based on type
        self._init_consensus()
        
        # Start Flask app in a thread
        thread = threading.Thread(
            target=self.app.run,
            kwargs={
                'host': self.config.host,
                'port': self.config.port,
                'debug': False,
                'use_reloader': False
            }
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"Node {self.config.node_id} started on {self.config.host}:{self.config.port}")
        
    def _init_consensus(self):
        """Initialize the consensus mechanism."""
        from market_sim.blockchain.consensus import RaftConsensus, StreamletConsensus, ProofOfWork
        
        if self.config.consensus_type == "raft":
            self.consensus = RaftConsensus(num_nodes=5)
        elif self.config.consensus_type == "streamlet":
            self.consensus = StreamletConsensus()
        elif self.config.consensus_type == "pow":
            self.consensus = ProofOfWork(difficulty=4)
        else:
            logger.warning(f"Unknown consensus type: {self.config.consensus_type}")
            

class DistributedNetwork:
    """Manages a network of distributed blockchain nodes."""
    
    def __init__(self):
        self.nodes: Dict[str, subprocess.Popen] = {}
        self.node_urls: Dict[str, str] = {}
        
    def find_free_port(self) -> int:
        """Find a free port for a node."""
        s = socket.socket()
        s.bind(('', 0))
        port = s.getsockname()[1]
        s.close()
        return port
        
    def start_node(self, node_id: str, consensus_type: str = "raft") -> str:
        """Start a new node as a subprocess."""
        port = self.find_free_port()
        node_url = f"http://127.0.0.1:{port}"
        
        # Create node startup script
        startup_script = f"""
import sys
sys.path.append('.')
from market_sim.blockchain.distributed import DistributedNode, NodeConfig

config = NodeConfig(
    node_id="{node_id}",
    port={port},
    consensus_type="{consensus_type}"
)

node = DistributedNode(config)
node.start()

# Keep running
import time
while True:
    time.sleep(1)
"""
        
        # Write script to temp file
        script_file = f"/tmp/node_{node_id}.py"
        with open(script_file, 'w') as f:
            f.write(startup_script)
            
        # Start node subprocess
        process = subprocess.Popen(['python3', script_file])
        self.nodes[node_id] = process
        self.node_urls[node_id] = node_url
        
        # Wait for node to start
        time.sleep(2)
        
        logger.info(f"Started node {node_id} on {node_url}")
        return node_url
        
    def register_peers(self):
        """Register all nodes as peers with each other."""
        all_urls = list(self.node_urls.values())
        
        for node_id, node_url in self.node_urls.items():
            # Each node gets all other nodes as peers
            peers = [url for url in all_urls if url != node_url]
            
            try:
                response = requests.post(
                    f"{node_url}/peers/register",
                    json={'peers': peers},
                    timeout=5
                )
                logger.info(f"Registered peers for node {node_id}: {response.json()}")
            except Exception as e:
                logger.error(f"Failed to register peers for node {node_id}: {e}")
                
    def stop_all(self):
        """Stop all nodes."""
        for node_id, process in self.nodes.items():
            logger.info(f"Stopping node {node_id}")
            process.terminate()
            process.wait()
            
        self.nodes.clear()
        self.node_urls.clear()
        

async def run_distributed_simulation(num_nodes: int = 4, duration: int = 60):
    """Run a distributed blockchain simulation."""
    network = DistributedNetwork()
    
    try:
        # Start nodes
        for i in range(num_nodes):
            node_id = f"node_{i}"
            consensus_type = "raft" if i % 2 == 0 else "streamlet"
            network.start_node(node_id, consensus_type)
            
        # Register peers
        network.register_peers()
        
        # Submit some test transactions
        test_transactions = [
            {"id": f"tx_{i}", "type": "trade", "amount": 100 * i}
            for i in range(10)
        ]
        
        for tx in test_transactions:
            node_url = list(network.node_urls.values())[0]
            try:
                response = requests.post(
                    f"{node_url}/transaction",
                    json=tx,
                    timeout=5
                )
                logger.info(f"Transaction result: {response.json()}")
            except Exception as e:
                logger.error(f"Failed to submit transaction: {e}")
                
            await asyncio.sleep(2)
            
        # Let simulation run
        logger.info(f"Running simulation for {duration} seconds...")
        await asyncio.sleep(duration)
        
    finally:
        # Cleanup
        network.stop_all()
        

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_distributed_simulation(num_nodes=4, duration=30)) 
