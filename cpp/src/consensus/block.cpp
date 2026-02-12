#include "consensus/types.hpp"
#include <sstream>
#include <iomanip>
#include <functional>

namespace consensus {

Block::Block(int epoch,
             const std::string& parent_hash,
             const std::vector<std::string>& transactions,
             int proposer_id)
    : epoch_(epoch)
    , parent_hash_(parent_hash)
    , transactions_(transactions)
    , proposer_id_(proposer_id)
    , timestamp_(std::chrono::system_clock::now())
    , hash_(calculateHash()) {}

std::string Block::calculateHash() const {
    std::ostringstream oss;
    oss << epoch_ << ':' << parent_hash_ << ':';
    for (const auto& tx : transactions_) {
        oss << tx << '|';
    }
    oss << ':' << proposer_id_;
    auto t = std::chrono::system_clock::to_time_t(timestamp_);
    oss << ':' << t;
    std::string content = oss.str();
    size_t h = std::hash<std::string>{}(content);
    std::ostringstream hex;
    hex << std::hex << h;
    return hex.str();
}

bool Block::isValid() const {
    return !hash_.empty() && epoch_ >= 0 && proposer_id_ >= 0;
}

} // namespace consensus
