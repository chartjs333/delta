# Feature 003 native toolchain lock

These manifests freeze the supported Linux x86_64 reference class before production native
source exists. They do not infer compilers or JDKs from the developer host.

- GCC 14.2.0 and Clang 20.1.8 both compile C++20 baseline and C++23 compatibility modes.
- CMake 4.0.1 and Ninja 1.12.1 archives are content-addressed.
- Compiler source tags/commits are fixed; every execution report must additionally record the
  actual compiler executable SHA-256 and complete version output.
- The feature-003 core/runtime/ABI dependency set starts empty and standard-library-only.
- JDK and jextract locks live at their owning Java/FFI boundaries.

Provisioning may use a pre-populated verified cache. Build and test execution runs with public
network access blocked. Changing a version, source commit, archive hash or supported mode requires
an explicit reviewed lock update and regenerated toolchain evidence.
