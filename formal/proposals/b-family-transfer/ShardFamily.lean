import SyncFamily

/-! R2 option B: simultaneous scalar views of the SAME heterogeneous shard set.
Selectors are mathematical indices only; no selector/coordinate is a protocol
identifier. Common contains the original control/identity/certificate/journal
objects once. No transition, authentication or recovery predicate is introduced.
-/
namespace DeltaReduce.ShardFamily

structure Layout where
  count : Nat
  width : Fin count → Nat
  positive : ∀ s, 0 < width s

abbrev Selector (l : Layout) := (s : Fin l.count) → Fin (l.width s)

def base (l : Layout) : Selector l := fun s => ⟨0,l.positive s⟩

def select (l : Layout) (s : Fin l.count) (k : Fin (l.width s)) : Selector l :=
  Function.update (base l) s k

@[simp] theorem select_self (l : Layout) (s : Fin l.count) (k : Fin (l.width s)) :
    select l s k s = k := by simp [select]

structure Whole (l : Layout) (Common Cell : Type) where
  common : Common
  values : (s : Fin l.count) → List Cell
  shape : ∀ s, (values s).length = l.width s

/-- Locality is essential: changing the coordinate selected in another shard
cannot change this shard's value. Common is stored once, outside the views. -/
structure Family (l : Layout) (Common Cell : Type) where
  common : Common
  view : Selector l → Fin l.count → Cell
  locality : ∀ a b s, a s = b s → view a s = view b s

def project (w : Whole l Common Cell) : Family l Common Cell :=
  ⟨w.common,fun a s => (w.values s)[(a s).val]'(by rw [w.shape]; exact (a s).isLt),by
    intro a b s h; simp [h]⟩

def reconstruct (f : Family l Common Cell) : Whole l Common Cell :=
  ⟨f.common,fun s => List.ofFn (fun k => f.view (select l s k) s),by
    intro s; exact List.length_ofFn⟩

theorem reconstruct_values (w : Whole l Common Cell) (s : Fin l.count) :
    (reconstruct (project w)).values s = w.values s := by
  apply List.ext_getElem?
  intro k
  by_cases hk : k < l.width s
  · simp [reconstruct,project,hk,w.shape]
  · simp [reconstruct,hk,show (w.values s).length ≤ k by rw [w.shape]; omega]

theorem reconstruct_project (w : Whole l Common Cell) : reconstruct (project w) = w := by
  have hv := funext (reconstruct_values w)
  cases w
  simp_all [reconstruct,project]

theorem project_reconstruct (f : Family l Common Cell) : project (reconstruct f) = f := by
  have hv : (project (reconstruct f)).view = f.view := by
    funext a s
    simp only [project,reconstruct,List.getElem_ofFn]
    exact f.locality _ _ s (select_self _ _ _)
  cases f
  simp_all [project,reconstruct]

theorem injective {a b : Whole l Common Cell} (equal : project a = project b) : a = b := by
  simpa only [reconstruct_project] using congrArg reconstruct equal

/-- A changed/missing/extra/reordered coordinate cannot hide behind a family
comparison. No default value is used for absent coordinates. -/
def rows (f : Family l Common Cell) (s : Fin l.count) : List (Nat × Cell) :=
  List.ofFn (fun k => (k.val,f.view (select l s k) s))

theorem complete_rows (f : Family l Common Cell) (s : Fin l.count) :
    (rows f s).map Prod.fst = List.range (l.width s) := by
  simp only [rows,List.map_ofFn,Function.comp_def]
  apply List.ext_getElem?
  intro k
  by_cases hk : k < l.width s <;> simp [hk]

theorem exact_rows (w : Whole l Common Cell) (s : Fin l.count) :
    (rows (project w) s).map Prod.snd = w.values s := by
  simpa [rows,reconstruct,List.map_ofFn,Function.comp_def] using reconstruct_values w s

def validateRows [DecidableEq Cell] (f : Family l Common Cell) (s : Fin l.count)
    (candidate : List (Nat × Cell)) : Bool := decide (candidate = rows f s)

theorem validate_exact [DecidableEq Cell] (f : Family l Common Cell) (s : Fin l.count)
    (candidate : List (Nat × Cell)) (accepted : validateRows f s candidate = true) :
    candidate = rows f s := by simpa [validateRows] using accepted

def scalarView (f : Family l Common Cell) (a : Selector l) : Common × (Fin l.count → Cell) :=
  (f.common,f.view a)

theorem one_common (f : Family l Common Cell) (a b : Selector l) :
    (scalarView f a).1 = (scalarView f b).1 := rfl

/-- Applies to actual signer/quorum, original envelope, WAL sequence and parent
checks once they are bound to Common. It does not authenticate those inputs. -/
theorem common_predicate (w : Whole l Common Cell) (a : Selector l) (p : Common → Prop) :
    p (scalarView (project w) a).1 ↔ p w.common := Iff.rfl

/-- All coordinate copies of a signer set collapse to the SAME set, not a
coordinate-multiplied quorum. This is not a certificate authentication proof. -/
theorem signer_union (w : Whole l Common Cell) (signers : Common → Set Signer) :
    {v | ∃ a : Selector l, v ∈ signers (scalarView (project w) a).1} = signers w.common := by
  ext v
  constructor
  · rintro ⟨a,h⟩; exact h
  · intro h; exact ⟨base l,h⟩

/-- The complete scalar family is equivalent to the complete coordinate
relation. Each scalar view contains one cell per ORIGINAL shard. -/
theorem all_views_iff (left right : Whole l Common Cell)
    (r : Fin l.count → Cell → Cell → Prop) :
    (∀ a : Selector l, ∀ s, r s ((project left).view a s) ((project right).view a s)) ↔
      (∀ s, ∀ k : Fin (l.width s),
        r s ((project left).view (select l s k) s) ((project right).view (select l s k) s)) := by
  constructor
  · intro h s k; exact h _ s
  · intro h a s
    simpa [project] using h s (a s)

def ordered (w : Whole l Common Cell) : List (List Cell) := List.ofFn w.values
def flatten (w : Whole l Common Cell) : List Cell := (ordered w).flatten

theorem original_shard_count (w : Whole l Common Cell) : (ordered w).length = l.count :=
  List.length_ofFn

theorem complete_ordered_reconstruction (w : Whole l Common Cell) :
    ordered (reconstruct (project w)) = ordered w ∧
    flatten (reconstruct (project w)) = flatten w := by rw [reconstruct_project]; exact ⟨rfl,rfl⟩

end DeltaReduce.ShardFamily
