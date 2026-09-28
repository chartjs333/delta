import DeltaReduce.PublicPlanningBody

/-! Primitive metadata agreement between original certificates and computed
arithmetic authority. No whole public body or translation is an input. -/
namespace DeltaReduce.PublicParentNames
open NativeBinding PublicState

def entriesAgree {metadataTrust earlyTrust} (source : PublicAuthority.Metadata metadataTrust)
    (isc : Ref) (vocabulary : PublicArithmeticInputs.Vocabulary)
    {early : PublicEarlyBody.Metadata earlyTrust} {id body} :
    List Commitment → List (PublicEarlyBody.Entry early id body) → Bool
  | [],[] => true
  | c::cs,e::es => decide (c.ticket = NativeVectorLayout.text e.original.ticket ∧
      c.domain = NativeVectorLayout.text e.original.domain ∧
      vocabulary.ticket c.ticket = some e.ticket.text ∧
      source.atom (.content isc c) = some e.content.text) && entriesAgree source isc vocabulary cs es
  | _,_ => false

theorem entryValue {metadataTrust earlyTrust source isc vocabulary early id body c}
    (a : PublicAuthority.Entry (metadataTrust := metadataTrust) source isc vocabulary c)
    (e : PublicEarlyBody.Entry (trust := earlyTrust) early id body)
    (ticket : vocabulary.ticket c.ticket = some e.ticket.text)
    (content : source.atom (.content isc c) = some e.content.text) : a.value = e.value := by
  have ht := Option.some.inj (a.ticketSelected.symm.trans ticket)
  have hc := Option.some.inj (a.content.selected.symm.trans content)
  simp only [PublicAuthority.Entry.value,PublicEarlyBody.Entry.value,
    PublicAuthority.Atom.value,PublicEarlyBody.Name.value,ht,hc]

theorem completeEntries {metadataTrust earlyTrust source isc vocabulary early id body cs vs}
    (original : PublicAuthority.EntriesFor (metadataTrust := metadataTrust) source isc vocabulary cs vs)
    (es : List (PublicEarlyBody.Entry (trust := earlyTrust) early id body))
    (agree : entriesAgree source isc vocabulary cs es = true) :
    vs = es.map PublicEarlyBody.Entry.value := by
  induction original generalizing es with
  | nil => cases es <;> simp_all [entriesAgree]
  | cons a tail ih =>
    cases es with
    | nil => simp [entriesAgree] at agree
    | cons e es =>
      have h := Bool.and_eq_true_iff.mp agree
      have primitive := of_decide_eq_true h.1
      simp only [List.map_cons,entryValue a e primitive.2.2.1 primitive.2.2.2,ih es h.2]

def membersAgree (vocabulary : PublicArithmeticInputs.Vocabulary)
    {trust} {source : PublicEarlyBody.Metadata trust} {context} :
    List String → List (PublicPlanningBody.Member source context) → Bool
  | [],[] => true
  | t::ts,m::ms => decide (t = NativeVectorLayout.text m.original ∧
      vocabulary.ticket t = some m.name.text) && membersAgree vocabulary ts ms
  | _,_ => false

theorem completeMembers {trust vocabulary source context ts names}
    (collected : NativeInputProjection.collect vocabulary.ticket ts = some names)
    (ms : List (PublicPlanningBody.Member (trust := trust) source context))
    (agree : membersAgree vocabulary ts ms = true) :
    names.map Value.model = ms.map PublicPlanningBody.Member.value := by
  induction ts generalizing names ms with
  | nil =>
    cases ms with
    | nil => cases Option.some.inj collected; rfl
    | cons m ms => simp [membersAgree] at agree
  | cons t ts ih =>
    cases ms with
    | nil => simp [membersAgree] at agree
    | cons m ms =>
      have h := Bool.and_eq_true_iff.mp agree
      have primitive := of_decide_eq_true h.1
      simp only [NativeInputProjection.collect,bind,Option.bind_eq_some_iff] at collected
      obtain ⟨name,hn,rest,hr,last⟩ := collected
      have same := Option.some.inj (hn.symm.trans primitive.2)
      cases Option.some.inj last
      simp only [List.map_cons,ih hr ms h.2,PublicPlanningBody.Member.value,PublicEarlyBody.Name.value,same]

theorem extraEntryRejects {metadataTrust earlyTrust source isc vocabulary early id body}
    (e : PublicEarlyBody.Entry (trust := earlyTrust) early id body) (es) :
    entriesAgree (metadataTrust := metadataTrust) source isc vocabulary [] (e::es) = false := rfl

theorem missingEntryRejects {metadataTrust earlyTrust source isc vocabulary early id body} (c cs) :
    entriesAgree (metadataTrust := metadataTrust) (earlyTrust := earlyTrust) source isc vocabulary
      (early := early) (id := id) (body := body) (c::cs) [] = false := rfl

theorem missingContentRejects {metadataTrust earlyTrust source isc vocabulary early id body c cs}
    (e : PublicEarlyBody.Entry (trust := earlyTrust) early id body) (es)
    (missing : source.atom (.content isc c) = none) :
    entriesAgree (metadataTrust := metadataTrust) source isc vocabulary (c::cs) (e::es) = false := by
  simp [entriesAgree,missing]

end DeltaReduce.PublicParentNames
