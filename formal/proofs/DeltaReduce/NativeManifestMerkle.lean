import DeltaReduce.NativeVoteBytes
/-! Original004 ordered Merkle recurrence. The hash function is UNVERIFIED. -/
namespace DeltaReduce.NativeManifestMerkle
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ascii ContentId)

def nibble (c : UInt8) : Nat := if c.toNat ≤ 57 then c.toNat-48 else c.toNat-87

def unhex : Bytes → Option Bytes
  | [] => some []
  | [_] => none
  | a::b::rest => if NativeVoteBytes.hexDigit a ∧ NativeVoteBytes.hexDigit b then
      (unhex rest).map (UInt8.ofNat (16*nibble a+nibble b) :: ·) else none

theorem unhexLength {raw out} (h : unhex raw = some out) : raw.length = 2*out.length := by
  match raw with
  | [] => simp [unhex] at h; subst out; rfl
  | [_] => simp [unhex] at h
  | a::b::rest =>
    simp only [unhex] at h
    split at h <;> try contradiction
    simp only [Option.map_eq_some_iff] at h
    obtain ⟨tail,ht,last⟩ := h
    subst out
    have len := unhexLength ht
    simp only [List.length_cons]; omega

def digest (id : Bytes) : Option Bytes :=
  if ContentId id then unhex (id.drop 7) else none

theorem digestLength {id out} (h : digest id = some out) : out.length = 32 := by
  unfold digest at h
  split at h <;> try contradiction
  rename_i valid
  have len := unhexLength h
  have size := valid.1
  simp only [List.length_drop] at len
  omega

def nodeInput (a b : Bytes) := ascii "deltareduce.004.merkle-node.v1" ++ [0] ++ a ++ b

def pair (hash : Bytes → Bytes) (a b : Bytes) : Option Bytes := do
  let da ← digest a
  let db ← digest b
  let result := hash (nodeInput da db)
  if ContentId result then some result else none

theorem pairSource {hash a b out} (h : pair hash a b = some out) :
    ∃ da db, digest a = some da ∧ digest b = some db ∧
    da.length = 32 ∧ db.length = 32 ∧ out = hash (nodeInput da db) ∧ ContentId out := by
  simp only [pair,bind,Option.bind_eq_some_iff] at h
  obtain ⟨da,ha,db,hb,last⟩ := h
  split at last <;> try contradiction
  rename_i valid
  cases Option.some.inj last
  exact ⟨da,db,ha,hb,digestLength ha,digestLength hb,rfl,valid⟩

theorem pairFromSource {hash a b da db out}
    (ha : digest a = some da) (hb : digest b = some db)
    (hh : hash (nodeInput da db) = out) (valid : ContentId out) :
    pair hash a b = some out := by
  simp [pair,ha,hb,hh,valid]

def level (hash : Bytes → Bytes) : List Bytes → Option (List Bytes)
  | [] => some []
  | [a] => (pair hash a a).map (· :: [])
  | a::b::rest => do
      let p ← pair hash a b
      let tail ← level hash rest
      some (p::tail)

inductive Layer (hash : Bytes → Bytes) : List Bytes → List Bytes → Prop
  | nil : Layer hash [] []
  | odd {a p} (checked : pair hash a a = some p) : Layer hash [a] [p]
  | cons {a b p rest tail} (checked : pair hash a b = some p)
      (remaining : Layer hash rest tail) : Layer hash (a::b::rest) (p::tail)

theorem levelSource {hash xs ys} (h : level hash xs = some ys) : Layer hash xs ys := by
  match xs with
  | [] => simp [level] at h; subst ys; exact .nil
  | [a] =>
    simp only [level,Option.map_eq_some_iff] at h
    obtain ⟨p,hp,last⟩ := h; subst ys; exact .odd hp
  | a::b::rest =>
    simp only [level,bind,Option.bind_eq_some_iff] at h
    obtain ⟨p,hp,tail,ht,last⟩ := h
    cases Option.some.inj last
    exact .cons hp (levelSource ht)

theorem levelLength {hash xs ys} (h : Layer hash xs ys) : ys.length = (xs.length+1)/2 := by
  induction h with
  | nil => rfl
  | odd => simp
  | cons checked remaining ih => simp only [List.length_cons]; omega

def tree (hash : Bytes → Bytes) : Nat → List Bytes → Option Bytes
  | 0,_ => none
  | _+1,[] => none
  | _+1,[a] => if ContentId a then some a else none
  | n+1,a::b::rest => do
      let next ← level hash (a::b::rest)
      tree hash n next

inductive Tree (hash : Bytes → Bytes) : List Bytes → Bytes → Prop
  | leaf {a} (valid : ContentId a) : Tree hash [a] a
  | step {a b rest next root} (layer : Layer hash (a::b::rest) next)
      (remaining : Tree hash next root) : Tree hash (a::b::rest) root

theorem treeSource {hash fuel leaves root} (h : tree hash fuel leaves = some root) :
    Tree hash leaves root := by
  induction fuel generalizing leaves with
  | zero => simp [tree] at h
  | succ n ih =>
    match leaves with
    | [] => simp [tree] at h
    | [a] =>
      simp only [tree] at h
      split at h <;> try contradiction
      cases Option.some.inj h
      exact .leaf (by assumption)
    | a::b::rest =>
      simp only [tree,bind,Option.bind_eq_some_iff] at h
      obtain ⟨next,hn,hr⟩ := h
      exact .step (levelSource hn) (ih hr)

def root (hash : Bytes → Bytes) (leaves : List Bytes) : Option Bytes :=
  if 0 < leaves.length ∧ leaves.length ≤ 4096 ∧ (∀ id ∈ leaves, ContentId id) then
    tree hash 13 leaves else none

theorem rootSource {hash leaves out} (h : root hash leaves = some out) :
    0 < leaves.length ∧ leaves.length ≤ 4096 ∧ (∀ id ∈ leaves, ContentId id) ∧ Tree hash leaves out := by
  unfold root at h
  split at h <;> try contradiction
  rename_i checks
  exact ⟨checks.1,checks.2.1,checks.2.2,treeSource h⟩

end DeltaReduce.NativeManifestMerkle
