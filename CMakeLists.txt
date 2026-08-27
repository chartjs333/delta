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
  delta-core-cpp/src/canonical.cpp
  delta-core-cpp/src/sha256.cpp)
add_library(delta::core ALIAS delta_core)
target_include_directories(
  delta_core
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/delta-core-cpp/include>)
delta_target_defaults(delta_core)

add_library(delta_runtime INTERFACE)
add_library(delta::runtime ALIAS delta_runtime)
target_link_libraries(delta_runtime INTERFACE delta::core)

add_library(delta_ffi INTERFACE)
add_library(delta::ffi ALIAS delta_ffi)
target_link_libraries(delta_ffi INTERFACE delta::runtime)

if(BUILD_TESTING)
  add_executable(delta_core_canonical_test delta-core-cpp/tests/canonical_test.cpp)
  target_link_libraries(delta_core_canonical_test PRIVATE delta::core)
  target_compile_definitions(
    delta_core_canonical_test
    PRIVATE DELTA_GOLDEN_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/delta-protocol/fixtures/003/cross-language/golden-v1.json")
  delta_target_defaults(delta_core_canonical_test)
  add_test(NAME delta_core.canonical COMMAND delta_core_canonical_test)

  add_executable(delta_runtime_target_test delta-runtime-cpp/tests/target_smoke_test.cpp)
  target_link_libraries(delta_runtime_target_test PRIVATE delta::runtime)
  delta_target_defaults(delta_runtime_target_test)
  add_test(NAME delta_runtime.target COMMAND delta_runtime_target_test)

  add_executable(delta_ffi_target_test delta-ffi/tests/target_smoke_test.cpp)
  target_link_libraries(delta_ffi_target_test PRIVATE delta::ffi)
  delta_target_defaults(delta_ffi_target_test)
  add_test(NAME delta_ffi.target COMMAND delta_ffi_target_test)
endif()
