"""Reproduce the original single-instance composition defect; public test keys only."""

import json

from formal.reference.seed_source import durability as d
from formal.reference.seed_source import generation as g
from formal.reference.seed_source.test_source_history import Capture, SourceHistoryTests, event

SourceHistoryTests.setUpClass()
t = SourceHistoryTests()
other = dict(t.ctx, round_id="second-original-round", height="2")
state = d.initial(t.group, t.boot, other, t.bootstrap_id, t.actor, t.native_wal)
capture = Capture(state).record("INTENT", g.deal_body(t.group, t.boot, other, t.actor, t.seeds[t.actor]))
capture, signed = capture.sign(1, t.seeds[t.actor])
capture.record("SIGNED", signed, 1).step("EXPOSE", ordinal=1)
rows = list(t.capture.events)
for old in capture.events:
    rows.append(event(len(rows), old.actor, old.action, old.original, old.inputs))
trace = t.fold(rows)
print(json.dumps({
    "claim": "single-instance facet composition only; not a full lawful snapshot",
    "original_event_count": len(rows),
    "unresolved": trace.unresolved,
    "second_original_SIGN": len(t.capture.events) + 3,
    "native_wal_preserved": trace.state.native_wal == t.native_wal,
}))
