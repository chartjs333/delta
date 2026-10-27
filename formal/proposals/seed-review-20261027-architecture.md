# Architecture process review — seed components, 27 October 2026

T047/T053 / ISC-S16-D01. Reviewer role 2791, assignment
`175ecd89-813e-48aa-978b-7537efe5758e`, scope 3, reviewed worker assignment
`20451db6-b10f-4613-96fa-f1fa2e3c4d37` at
`3f51e324624eb4f56711c011d1f7df91e58fc28c`. **REJECT / technical rework**.
Same sequential executor; this is not an independent Formal GO attestation.

The result correctly keeps R2.3 OPEN/NO_GO and explicitly distinguishes the
cross-view factor theorem's local premises from complete source closure. The
selected existing-key seed purpose and isolated T companion are within standing
scope 3. No new semantic choice or authority is requested by this review.

## Must fix: repeated crash promotes a blocked foreign frame

`formal/reference/seed_source/durability.py:crash` unconditionally assigns
`recovery_base=state.stable` and `recovery_target=state.volatile`. After an initial
crash, these buffers can contain an unrecognized tail. A second crash in CRASHED,
BLOCKED or an uncommitted recovery state can replace the ORIGINAL append provenance
with that tail. `recover` then treats the same foreign bytes as an authorized base.

Minimal concrete reference counterexample, using only public synthetic fixture
keys and an initially empty companion:

1. RECEIVE `b"bad"`, barrier, commit. Retain this invalid original occurrence.
2. Append the valid deterministic own DEAL INTENT; do not barrier it.
3. The allowed modeled torn-write region contains a complete alternative RECEIVE
   frame: same original ordinal/predecessor/knowledge binding, payload `b"bad"`,
   correct recomputed frame digest. Its length is within the attempted extent.
4. First crash/recover returns BLOCKED, correctly retaining the unknown frame.
5. Crash that BLOCKED state again with identical surviving bytes; recover now
   returns RECOVERY_VERIFIED, barrier/commit returns READY and knowledge has two
   `b"bad"` occurrences although the second original attempted append was INTENT.

Observed on the reviewed exact head: attempted extent 1352 bytes, alternative
surviving extent 1350 bytes; states BLOCKED → RECOVERY_VERIFIED → READY. This is
an adversarial primitive-model/reference counterexample, not a production disk
attack, real history or complete authenticated snapshot counterexample.

Repair inside the existing contract: preserve the original unresolved append's
base/target across repeated crashes until verified recovery is durably committed;
an arbitrary surviving buffer cannot become its own new source authority. Keep
every observed byte, native WAL and original ordinal unchanged. Add repeated
crash cases before recovery, in BLOCKED, and after recovery verification but
before its barrier/commit. Requalify the corrected reference/Lean association;
do not label the currently checked one-transaction kernel as proving this full
multi-crash association. No new trust, production change, source restriction or
new human decision is necessary.

The worker's component receipt is insufficient for this discovered case. Preserve
the failing reproduction and the previous receipt as history, fix under the next
normal worker assignment, and run applicable checks/reviews again. The remaining
original-index/global-source composition and full R2.3 obligations stay OPEN.

## Rework architecture review at 299b2fed

Current reviewer assignment `3c9d91a3-bdf4-4321-ad25-3fa2634af867`, fresh scope3
ACK GET-confirmed. The worker correction keeps `recovery_active` until verified
commit and does not recapture unknown bytes across further crashes. Repeated
crashes in CRASHED/BLOCKED and after recovery verification/barrier were rerun;
the original foreign frame remains BLOCKED, while a fully verified committed
prefix can begin a new transaction. The Lean origin retention proofs compile
with only standard kernel axioms. **APPROVE the architecture correction**, not
whole source closure, independent attestation or Formal GO.

The second evidence review must address a separately identified source-map gap:
the new durability module imports `formal/reference/profile_source/metadata.py`,
but the component qualifier's sources omit it and its package `__init__.py`.
Complete transitive qualification binding must be repaired/re-run before an
aggregate component acceptance; this architecture APPROVE does not waive that
pending evidence gate. Both files exist at the reviewed Git head; the problem
is incomplete reproducibility/change detection in the qualifier, not a new trust
or source-domain choice. No Pending semantic decision is needed.

## Qualification-source correction at 4e0dcb51

Role 2791 assignment `40a036aa-9498-4f42-8446-e911f60fc1b6`, scope3 exact ACK
GET-confirmed after a transient API failure. **APPROVE this correction**.
Comparison to 299b2fed shows no producer, cryptographic, protocol or Lean change.
The added dependency coverage rejects both omissions found in evidence review;
all receipt source hashes and successful log hashes match the reviewed head.
The runner accurately labels its evidence as executed import closure, without
claiming coverage of unexecuted dynamic imports. The receipt still marks complete
source/producer composition and full R2.3 OPEN/NO_GO. Second process review remains
required. This is the same sequential executor, not independent attestation.
