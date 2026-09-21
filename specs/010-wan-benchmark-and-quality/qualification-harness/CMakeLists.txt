cmake_minimum_required(VERSION 3.25)

project(DeltaReduceFeature010Exactness LANGUAGES CXX)

if(NOT DEFINED DELTA_SOURCE_ROOT)
  message(FATAL_ERROR "DELTA_SOURCE_ROOT must identify the exact qualified source")
endif()

set(BUILD_TESTING OFF CACHE BOOL "Feature010 harness uses selected production targets" FORCE)
add_subdirectory("${DELTA_SOURCE_ROOT}" delta-qualified-source EXCLUDE_FROM_ALL)

add_executable(feature010_exactness_probe exactness_probe.cpp)
target_link_libraries(
  feature010_exactness_probe
  PRIVATE delta::apply delta::hierarchy delta::robust delta::runtime)
delta_target_defaults(feature010_exactness_probe)
