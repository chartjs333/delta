#!/bin/sh
set -eu

if [ "$#" -ne 6 ]; then
  echo "usage: build_exactness_probe.sh COMPILER STANDARD VERSION_PATTERN VERSION_OUTPUT PROBE_OUTPUT CONSUMER_OUTPUT" >&2
  exit 2
fi

compiler="$1"
standard="$2"
version_pattern="$3"
version_output="$4"
probe_output="$5"
consumer_output="$6"

case "$standard" in
  20|23) ;;
  *) echo "unsupported C++ standard: $standard" >&2; exit 2 ;;
esac

actual_version=$("$compiler" --version | head -n 1)
printf '%s\n' "$actual_version" | grep -F "$version_pattern"
printf '%s\n' "$actual_version" > "$version_output"
test "$(uname -m)" = "x86_64"

"$compiler" \
  "-std=c++$standard" \
  -Wall -Wextra -Wpedantic -Werror -fno-fast-math -pthread \
  -static-libgcc -static-libstdc++ \
  -Idelta-core-cpp/include \
  -Idelta-runtime-cpp/include \
  delta-core-cpp/src/arithmetic.cpp \
  delta-core-cpp/src/canonical.cpp \
  delta-core-cpp/src/consensus.cpp \
  delta-core-cpp/src/protocol.cpp \
  delta-core-cpp/src/sha256.cpp \
  delta-core-cpp/src/transition.cpp \
  delta-core-cpp/src/fixedpoint/bounds.cpp \
  delta-core-cpp/src/fixedpoint/checked.cpp \
  delta-core-cpp/src/fixedpoint/direct_q.cpp \
  delta-core-cpp/src/fixedpoint/encoder.cpp \
  delta-core-cpp/src/fixedpoint/profile.cpp \
  delta-core-cpp/src/fixedpoint/rounding.cpp \
  delta-core-cpp/src/fixedpoint/scale.cpp \
  delta-core-cpp/src/certificates/contracts.cpp \
  delta-core-cpp/src/certificates/verifier.cpp \
  delta-core-cpp/src/certificates/vote_admission.cpp \
  delta-core-cpp/src/robust/plan.cpp \
  delta-core-cpp/src/apply/engine.cpp \
  delta-core-cpp/src/reduce/hierarchy.cpp \
  delta-core-cpp/src/reduce/topology.cpp \
  delta-runtime-cpp/src/certificate_runtime.cpp \
  delta-runtime-cpp/src/runtime.cpp \
  delta-runtime-cpp/src/vote_codec.cpp \
  delta-runtime-cpp/src/wal.cpp \
  specs/010-wan-benchmark-and-quality/qualification-harness/exactness_probe.cpp \
  -o "$probe_output"

"$compiler" \
  "-std=c++$standard" \
  -Wall -Wextra -Wpedantic -Werror -fno-fast-math \
  -static-libgcc -static-libstdc++ \
  specs/010-wan-benchmark-and-quality/conformance/foundation_fixture_consumer.cpp \
  -o "$consumer_output"
