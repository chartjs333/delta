# MNIST Delta Netty relay

This directory contains a demo-only adapter that sends already signed, opaque MNIST contribution
bytes over a real Netty loopback TCP connection. The receiver uses the existing
`BenchmarkTransport`, persists every payload with an atomic move, and verifies its exact size and
SHA-256 content identity.

This is deliberately **not** a consensus or governance authority. It does not invoke the C ABI,
native WAL, ISC/QC/APPLY transitions, aggregation, training, or Campaign 02 execution. Its receipt
proves only the local Java/Netty transfer and exact-byte persistence described above.

It is also not the deployable `delta-node-java` service and does not exercise production TLS,
peer routing, admission policy, or WAN behavior. The end-to-end demo invokes the native adapter
only after this relay has completed and its byte-preservation evidence has been validated.

## Interface

```text
MnistDeltaNettyRelay MANIFEST OUTPUT_ROOT RECEIPT TRACE
```

`MANIFEST` is an absolute path to a UTF-8 TSV file with no header. Each line has exactly five
fields:

```text
source_abs<TAB>destination_relative<TAB>sha256:<64-lowercase-hex><TAB>public_key_base64<TAB>signature_base64
```

The source path must be absolute. Destinations are portable ASCII paths relative to `OUTPUT_ROOT`.
Duplicate sources, destinations, and content IDs are rejected. Existing outputs, symlinks, path
traversal, overlong inputs, and parent/child target collisions are also rejected.

The signature is Ed25519 over these exact bytes:

```text
ASCII("deltareduce.mnist-demo.transport.v1") || 0x00 || source_file_bytes
```

`RECEIPT` and `TRACE` may be relative to `OUTPUT_ROOT` or absolute paths contained by that root.
They and all destination files are create-only. The compact JSON receipt includes the process ID,
component identity `delta-node-java/netty`, ordered input/output content IDs, exact output sizes,
and transport metrics. The JSONL trace contains ordered `SOURCE_VERIFIED`, `NETTY_TRANSMITTED`,
`NETTY_RECEIVED`, and `ATOMIC_WRITE_VERIFIED` events with input/output content IDs.

## Compilation

Compile on JDK 25 with `-Xlint:all -Werror`, providing the repository's pinned Netty jars on the
classpath. The adapter intentionally reuses these production benchmark helpers without modifying
them:

```text
delta-node-java/src/main/java/io/deltareduce/node/benchmark/BenchmarkContracts.java
delta-node-java/src/main/java/io/deltareduce/node/benchmark/BenchmarkTransport.java
delta-node-java/src/main/java/io/deltareduce/node/benchmark/NettyMetricsCollector.java
```

Then compile this source in the same invocation:

```text
integration/mnist-delta/java/io/deltareduce/demo/MnistDeltaNettyRelay.java
```

Run with a classpath containing the resulting classes plus the same pinned Netty jars. Successful
execution writes the receipt to the requested path and prints the identical compact JSON object to
standard output. Any validation, signature, transport, persistence, or coverage failure exits with
status 2 and does not create a PASS receipt.
