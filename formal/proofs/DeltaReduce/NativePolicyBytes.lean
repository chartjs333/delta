import DeltaReduce.NativePolicySchema

/-! Canonical DVPOL001 shape gates, preserving the complete snapshot tree.
No startup state, certificate authority or arithmetic admission is inferred. -/
namespace DeltaReduce.NativePolicyBytes
open NativePolicyCodec NativePolicySchema NativeReceiptBytes

def header : Bytes := [68,86,80,79,76,48,48,49,0,1,0,0,0,0,0,0]
def text (v : Value) : Option Bytes := match v with | .text b => some b | _ => none
def number (v : Value) : Option Nat := match v with | .number n => some n | _ => none
def items (v : Value) : Option (List Value) := match v with | .items vs => some vs | _ => none
def field (f : Format) (v : Value) (key : String) := lookup f v key

structure Candidate where
  action : Nat
  body : Bytes
  context : Bytes
  height : Nat
  view : Nat
  parents : Value
  source : Value
  deriving Repr

def candidate (v : Value) : Option Candidate := do
  let action ← field fmtCandidate v "action" >>= number
  let body ← field fmtCandidate v "body_hash" >>= text
  let context ← field fmtCandidate v "context_id" >>= text
  let height ← field fmtCandidate v "height" >>= number
  let view ← field fmtCandidate v "view" >>= number
  let parents ← field fmtCandidate v "parents"
  some ⟨action,body,context,height,view,parents,v⟩

structure Policy where
  localValidator : Bytes
  epoch : Bytes
  validators : List Bytes
  role : Nat
  round : Bytes
  config : Bytes
  reason : Bytes
  initialTick : Nat
  softDeadline : Nat
  hardDeadline : Nat
  snapshot : Value
  candidates : List Candidate
  source : Value
  deriving Repr

def extract (v : Value) : Option Policy := do
  let localId ← field fmtPolicy v "local_validator_id" >>= text
  let epoch ← field fmtPolicy v "validator_epoch_id" >>= text
  let validators ← field fmtPolicy v "validator_ids" >>= items
  let validators ← validators.mapM text
  let role ← field fmtPolicy v "role" >>= number
  let round ← field fmtPolicy v "round_id" >>= text
  let config ← field fmtPolicy v "round_config_id" >>= text
  let reason ← field fmtPolicy v "configured_abort_reason" >>= text
  let initial ← field fmtPolicy v "initial_logical_tick" >>= number
  let soft ← field fmtPolicy v "soft_deadline_tick" >>= number
  let hard ← field fmtPolicy v "hard_deadline_tick" >>= number
  let snapshot ← field fmtPolicy v "snapshot"
  let cs ← field fmtPolicy v "candidates" >>= items
  let cs ← cs.mapM candidate
  some ⟨localId,epoch,validators,role,round,config,reason,initial,soft,hard,snapshot,cs,v⟩

def bytesLT : Bytes → Bytes → Bool
  | [], [] => false
  | [], _::_ => true
  | _::_, [] => false
  | a::as, b::bs => if a = b then bytesLT as bs else a.toNat < b.toNat

def candidateLT (a b : Candidate) : Bool :=
  if a.height ≠ b.height then a.height < b.height
  else if a.view ≠ b.view then a.view < b.view
  else if a.action ≠ b.action then a.action < b.action
  else bytesLT a.context b.context

def strictly {α : Type} (less : α → α → Bool) : List α → Bool
  | [] => true
  | [_] => true
  | a::b::rest => less a b && strictly less (b::rest)

def ascii (s : String) : Bytes := s.toList.map (fun c => UInt8.ofNat c.toNat)
def reasons : List Bytes :=
  ["HARD_DEADLINE","INCOMPLETE_INPUT","UNSAFE_COEFFICIENTS",
   "IRRECOVERABLE_AVAILABILITY","PARAMETER_FAILURE","APPLY_FAILURE"].map ascii

