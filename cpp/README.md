# C++ Streamlet Consensus Module

This module implements a minimal Streamlet-style consensus simulation in C++ for the Torbellino Tech introductory test.

## Requirements
- CMake >= 3.16
- A C++17 compiler (AppleClang, clang, or gcc)

## Build
```bash
cd cpp
mkdir -p build && cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . -j 8
```

## Run Demo
Arguments: `[num_nodes] [num_epochs]`
```bash
./streamlet_demo        # defaults: 4 nodes, 6 epochs
./streamlet_demo 5 8    # example: 5 nodes, 8 epochs
```

## Run Tests
```bash
ctest -V
# or run the test binary directly
./test_streamlet
```

## Notes
- The simulation is synchronous and simplified for clarity.
- Build artifacts are ignored via the repository `.gitignore`.
