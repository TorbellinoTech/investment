#pragma once

#include "streamlet_node.hpp"
#include <memory>
#include <vector>

namespace consensus {

class StreamletProtocol {
public:
    explicit StreamletProtocol(int n_nodes);

    void runEpoch(int epoch, const std::vector<std::string>& transactions);
    void runSimulation(int num_epochs, int transactions_per_epoch = 3);

    int getNodeCount() const { return n_nodes_; }
    const std::vector<std::shared_ptr<StreamletNode>>& getNodes() const { return nodes_; }

    void showEpochSummary(int epoch) const;
    void showFinalSummary() const;

private:
    int n_nodes_;
    std::vector<std::shared_ptr<StreamletNode>> nodes_;
};

} // namespace consensus
