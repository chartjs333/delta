# Checklist: 005 Java Transport Boundary

- [x] Java owns network mechanics but not consensus validity.
- [x] Zero-copy is optional and has an identical bounded-copy fallback.
- [x] Native pointer retention and Java-memory free are forbidden.
- [x] Event loops cannot execute blocking FFM/WAL/CAS operations.
- [x] Discovery is non-authoritative and certification downgrade fails closed.
- [x] Buffer leaks, stream bounds, restart and seed loss are measurable gates.
