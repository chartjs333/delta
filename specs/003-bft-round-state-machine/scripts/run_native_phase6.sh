#!/bin/sh
set -eu

compiler="${1:?compiler is required}"
standard="${2:?C++ standard is required}"
output="${3:?output directory is required}"

mkdir -p "$output/traces" "$output/mutants"

flags="-std=c++${standard} -Wall -Wextra -Wpedantic -Werror -fno-fast-math -pthread"
includes="-I/workspace/delta-core-cpp/include -I/workspace/delta-runtime-cpp/include -I/workspace/delta-ffi/include"
core_sources="/workspace/delta-core-cpp/src/arithmetic.cpp /workspace/delta-core-cpp/src/canonical.cpp /workspace/delta-core-cpp/src/consensus.cpp /workspace/delta-core-cpp/src/protocol.cpp /workspace/delta-core-cpp/src/sha256.cpp /workspace/delta-core-cpp/src/transition.cpp"
runtime_sources="/workspace/delta-runtime-cpp/src/runtime.cpp /workspace/delta-runtime-cpp/src/wal.cpp"

# Four independent runtimes, 100 prepared integer tickets and crash/restart identity.
# Intentional word splitting expands the frozen source/flag lists above.
# shellcheck disable=SC2086
"$compiler" $flags $includes $core_sources $runtime_sources \
  /workspace/delta-runtime-cpp/tests/native_exit_test.cpp \
  -DDELTA_GOLDEN_FIXTURE_PATH=\"/workspace/delta-protocol/fixtures/003/cross-language/golden-v1.json\" \
  -DDELTA_PREPARED_100_FIXTURE_PATH=\"/workspace/delta-protocol/fixtures/003/cross-language/prepared-100-v1.json\" \
  -o "$output/native-exit"
"$output/native-exit"

# Runtime-derived legal implementation traces must reproduce checked-in bytes.
# shellcheck disable=SC2086
"$compiler" $flags $includes $core_sources $runtime_sources \
  /workspace/delta-runtime-cpp/tests/trace_exporter.cpp \
  -DDELTA_GOLDEN_FIXTURE_PATH=\"/workspace/delta-protocol/fixtures/003/cross-language/golden-v1.json\" \
  -o "$output/trace-exporter"
"$output/trace-exporter" "$output/traces"
for trace in native-normal native-view-change native-certified-abort native-crash-recovery; do
  cmp "$output/traces/$trace.json" \
    "/workspace/specs/003-bft-round-state-machine/evidence/traces/$trace.json"
done

# Bounded parser and C ABI invalid-corpus smoke path.
# shellcheck disable=SC2086
"$compiler" $flags $includes $core_sources $runtime_sources \
  /workspace/delta-ffi/src/delta_abi.cpp \
  /workspace/delta-ffi/tests/fuzz_smoke_test.cpp \
  -DDELTA_FFI_BUILD \
  -DDELTA_GOLDEN_FIXTURE_PATH=\"/workspace/delta-protocol/fixtures/003/cross-language/golden-v1.json\" \
  -o "$output/fuzz-smoke"
"$output/fuzz-smoke"

# These targets compile the real production actions with one weakening each.
# The resulting implementation traces must reproduce the expected counterexamples.
# shellcheck disable=SC2086
"$compiler" $flags $includes $core_sources \
  /workspace/delta-runtime-cpp/tests/native_mutant_test.cpp \
  -DDELTA_NATIVE_MUTANT_ALLOW_VIEW_JUMP \
  -DDELTA_EXPECT_VIEW_MUTANT \
  -DDELTA_GOLDEN_FIXTURE_PATH=\"/workspace/delta-protocol/fixtures/003/cross-language/golden-v1.json\" \
  -o "$output/view-mutant"
"$output/view-mutant" "$output/mutants/native-view-without-qc.json"
cmp "$output/mutants/native-view-without-qc.json" \
  /workspace/specs/003-bft-round-state-machine/evidence/mutants/native-view-without-qc.json

# shellcheck disable=SC2086
"$compiler" $flags $includes $core_sources $runtime_sources \
  /workspace/delta-runtime-cpp/tests/native_mutant_test.cpp \
  -DDELTA_NATIVE_MUTANT_EXPOSE_BEFORE_DURABILITY \
  -DDELTA_EXPECT_DURABILITY_MUTANT \
  -DDELTA_GOLDEN_FIXTURE_PATH=\"/workspace/delta-protocol/fixtures/003/cross-language/golden-v1.json\" \
  -o "$output/durability-mutant"
"$output/durability-mutant" "$output/mutants/native-effect-before-durability.json"
cmp "$output/mutants/native-effect-before-durability.json" \
  /workspace/specs/003-bft-round-state-machine/evidence/mutants/native-effect-before-durability.json

echo "native phase-6 verification passed for ${compiler} C++${standard}"
