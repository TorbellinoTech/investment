#include "consensus/streamlet_protocol.hpp"
#include <iostream>

int main(int argc, char** argv) {
    int n = 4;
    int epochs = 6;
    if (argc >= 2) n = std::max(1, std::atoi(argv[1]));
    if (argc >= 3) epochs = std::max(1, std::atoi(argv[2]));
    consensus::StreamletProtocol proto(n);
    proto.runSimulation(epochs, 3);
    return 0;
}
