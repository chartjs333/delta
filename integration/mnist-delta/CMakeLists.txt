cmake_minimum_required(VERSION 3.25)

project(DeltaMnistNativeNode LANGUAGES CXX)

if(NOT DEFINED DELTA_SOURCE_ROOT)
  message(FATAL_ERROR "DELTA_SOURCE_ROOT must identify the unchanged Delta source checkout")
endif()
set(
  DELTA_SOURCE_ROOT
  "${DELTA_SOURCE_ROOT}"
  CACHE PATH
  "Path to an unchanged Delta source checkout")
if(NOT EXISTS "${DELTA_SOURCE_ROOT}/CMakeLists.txt")
  message(FATAL_ERROR "DELTA_SOURCE_ROOT does not contain the Delta CMakeLists.txt")
endif()

set(BUILD_TESTING OFF CACHE BOOL "Do not build Delta production test targets" FORCE)
add_subdirectory("${DELTA_SOURCE_ROOT}" delta-source EXCLUDE_FROM_ALL)

add_executable(
  delta_mnist_native_node
  native/mnist_delta_node.cpp)

target_link_libraries(
  delta_mnist_native_node
  PRIVATE delta::runtime delta::certificates delta::robust delta::apply)

if(COMMAND delta_target_defaults)
  delta_target_defaults(delta_mnist_native_node)
else()
  target_compile_features(delta_mnist_native_node PRIVATE cxx_std_20)
endif()
