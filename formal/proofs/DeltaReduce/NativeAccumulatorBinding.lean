import DeltaReduce.NativeAccumulatorBytes
import DeltaReduce.NativeManifestBinding
import DeltaReduce.FixedPoint

/-! Actual original004 proof/configuration decoding and recomputed bounds.
Hash remains an UNVERIFIED adapter. No theorem-name/PASS field is evidence;
headroom reconstruction is not an authenticated observation of a native call. -/
namespace DeltaReduce.NativeAccumulatorBinding
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ascii ContentId decimalValue digit)
open NativeAccumulatorBytes (Config Proof)

def i64 : Nat := 2^63-1
def u64 : Nat := 2^64-1
def i128 : Nat := 2^127-1
def Width (n : Nat) : Prop := n = 64 ∨ n = 128
instance (n) : Decidable (Width n) := by unfold Width; infer_instance
def limit (n : Nat) : Nat := if n = 64 then i64 else i128

/-- The old vote decimal parser is uint64 only. Proof bounds need all127 bits.
Canonical digits are checked before interpreting; signs and leading zeros fail. -/
def Decimal (maximum : Nat) (raw : Bytes) : Prop :=
  raw ≠ [] ∧ raw.length ≤ 39 ∧
  (raw = [48] ∨ (∃ c ∈ raw.head?, 49 ≤ c.toNat ∧ c.toNat ≤ 57)) ∧
  (∀ c ∈ raw, digit c) ∧ decimalValue raw ≤ maximum
instance (maximum raw) : Decidable (Decimal maximum raw) := by unfold Decimal; infer_instance
def number (maximum : Nat) (raw : Bytes) : Option Nat :=
  if Decimal maximum raw then some (decimalValue raw) else none

theorem numberSource {maximum raw n} (h : number maximum raw = some n) :
    Decimal maximum raw ∧ n = decimalValue raw ∧ n ≤ maximum := by
  unfold number at h
  split at h <;> try contradiction
  rename_i valid
  cases Option.some.inj h
  exact ⟨valid,rfl,valid.2.2.2.2⟩

structure Numbers where
  coefficient : Nat
  count : Nat
  denominator : Nat
  product : Nat
  prefixBound : Nat
  finalBound : Nat
  productBits : Nat
  accumulatorBits : Nat
  deriving DecidableEq, Repr

def NumericValid (n : Numbers) : Prop :=
  0 < n.coefficient ∧ n.coefficient ≤ i64 ∧ 0 < n.count ∧ n.count ≤ u64 ∧
  0 < n.denominator ∧ n.denominator ≤ u64 ∧ Width n.productBits ∧ Width n.accumulatorBits ∧
  n.product = 32767*n.coefficient ∧ n.product ≤ i128 ∧
  n.prefixBound = n.product*n.count ∧ n.prefixBound ≤ i128 ∧
  n.prefixBound ≤ n.finalBound ∧ n.finalBound ≤ i128 ∧
  n.product ≤ limit n.productBits ∧ n.finalBound ≤ limit n.accumulatorBits
instance (n) : Decidable (NumericValid n) := by unfold NumericValid; infer_instance

def readNumbers (p : Proof) : Option Numbers := do
  let a ← number i64 p.coefficient
  let n ← number u64 p.count
  let d ← number u64 p.denominator
  let product ← number i128 p.product
  let prefixBound ← number i128 p.prefixBound
  let finalBound ← number i128 p.finalBound
  let productBits ← number u64 p.productWidth
  let bits ← number u64 p.width
  let ns := Numbers.mk a n d product prefixBound finalBound productBits bits
  if NumericValid ns then some ns else none

structure NumericSource (p : Proof) (n : Numbers) : Prop where
  coefficient : number i64 p.coefficient = some n.coefficient
  count : number u64 p.count = some n.count
  denominator : number u64 p.denominator = some n.denominator
  product : number i128 p.product = some n.product
  prefixBound : number i128 p.prefixBound = some n.prefixBound
  finalBound : number i128 p.finalBound = some n.finalBound
  productBits : number u64 p.productWidth = some n.productBits
  accumulatorBits : number u64 p.width = some n.accumulatorBits
  valid : NumericValid n

