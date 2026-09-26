import DeltaReduce.NativeSnapshotBase
import DeltaReduce.NativeIscCertificateVectors

/-! Original proposed ISC/base component composition; finite SHA plus original
body hash. No complete bindSnapshot/prepare fixture or native run is claimed. -/
namespace DeltaReduce.NativeSnapshotBaseVectors
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativeConfigAdmission (ascii)
open NativeSnapshotBase
set_option maxRecDepth 16384
set_option maxHeartbeats 200000

def policy := NativeIscAdmissionVectors.policy
def state := NativeIscAdmissionVectors.state
def body := NativeIscAdmissionVectors.inputBody
def inputTree := NativeIscAdmissionVectors.inputTree
def committee := NativeIscCertificateVectors.committee
def expanded := NativeProposedIsc.certificate committee body
def preimage := NativeStateBytes.contentPreimage NativeIscCertificate.domain
  (NativeIscCertificate.json expanded)
def digest : Bytes := [127,240,252,246,219,36,71,182,184,142,185,26,31,121,66,31,21,202,61,171,230,249,37,24,10,114,220,33,255,72,62,26]
def sha (raw : Bytes) : Bytes :=
  if raw = preimage then digest else NativeIscCertificateVectors.sha raw
def qc : Bytes := ascii "sha256:7ff0fcf6db2447b6b88eb91a1f79421f15ca3dabe6f925180a72dc21ff483e1a"
def checkedBody : NativeInputSetBody.Checked :=
  ⟨body,NativeIscCertificateVectors.bodyId,inputTree⟩
def checked : NativeProposedIsc.Checked := ⟨checkedBody,qc⟩

theorem bodyPreimageDifferent : NativeStateBytes.contentPreimage NativeInputSetBody.bodyDomain
    (NativeInputSetBody.bodyBytes body) ≠ preimage := by decide
theorem bodyHash : NativeInputSetBody.bodyId sha body = some checkedBody.id := by
  unfold NativeInputSetBody.bodyId NativeStateBytes.contentId sha
  rw [if_neg bodyPreimageDifferent]
  exact NativeIscCertificateVectors.bodyComputed
theorem originalBody : NativeInputSetBody.check sha body.context inputTree = some checkedBody :=
  NativeInputSetBody.checkFromComponents NativeIscAdmissionVectors.bodyRead bodyHash
    NativeIscAdmissionVectors.inputValid
theorem expandedValid : NativeIscCertificate.Valid body.context committee expanded := by decide
theorem allFourSigners : expanded.signers = committee ∧ expanded.threshold = 3 := by decide
theorem exactLength : (NativeIscCertificate.json expanded).length = 1023 := by decide
theorem boundedHash : NativeContractSize.contentId sha NativeIscCertificate.domain
    (NativeIscCertificate.json expanded) = some qc := by
  apply NativeContractSize.fromComponents
  · rw [exactLength]; decide
  · unfold NativeStateBytes.contentId sha
    change (let d := if preimage = preimage then digest else _;
      if d.length = 32 then some (ascii "sha256:" ++ NativeVoteBytes.hexBytes d) else none) = _
    simp only [ite_true]; rfl
theorem originalProposal :
    NativeProposedIsc.check sha body.context committee inputTree = some checked :=
  NativeProposedIsc.fromComponents ⟨originalBody,expandedValid,boundedHash⟩
theorem originalSingleton : NativeProposedIsc.checkAll sha body.context committee [inputTree] =
    some [checked] := NativeProposedIsc.listFromComponents originalProposal rfl
theorem differentBodyIdentity : qc ≠ checkedBody.id := by decide
theorem differentFinalizedIdentity : qc ≠ NativeIscCertificateVectors.qc := by decide
theorem exactOriginalPosition : [inputTree][0]? = some checked.body.source :=
  NativeProposedIsc.exactPosition originalSingleton rfl

def base : Base := ⟨body.context.schema,body.context.arithmetic,
  NativeIscAdmissionVectors.bound.accumulator,[policy.config],[policy.config],
  [inputTree],[checked],[checkedBody.id]⟩
theorem baseChecks : Checks policy state base := by decide
theorem originalBase : checkBase sha policy state = some base := by
  apply baseFromComponents
  exact ⟨rfl,rfl,rfl,rfl,rfl,rfl,originalSingleton,rfl,baseChecks⟩
theorem originalFields : BaseSource sha policy state base := checkedBase originalBase
theorem retainedAllInputs : base.inputs.map (fun c => c.body.source) = base.inputTrees :=
  originalInputList originalBase
