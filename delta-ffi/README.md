# delta-ffi

Feature-003 ownership boundary for the versioned C ABI. The `delta_ffi` CMake target is isolated
now and depends on the native runtime boundary; the opaque ABI and generated JDK 25 FFM bindings
follow after native recovery is proven. No C++ ABI or Java-owned pointer retention is exposed.
