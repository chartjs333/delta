# Formal and Feature 010 Prerequisite

No remote provisioning or training may begin unless both the exact accepted
`FormalVerificationReport(GO)` and a compatible Feature 010
`BenchmarkResultQC(GO)` verify under the same semantics/profile lineage.

The PilotDefinition must bind their report/evidence roots, source/tree, protocol,
model/data/ticket/arithmetic profiles, selected embedded/sidecar profile, and
validity window. Any mismatch is STOP.

Mandatory pilot trace projection includes normal certified rounds, view change,
hard abort, crash before/after durable vote/send, journal recovery/replay,
pre/post-ISC storage loss, partition with/without quorum, mixed-certificate
attempts, apply disagreement/quorum loss, crash after ApplyQC before pointer,
P2P seed loss, emergency stop, and key/epoch rotation.

Any real behavior that cannot project to an accepted formal transition, violates a
proof precondition, or differs from the preregistered terminal outcome is a
mandatory gate failure. Missing formal evidence is never GO.

Current state: Formal GO verifies, but Feature 010 GO is absent; admission is
therefore closed.
