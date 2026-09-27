import DeltaReduce.NativeSchemaBinding

/-! Executable original004 shard partition. Fuel rejects incomplete plans;
no caller-supplied partition, hash identity or manifest authority. -/
namespace DeltaReduce.NativeShardPartition
open NativeReceiptBytes (Bytes)

structure Entry where
  count : Nat
  start : Nat
  ordinal : Nat
  payload : Nat
  name : Bytes
  offset : Nat
  deriving DecidableEq, Repr

def chunks : Nat → Nat → Bytes → Nat → Nat → Nat → Nat → Option (List Entry)
  | 0, _, _, _, _, left, _ => if left = 0 then some [] else none
  | fuel+1, width, name, base, offset, left, ordinal =>
      if left = 0 then some [] else
        let count := min width left
        if count = 0 then none else do
          let tail ← chunks fuel width name base (offset+count) (left-count) (ordinal+1)
          some (⟨count,base+offset,ordinal,2*count,name,offset⟩::tail)

def rows : Nat → List NativeSchemaBinding.Row → Nat → Nat → Option (List Entry)
  | _, [], _, _ => some []
  | fuel, r::rs, width, ordinal => do
      let head ← chunks fuel width r.name r.start 0 r.count ordinal
      let tail ← rows (fuel-head.length) rs width (ordinal+head.length)
      some (head++tail)

def Target (target : Nat) : Prop := 2 ≤ target ∧ target ≤ 1048576 ∧ target % 2 = 0
instance (target) : Decidable (Target target) := by unfold Target; infer_instance

def build (s : NativeSchemaBinding.Schema) (target : Nat) : Option (List Entry) :=
  if Target target then rows 4096 s.rows (target/2) 0 else none

inductive Span : Nat → Nat → List Entry → Nat → Prop where
  | nil (start ordinal) : Span start ordinal [] start
  | cons {start ordinal e es stop} : e.start = start → e.ordinal = ordinal →
      0 < e.count → Span (start+e.count) (ordinal+1) es stop →
      Span start ordinal (e::es) stop

theorem spanTotal {start ordinal es stop} (h : Span start ordinal es stop) :
    start + (es.map Entry.count).sum = stop := by
  induction h with
  | nil => simp
  | cons _ _ _ _ ih => simpa [Nat.add_assoc] using ih

theorem spanAppend {a n xs b ys c} (h : Span a n xs b)
    (tail : Span b (n+xs.length) ys c) : Span a n (xs++ys) c := by
  induction h with
  | nil => simpa using tail
  | cons start ordinal positive _ ih =>
    apply Span.cons start ordinal positive
    apply ih
    simpa [Nat.add_assoc,Nat.add_comm,Nat.add_left_comm] using tail

theorem spanBounds {a n xs b} (h : Span a n xs b) {e} (mem : e ∈ xs) :
    a ≤ e.start ∧ e.start+e.count ≤ b ∧ 0 < e.count := by
  induction h with
  | nil => simp at mem
  | @cons a n head es b hs ho positive tail ih =>
    rcases List.mem_cons.mp mem with rfl | hm
    · have total := spanTotal tail
      exact ⟨by omega,by omega,positive⟩
    · have result := ih hm
      exact ⟨by omega,result.2⟩

theorem spanOrdered {a n xs b} (h : Span a n xs b) :
    xs.Pairwise (fun x y => x.start+x.count ≤ y.start ∧ x.ordinal < y.ordinal) := by
  have indexed : ∀ {a n xs b}, Span a n xs b → ∀ e ∈ xs, n ≤ e.ordinal := by
    intro a n xs b h
    induction h with
    | nil => simp
    | cons hs ho positive tail ih =>
      intro e mem
      rcases List.mem_cons.mp mem with rfl | hm
      · omega
      · have := ih e hm; omega
  induction h with
  | nil => simp
  | cons hs ho positive tail ih =>
    apply List.pairwise_cons.mpr
    refine ⟨?_,ih⟩
    intro e mem
    have bounds := spanBounds tail mem
    have ord := indexed tail e mem
    exact ⟨by omega,by omega⟩

theorem spanCovers {a n xs b} (h : Span a n xs b) (c : Nat) (inside : a ≤ c ∧ c < b) :
    ∃ e ∈ xs, e.start ≤ c ∧ c < e.start+e.count := by
  induction h with
  | nil => omega
  | @cons a n e es b hs ho positive tail ih =>
    by_cases first : c < a+e.count
    · exact ⟨e,by simp,by omega,by omega⟩
    · obtain ⟨x,mem,hx⟩ := ih ⟨by omega,inside.2⟩
      exact ⟨x,by simp [mem],hx⟩

