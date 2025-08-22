#include "consensus/streamlet_node.hpp"
#include <algorithm>

namespace consensus {

StreamletNode::StreamletNode(int node_id, int n_nodes)
    : node_id_(node_id), n_nodes_(n_nodes) {
    createGenesisBlock();
}

void StreamletNode::createGenesisBlock() {
    auto genesis = std::make_shared<Block>(0, "GENESIS", std::vector<std::string>{"genesis"}, -1);
    blockchain_.push_back(genesis);
    block_by_hash_[genesis->getHash()] = genesis;
    notarized_blocks_.insert(genesis->getHash());
}

int StreamletNode::getEpochLeader(int epoch) const {
    return epoch % n_nodes_;
}

std::shared_ptr<Block> StreamletNode::findLongestNotarizedChain() const {
    // For simplicity, treat blockchain_ as the chain; last element is the head
    if (blockchain_.empty()) return nullptr;
    return blockchain_.back();
}

bool StreamletNode::validateBlock(const std::shared_ptr<Block>& block, int proposer_id) const {
    if (!block || !block->isValid()) return false;
    if (proposer_id != block->getProposerId()) return false;
    return true;
}

std::shared_ptr<Block> StreamletNode::proposeBlock(int epoch, const std::vector<std::string>& transactions) {
    auto head = findLongestNotarizedChain();
    std::string parent = head ? head->getHash() : std::string{"GENESIS"};
    auto block = std::make_shared<Block>(epoch, parent, transactions, node_id_);
    // self-accept for simplicity
    receiveProposal(block, node_id_);
    return block;
}

bool StreamletNode::receiveProposal(const std::shared_ptr<Block>& block, int proposer_id) {
    if (!validateBlock(block, proposer_id)) return false;
    block_by_hash_[block->getHash()] = block;
    blockchain_.push_back(block);
    castVote(block->getHash(), block->getEpoch());
    return true;
}

void StreamletNode::castVote(const std::string& block_hash, int epoch) {
    votes_by_epoch_[epoch][block_hash].insert(node_id_);
    // Notarize if >= 2f+1 with f = floor((n_nodes_-1)/3)
    int f = (n_nodes_ - 1) / 3;
    int threshold = 2 * f + 1;
    if ((int)votes_by_epoch_[epoch][block_hash].size() >= std::max(1, threshold)) {
        notarizeBlock(block_hash);
    }
    checkFinalization();
}

void StreamletNode::notarizeBlock(const std::string& block_hash) {
    notarized_blocks_.insert(block_hash);
}

void StreamletNode::checkFinalization() {
    // Simplified: finalize every notarized block that has a notarized child (2-chain)
    if (blockchain_.size() < 2) return;
    const auto& last = blockchain_.back();
    const auto& prev = blockchain_[blockchain_.size() - 2];
    if (notarized_blocks_.count(last->getHash()) && notarized_blocks_.count(prev->getHash())) {
        finalized_blocks_.push_back(prev);
    }
}

NodeStats StreamletNode::getStats() const {
    NodeStats s;
    s.node_id = node_id_;
    s.total_blocks = blockchain_.size();
    s.finalized_blocks = finalized_blocks_.size();
    s.notarized_blocks = notarized_blocks_.size();
    s.latest_epoch = blockchain_.empty() ? 0 : blockchain_.back()->getEpoch();
    return s;
}

} // namespace consensus