theorem numbersSource {p n} (h : readNumbers p = some n) : NumericSource p n := by
  simp only [readNumbers,bind,Option.bind_eq_some_iff] at h
  obtain ⟨a,ha,c,hc,d,hd,pr,hpr,pf,hpf,f,hf,pb,hpb,ab,hab,last⟩ := h
  split at last <;> try contradiction
  rename_i valid
  cases Option.some.inj last
  exact ⟨ha,hc,hd,hpr,hpf,hf,hpb,hab,valid⟩

theorem numbersFromSource {p n} (h : NumericSource p n) : readNumbers p = some n := by
  simp only [readNumbers,h.coefficient,h.count,h.denominator,h.product,h.prefixBound,
    h.finalBound,h.productBits,h.accumulatorBits,bind,Option.bind]
  exact if_pos h.valid

def headroom (n : Numbers) : Nat := n.finalBound - n.prefixBound

theorem reconstructedHeadroom {n} (h : NumericValid n) :
    n.prefixBound + headroom n = n.finalBound := by
  rcases h with ⟨_,_,_,_,_,_,_,_,_,_,_,_,lower,_⟩
  exact Nat.add_sub_of_le lower

theorem admissibleHeadroomUnique {n} (h : NumericValid n) (observed : Nat)
    (nativeEquation : n.prefixBound + observed = n.finalBound) : observed = headroom n := by
  have exactSum := reconstructedHeadroom h
  omega

theorem computedBounds {n} (h : NumericValid n) :
    n.product = 32767*n.coefficient ∧
    n.prefixBound = 32767*n.coefficient*n.count ∧
    n.product ≤ limit n.productBits ∧ n.prefixBound ≤ limit n.accumulatorBits := by
  rcases h with ⟨_,_,_,_,_,_,_,_,product,_,prefixEq,_,lower,_,pw,aw⟩
  exact ⟨product,by rw [prefixEq,product],pw,lower.trans aw⟩

/-- The actual coefficient/count/Q premises are explicit, not inferred from
metadata names or a manifest of one contribution. -/
theorem everyBoundedProduct {n} (h : NumericValid n) (a q : Int)
    (ha : |a| ≤ (n.coefficient : Int)) (hq : |q| ≤ 32767) :
    |a*q| ≤ (limit n.productBits : Int) := by
  have b := computedBounds h
  have wide : (n.coefficient : Int)*32767 ≤ (limit n.productBits : Int) := by
    have hp : n.coefficient*32767 ≤ limit n.productBits := by
      simpa [b.1,Nat.mul_comm] using b.2.2.1
    exact_mod_cast hp
  exact intermediateProductFits a q n.coefficient 32767 (limit n.productBits)
    (Int.natCast_nonneg _) (by decide) ha hq wide

open scoped BigOperators
theorem everyBoundedPrefix {n} (h : NumericValid n) {ι : Type*} [DecidableEq ι]
    (tickets : Finset ι) (a q : ι → Int) (size : tickets.card ≤ n.count)
    (coefficients : ∀ j ∈ tickets, |a j| ≤ (n.coefficient : Int))
    (quantized : ∀ j ∈ tickets, |q j| ≤ 32767) :
    ∀ subset : Finset ι, subset ⊆ tickets →
      |∑ j ∈ subset, a j*q j| ≤ (limit n.accumulatorBits : Int) := by
  have b := computedBounds h
  have hn : n.count*n.coefficient*32767 ≤ limit n.accumulatorBits := by
    simpa [b.2.1,Nat.mul_assoc,Nat.mul_comm,Nat.mul_left_comm] using b.2.2.2
  have hi : (n.count : Int)*n.coefficient*32767 ≤ (limit n.accumulatorBits : Int) := by
    exact_mod_cast hn
  exact everyCanonicalPrefixFits tickets a q n.count n.coefficient 32767
    (limit n.accumulatorBits) size (Int.natCast_nonneg _) (by decide)
    coefficients quantized hi

def configInput (raw : Bytes) := ascii "deltareduce.004.fixedpoint-config.v1" ++ [0] ++ raw
def proofInput (raw : Bytes) := ascii "deltareduce.004.proof-instance.v1" ++ [0] ++ raw
def profileInput (raw : Bytes) := ascii "deltareduce.004.profile.v1" ++ [0] ++ raw
def historicalLean : Bytes := ascii
  "sha256:6d8c715eacf55f99a2bbc5fca7242610d871a1ef76ae58d51305b81e66364736"

