#include "consensus/streamlet_protocol.hpp"
#include <iostream>
#include <cstdlib>

static void require(bool condition, const char* msg) {
    if (!condition) {
        std::cerr << "FAIL: " << msg << std::endl;
        std::exit(1);
    }
}

int main() {
    // n = 4 satisfies n >= 3f + 1 with f = 1
    consensus::StreamletProtocol proto(4);
    proto.runSimulation(3, 2);

    // Basic sanity: each node should have > genesis blocks
    for (const auto& node : proto.getNodes()) {
        auto stats = node->getStats();
        require(stats.total_blocks >= 2, "each node should have at least 2 blocks including genesis");
    }

    std::cout << "All checks passed." << std::endl;
    return 0;
}
