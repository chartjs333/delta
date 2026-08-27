# delta-node-java

Java orchestration boundary for feature 003. The current test-only compatibility harness decodes
and hashes the frozen canonical runtime descriptor identically on the pinned JDK 25 baseline and
JDK 26 compatibility toolchains. It does not own consensus decisions or native pointers.

Production FFM integration begins only after the native ABI and recovery gates are complete;
authenticated transport remains feature 005 scope.
