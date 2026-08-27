# delta-runtime-cpp

Feature-003 ownership boundary for the single-writer consensus reactor, WAL, snapshots and
persist-before-expose recovery. The `delta_runtime` CMake target is isolated now; durability source
is introduced only after the pure transition core passes its canonical-byte gates.
