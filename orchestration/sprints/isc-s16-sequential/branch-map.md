# ISC S16 sequential branch map

```text
agent/isc-s16-sequential-sprint
  └─ agent/isc-s16-a01-handoff
      ──[2 reviews]→ agent/isc-s16-w1-reference-engine
      ──[2 reviews]→ agent/isc-s16-ed25519-reference
      ──[2 reviews]→ agent/isc-s16-formal-linkage
      ──[2 reviews]→ agent/isc-s16-formal-qualification
      ──[2 reviews]→ terminal
```

Persistent reviewer branches:

- `review/isc-s16-sequential-architecture`
- `review/isc-s16-sequential-evidence`

The existing A01 result is immutable input:

- `agent/isc-s16-contract-freeze@a579a5c66586ba3f8f1d7cc26c454aba5addbd8f`

Every newly created branch derives from `origin/agent/isc-s16-sequential-sprint` so all sprint files
remain available in its ancestry. Reviewer rejection returns the current source node
for rework; STOP/NO_GO goes to the blocked terminal. No node may skip reviewers or
manually select the successor.
