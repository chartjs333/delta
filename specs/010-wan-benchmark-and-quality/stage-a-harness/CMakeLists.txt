cmake_minimum_required(VERSION 3.25)

project(DeltaReduceStageAPrimaryExactness LANGUAGES CXX)

if(NOT DEFINED DELTA_SOURCE_ROOT)
  message(FATAL_ERROR "DELTA_SOURCE_ROOT must identify the qualified source worktree")
endif()

option(STAGE_A_BUILD_SOURCE_TESTS "Register qualified-source negative tests" OFF)
set(BUILD_TESTING ${STAGE_A_BUILD_SOURCE_TESTS} CACHE BOOL "Qualified source tests" FORCE)
add_subdirectory("${DELTA_SOURCE_ROOT}" delta-qualified-source EXCLUDE_FROM_ALL)

add_executable(stage_a_primary_exactness_probe primary_exactness_probe.cpp)
target_link_libraries(
  stage_a_primary_exactness_probe
  PRIVATE delta::apply delta::hierarchy delta::robust delta::runtime)
delta_target_defaults(stage_a_primary_exactness_probe)