theorem chunksProperties {fuel width name base offset left ordinal es}
    (h : chunks fuel width name base offset left ordinal = some es) :
    Span (base+offset) ordinal es (base+offset+left) ∧ es.length ≤ fuel ∧
    ∀ e ∈ es, e.name = name ∧ e.start = base+e.offset ∧
      0 < e.count ∧ e.count ≤ width ∧ e.payload = 2*e.count := by
  induction fuel generalizing offset left ordinal es with
  | zero =>
    unfold chunks at h
    split at h <;> try contradiction
    rename_i zero
    cases Option.some.inj h
    simp only [zero,Nat.add_zero]
    exact ⟨Span.nil _ _,by simp,by simp⟩
  | succ fuel ih =>
    unfold chunks at h
    split at h
    · rename_i zero
      cases Option.some.inj h
      simp only [zero,Nat.add_zero]
      exact ⟨Span.nil _ _,by simp,by simp⟩
    · dsimp only at h
      split at h <;> try contradiction
      rename_i nz
      simp only [bind,Option.bind_eq_some_iff] at h
      obtain ⟨tail,ht,last⟩ := h
      cases Option.some.inj last
      have rest := ih ht
      have le := Nat.min_le_right width left
      have small := Nat.min_le_left width left
      have pos : 0 < min width left := by omega
      refine ⟨?_,by simpa using Nat.succ_le_succ rest.2.1,?_⟩
      · refine Span.cons (e := ⟨min width left,base+offset,ordinal,2*min width left,name,offset⟩) rfl rfl pos ?_
        have a : base + (offset + min width left) = base + offset + min width left := by omega
        have b : base + (offset + min width left) + (left-min width left) = base+offset+left := by omega
        rw [b,a] at rest
        exact rest.1
      · intro e mem
        rcases List.mem_cons.mp mem with rfl | hm
        · exact ⟨rfl,rfl,pos,small,rfl⟩
        · exact rest.2.2 e hm

theorem rowsBound {fuel rs width ordinal es}
    (h : rows fuel rs width ordinal = some es) : es.length ≤ fuel := by
  induction rs generalizing fuel ordinal es with
  | nil => simp [rows] at h; subst es; simp
  | cons r rs ih =>
    simp only [rows,bind,Option.bind_eq_some_iff] at h
    obtain ⟨head,hh,tail,ht,last⟩ := h
    cases Option.some.inj last
    have hc := (chunksProperties hh).2.1
    have tc := ih ht
    simp only [List.length_append]; omega

theorem rowsEntries {fuel rs width ordinal es}
    (h : rows fuel rs width ordinal = some es) (e : Entry) (member : e ∈ es) :
    0 < e.count ∧ e.count ≤ width ∧ e.payload = 2*e.count ∧
    ∃ r ∈ rs, e.name = r.name ∧ e.start = r.start+e.offset := by
  induction rs generalizing fuel ordinal es with
  | nil => simp [rows] at h; subst es; simp at member
  | cons r rs ih =>
    simp only [rows,bind,Option.bind_eq_some_iff] at h
    obtain ⟨head,hh,tail,ht,last⟩ := h
    cases Option.some.inj last
    rcases List.mem_append.mp member with hm | hm
    · have head := (chunksProperties hh).2.2 e hm
      exact ⟨head.2.2.1,head.2.2.2.1,head.2.2.2.2,r,by simp,head.1,head.2.1⟩
    · have rest := ih ht hm
      obtain ⟨r',mem,name,start⟩ := rest.2.2.2
      exact ⟨rest.1,rest.2.1,rest.2.2.1,r',by simp [mem],name,start⟩

theorem placedRowsSpan {fuel ps width ordinal cursor first es}
    (h : rows fuel (NativeSchemaBinding.place cursor first ps) width ordinal = some es) :
    Span cursor ordinal es (cursor+(ps.map NativeSchemaBinding.Tensor.count).sum) := by
  induction ps generalizing fuel ordinal cursor first es with
  | nil => simp [NativeSchemaBinding.place,rows] at h; subst es; simpa using Span.nil cursor ordinal
  | cons p ps ih =>
    simp only [NativeSchemaBinding.place,rows,bind,Option.bind_eq_some_iff] at h
    obtain ⟨head,hh,tail,ht,last⟩ := h
    cases Option.some.inj last
    have hc := (chunksProperties hh).1
    have tc := ih ht
    have combined := spanAppend hc tc
    simpa [Nat.add_assoc] using combined

theorem builtPartition {s target es} (h : build s target = some es) :
    Target target ∧ es.length ≤ 4096 ∧ Span 0 0 es s.total := by
  unfold build at h
  split at h <;> try contradiction
  rename_i targetOk
  exact ⟨targetOk,rowsBound h,by simpa [NativeSchemaBinding.Schema.rows,
    NativeSchemaBinding.Schema.total] using placedRowsSpan h⟩

theorem builtComplete {s target es} (h : build s target = some es) (c : Nat) (inside : c < s.total) :
    ∃ e ∈ es, e.start ≤ c ∧ c < e.start+e.count :=
  spanCovers (builtPartition h).2.2 c ⟨Nat.zero_le _,inside⟩

theorem builtNoOverlap {s target es} (h : build s target = some es) :
    es.Pairwise (fun x y => x.start+x.count ≤ y.start ∧ x.ordinal < y.ordinal) :=
  spanOrdered (builtPartition h).2.2

theorem builtTotal {s target es} (h : build s target = some es) :
    (es.map Entry.count).sum = s.total := by simpa using spanTotal (builtPartition h).2.2

theorem builtPayload {s target es} (h : build s target = some es) (e : Entry) (member : e ∈ es) :
    0 < e.count ∧ e.count ≤ 524288 ∧ e.payload = 2*e.count ∧ e.payload ≤ target ∧
    e.payload ≤ 1048576 := by
  unfold build at h
  split at h <;> try contradiction
  rename_i targetOk
  have props := rowsEntries h e member
  have mul : 2*(target/2) ≤ target := by omega
  have limit : target ≤ 1048576 := targetOk.2.1
  exact ⟨props.1,by omega,props.2.2.1,by omega,by omega⟩

end DeltaReduce.NativeShardPartition
