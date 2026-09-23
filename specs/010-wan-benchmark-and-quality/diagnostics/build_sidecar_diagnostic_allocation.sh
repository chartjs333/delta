#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
  echo "usage: build_sidecar_diagnostic_allocation.sh ALLOCATION_ROOT BUILD_ROOT" >&2
  exit 2
fi

allocation_root=$1
build_root=$2

case "$allocation_root" in
  /*) ;;
  *) echo "allocation root must be absolute" >&2; exit 2 ;;
esac
case "$build_root" in
  /*) ;;
  *) echo "build root must be absolute" >&2; exit 2 ;;
esac
if [ "$allocation_root" = "/" ] || [ "$build_root" = "/" ] ||
   [ "$allocation_root" = "$build_root" ]; then
  echo "allocation and build roots must be distinct non-root paths" >&2
  exit 2
fi
if [ -e "$allocation_root" ] || [ -e "$build_root" ]; then
  echo "allocation and build roots must both be fresh" >&2
  exit 2
fi

source_root=$(/bin/pwd -P)
fixture="$source_root/delta-protocol/fixtures/003/cross-language/golden-v1.json"
native_build="$build_root/native"
java_classes="$build_root/java-classes"
java_sources="$build_root/java-sources.txt"

if [ ! -f "$source_root/CMakeLists.txt" ] || [ ! -f "$fixture" ]; then
  echo "working directory is not the frozen DeltaReduce source checkout" >&2
  exit 2
fi

umask 022
/usr/bin/mkdir -p "$allocation_root" "$native_build" "$java_classes"

/usr/bin/cmake \
  -S "$source_root" \
  -B "$native_build" \
  -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_COMPILER=/usr/bin/g++ \
  -DDELTA_CXX_STANDARD=20 \
  -DDELTA_WARNINGS_AS_ERRORS=ON \
  -DDELTA_BUILD_ISOLATED_SIDECAR=ON \
  -DDELTA_BUILD_ISOLATED_SIDECAR_TESTS=OFF \
  -DDELTA_BUILD_SIDECAR_QUALIFICATION=OFF \
  -DBUILD_TESTING=OFF
/usr/bin/cmake --build "$native_build" --parallel 8 --target \
  delta_ffi delta_runtime_sidecar delta_sidecar_trace_generator

/usr/bin/install -m 0644 "$native_build/libdelta_ffi.so" \
  "$allocation_root/libdelta_ffi.so"
/usr/bin/install -m 0755 "$native_build/delta_runtime_sidecar" \
  "$allocation_root/delta_runtime_sidecar"
"$native_build/delta_sidecar_trace_generator" \
  "$fixture" 7000 "$allocation_root/corpus.bin"

/usr/bin/find \
  "$source_root/delta-node-java/src/main/java/io/deltareduce/node/sidecar" \
  "$source_root/delta-node-java/src/test/java/io/deltareduce/node/sidecar" \
  -type f -name '*.java' -print | LC_ALL=C /usr/bin/sort > "$java_sources"
if [ ! -s "$java_sources" ]; then
  echo "sidecar Java source set is empty" >&2
  exit 2
fi
/opt/java/openjdk/bin/javac \
  --release 25 \
  -Xlint:all \
  -Werror \
  -d "$java_classes" \
  "@$java_sources"
/opt/java/openjdk/bin/jar \
  --create \
  --file "$allocation_root/sidecar-diagnostic-tests.jar" \
  --date=2020-01-01T00:00:00Z \
  -C "$java_classes" .

/usr/bin/mkdir -p "$allocation_root/jdk" "$allocation_root/bin"
/usr/bin/cp -a /opt/java/openjdk/. "$allocation_root/jdk/"
/usr/bin/install -m 0755 /usr/bin/strace "$allocation_root/bin/strace"

for artifact in \
  "$allocation_root/corpus.bin" \
  "$allocation_root/sidecar-diagnostic-tests.jar" \
  "$allocation_root/jdk/bin/java" \
  "$allocation_root/jdk/bin/jfr" \
  "$allocation_root/libdelta_ffi.so" \
  "$allocation_root/delta_runtime_sidecar" \
  "$allocation_root/bin/strace"; do
  if [ ! -s "$artifact" ]; then
    echo "required allocation artifact is missing or empty: $artifact" >&2
    exit 2
  fi
done

/usr/bin/sync -f "$allocation_root"
