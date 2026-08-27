#!/bin/sh
set -eu

compiler="${1:?compiler is required}"
output="${2:?output directory is required}"
mkdir -p "$output"

base_flags="-std=c++20 -O1 -g -Wall -Wextra -Wpedantic -Werror -fno-fast-math -fno-omit-frame-pointer -pthread"
includes="-I/workspace/delta-core-cpp/include -I/workspace/delta-runtime-cpp/include -I/workspace/delta-ffi/include"
core_sources="/workspace/delta-core-cpp/src/arithmetic.cpp /workspace/delta-core-cpp/src/canonical.cpp /workspace/delta-core-cpp/src/consensus.cpp /workspace/delta-core-cpp/src/protocol.cpp /workspace/delta-core-cpp/src/sha256.cpp /workspace/delta-core-cpp/src/transition.cpp"
fixedpoint_sources="/workspace/delta-core-cpp/src/fixedpoint/bounds.cpp /workspace/delta-core-cpp/src/fixedpoint/checked.cpp /workspace/delta-core-cpp/src/fixedpoint/direct_q.cpp /workspace/delta-core-cpp/src/fixedpoint/encoder.cpp /workspace/delta-core-cpp/src/fixedpoint/profile.cpp /workspace/delta-core-cpp/src/fixedpoint/rounding.cpp /workspace/delta-core-cpp/src/fixedpoint/scale.cpp"
shard_sources="/workspace/delta-core-cpp/src/shards/envelope.cpp /workspace/delta-core-cpp/src/shards/plan.cpp /workspace/delta-core-cpp/src/shards/reader.cpp"
runtime_sources="/workspace/delta-runtime-cpp/src/runtime.cpp /workspace/delta-runtime-cpp/src/wal.cpp"
sanitize_flags="-fsanitize=address,undefined -fno-sanitize-recover=all"

# shellcheck disable=SC2086
"$compiler" $base_flags $sanitize_flags $includes $core_sources $fixedpoint_sources $shard_sources \
  /workspace/delta-core-cpp/tests/shards_test.cpp \
  -DDELTA_FIXEDPOINT_GOLDEN_PATH=\"/workspace/delta-protocol/fixtures/004/cross-language/golden-v1.json\" \
  -o "$output/shards-sanitized"

# shellcheck disable=SC2086
"$compiler" $base_flags $sanitize_flags $includes $core_sources $fixedpoint_sources $shard_sources \
  $runtime_sources \
  /workspace/delta-ffi/src/delta_abi.cpp \
  /workspace/delta-ffi/src/fixedpoint_abi.cpp \
  /workspace/delta-ffi/tests/abi_test.cpp \
  -DDELTA_FFI_BUILD \
  -DDELTA_GOLDEN_FIXTURE_PATH=\"/workspace/delta-protocol/fixtures/003/cross-language/golden-v1.json\" \
  -DDELTA_FIXEDPOINT_GOLDEN_FIXTURE_PATH=\"/workspace/delta-protocol/fixtures/004/cross-language/golden-v1.json\" \
  -o "$output/ffi-sanitized"

# shellcheck disable=SC2086
"$compiler" $base_flags -fsanitize=fuzzer,address,undefined -fno-sanitize-recover=all \
  $includes $core_sources $fixedpoint_sources $shard_sources \
  /workspace/delta-core-cpp/fuzz/fixedpoint_parser_fuzz.cpp \
  -o "$output/parser-fuzzer"

ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 \
  "$output/shards-sanitized"
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 \
  "$output/ffi-sanitized"
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 \
  "$output/parser-fuzzer" \
    -runs=2000 \
    -max_len=1052688 \
    /workspace/delta-core-cpp/fuzz/corpus

echo "feature-004 ASan/UBSan/libFuzzer gate passed"