def Canonical (p : Policy) : Prop :=
  0 < p.validators.length ∧ p.validators.length ≤ 4096 ∧
  strictly bytesLT p.validators = true ∧ p.role = 1 ∧ p.reason ∈ reasons ∧
  0 < p.candidates.length ∧ p.candidates.length ≤ 8192 ∧
  (∀ c ∈ p.candidates, 1 ≤ c.action ∧ c.action ≤ 9) ∧
  strictly candidateLT p.candidates = true ∧ (p.candidates.map Candidate.context).Nodup
instance (p : Policy) : Decidable (Canonical p) := by unfold Canonical; infer_instance

def read (raw : Bytes) : Option (Value × Policy) := do
  if raw.length ≤ 4*1024*1024 then
    let body ← consume header raw
    let v ← decode fmtPolicy body
    let p ← extract v
    if Canonical p then some (v,p) else none
  else none

def decodePolicy (raw : Bytes) : Option (Value × Policy) := do
  let (v,p) ← read raw
  let body ← encode fmtPolicy v
  if header ++ body = raw then some (v,p) else none

theorem readChecks {raw v p} (ok : read raw = some (v,p)) :
    raw.length ≤ 4*1024*1024 ∧ extract v = some p ∧ Canonical p := by
  unfold read at ok
  split at ok
  · rename_i bound
    cases a : consume header raw with
    | none => simp [a] at ok
    | some body =>
      cases b : decode fmtPolicy body with
      | none => simp [a,b] at ok
      | some value =>
        cases c : extract value with
        | none => simp [a,b,c] at ok
        | some policy =>
          simp only [a,b,c,bind,Option.bind] at ok
          split at ok
          · cases Option.some.inj ok; exact ⟨bound,c,‹Canonical _›⟩
          · contradiction
  · contradiction

theorem decoded {raw v p} (ok : decodePolicy raw = some (v,p)) :
    read raw = some (v,p) ∧ ∃ body, encode fmtPolicy v = some body ∧ header ++ body = raw := by
  unfold decodePolicy at ok
  cases a : read raw with
  | none => simp [a] at ok
  | some pair =>
    rcases pair with ⟨value,policy⟩
    cases b : encode fmtPolicy value with
    | none => simp [a,b] at ok
    | some body =>
      simp only [a,b,bind,Option.bind] at ok
      split at ok
      · cases Option.some.inj ok; exact ⟨rfl,body,b,‹header ++ body = raw›⟩
      · contradiction

theorem acceptedCanonical {raw v p} (ok : decodePolicy raw = some (v,p)) : Canonical p :=
  (readChecks (decoded ok).1).2.2

theorem acceptedBound {raw v p} (ok : decodePolicy raw = some (v,p)) :
    raw.length ≤ 4*1024*1024 := (readChecks (decoded ok).1).1

theorem acceptedExtraction {raw v p} (ok : decodePolicy raw = some (v,p)) :
    extract v = some p := (readChecks (decoded ok).1).2.1

theorem encoded {v p body} (bytes : encode fmtPolicy v = some body)
    (projection : extract v = some p) (valid : Canonical p)
    (bound : (header ++ body).length ≤ 4*1024*1024) :
    decodePolicy (header ++ body) = some (v,p) := by
  have decoder := NativePolicyCodec.encoded bytes
  simp only [decodePolicy,read,if_pos bound,consumeAppend,decoder,projection,
    bind,Option.bind,if_pos valid,bytes,ite_true]

theorem treeUnique {raw a pa b pb}
    (ha : decodePolicy raw = some (a,pa)) (hb : decodePolicy raw = some (b,pb)) : a = b := by
  have h := Option.some.inj (ha.symm.trans hb)
  exact congrArg Prod.fst h

theorem originalPayloadRetained {raw v p} (ok : decodePolicy raw = some (v,p)) :
    ∃ body, raw = header ++ body ∧ parse fmtPolicy body = some (v,[]) := by
  obtain ⟨body,enc,eq⟩ := (decoded ok).2
  exact ⟨body,eq.symm,by simpa using roundTrip fmtPolicy v body [] enc⟩

end DeltaReduce.NativePolicyBytes