theorem retainedClosed : ∃ c ∈ base.inputs, c.body.id = checkedBody.id ∧
    NativeProposedIsc.Source sha
      (NativeIscAdmission.expected policy state base.schema base.arithmetic)
      policy.validators c.body.source c := closedHasOriginalBody originalBase (by decide)

theorem wrongProposedConfig :
    ¬ Checks policy state {base with proposedConfigs := [body.context.schema]} := by decide
theorem wrongFinalizedConfig :
    ¬ Checks policy state {base with finalizedConfigs := [body.context.schema]} := by decide
theorem duplicateConfig :
    ¬ Checks policy state {base with proposedConfigs := [policy.config,policy.config]} := by decide
theorem invalidAccumulator :
    ¬ Checks policy state {base with accumulator := ascii "wrong"} := by decide
theorem optionalAccumulator : Checks policy state {base with accumulator := []} := by decide
theorem missingClosedBody : ¬ Checks policy state {base with inputs := []} := by decide
theorem certificateIsNotClosedBody : ¬ Checks policy state {base with closed := [qc]} := by decide
theorem duplicateClosed :
    ¬ Checks policy state {base with closed := [checkedBody.id,checkedBody.id]} := by decide
theorem duplicateBody : ¬ Checks policy state {base with inputs := [checked,checked]} := by decide
theorem noProposalsMayBeClosed : Checks policy state {base with closed := []} := by decide
theorem wrongSchema : ¬ Checks policy state {base with schema := []} := by decide
theorem wrongArithmetic : ¬ Checks policy state {base with arithmetic := []} := by decide
theorem wrongRoundStillRejected : ¬ NativeInputSetBody.ContextValid
    {body.context with round := ascii "round with spaces"} := by decide
theorem wrongEpoch : ¬ NativeInputSetBody.ContextValid {body.context with epoch := []} := by decide
theorem zeroHeight : ¬ NativeInputSetBody.ContextValid {body.context with height := 0} := by decide
theorem changedPolicyCoordinate : ¬ Checks policy {state with height := 0} base := by decide
theorem foreignLocal :
    ¬ Checks {policy with localValidator := ascii "foreign"} state base := by decide
theorem wrongDeadlines :
    ¬ Checks {policy with softDeadline := policy.hardDeadline} state base := by decide

def unusedNonLabel := committee.take 3 ++ [ascii "validator~unused"]
theorem unusedValidatorAllowed : NativeIscCertificate.CommitteeValid unusedNonLabel := by decide
theorem unusedNotASigner : NativeIscCertificate.Valid body.context unusedNonLabel
    NativeIscCertificateVectors.certificate := by decide
theorem unusedIsNotLabel : ¬ NativeConfigAdmission.Label (ascii "validator~unused") := by decide
theorem proposalUsesItRejects : ¬ NativeIscCertificate.Valid body.context unusedNonLabel
    (NativeProposedIsc.certificate unusedNonLabel body) := by decide
theorem proposalRejects {out} :
    NativeProposedIsc.check sha body.context unusedNonLabel inputTree ≠ some out :=
  NativeProposedIsc.nonLabelSignerRejected (by decide) unusedIsNotLabel
theorem emptyValidator : ¬ NativeIscCertificate.CommitteeValid [[]] := by decide
theorem reversedCommittee : ¬ NativeIscCertificate.CommitteeValid committee.reverse := by decide
theorem noThreeCommittee : ¬ NativeIscCertificate.CommitteeValid (committee.take 3) := by decide
theorem wrongContext :
    ¬ NativeIscCertificate.Valid {body.context with view := 1} committee expanded := by decide
theorem wrongTupleOrder : ¬ NativeIscCertificate.Valid body.context committee
    {expanded with body := {body with tuples := body.tuples ++ body.tuples}} := by decide
theorem wrongRoot : ¬ NativeIscCertificate.Valid body.context committee
    {expanded with body := {body with root := []}} := by decide
theorem wrongThreshold : ¬ NativeIscCertificate.Valid body.context committee
    {expanded with threshold := 2} := by decide
theorem boundedProjectionRequired {largeBody : NativeInputSetBody.Checked}
    (source : NativeInputSetBody.check sha body.context inputTree = some largeBody)
    (large : NativeContractSize.maxBytes <
      (NativeIscCertificate.json (NativeProposedIsc.certificate committee largeBody.body)).length) :
    NativeProposedIsc.check sha body.context committee inputTree = none :=
  NativeProposedIsc.oversizedRejected source large

end DeltaReduce.NativeSnapshotBaseVectors
