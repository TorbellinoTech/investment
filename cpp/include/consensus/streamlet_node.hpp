#pragma once

#include "types.hpp"
#include <memory>
#include <vector>
#include <unordered_map>
#include <unordered_set>

namespace consensus {

class StreamletNode {
public:
    StreamletNode(int node_id, int n_nodes);

    std::shared_ptr<Block> proposeBlock(int epoch, const std::vector<std::string>& transactions);
    bool receiveProposal(const std::shared_ptr<Block>& block, int proposer_id);

    int getNodeId() const { return node_id_; }
    int getTotalNodes() const { return n_nodes_; }
    const std::vector<std::shared_ptr<Block>>& getBlockchain() const { return blockchain_; }
    const std::vector<std::shared_ptr<Block>>& getFinalizedBlocks() const { return finalized_blocks_; }
    const std::unordered_set<std::string>& getNotarizedBlocks() const { return notarized_blocks_; }

    NodeStats getStats() const;
    int getEpochLeader(int epoch) const;

private:
    void createGenesisBlock();
    std::shared_ptr<Block> findLongestNotarizedChain() const;
    bool validateBlock(const std::shared_ptr<Block>& block, int proposer_id) const;
    void castVote(const std::string& block_hash, int epoch);
    void notarizeBlock(const std::string& block_hash);
    void checkFinalization();

    int node_id_;
    int n_nodes_;
    std::vector<std::shared_ptr<Block>> blockchain_;
    std::unordered_map<std::string, std::shared_ptr<Block>> block_by_hash_;
    std::vector<std::shared_ptr<Block>> finalized_blocks_;

    std::unordered_map<int, std::unordered_map<std::string, std::unordered_set<int>>> votes_by_epoch_;
    std::unordered_set<std::string> notarized_blocks_;
};

} // namespace consensus
