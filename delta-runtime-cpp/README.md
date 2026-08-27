# delta-runtime-cpp

Feature-003 durable host for the pure consensus transition. Each runtime handle owns one bounded
MPSC submission port and one single-writer reactor; callers never mutate consensus state directly.

For every accepted command the reactor computes the pure transition, appends a canonical
checksummed WAL record with a monotonic sequence, crosses the durability barrier, commits the new
in-memory state and only then releases the canonical effect bytes. A request ID is idempotent;
conflicting reuse is rejected. Effects are never exposed from an append that is torn, corrupt or
not durable.

Startup verifies the snapshot before use, replays the valid WAL suffix in sequence and restores
the durable vote journal before accepting a new command. Recovery rejects checksum corruption,
sequence gaps, conflicting votes and state-root divergence. Replaying an already durable request
returns the same effect bytes. Snapshotting does not weaken WAL verification or vote uniqueness.

Crash injection covers before/during/after append, durability, commit and effect return. The
checked-in exit fixture also compares an uninterrupted runtime with crash/restart byte-for-byte
and runs four independent handles over 100 prepared integer tickets.

This component does not provide sockets, peer discovery, TLS, protobuf/gRPC or P2P distribution.
Those are later-feature adapter responsibilities. Production quantization and clipping are also
outside feature 003.