/-- Entire immutable original004 worker profile; independent from APPLY. -/
def workerProfileBytes : Bytes := [123, 34, 97, 99, 99, 117, 109, 117, 108, 97, 116, 111, 114, 95, 119, 105, 100, 116, 104, 115, 34, 58, 91, 54, 52, 44, 49, 50, 56, 93, 44, 34, 98, 121, 116, 101, 95, 111, 114, 100, 101, 114, 34, 58, 34, 76, 73, 84, 84, 76, 69, 95, 69, 78, 68, 73, 65, 78, 34, 44, 34, 101, 108, 101, 109, 101, 110, 116, 95, 101, 110, 99, 111, 100, 105, 110, 103, 34, 58, 34, 83, 73, 71, 78, 69, 68, 95, 84, 87, 79, 83, 95, 67, 79, 77, 80, 76, 69, 77, 69, 78, 84, 95, 73, 78, 84, 49, 54, 34, 44, 34, 102, 111, 114, 109, 97, 108, 95, 115, 101, 109, 97, 110, 116, 105, 99, 115, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 99, 99, 57, 56, 102, 49, 53, 97, 99, 50, 48, 102, 99, 51, 101, 100, 50, 54, 53, 99, 98, 55, 54, 54, 56, 50, 99, 97, 49, 53, 97, 57, 51, 54, 101, 50, 52, 54, 54, 48, 97, 54, 53, 49, 101, 50, 98, 56, 102, 56, 49, 54, 51, 56, 97, 98, 98, 51, 50, 54, 53, 99, 98, 54, 34, 44, 34, 108, 105, 109, 105, 116, 115, 34, 58, 123, 34, 109, 97, 120, 95, 104, 101, 97, 100, 101, 114, 95, 98, 121, 116, 101, 115, 34, 58, 54, 53, 53, 51, 54, 44, 34, 109, 97, 120, 95, 112, 97, 121, 108, 111, 97, 100, 95, 98, 121, 116, 101, 115, 34, 58, 49, 48, 52, 56, 53, 55, 54, 44, 34, 109, 97, 120, 95, 115, 101, 103, 109, 101, 110, 116, 115, 34, 58, 54, 53, 53, 51, 54, 44, 34, 109, 97, 120, 95, 115, 104, 97, 114, 100, 115, 34, 58, 52, 48, 57, 54, 44, 34, 109, 97, 120, 95, 116, 111, 116, 97, 108, 95, 101, 108, 101, 109, 101, 110, 116, 115, 34, 58, 49, 48, 55, 51, 55, 52, 49, 56, 50, 52, 125, 44, 34, 111, 117, 116, 95, 111, 102, 95, 114, 97, 110, 103, 101, 95, 97, 99, 116, 105, 111, 110, 34, 58, 34, 82, 69, 74, 69, 67, 84, 34, 44, 34, 112, 114, 111, 102, 105, 108, 101, 95, 110, 97, 109, 101, 34, 58, 34, 105, 110, 116, 49, 54, 45, 102, 105, 120, 101, 100, 45, 118, 49, 34, 44, 34, 113, 95, 109, 97, 120, 34, 58, 51, 50, 55, 54, 55, 44, 34, 113, 95, 109, 105, 110, 34, 58, 45, 51, 50, 55, 54, 55, 44, 34, 114, 101, 115, 105, 100, 117, 97, 108, 95, 109, 111, 100, 101, 34, 58, 34, 70, 79, 82, 66, 73, 68, 68, 69, 78, 34, 44, 34, 114, 111, 117, 110, 100, 105, 110, 103, 34, 58, 34, 82, 79, 85, 78, 68, 95, 84, 79, 95, 78, 69, 65, 82, 69, 83, 84, 95, 84, 73, 69, 83, 95, 84, 79, 95, 69, 86, 69, 78, 34, 44, 34, 115, 99, 97, 108, 101, 95, 103, 114, 97, 110, 117, 108, 97, 114, 105, 116, 121, 34, 58, 34, 67, 65, 78, 79, 78, 73, 67, 65, 76, 95, 80, 65, 82, 65, 77, 69, 84, 69, 82, 95, 83, 69, 71, 77, 69, 78, 84, 34, 44, 34, 115, 99, 97, 108, 101, 95, 114, 101, 112, 114, 101, 115, 101, 110, 116, 97, 116, 105, 111, 110, 34, 58, 34, 82, 69, 68, 85, 67, 69, 68, 95, 80, 79, 83, 73, 84, 73, 86, 69, 95, 82, 65, 84, 73, 79, 78, 65, 76, 95, 85, 51, 50, 34, 44, 34, 115, 99, 104, 101, 109, 97, 95, 118, 101, 114, 115, 105, 111, 110, 34, 58, 34, 49, 46, 48, 46, 48, 34, 44, 34, 115, 111, 117, 114, 99, 101, 95, 114, 101, 112, 114, 101, 115, 101, 110, 116, 97, 116, 105, 111, 110, 34, 58, 34, 82, 69, 68, 85, 67, 69, 68, 95, 82, 65, 84, 73, 79, 78, 65, 76, 95, 73, 54, 52, 95, 85, 51, 50, 34, 44, 34, 116, 114, 97, 105, 108, 105, 110, 103, 95, 98, 121, 116, 101, 115, 95, 97, 99, 116, 105, 111, 110, 34, 58, 34, 82, 69, 74, 69, 67, 84, 34, 44, 34, 116, 121, 112, 101, 95, 110, 97, 109, 101, 34, 58, 34, 70, 73, 88, 69, 68, 95, 80, 79, 73, 78, 84, 95, 80, 82, 79, 70, 73, 76, 69, 34, 125]

