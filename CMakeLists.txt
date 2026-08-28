cmake_minimum_required(VERSION 3.25)

project(DeltaReduce LANGUAGES CXX)

include(CTest)

set(DELTA_CXX_STANDARD "20" CACHE STRING "C++ language mode (20 or 23)")
set_property(CACHE DELTA_CXX_STANDARD PROPERTY STRINGS 20 23)
if(NOT DELTA_CXX_STANDARD STREQUAL "20" AND NOT DELTA_CXX_STANDARD STREQUAL "23")
  message(FATAL_ERROR "DELTA_CXX_STANDARD must be 20 or 23")
endif()

option(DELTA_WARNINGS_AS_ERRORS "Treat compiler warnings as errors" ON)

function(delta_target_defaults target)
  target_compile_features(${target} PUBLIC cxx_std_${DELTA_CXX_STANDARD})
  set_target_properties(
    ${target}
    PROPERTIES CXX_EXTENSIONS OFF
               CXX_VISIBILITY_PRESET hidden
               VISIBILITY_INLINES_HIDDEN YES)
  if(MSVC)
    target_compile_options(${target} PRIVATE /W4 /permissive- /fp:strict)
    if(DELTA_WARNINGS_AS_ERRORS)
      target_compile_options(${target} PRIVATE /WX)
    endif()
  else()
    target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic -fno-fast-math)
    if(DELTA_WARNINGS_AS_ERRORS)
      target_compile_options(${target} PRIVATE -Werror)
    endif()
  endif()
endfunction()

add_library(delta_core STATIC
  delta-core-cpp/src/arithmetic.cpp
  delta-core-cpp/src/canonical.cpp
  delta-core-cpp/src/consensus.cpp
  delta-core-cpp/src/protocol.cpp
  delta-core-cpp/src/sha256.cpp
  delta-core-cpp/src/transition.cpp)
