"""
Visualization tools for the Streamlet consensus protocol.

Creates visualizations to demonstrate:
1. Consensus protocol operation across epochs
2. Byzantine behavior detection and handling  
3. Block finalization over time
4. Network topology and voting patterns
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import networkx as nx
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Tuple
import pandas as pd
import seaborn as sns

from .streamlet import StreamletConsensus
from .distributed_exchange import DistributedExchange
from .models import Block, Vote, VoteType


class ConsensusVisualizer:
    """Visualizes the operation of the Streamlet consensus protocol."""
    
    def __init__(self):
        plt.style.use('seaborn-v0_8')
        self.colors = {
            'honest': '#2E86C1',
            'byzantine': '#E74C3C', 
            'finalized': '#28B463',
            'notarized': '#F39C12',
            'proposed': '#AEB6BF'
        }
    
    def plot_consensus_timeline(self, results: Dict[str, Any], save_path: str = None) -> None:
        """Plot consensus epochs and block finalization over time."""
        epochs = results["epochs"]
        df = pd.DataFrame(epochs)
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10))
        
        # Plot 1: Block status over epochs
        epoch_nums = df['epoch']
        proposed = df['block_proposed'].astype(int)
        notarized = df['block_notarized'].astype(int)  
        finalized = df['block_finalized'].astype(int)
        
        ax1.bar(epoch_nums, proposed, alpha=0.3, label='Proposed', color=self.colors['proposed'])
        ax1.bar(epoch_nums, notarized, alpha=0.7, label='Notarized', color=self.colors['notarized'])
        ax1.bar(epoch_nums, finalized, alpha=1.0, label='Finalized', color=self.colors['finalized'])
        
        ax1.set_title('Block Status Across Epochs', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Block Status')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Leader rotation
        leaders = df['leader'].value_counts()
        ax2.bar(leaders.index, leaders.values, color=self.colors['honest'])
        ax2.set_title('Leader Selection Distribution', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Node ID')
        ax2.set_ylabel('Times Selected as Leader')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Pending transactions over time
        ax3.plot(epoch_nums, df['pending_transactions'], marker='o', color=self.colors['honest'])
        ax3.set_title('Pending Transaction Pool Size', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Epoch')
        ax3.set_ylabel('Pending Transactions')
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_network_topology(self, consensus: StreamletConsensus, save_path: str = None) -> None:
        """Plot the network topology showing honest and Byzantine nodes."""
        G = nx.Graph()
        
        # Add nodes
        for node_id, node in consensus.nodes.items():
            node_type = 'byzantine' if node.is_byzantine else 'honest'
            G.add_node(node_id, node_type=node_type)
        
        # Add edges (fully connected network for simplicity)
        nodes = list(G.nodes())
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                G.add_edge(nodes[i], nodes[j])
        
        # Create layout
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        plt.figure(figsize=(12, 8))
        
        # Draw nodes
        honest_nodes = [n for n in G.nodes() if G.nodes[n]['node_type'] == 'honest']
        byzantine_nodes = [n for n in G.nodes() if G.nodes[n]['node_type'] == 'byzantine']
        
        nx.draw_networkx_nodes(G, pos, nodelist=honest_nodes, 
                              node_color=self.colors['honest'], 
                              node_size=1000, alpha=0.8, label='Honest Nodes')
        
        nx.draw_networkx_nodes(G, pos, nodelist=byzantine_nodes,
                              node_color=self.colors['byzantine'],
                              node_size=1000, alpha=0.8, label='Byzantine Nodes')
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, alpha=0.3, edge_color='gray')
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
        
        plt.title('Consensus Network Topology', fontsize=16, fontweight='bold')
        plt.legend()
        plt.axis('off')
        
        # Add metrics
        total_nodes = len(consensus.nodes)
        byzantine_count = len([n for n in consensus.nodes.values() if n.is_byzantine])
        tolerance = consensus.consensus_state.get_byzantine_tolerance()
        
        metrics_text = f"""Network Metrics:
        Total Nodes: {total_nodes}
        Byzantine Nodes: {byzantine_count}
        Byzantine Tolerance: {tolerance}
        Safety Threshold: f < n/3"""
        
        plt.text(0.02, 0.98, metrics_text, transform=plt.gca().transAxes, 
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_voting_patterns(self, blocks: List[Dict], save_path: str = None) -> None:
        """Plot voting patterns for blocks."""
        if not blocks:
            print("No blocks to visualize voting patterns")
            return
            
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Voting participation by block
        block_votes = []
        block_labels = []
        
        for i, block in enumerate(blocks):
            votes = len(block.get('votes', []))
            block_votes.append(votes)
            block_labels.append(f"Block {i+1}\n(Epoch {block.get('epoch', 'N/A')})")
        
        bars = ax1.bar(range(len(block_votes)), block_votes, 
                      color=[self.colors['finalized'] if blocks[i].get('finalized') else 
                            self.colors['notarized'] if blocks[i].get('notarized') else 
                            self.colors['proposed'] for i in range(len(blocks))])
        
        ax1.set_title('Votes per Block', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Block')
        ax1.set_ylabel('Number of Votes')
        ax1.set_xticks(range(len(block_labels)))
        ax1.set_xticklabels(block_labels, rotation=45, ha='right')
        ax1.grid(True, alpha=0.3)
        
        # Block status distribution
        statuses = []
        for block in blocks:
            if block.get('finalized'):
                statuses.append('Finalized')
            elif block.get('notarized'):
                statuses.append('Notarized')  
            else:
                statuses.append('Proposed Only')
        
        status_counts = pd.Series(statuses).value_counts()
        colors_for_pie = [self.colors['finalized'], self.colors['notarized'], self.colors['proposed']]
        
        ax2.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%',
               colors=colors_for_pie[:len(status_counts)])
        ax2.set_title('Block Status Distribution', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_byzantine_behavior_analysis(self, results: Dict[str, Any], save_path: str = None) -> None:
        """Analyze and plot Byzantine behavior over time."""
        consensus_metrics = results["final_status"]["metrics"]
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Metrics overview
        metrics = {
            'Blocks Proposed': consensus_metrics['blocks_proposed'],
            'Blocks Notarized': consensus_metrics['blocks_notarized'], 
            'Blocks Finalized': consensus_metrics['blocks_finalized'],
            'Votes Cast': consensus_metrics['votes_cast'],
            'Byzantine Actions': consensus_metrics['byzantine_actions']
        }
        
        bars = ax1.bar(metrics.keys(), metrics.values(), 
                      color=[self.colors['honest'] if 'Byzantine' not in k else self.colors['byzantine'] 
                            for k in metrics.keys()])
        ax1.set_title('Consensus Protocol Metrics', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Count')
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)
        
        # Success rate analysis
        proposal_success = consensus_metrics['blocks_notarized'] / max(consensus_metrics['blocks_proposed'], 1)
        finalization_success = consensus_metrics['blocks_finalized'] / max(consensus_metrics['blocks_notarized'], 1)
        
        success_rates = {
            'Proposal → Notarization': proposal_success * 100,
            'Notarization → Finalization': finalization_success * 100
        }
        
        ax2.bar(success_rates.keys(), success_rates.values(), color=self.colors['finalized'])
        ax2.set_title('Success Rates', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Success Rate (%)')
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.3)
        
        # Safety analysis
        epochs = results["epochs"]
        safety_violations = sum(1 for epoch in epochs if not epoch.get('block_finalized', False))
        safety_score = (len(epochs) - safety_violations) / len(epochs) * 100
        
        ax3.pie([safety_score, 100 - safety_score], 
               labels=['Safe Epochs', 'Unsafe/Stalled Epochs'],
               colors=[self.colors['finalized'], self.colors['byzantine']],
               autopct='%1.1f%%')
        ax3.set_title(f'Safety Analysis\n({safety_score:.1f}% Safe)', fontsize=14, fontweight='bold')
        
        # Liveness analysis  
        consecutive_successes = []
        current_streak = 0
        for epoch in epochs:
            if epoch.get('block_finalized', False):
                current_streak += 1
            else:
                if current_streak > 0:
                    consecutive_successes.append(current_streak)
                current_streak = 0
        if current_streak > 0:
            consecutive_successes.append(current_streak)
        
        if consecutive_successes:
            ax4.hist(consecutive_successes, bins=min(10, len(consecutive_successes)), 
                    color=self.colors['honest'], alpha=0.7)
            ax4.set_title('Liveness: Consecutive Successful Epochs', fontsize=14, fontweight='bold')
            ax4.set_xlabel('Consecutive Successful Epochs')
            ax4.set_ylabel('Frequency')
            ax4.grid(True, alpha=0.3)
        else:
            ax4.text(0.5, 0.5, 'No successful\nconsecutive epochs', 
                    transform=ax4.transAxes, ha='center', va='center',
                    fontsize=12, color='red')
            ax4.set_title('Liveness Analysis', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def create_consensus_dashboard(self, consensus: StreamletConsensus, results: Dict[str, Any], 
                                 save_path: str = None) -> None:
        """Create a comprehensive dashboard showing all consensus metrics."""
        fig = plt.figure(figsize=(20, 16))
        
        # Create subplot layout
        gs = fig.add_gridspec(4, 3, height_ratios=[1, 1, 1, 1], width_ratios=[1, 1, 1])
        
        # Network topology (top left)
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_network_subplot(consensus, ax1)
        
        # Timeline (top center and right)
        ax2 = fig.add_subplot(gs[0, 1:])
        self._plot_timeline_subplot(results, ax2)
        
        # Metrics (second row)
        ax3 = fig.add_subplot(gs[1, 0])
        ax4 = fig.add_subplot(gs[1, 1])
        ax5 = fig.add_subplot(gs[1, 2])
        self._plot_metrics_subplots(results, ax3, ax4, ax5)
        
        # Byzantine analysis (third row)
        ax6 = fig.add_subplot(gs[2, :])
        self._plot_byzantine_analysis_subplot(results, ax6)
        
        # Summary statistics (bottom row)
        ax7 = fig.add_subplot(gs[3, :])
        self._plot_summary_subplot(consensus, results, ax7)
        
        plt.suptitle('Streamlet Consensus Protocol Dashboard', fontsize=20, fontweight='bold', y=0.98)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def _plot_network_subplot(self, consensus: StreamletConsensus, ax) -> None:
        """Helper to plot network topology in subplot."""
        G = nx.Graph()
        for node_id, node in consensus.nodes.items():
            node_type = 'byzantine' if node.is_byzantine else 'honest'
            G.add_node(node_id, node_type=node_type)
        
        # Simple circular layout for subplot
        pos = nx.circular_layout(G)
        
        honest_nodes = [n for n in G.nodes() if G.nodes[n]['node_type'] == 'honest']
        byzantine_nodes = [n for n in G.nodes() if G.nodes[n]['node_type'] == 'byzantine']
        
        nx.draw_networkx_nodes(G, pos, nodelist=honest_nodes, ax=ax,
                              node_color=self.colors['honest'], node_size=300)
        nx.draw_networkx_nodes(G, pos, nodelist=byzantine_nodes, ax=ax,
                              node_color=self.colors['byzantine'], node_size=300)
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=8)
        
        ax.set_title('Network Topology', fontweight='bold')
        ax.axis('off')
    
    def _plot_timeline_subplot(self, results: Dict[str, Any], ax) -> None:
        """Helper to plot consensus timeline in subplot."""
        epochs = results["epochs"]
        df = pd.DataFrame(epochs)
        
        epoch_nums = df['epoch']
        finalized = df['block_finalized'].astype(int)
        
        ax.plot(epoch_nums, finalized, marker='o', color=self.colors['finalized'], linewidth=2)
        ax.fill_between(epoch_nums, finalized, alpha=0.3, color=self.colors['finalized'])
        ax.set_title('Block Finalization Timeline', fontweight='bold')
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Finalized')
        ax.grid(True, alpha=0.3)
    
    def _plot_metrics_subplots(self, results: Dict[str, Any], ax1, ax2, ax3) -> None:
        """Helper to plot various metrics in subplots."""
        metrics = results["final_status"]["metrics"]
        
        # Blocks metrics
        block_metrics = ['blocks_proposed', 'blocks_notarized', 'blocks_finalized']
        values = [metrics[m] for m in block_metrics]
        labels = ['Proposed', 'Notarized', 'Finalized']
        
        ax1.bar(labels, values, color=[self.colors['proposed'], self.colors['notarized'], self.colors['finalized']])
        ax1.set_title('Block Processing', fontweight='bold')
        ax1.set_ylabel('Count')
        
        # Success rates
        prop_success = metrics['blocks_notarized'] / max(metrics['blocks_proposed'], 1) * 100
        final_success = metrics['blocks_finalized'] / max(metrics['blocks_notarized'], 1) * 100
        
        ax2.bar(['Proposal Success', 'Finalization Success'], [prop_success, final_success],
               color=self.colors['honest'])
        ax2.set_title('Success Rates', fontweight='bold')
        ax2.set_ylabel('Success Rate (%)')
        ax2.set_ylim(0, 100)
        
        # Byzantine activity
        ax3.bar(['Votes Cast', 'Byzantine Actions'], 
               [metrics['votes_cast'], metrics['byzantine_actions']],
               color=[self.colors['honest'], self.colors['byzantine']])
        ax3.set_title('Network Activity', fontweight='bold')
        ax3.set_ylabel('Count')
    
    def _plot_byzantine_analysis_subplot(self, results: Dict[str, Any], ax) -> None:
        """Helper to plot Byzantine behavior analysis."""
        epochs = results["epochs"]
        epoch_nums = [e['epoch'] for e in epochs]
        byzantine_detected = [len(e.get('byzantine_suspects', [])) for e in epochs if 'byzantine_suspects' in e]
        
        if byzantine_detected:
            ax.plot(epoch_nums[:len(byzantine_detected)], byzantine_detected, 
                   marker='s', color=self.colors['byzantine'], linewidth=2)
            ax.fill_between(epoch_nums[:len(byzantine_detected)], byzantine_detected, 
                           alpha=0.3, color=self.colors['byzantine'])
        
        ax.set_title('Byzantine Behavior Detection', fontweight='bold')
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Detected Byzantine Nodes')
        ax.grid(True, alpha=0.3)
    
    def _plot_summary_subplot(self, consensus: StreamletConsensus, results: Dict[str, Any], ax) -> None:
        """Helper to plot summary statistics."""
        ax.axis('off')
        
        # Calculate summary stats
        total_epochs = len(results["epochs"])
        successful_epochs = sum(1 for e in results["epochs"] if e.get('block_finalized', False))
        success_rate = successful_epochs / total_epochs * 100 if total_epochs > 0 else 0
        
        consensus_state = results["final_status"]["consensus_state"]
        metrics = results["final_status"]["metrics"]
        
        summary_text = f"""
        CONSENSUS PROTOCOL SUMMARY
        
        Network Configuration:
        • Total Nodes: {consensus_state['total_nodes']}
        • Byzantine Nodes: {consensus_state['byzantine_nodes']} 
        • Byzantine Tolerance: {consensus_state['byzantine_tolerance']} (f < n/3)
        
        Performance Metrics:
        • Total Epochs: {total_epochs}
        • Successful Epochs: {successful_epochs} ({success_rate:.1f}%)
        • Blocks Finalized: {metrics['blocks_finalized']}
        • Votes Cast: {metrics['votes_cast']}
        • Byzantine Actions: {metrics['byzantine_actions']}
        
        Safety & Liveness:
        • Safety: {'✓ SAFE' if success_rate > 80 else '⚠ COMPROMISED'} 
        • Liveness: {'✓ LIVE' if successful_epochs > total_epochs * 0.6 else '⚠ STALLED'}
        • Fault Tolerance: {'✓ MAINTAINED' if consensus_state['byzantine_nodes'] <= consensus_state['byzantine_tolerance'] else '❌ EXCEEDED'}
        """
        
        ax.text(0.1, 0.5, summary_text, transform=ax.transAxes, fontsize=12,
               verticalalignment='center', fontfamily='monospace',
               bbox=dict(boxstyle='round,pad=1', facecolor='lightgray', alpha=0.8)) 