def Metadata (c : Config) (p : Proof) : Prop :=
  c.semantics = NativeVoteBytes.nativeSemantics ∧ p.semantics = c.semantics ∧
  c.profile = NativeQHeader.nativeProfile ∧ p.profile = c.profile ∧
  c.version = ascii "1.0.0" ∧ p.version = c.version ∧
  c.kind = ascii "FIXEDPOINT_ROUND_CONFIG" ∧ p.kind = ascii "ACCUMULATOR_PROOF_INSTANCE" ∧
  p.lean = historicalLean ∧ p.result = ascii "PASS" ∧
  p.coefficient = c.coefficient ∧ p.count = c.count ∧
  p.q = ascii "32767" ∧ p.q = c.q ∧ p.width = c.width ∧ p.scale = c.scale ∧
  (∀ id ∈ [c.base,c.schema,c.scale,c.plan,p.config], ContentId id)
instance (c p) : Decidable (Metadata c p) := by unfold Metadata; infer_instance

structure Bound where
  config : Config
  proof : Proof
  numbers : Numbers
  deriving DecidableEq, Repr

def load (hash : Bytes → Bytes) (configRaw proofRaw profileRaw proofId : Bytes) : Option Bound := do
  let c ← NativeAccumulatorBytes.decodeConfig configRaw
  let p ← NativeAccumulatorBytes.decodeProof proofRaw
  let n ← readNumbers p
  if Metadata c p ∧ profileRaw = workerProfileBytes ∧
      hash (profileInput profileRaw) = c.profile ∧ hash (configInput configRaw) = p.config ∧
      ContentId proofId ∧ hash (proofInput proofRaw) = proofId then
    some ⟨c,p,n⟩ else none

structure Source (hash : Bytes → Bytes) (configRaw proofRaw profileRaw proofId : Bytes)
    (b : Bound) : Prop where
  config : NativeAccumulatorBytes.decodeConfig configRaw = some b.config
  proof : NativeAccumulatorBytes.decodeProof proofRaw = some b.proof
  numbers : readNumbers b.proof = some b.numbers
  metadata : Metadata b.config b.proof
  profile : profileRaw = workerProfileBytes
  profileId : hash (profileInput profileRaw) = b.config.profile
  configId : hash (configInput configRaw) = b.proof.config
  proofId : ContentId proofId ∧ hash (proofInput proofRaw) = proofId

