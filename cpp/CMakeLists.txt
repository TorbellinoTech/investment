cmake_minimum_required(VERSION 3.16)
project(InvestmentConsensusCpp VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(BUILD_TESTS "Build tests" ON)

include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

set(CONSENSUS_SOURCES
    src/consensus/block.cpp
    src/consensus/message.cpp
    src/consensus/streamlet_node.cpp
    src/consensus/streamlet_protocol.cpp
)

add_library(streamlet_consensus STATIC ${CONSENSUS_SOURCES})

add_executable(streamlet_demo src/main.cpp)
target_link_libraries(streamlet_demo streamlet_consensus)

if(BUILD_TESTS)
  enable_testing()
  add_executable(test_streamlet tests/test_streamlet.cpp)
  target_link_libraries(test_streamlet streamlet_consensus)
  add_test(NAME streamlet_basic COMMAND test_streamlet)
endif()
