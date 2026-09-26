# Native COMMAND/ROUND_STATE byte layer (candidate)

T044/T048/T049/T053/T057/T060; amendment 0001. NO_GO.

NativeStateBytes parses the concrete native DRC1 COMMAND (type 6, eleven exact
fields) and ROUND_STATE (type 5, fourteen exact fields). It preserves every
field, type tag, order, header and original byte sequence. Successful decoding
derives the typed validity conditions and canonical re-encoding; valid encoded
values decode and their encodings are injective. These are general Lean results,
not lookup-based acceptance of complete frames.

Command actor/kind/request/round must be nonempty printable text; body is a
lowercase content ID. Height, logical tick and view use canonical unsigned
decimal text with uint64 limits. Unknown nonempty command kinds can parse,
matching native parse_command; transition admission is a separate requirement.

The state's three ticket counts have the native unsigned tag followed by EIGHT
big-endian bytes. The semantic reader then enforces uint32 and ordered
available <= committed <= total. Sequence/height/view use canonical uint64
decimal text. All six native phase names are checked. Configuration/parent/root
have exact content-ID syntax; zero state sequence is permitted. The codec does
not infer what a state root authenticates or whether this is a legal next state.

The public decode APIs check the fixed known type/schema/field layout, original
merged native semantics cc98f15a..., 16MiB envelope and 4MiB text defaults. Fixed
shapes stay within native default map/depth limits. Low-level scalar/envelope
helpers are compositional encoders for the two fixed shapes; they are not a
general map-key/type registry or proof of arbitrary custom parser limits.
The Python fixture reader has narrower 16KiB/4096-text tooling bounds, which are
not substituted for native default admission limits.

Content-ID helpers bind the exact existing native command or round-state domain,
NUL separator and complete encoded frame. SHA remains a named executable adapter.
Kernel examples use finite exact-preimage digest samples. This is not a SHA proof,
collision-resistance theorem, signature check or authenticated exporter.

The entry inspector reads the actual command and recorded next-state sections
of an already parsed DRW1 transition entry. Its general composition with the
whole-byte scanner retains exact original WAL/frame bytes and the all-entry
sequence. Effects and the inner transition WAL record remain exact opaque bytes
in the Entry. This inspector deliberately does NOT re-execute the transition,
compare its outputs, establish parent/current state or infer recovery readiness.

Three original frames are reused from the pinned prior Windows runtime evidence:
the configured initial state, the FINALIZE_INPUT_FREEZE command, and its recorded
next state. The original two-entry journal remains 3546 bytes. Its state-command
WAL sequence is 2 while the next state's durable transition sequence is 1; the
earlier vote's original receipt remains unchanged. The separate proposal
arithmetic sequences 5/6/8 are not renumbered or claimed as this native history.

A new isolated codec harness compiles three unchanged translation units from
60c692f6e391f839829dfc64e93380db54cd507b. It executes 55 cases (12 accepted,
43 rejected), with exact native parse/re-encode and content-ID comparisons.
Cases cover both layouts, numeric endpoints, field/type/order/constant/text
substitution, inconsistent counts and unknown phases. Unknown nonempty commands
and a different syntactically valid state root are accepted at the codec layer,
and matching Lean counterchecks explicitly preserve this admission gap.
Compiler flags and source blobs are recorded. This is native codec execution,
not a new Runtime/WAL crash run or production arithmetic-admission mutant suite.

The mandatory Lean project/audit includes the general module and generated
vectors. The original frame proofs use per-text/per-field encoding lemmas and
the general decoder inverse; small guard examples use kernel decide. Python
tests reproduce exact output, compare field inventory with pinned C++, and
reject substituted original evidence or forged source metadata before output.
Source pins and self-run logs are not independent authentication or attestation.

Next: implement the concrete native state-command transition relation, exact
effect/inner-WAL byte construction, logical-time/request-cache behavior and
native vote-policy reconstruction from independently bound startup data. Then
compose snapshots, full public histories and known/unknown recovery. Native
RoundState is a summary, not the complete 64-variable public model. A valid
codec result or caller-supplied result equality cannot substitute for that
relation. nativeArithmeticRecoveryRefines, initial snapshots/repair, physical
file/provenance, contract freeze, offline reproduction and independent reviews
remain open. No formal GO or local acceptance PASS is issued.
