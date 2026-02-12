#pragma once

#include <string>
#include <vector>
#include <chrono>
#include <memory>
#include <unordered_map>
#include <unordered_set>

namespace consensus {

class Block;
class Message;
class StreamletNode;
class StreamletProtocol;

enum class MessageType { PROPOSE, VOTE, NOTARIZE };

class Block {
public:
    Block(int epoch,
          const std::string& parent_hash,
          const std::vector<std::string>& transactions,
          int proposer_id);

    int getEpoch() const { return epoch_; }
    const std::string& getParentHash() const { return parent_hash_; }
    const std::vector<std::string>& getTransactions() const { return transactions_; }
    int getProposerId() const { return proposer_id_; }
    const std::string& getHash() const { return hash_; }
    std::chrono::system_clock::time_point getTimestamp() const { return timestamp_; }

    bool isValid() const;

private:
    std::string calculateHash() const;

    int epoch_;
    std::string parent_hash_;
    std::vector<std::string> transactions_;
    int proposer_id_;
    std::string hash_;
    std::chrono::system_clock::time_point timestamp_;
};

class Message {
public:
    Message(MessageType type, int sender_id, int epoch, const std::string& block_hash);

    MessageType getType() const { return type_; }
    int getSenderId() const { return sender_id_; }
    int getEpoch() const { return epoch_; }
    const std::string& getBlockHash() const { return block_hash_; }
    std::chrono::system_clock::time_point getTimestamp() const { return timestamp_; }

    void setBlock(std::shared_ptr<Block> block) { block_ = block; }
    std::shared_ptr<Block> getBlock() const { return block_; }

private:
    MessageType type_;
    int sender_id_;
    int epoch_;
    std::string block_hash_;
    std::shared_ptr<Block> block_;
    std::chrono::system_clock::time_point timestamp_;
};

struct NodeStats {
    int node_id{0};
    size_t total_blocks{0};
    size_t finalized_blocks{0};
    size_t notarized_blocks{0};
    int latest_epoch{0};
};

} // namespace consensus
