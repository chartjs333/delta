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

add_library(delta_ffi SHARED delta-ffi/src/delta_abi.cpp)
add_library(delta::ffi ALIAS delta_ffi)
target_include_directories(
  delta_ffi
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/delta-ffi/include>)
target_compile_definitions(delta_ffi PRIVATE DELTA_FFI_BUILD)
target_link_libraries(delta_ffi PUBLIC delta::runtime)
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
  target_link_libraries(delta_core_prepared_100_test PRIVATE delta::core)
  target_compile_definitions(
    delta_core_prepared_100_test
    PRIVATE DELTA_GOLDEN_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json"
            DELTA_PREPARED_100_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/prepared-100-v1.json")
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
    PRIVATE DELTA_GOLDEN_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json")
  delta_target_defaults(delta_ffi_abi_test)
  add_test(NAME delta_ffi.abi COMMAND delta_ffi_abi_test)

  add_executable(delta_ffi_fuzz_smoke_test delta-ffi/tests/fuzz_smoke_test.cpp)
  target_link_libraries(delta_ffi_fuzz_smoke_test PRIVATE delta::ffi)
  target_compile_definitions(
    delta_ffi_fuzz_smoke_test
    PRIVATE DELTA_GOLDEN_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json")
  delta_target_defaults(delta_ffi_fuzz_smoke_test)
  add_test(NAME delta_ffi.fuzz_smoke COMMAND delta_ffi_fuzz_smoke_test)
endif()
