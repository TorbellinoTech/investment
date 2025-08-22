#include "consensus/types.hpp"

namespace consensus {

Message::Message(MessageType type, int sender_id, int epoch, const std::string& block_hash)
    : type_(type)
    , sender_id_(sender_id)
    , epoch_(epoch)
    , block_hash_(block_hash)
    , timestamp_(std::chrono::system_clock::now()) {}

} // namespace consensus