add_library(delta::core ALIAS delta_core)
set_target_properties(delta_core PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories(
  delta_core
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/delta-core-cpp/include>)
delta_target_defaults(delta_core)

add_library(delta_fixedpoint STATIC
  delta-core-cpp/src/fixedpoint/bounds.cpp
  delta-core-cpp/src/fixedpoint/checked.cpp
  delta-core-cpp/src/fixedpoint/direct_q.cpp
  delta-core-cpp/src/fixedpoint/encoder.cpp
  delta-core-cpp/src/fixedpoint/profile.cpp
  delta-core-cpp/src/fixedpoint/rounding.cpp
  delta-core-cpp/src/fixedpoint/scale.cpp)
add_library(delta::fixedpoint ALIAS delta_fixedpoint)
set_target_properties(delta_fixedpoint PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories(
  delta_fixedpoint
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/delta-core-cpp/include>)
target_link_libraries(delta_fixedpoint PUBLIC delta::core)
delta_target_defaults(delta_fixedpoint)

add_library(delta_shards STATIC
  delta-core-cpp/src/shards/envelope.cpp
  delta-core-cpp/src/shards/plan.cpp
  delta-core-cpp/src/shards/reader.cpp)
add_library(delta::shards ALIAS delta_shards)
set_target_properties(delta_shards PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories(
  delta_shards
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/delta-core-cpp/include>)
target_link_libraries(delta_shards PUBLIC delta::fixedpoint)
delta_target_defaults(delta_shards)

add_library(delta_distribution STATIC
  delta-core-cpp/src/distribution/certification_policy.cpp
  delta-core-cpp/src/distribution/manifest_verifier.cpp)
add_library(delta::distribution ALIAS delta_distribution)
set_target_properties(delta_distribution PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories(
  delta_distribution
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/delta-core-cpp/include>)
target_link_libraries(delta_distribution PUBLIC delta::core)
delta_target_defaults(delta_distribution)

add_library(delta_hierarchy STATIC
  delta-core-cpp/src/reduce/hierarchy.cpp
  delta-core-cpp/src/reduce/topology.cpp)
add_library(delta::hierarchy ALIAS delta_hierarchy)
set_target_properties(delta_hierarchy PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories(
  delta_hierarchy
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/delta-core-cpp/include>)
target_link_libraries(delta_hierarchy PUBLIC delta::fixedpoint)
delta_target_defaults(delta_hierarchy)

add_library(delta_scheduling STATIC
  delta-core-cpp/src/scheduling/contracts.cpp
  delta-core-cpp/src/scheduling/planner.cpp)
add_library(delta::scheduling ALIAS delta_scheduling)
set_target_properties(delta_scheduling PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories(
  delta_scheduling
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/delta-core-cpp/include>)
target_link_libraries(delta_scheduling PUBLIC delta::core)
delta_target_defaults(delta_scheduling)

add_library(delta_runtime STATIC
  delta-runtime-cpp/src/runtime.cpp
  delta-runtime-cpp/src/wal.cpp)
add_library(delta::runtime ALIAS delta_runtime)
set_target_properties(delta_runtime PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories(
  delta_runtime
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/delta-runtime-cpp/include>)
target_link_libraries(delta_runtime PUBLIC delta::core)
if(NOT WIN32)
  target_compile_options(delta_runtime PRIVATE -pthread)
  target_link_options(delta_runtime PUBLIC -pthread)
endif()
delta_target_defaults(delta_runtime)

add_library(delta_ffi SHARED
  delta-ffi/src/delta_abi.cpp
  delta-ffi/src/distribution_abi.cpp
  delta-ffi/src/fixedpoint_abi.cpp
  delta-ffi/src/hierarchy_abi.cpp)
add_library(delta::ffi ALIAS delta_ffi)
target_include_directories(
  delta_ffi
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/delta-ffi/include>)
target_compile_definitions(delta_ffi PRIVATE DELTA_FFI_BUILD)
target_link_libraries(
  delta_ffi PUBLIC delta::runtime delta::shards delta::distribution delta::hierarchy)
delta_target_defaults(delta_ffi)

if(BUILD_TESTING)
  add_executable(delta_core_canonical_test delta-core-cpp/tests/canonical_test.cpp)
  target_link_libraries(delta_core_canonical_test PRIVATE delta::core)
  target_compile_definitions(
    delta_core_canonical_test
    PRIVATE DELTA_GOLDEN_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json")
  delta_target_defaults(delta_core_canonical_test)
  add_test(NAME delta_core.canonical COMMAND delta_core_canonical_test)

  add_executable(delta_core_protocol_test delta-core-cpp/tests/protocol_test.cpp)
  target_link_libraries(delta_core_protocol_test PRIVATE delta::core)
  target_compile_definitions(
    delta_core_protocol_test
    PRIVATE DELTA_GOLDEN_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json")
  delta_target_defaults(delta_core_protocol_test)
  add_test(NAME delta_core.protocol COMMAND delta_core_protocol_test)

  add_executable(delta_core_arithmetic_test delta-core-cpp/tests/arithmetic_test.cpp)
  target_link_libraries(delta_core_arithmetic_test PRIVATE delta::core)
  delta_target_defaults(delta_core_arithmetic_test)
  add_test(NAME delta_core.arithmetic COMMAND delta_core_arithmetic_test)

  add_executable(delta_fixedpoint_test delta-core-cpp/tests/fixedpoint_test.cpp)
  target_link_libraries(delta_fixedpoint_test PRIVATE delta::fixedpoint)
  target_compile_definitions(
    delta_fixedpoint_test
    PRIVATE DELTA_FIXEDPOINT_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/004/cross-language/golden-v1.json")
  delta_target_defaults(delta_fixedpoint_test)
  add_test(NAME delta_core.fixedpoint COMMAND delta_fixedpoint_test)

  add_executable(delta_direct_q_test delta-core-cpp/tests/direct_q_test.cpp)
  target_link_libraries(delta_direct_q_test PRIVATE delta::fixedpoint)
  delta_target_defaults(delta_direct_q_test)
  add_test(NAME delta_core.direct_q COMMAND delta_direct_q_test)

  add_library(delta_fixedpoint_unchecked_count_mutant STATIC
    delta-core-cpp/src/fixedpoint/bounds.cpp
    delta-core-cpp/src/fixedpoint/checked.cpp
    delta-core-cpp/src/fixedpoint/direct_q.cpp
    delta-core-cpp/src/fixedpoint/encoder.cpp
    delta-core-cpp/src/fixedpoint/profile.cpp
    delta-core-cpp/src/fixedpoint/rounding.cpp
    delta-core-cpp/src/fixedpoint/scale.cpp)
  target_include_directories(
    delta_fixedpoint_unchecked_count_mutant
    PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/delta-core-cpp/include>)
  target_link_libraries(delta_fixedpoint_unchecked_count_mutant PUBLIC delta::core)
  target_compile_definitions(
    delta_fixedpoint_unchecked_count_mutant
    PRIVATE DELTA_FIXEDPOINT_MUTANT_UNCHECKED_COUNT)
  delta_target_defaults(delta_fixedpoint_unchecked_count_mutant)
  add_executable(
    delta_fixedpoint_unchecked_count_mutant_test
    delta-core-cpp/tests/direct_q_test.cpp)
  target_link_libraries(
    delta_fixedpoint_unchecked_count_mutant_test
    PRIVATE delta_fixedpoint_unchecked_count_mutant)
  delta_target_defaults(delta_fixedpoint_unchecked_count_mutant_test)
  add_test(
    NAME delta_core.mutant_unchecked_count
    COMMAND delta_fixedpoint_unchecked_count_mutant_test)
  set_tests_properties(delta_core.mutant_unchecked_count PROPERTIES WILL_FAIL TRUE)

  add_executable(delta_shards_test delta-core-cpp/tests/shards_test.cpp)
  target_link_libraries(delta_shards_test PRIVATE delta::shards)
  target_compile_definitions(
    delta_shards_test
    PRIVATE DELTA_FIXEDPOINT_GOLDEN_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/004/cross-language/golden-v1.json")
  delta_target_defaults(delta_shards_test)
  add_test(NAME delta_core.shards COMMAND delta_shards_test)

  foreach(mutant IN ITEMS UNBOUNDED_HEADER SKIP_CONTEXT)
    string(TOLOWER "${mutant}" mutant_lower)
    set(mutant_library "delta_shards_${mutant_lower}_mutant")
    set(mutant_test "${mutant_library}_test")
    add_library(${mutant_library} STATIC
      delta-core-cpp/src/shards/envelope.cpp
      delta-core-cpp/src/shards/plan.cpp
      delta-core-cpp/src/shards/reader.cpp)
    target_include_directories(
      ${mutant_library}
      PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/delta-core-cpp/include>)
    target_link_libraries(${mutant_library} PUBLIC delta::fixedpoint)
    target_compile_definitions(
      ${mutant_library} PRIVATE "DELTA_FIXEDPOINT_MUTANT_${mutant}")
    delta_target_defaults(${mutant_library})
    add_executable(${mutant_test} delta-core-cpp/tests/shards_test.cpp)
    target_link_libraries(${mutant_test} PRIVATE ${mutant_library})
    target_compile_definitions(
      ${mutant_test}
      PRIVATE DELTA_FIXEDPOINT_GOLDEN_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/004/cross-language/golden-v1.json")
    delta_target_defaults(${mutant_test})
    add_test(NAME "delta_core.mutant_${mutant_lower}" COMMAND ${mutant_test})
    set_tests_properties("delta_core.mutant_${mutant_lower}" PROPERTIES WILL_FAIL TRUE)
  endforeach()

  add_executable(delta_fixedpoint_parser_fuzz delta-core-cpp/fuzz/fixedpoint_parser_fuzz.cpp)
  target_link_libraries(delta_fixedpoint_parser_fuzz PRIVATE delta::shards)
  target_compile_definitions(delta_fixedpoint_parser_fuzz PRIVATE DELTA_FIXEDPOINT_FUZZ_SMOKE_MAIN)
  delta_target_defaults(delta_fixedpoint_parser_fuzz)
  add_test(NAME delta_core.fixedpoint_parser_fuzz COMMAND delta_fixedpoint_parser_fuzz)

  add_executable(delta_distribution_test delta-core-cpp/tests/distribution_test.cpp)
  target_link_libraries(delta_distribution_test PRIVATE delta::distribution)
  target_compile_definitions(
    delta_distribution_test
    PRIVATE DELTA_DISTRIBUTION_GOLDEN_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/005/cross-language/golden-v1.json")
  delta_target_defaults(delta_distribution_test)
  add_test(NAME delta_core.distribution COMMAND delta_distribution_test)

  foreach(mutant IN ITEMS ALLOW_DOWNGRADE ALLOW_FORBIDDEN ALLOW_NONCANONICAL)
    string(TOLOWER "${mutant}" mutant_lower)
    set(mutant_library "delta_distribution_${mutant_lower}_mutant")
    set(mutant_test "${mutant_library}_test")
    add_library(${mutant_library} STATIC
      delta-core-cpp/src/distribution/certification_policy.cpp
      delta-core-cpp/src/distribution/manifest_verifier.cpp)
    target_include_directories(
      ${mutant_library}
      PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/delta-core-cpp/include>)
    target_link_libraries(${mutant_library} PUBLIC delta::core)
    target_compile_definitions(
      ${mutant_library} PRIVATE "DELTA_DISTRIBUTION_MUTANT_${mutant}")
    delta_target_defaults(${mutant_library})
    add_executable(${mutant_test} delta-core-cpp/tests/distribution_test.cpp)
    target_link_libraries(${mutant_test} PRIVATE ${mutant_library})
    target_compile_definitions(
      ${mutant_test}
      PRIVATE DELTA_DISTRIBUTION_GOLDEN_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/005/cross-language/golden-v1.json")
    delta_target_defaults(${mutant_test})
    add_test(NAME "delta_core.distribution_mutant_${mutant_lower}" COMMAND ${mutant_test})
    set_tests_properties(
      "delta_core.distribution_mutant_${mutant_lower}" PROPERTIES WILL_FAIL TRUE)
  endforeach()

  add_executable(
    delta_distribution_parser_fuzz delta-core-cpp/fuzz/distribution_parser_fuzz.cpp)
  target_link_libraries(delta_distribution_parser_fuzz PRIVATE delta::distribution)
  target_compile_definitions(
    delta_distribution_parser_fuzz PRIVATE DELTA_DISTRIBUTION_FUZZ_SMOKE_MAIN)
  delta_target_defaults(delta_distribution_parser_fuzz)
  add_test(NAME delta_core.distribution_parser_fuzz COMMAND delta_distribution_parser_fuzz)

  add_executable(delta_hierarchy_test delta-core-cpp/tests/hierarchy_test.cpp)
  target_link_libraries(delta_hierarchy_test PRIVATE delta::hierarchy)
  target_compile_definitions(
    delta_hierarchy_test
    PRIVATE DELTA_HIERARCHY_GOLDEN_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/006/cross-language/golden-v1.json")
  delta_target_defaults(delta_hierarchy_test)
  add_test(NAME delta_core.hierarchy COMMAND delta_hierarchy_test)

  foreach(mutant IN ITEMS SKIP_COVERAGE SKIP_SHARD_COVERAGE UNCHECKED_OVERFLOW)
    string(TOLOWER "${mutant}" mutant_lower)
    set(mutant_library "delta_hierarchy_${mutant_lower}_mutant")
    set(mutant_test "${mutant_library}_test")
    add_library(${mutant_library} STATIC delta-core-cpp/src/reduce/topology.cpp)
    target_include_directories(
      ${mutant_library}
      PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/delta-core-cpp/include>)
    target_link_libraries(${mutant_library} PUBLIC delta::fixedpoint)
    target_compile_definitions(${mutant_library} PRIVATE "DELTA_HIERARCHY_MUTANT_${mutant}")
    delta_target_defaults(${mutant_library})
    add_executable(${mutant_test} delta-core-cpp/tests/hierarchy_test.cpp)
    target_link_libraries(${mutant_test} PRIVATE ${mutant_library})
    target_compile_definitions(
      ${mutant_test}
      PRIVATE DELTA_HIERARCHY_GOLDEN_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/006/cross-language/golden-v1.json")
    delta_target_defaults(${mutant_test})
    add_test(NAME "delta_core.hierarchy_mutant_${mutant_lower}" COMMAND ${mutant_test})
    set_tests_properties(
      "delta_core.hierarchy_mutant_${mutant_lower}" PROPERTIES WILL_FAIL TRUE)
  endforeach()

  add_executable(delta_hierarchy_parser_fuzz delta-core-cpp/fuzz/hierarchy_parser_fuzz.cpp)
  target_link_libraries(delta_hierarchy_parser_fuzz PRIVATE delta::hierarchy)
  target_compile_definitions(
    delta_hierarchy_parser_fuzz
    PRIVATE DELTA_HIERARCHY_FUZZ_SMOKE_MAIN
            DELTA_HIERARCHY_GOLDEN_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/006/cross-language/golden-v1.json")
  delta_target_defaults(delta_hierarchy_parser_fuzz)
  add_test(NAME delta_core.hierarchy_parser_fuzz COMMAND delta_hierarchy_parser_fuzz)

  add_executable(delta_hierarchy_reduce_test delta-core-cpp/tests/hierarchy_reduce_test.cpp)
  target_link_libraries(delta_hierarchy_reduce_test PRIVATE delta::hierarchy delta::runtime)
  target_compile_definitions(
    delta_hierarchy_reduce_test
    PRIVATE DELTA_HIERARCHY_GOLDEN_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/006/cross-language/golden-v1.json"
            DELTA_CORE_GOLDEN_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json")
  delta_target_defaults(delta_hierarchy_reduce_test)
  add_test(NAME delta_core.hierarchy_reduce COMMAND delta_hierarchy_reduce_test)
  add_test(
    NAME delta_core.hierarchy_trace_export
    COMMAND delta_hierarchy_reduce_test "${CMAKE_CURRENT_BINARY_DIR}/hierarchy-traces")

  foreach(mutant IN ITEMS PARTIAL_GLOBAL AVERAGE_REGIONS)
    string(TOLOWER "${mutant}" mutant_lower)
    set(mutant_library "delta_hierarchy_${mutant_lower}_mutant")
    set(mutant_test "${mutant_library}_test")
    add_library(${mutant_library} STATIC
      delta-core-cpp/src/reduce/hierarchy.cpp
      delta-core-cpp/src/reduce/topology.cpp)
    target_include_directories(
      ${mutant_library}
      PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/delta-core-cpp/include>)
    target_link_libraries(${mutant_library} PUBLIC delta::fixedpoint)
    target_compile_definitions(${mutant_library} PRIVATE "DELTA_HIERARCHY_MUTANT_${mutant}")
    delta_target_defaults(${mutant_library})
    add_executable(${mutant_test} delta-core-cpp/tests/hierarchy_reduce_test.cpp)
    target_link_libraries(${mutant_test} PRIVATE ${mutant_library} delta::runtime)
    target_compile_definitions(
      ${mutant_test}
      PRIVATE DELTA_HIERARCHY_GOLDEN_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/006/cross-language/golden-v1.json"
              DELTA_CORE_GOLDEN_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json")
    delta_target_defaults(${mutant_test})
    add_test(NAME "delta_core.hierarchy_mutant_${mutant_lower}" COMMAND ${mutant_test})
    set_tests_properties(
      "delta_core.hierarchy_mutant_${mutant_lower}" PROPERTIES WILL_FAIL TRUE)
  endforeach()

  add_executable(delta_scheduling_planner_test delta-core-cpp/tests/scheduling_planner_test.cpp)
  target_link_libraries(delta_scheduling_planner_test PRIVATE delta::scheduling)
  target_compile_definitions(
    delta_scheduling_planner_test
    PRIVATE DELTA_SCHEDULING_GOLDEN_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/007/cross-language/golden-v1.json")
  delta_target_defaults(delta_scheduling_planner_test)
  add_test(NAME delta_core.scheduling_planner COMMAND delta_scheduling_planner_test)

  foreach(mutant IN ITEMS ADAPT_WORK OVERLAP_RANGES SKIP_INFEASIBILITY)
    string(TOLOWER "${mutant}" mutant_lower)
    set(mutant_library "delta_scheduling_${mutant_lower}_mutant")
    set(mutant_test "${mutant_library}_test")
    add_library(${mutant_library} STATIC
      delta-core-cpp/src/scheduling/contracts.cpp
      delta-core-cpp/src/scheduling/planner.cpp)
    target_include_directories(
      ${mutant_library}
      PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/delta-core-cpp/include>)
    target_link_libraries(${mutant_library} PUBLIC delta::core)
    target_compile_definitions(${mutant_library} PRIVATE "DELTA_SCHEDULING_MUTANT_${mutant}")
    delta_target_defaults(${mutant_library})
    add_executable(${mutant_test} delta-core-cpp/tests/scheduling_planner_test.cpp)
    target_link_libraries(${mutant_test} PRIVATE ${mutant_library})
    target_compile_definitions(
      ${mutant_test}
      PRIVATE DELTA_SCHEDULING_GOLDEN_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/007/cross-language/golden-v1.json")
    delta_target_defaults(${mutant_test})
    add_test(NAME "delta_core.scheduling_mutant_${mutant_lower}" COMMAND ${mutant_test})
    set_tests_properties(
      "delta_core.scheduling_mutant_${mutant_lower}" PROPERTIES WILL_FAIL TRUE)
  endforeach()

  add_executable(delta_scheduling_contract_fuzz delta-core-cpp/fuzz/scheduling_contract_fuzz.cpp)
  target_link_libraries(delta_scheduling_contract_fuzz PRIVATE delta::scheduling)
  target_compile_definitions(
    delta_scheduling_contract_fuzz PRIVATE DELTA_SCHEDULING_FUZZ_SMOKE_MAIN)
  delta_target_defaults(delta_scheduling_contract_fuzz)
  add_test(NAME delta_core.scheduling_contract_fuzz COMMAND delta_scheduling_contract_fuzz)

  add_executable(delta_core_transition_test delta-core-cpp/tests/transition_test.cpp)
  target_link_libraries(delta_core_transition_test PRIVATE delta::core)
  target_compile_definitions(
    delta_core_transition_test
    PRIVATE DELTA_GOLDEN_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json")
  delta_target_defaults(delta_core_transition_test)
  add_test(NAME delta_core.transition COMMAND delta_core_transition_test)

  add_executable(delta_core_consensus_test delta-core-cpp/tests/consensus_test.cpp)
  target_link_libraries(delta_core_consensus_test PRIVATE delta::core)
  target_compile_definitions(
    delta_core_consensus_test
    PRIVATE DELTA_GOLDEN_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json")
  delta_target_defaults(delta_core_consensus_test)
  add_test(NAME delta_core.consensus COMMAND delta_core_consensus_test)

  add_executable(delta_core_portability_test delta-core-cpp/tests/portability_test.cpp)
  target_link_libraries(delta_core_portability_test PRIVATE delta::core)
  target_compile_definitions(
    delta_core_portability_test
    PRIVATE DELTA_GOLDEN_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json"
            DELTA_PORTABILITY_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/core-portability-v1.json")
  delta_target_defaults(delta_core_portability_test)
  add_test(NAME delta_core.portability COMMAND delta_core_portability_test)

  add_executable(delta_core_prepared_100_test delta-core-cpp/tests/prepared_100_test.cpp)
  target_link_libraries(delta_core_prepared_100_test PRIVATE delta::fixedpoint)
  target_compile_definitions(
    delta_core_prepared_100_test
    PRIVATE DELTA_GOLDEN_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json"
            DELTA_PREPARED_100_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/prepared-100-v1.json"
            DELTA_DIRECT_Q_100_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/004/cross-language/direct-q-100-v1.json")
  delta_target_defaults(delta_core_prepared_100_test)
  add_test(NAME delta_core.prepared_100 COMMAND delta_core_prepared_100_test)

  add_executable(delta_runtime_target_test delta-runtime-cpp/tests/target_smoke_test.cpp)
  target_link_libraries(delta_runtime_target_test PRIVATE delta::runtime)
  delta_target_defaults(delta_runtime_target_test)
  add_test(NAME delta_runtime.target COMMAND delta_runtime_target_test)

  add_executable(delta_runtime_test delta-runtime-cpp/tests/runtime_test.cpp)
  target_link_libraries(delta_runtime_test PRIVATE delta::runtime)
  target_compile_definitions(
    delta_runtime_test
    PRIVATE DELTA_GOLDEN_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json")
  delta_target_defaults(delta_runtime_test)
  add_test(NAME delta_runtime.behavior COMMAND delta_runtime_test)

  add_executable(delta_runtime_trace_exporter delta-runtime-cpp/tests/trace_exporter.cpp)
  target_link_libraries(delta_runtime_trace_exporter PRIVATE delta::runtime)
  target_compile_definitions(
    delta_runtime_trace_exporter
    PRIVATE DELTA_GOLDEN_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json")
  delta_target_defaults(delta_runtime_trace_exporter)
  add_test(
    NAME delta_runtime.trace_export
    COMMAND delta_runtime_trace_exporter "${CMAKE_CURRENT_BINARY_DIR}/native-traces")

  add_executable(delta_runtime_native_exit_test delta-runtime-cpp/tests/native_exit_test.cpp)
  target_link_libraries(delta_runtime_native_exit_test PRIVATE delta::runtime)
  target_compile_definitions(
    delta_runtime_native_exit_test
    PRIVATE DELTA_GOLDEN_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json"
            DELTA_PREPARED_100_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/prepared-100-v1.json")
  delta_target_defaults(delta_runtime_native_exit_test)
  add_test(NAME delta_runtime.native_exit COMMAND delta_runtime_native_exit_test)

  add_library(delta_core_view_mutant STATIC
    EXCLUDE_FROM_ALL
    delta-core-cpp/src/arithmetic.cpp
    delta-core-cpp/src/canonical.cpp
    delta-core-cpp/src/consensus.cpp
    delta-core-cpp/src/protocol.cpp
    delta-core-cpp/src/sha256.cpp
    delta-core-cpp/src/transition.cpp)
  target_include_directories(
    delta_core_view_mutant
    PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/delta-core-cpp/include>)
  target_compile_definitions(delta_core_view_mutant PRIVATE DELTA_NATIVE_MUTANT_ALLOW_VIEW_JUMP)
  delta_target_defaults(delta_core_view_mutant)
  add_executable(delta_core_view_mutant_test EXCLUDE_FROM_ALL delta-runtime-cpp/tests/native_mutant_test.cpp)
  target_link_libraries(delta_core_view_mutant_test PRIVATE delta_core_view_mutant)
  target_compile_definitions(
    delta_core_view_mutant_test
    PRIVATE DELTA_EXPECT_VIEW_MUTANT
            DELTA_GOLDEN_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json")
  delta_target_defaults(delta_core_view_mutant_test)

  add_library(delta_runtime_durability_mutant STATIC
    EXCLUDE_FROM_ALL
    delta-runtime-cpp/src/runtime.cpp
    delta-runtime-cpp/src/wal.cpp)
  target_include_directories(
    delta_runtime_durability_mutant
    PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/delta-runtime-cpp/include>)
  target_compile_definitions(
    delta_runtime_durability_mutant PRIVATE DELTA_NATIVE_MUTANT_EXPOSE_BEFORE_DURABILITY)
  target_link_libraries(delta_runtime_durability_mutant PUBLIC delta::core)
  if(NOT WIN32)
    target_compile_options(delta_runtime_durability_mutant PRIVATE -pthread)
    target_link_options(delta_runtime_durability_mutant PUBLIC -pthread)
  endif()
  delta_target_defaults(delta_runtime_durability_mutant)
  add_executable(
    delta_runtime_durability_mutant_test
    EXCLUDE_FROM_ALL
    delta-runtime-cpp/tests/native_mutant_test.cpp)
  target_link_libraries(delta_runtime_durability_mutant_test PRIVATE delta_runtime_durability_mutant)
  target_compile_definitions(
    delta_runtime_durability_mutant_test
    PRIVATE DELTA_EXPECT_DURABILITY_MUTANT
            DELTA_GOLDEN_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json")
  delta_target_defaults(delta_runtime_durability_mutant_test)

  add_executable(delta_ffi_target_test delta-ffi/tests/target_smoke_test.cpp)
  target_link_libraries(delta_ffi_target_test PRIVATE delta::ffi)
  delta_target_defaults(delta_ffi_target_test)
  add_test(NAME delta_ffi.target COMMAND delta_ffi_target_test)

  add_executable(delta_ffi_abi_test delta-ffi/tests/abi_test.cpp)
  target_link_libraries(delta_ffi_abi_test PRIVATE delta::ffi)
  target_compile_definitions(
    delta_ffi_abi_test
    PRIVATE DELTA_GOLDEN_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json"
            DELTA_FIXEDPOINT_GOLDEN_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/004/cross-language/golden-v1.json")
  delta_target_defaults(delta_ffi_abi_test)
  add_test(NAME delta_ffi.abi COMMAND delta_ffi_abi_test)

  add_executable(delta_ffi_distribution_test delta-ffi/tests/distribution_abi_test.cpp)
  target_link_libraries(delta_ffi_distribution_test PRIVATE delta::ffi)
  target_compile_definitions(
    delta_ffi_distribution_test
    PRIVATE DELTA_DISTRIBUTION_GOLDEN_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/005/cross-language/golden-v1.json")
  delta_target_defaults(delta_ffi_distribution_test)
  add_test(NAME delta_ffi.distribution COMMAND delta_ffi_distribution_test)

  add_executable(delta_ffi_hierarchy_test delta-ffi/tests/hierarchy_abi_test.cpp)
  target_link_libraries(delta_ffi_hierarchy_test PRIVATE delta::ffi)
  target_compile_definitions(
    delta_ffi_hierarchy_test
    PRIVATE DELTA_HIERARCHY_GOLDEN_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/006/cross-language/golden-v1.json")
  delta_target_defaults(delta_ffi_hierarchy_test)
  add_test(NAME delta_ffi.hierarchy COMMAND delta_ffi_hierarchy_test)

  add_executable(delta_ffi_fuzz_smoke_test delta-ffi/tests/fuzz_smoke_test.cpp)
  target_link_libraries(delta_ffi_fuzz_smoke_test PRIVATE delta::ffi)
  target_compile_definitions(
    delta_ffi_fuzz_smoke_test
    PRIVATE DELTA_GOLDEN_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json")
  delta_target_defaults(delta_ffi_fuzz_smoke_test)
  add_test(NAME delta_ffi.fuzz_smoke COMMAND delta_ffi_fuzz_smoke_test)
endif()
