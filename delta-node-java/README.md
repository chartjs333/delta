# delta-node-java

Java conformance boundary for feature 003. `RuntimeDescriptorCompatibility` validates the frozen
descriptor on pinned JDK 25 and JDK 26 toolchains. `NativeRuntimeFfmConformance` uses the standard
Foreign Function & Memory API to load the real C ABI, negotiate output capacity, exercise both
borrowed and copied submission paths, snapshot state and release the opaque handle.

The harness owns no validator state, transition rule, vote journal or native pointer beyond its
declared arena/call lifetime. ABI/schema/protocol/formal/build mismatch cases fail before command
admission. No protobuf, gRPC, Netty or Java transport dependency is introduced; authenticated
transport remains feature 005 scope.