theorem loadedSource {hash configRaw proofRaw profileRaw proofId b}
    (h : load hash configRaw proofRaw profileRaw proofId = some b) :
    Source hash configRaw proofRaw profileRaw proofId b := by
  simp only [load,bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,hc,p,hp,n,hn,last⟩ := h
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  exact ⟨hc,hp,hn,checks.1,checks.2.1,checks.2.2.1,checks.2.2.2.1,checks.2.2.2.2⟩

theorem loadFromSource {hash configRaw proofRaw profileRaw proofId b}
    (h : Source hash configRaw proofRaw profileRaw proofId b) :
    load hash configRaw proofRaw profileRaw proofId = some b := by
  simp only [load,h.config,h.proof,h.numbers,bind,Option.bind]
  exact if_pos ⟨h.metadata,h.profile,h.profileId,h.configId,h.proofId⟩

theorem originalPreimages {hash configRaw proofRaw profileRaw proofId b}
    (h : load hash configRaw proofRaw profileRaw proofId = some b) :
    NativeAccumulatorBytes.encodeConfig b.config = configRaw ∧
    NativeAccumulatorBytes.encodeProof b.proof = proofRaw ∧ profileRaw = workerProfileBytes := by
  have src := loadedSource h
  exact ⟨(NativeAccumulatorBytes.decodedConfig src.config).2.2.2,
    (NativeAccumulatorBytes.decodedProof src.proof).2.2.2,src.profile⟩

def CorpusLinks (m : NativeManifestBinding.Bound) (b : Bound) : Prop :=
  b.proof.config = m.manifest.wire.config ∧ b.config.schema = m.manifest.wire.schema ∧
  b.config.plan = m.manifest.wire.plan ∧ b.config.scale = m.manifest.wire.scale ∧
  b.config.profile = m.manifest.wire.profile ∧ b.config.semantics = m.manifest.wire.semantics
instance (m b) : Decidable (CorpusLinks m b) := by unfold CorpusLinks; infer_instance

structure BoundCorpus where
  manifest : NativeManifestBinding.Bound
  bounds : Bound
  deriving DecidableEq, Repr

def bindCorpus (hash : Bytes → Bytes)
    (schemaRaw scaleRaw planRaw manifestRaw manifestId configRaw proofRaw profileRaw : Bytes)
    (raws : List Bytes) : Option BoundCorpus := do
  let m ← NativeManifestBinding.bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws
  let b ← load hash configRaw proofRaw profileRaw m.manifest.wire.proof
  if CorpusLinks m b then some ⟨m,b⟩ else none

theorem corpusSource {hash schemaRaw scaleRaw planRaw manifestRaw manifestId
    configRaw proofRaw profileRaw raws b}
    (h : bindCorpus hash schemaRaw scaleRaw planRaw manifestRaw manifestId
      configRaw proofRaw profileRaw raws = some b) :
    NativeManifestBinding.bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some b.manifest ∧
    load hash configRaw proofRaw profileRaw b.manifest.manifest.wire.proof = some b.bounds ∧
    CorpusLinks b.manifest b.bounds := by
  simp only [bindCorpus,bind,Option.bind_eq_some_iff] at h
  obtain ⟨m,hm,out,ho,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨hm,ho,by assumption⟩

theorem corpusFromSources {hash schemaRaw scaleRaw planRaw manifestRaw manifestId
    configRaw proofRaw profileRaw raws m b}
    (manifest : NativeManifestBinding.bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some m)
    (bounds : load hash configRaw proofRaw profileRaw m.manifest.wire.proof = some b)
    (links : CorpusLinks m b) :
    bindCorpus hash schemaRaw scaleRaw planRaw manifestRaw manifestId configRaw proofRaw profileRaw raws =
      some ⟨m,b⟩ := by simp [bindCorpus,manifest,bounds,links]

theorem corpusKeepsEveryBlock {hash schemaRaw scaleRaw planRaw manifestRaw manifestId
    configRaw proofRaw profileRaw raws b}
    (h : bindCorpus hash schemaRaw scaleRaw planRaw manifestRaw manifestId
      configRaw proofRaw profileRaw raws = some b) :
    b.manifest.plan.plan.entries.length = raws.length ∧ raws.length = b.manifest.blocks.length :=
  NativeManifestBinding.noMissingOrExtraBlocks (corpusSource h).1

end DeltaReduce.NativeAccumulatorBinding
