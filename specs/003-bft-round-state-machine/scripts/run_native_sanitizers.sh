#!/bin/sh
set -eu

mode="${1:?sanitizer mode is required}"
compiler="${2:?compiler is required}"
output="${3:?output directory is required}"
mkdir -p "$output"

base_flags="-std=c++20 -O1 -g -Wall -Wextra -Wpedantic -Werror -fno-fast-math -fno-omit-frame-pointer -pthread"
includes="-I/workspace/delta-core-cpp/include -I/workspace/delta-runtime-cpp/include -I/workspace/delta-ffi/include"
core_sources="/workspace/delta-core-cpp/src/arithmetic.cpp /workspace/delta-core-cpp/src/canonical.cpp /workspace/delta-core-cpp/src/consensus.cpp /workspace/delta-core-cpp/src/protocol.cpp /workspace/delta-core-cpp/src/sha256.cpp /workspace/delta-core-cpp/src/transition.cpp"
runtime_sources="/workspace/delta-runtime-cpp/src/runtime.cpp /workspace/delta-runtime-cpp/src/wal.cpp"

if [ "$mode" = "address-undefined" ]; then
  sanitize_flags="-fsanitize=address,undefined -fno-sanitize-recover=all"
  # shellcheck disable=SC2086
  "$compiler" $base_flags $sanitize_flags $includes $core_sources \
    /workspace/delta-core-cpp/tests/transition_test.cpp \
    -DDELTA_GOLDEN_FIXTURE_PATH=\"/workspace/delta-protocol/fixtures/003/cross-language/golden-v1.json\" \
    -o "$output/core-sanitized"
  # shellcheck disable=SC2086
  "$compiler" $base_flags $sanitize_flags $includes $core_sources $runtime_sources \
    /workspace/delta-runtime-cpp/tests/runtime_test.cpp \
    -DDELTA_GOLDEN_FIXTURE_PATH=\"/workspace/delta-protocol/fixtures/003/cross-language/golden-v1.json\" \
    -o "$output/runtime-sanitized"
  # shellcheck disable=SC2086
  "$compiler" $base_flags $sanitize_flags $includes $core_sources $runtime_sources \
    /workspace/delta-ffi/src/delta_abi.cpp \
    /workspace/delta-ffi/tests/abi_test.cpp \
    -DDELTA_FFI_BUILD \
    -DDELTA_GOLDEN_FIXTURE_PATH=\"/workspace/delta-protocol/fixtures/003/cross-language/golden-v1.json\" \
    -o "$output/abi-sanitized"
  # shellcheck disable=SC2086
  "$compiler" $base_flags $sanitize_flags $includes $core_sources $runtime_sources \
    /workspace/delta-ffi/src/delta_abi.cpp \
    /workspace/delta-ffi/tests/fuzz_smoke_test.cpp \
    -DDELTA_FFI_BUILD \
    -DDELTA_GOLDEN_FIXTURE_PATH=\"/workspace/delta-protocol/fixtures/003/cross-language/golden-v1.json\" \
    -o "$output/fuzz-sanitized"
  ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 \
    "$output/core-sanitized"
  ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 \
    "$output/runtime-sanitized"
  ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 \
    "$output/abi-sanitized"
  ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 \
    "$output/fuzz-sanitized"
elif [ "$mode" = "thread" ]; then
  sanitize_flags="-fsanitize=thread -fno-sanitize-recover=all"
  # shellcheck disable=SC2086
  "$compiler" $base_flags $sanitize_flags $includes $core_sources $runtime_sources \
    /workspace/delta-runtime-cpp/tests/runtime_test.cpp \
    -DDELTA_GOLDEN_FIXTURE_PATH=\"/workspace/delta-protocol/fixtures/003/cross-language/golden-v1.json\" \
    -o "$output/runtime-tsan"
  TSAN_OPTIONS=halt_on_error=1:second_deadlock_stack=1 "$output/runtime-tsan"
else
  echo "unknown sanitizer mode: $mode" >&2
  exit 2
fi

echo "native sanitizer gate passed: $mode"
