#include "consensus/streamlet_protocol.hpp"
#include <iostream>

namespace consensus {

StreamletProtocol::StreamletProtocol(int n_nodes) : n_nodes_(n_nodes) {
    nodes_.reserve(n_nodes_);
    for (int i = 0; i < n_nodes_; ++i) {
        nodes_.push_back(std::make_shared<StreamletNode>(i, n_nodes_));
    }
}

void StreamletProtocol::runEpoch(int epoch, const std::vector<std::string>& transactions) {
    int leader = nodes_.front()->getEpochLeader(epoch);
    auto& leaderNode = nodes_[leader];
    auto proposal = leaderNode->proposeBlock(epoch, transactions);
    for (int i = 0; i < n_nodes_; ++i) {
        if (i == leader) continue;
        nodes_[i]->receiveProposal(proposal, leader);
    }
}

void StreamletProtocol::runSimulation(int num_epochs, int transactions_per_epoch) {
    for (int e = 1; e <= num_epochs; ++e) {
        std::vector<std::string> txs;
        for (int t = 0; t < transactions_per_epoch; ++t) {
            txs.push_back("tx_" + std::to_string(e) + "_" + std::to_string(t));
        }
        runEpoch(e, txs);
        showEpochSummary(e);
    }
    showFinalSummary();
}

void StreamletProtocol::showEpochSummary(int epoch) const {
    std::cout << "Epoch " << epoch << ":" << std::endl;
    for (const auto& n : nodes_) {
        auto s = n->getStats();
        std::cout << "  Node " << s.node_id
                  << " blocks=" << s.total_blocks
                  << " finalized=" << s.finalized_blocks
                  << " notarized=" << s.notarized_blocks
                  << std::endl;
    }
}

void StreamletProtocol::showFinalSummary() const {
    std::cout << "Finalized blocks per node:" << std::endl;
    for (const auto& n : nodes_) {
        std::cout << "  Node " << n->getStats().node_id
                  << ": " << n->getStats().finalized_blocks << std::endl;
    }
}

} // namespace consensus
