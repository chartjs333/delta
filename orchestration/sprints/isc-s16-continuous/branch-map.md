# ISC S16 continuous branch map

```text
agent/isc-s16-continuous-sprint  (canonical sprint + coordinator-owned fixes)
  ├─ agent/isc-s16-w1-reference-engine
  ├─ agent/isc-s16-ed25519-reference
  ├─ agent/isc-s16-formal-linkage
  └─ agent/isc-s16-formal-qualification
```

Persistent process-review branches:

- `review/isc-s16-continuous-architecture`
- `review/isc-s16-continuous-evidence`

Historical immutable inputs:

- `agent/isc-s16-contract-freeze@a579a5c66586ba3f8f1d7cc26c454aba5addbd8f`
- `agent/isc-s16-a01-handoff@85a2a526468293e90daf019c0e10781e3d753a8c`

Routing:

```text
Coordinator --START_W1/RESUME_W1--> W1
W1 --DONE--> Crypto
W1 --STOP/NEED_DECISION--> Coordinator

Crypto --DONE--> Formal
Crypto --STOP/NEED_DECISION--> Coordinator

Formal --GO--> Qualification
Formal --NO_GO/STOP/NEED_DECISION--> Coordinator

Qualification --GO--> completed
Qualification --NO_GO/STOP/NEED_DECISION--> Coordinator
```

There is no explicit `blocked` terminal. Coordinator decisions are source-bound and
reviewed before routing. Reference work never becomes production authority merely by
passing this graph.
