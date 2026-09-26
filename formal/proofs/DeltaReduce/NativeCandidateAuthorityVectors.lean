import DeltaReduce.NativeCandidateAuthority
import DeltaReduce.NativeSnapshotBaseVectors
import DeltaReduce.NativeApplyCertificateVectors
import DeltaReduce.NativeFailureAuthorityVectors

/-! One whole original CONFIG policy example; other candidate checks use
original individual rows in an explicitly synthetic mixed component snapshot.
No whole mixed-native run, authentication, arithmetic admission or recovery. -/
namespace DeltaReduce.NativeCandidateAuthorityVectors
open NativeReceiptBytes NativePolicyCodec
open NativeCandidateAuthority
open NativeCandidateShape (Parents)
open NativeVoteBytes (ascii)
set_option maxRecDepth 16384
set_option maxHeartbeats 800000

def policy := NativeConfigAdmissionVectors.policy
def state := NativeConfigAdmissionVectors.state
def parents1 : Parents := ⟨(ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111"),(ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222"),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii "")⟩
def candidate1 : NativePolicyBytes.Candidate := ⟨1,(ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111"),(ascii "sha256:5643f922e7810932c510057601fc59edf4817446d7fdce192abf6f86d93ef6e1"),1,0,NativeCandidateShape.value parents1,.pair (.number 1) (.pair (.text (ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111")) (.pair (.text (ascii "sha256:5643f922e7810932c510057601fc59edf4817446d7fdce192abf6f86d93ef6e1")) (.pair (.number 1) (.pair (.number 0) (.pair (NativeCandidateShape.value parents1) .end)))))⟩
def contextPre1 : Bytes := [100,101,108,116,97,114,101,100,117,99,101,46,118,111,116,101,45,99,111,110,116,101,120,116,46,99,111,110,102,105,103,46,118,49,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,71,115,104,97,50,53,54,58,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100]
def contextHash1 : Bytes := [86,67,249,34,231,129,9,50,197,16,5,118,1,252,89,237,244,129,116,70,215,253,206,25,42,191,111,134,217,62,246,225]
def parents2 : Parents := ⟨(ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111"),(ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222"),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii "")⟩
def candidate2 : NativePolicyBytes.Candidate := ⟨2,(ascii "sha256:33e327fe50bd52a92e0675c846fe2ee53671dde65350152380c82a99af21c27d"),(ascii "sha256:60d1e04e0f0a691d726f1ab0ca93f15c22c1757162a4b6e960ff4586ca4dd20b"),1,0,NativeCandidateShape.value parents2,.pair (.number 2) (.pair (.text (ascii "sha256:33e327fe50bd52a92e0675c846fe2ee53671dde65350152380c82a99af21c27d")) (.pair (.text (ascii "sha256:60d1e04e0f0a691d726f1ab0ca93f15c22c1757162a4b6e960ff4586ca4dd20b")) (.pair (.number 1) (.pair (.number 0) (.pair (NativeCandidateShape.value parents2) .end)))))⟩
def contextPre2 : Bytes := [100,101,108,116,97,114,101,100,117,99,101,46,118,111,116,101,45,99,111,110,116,101,120,116,46,105,115,99,46,118,49,0,0,0,0,0,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45,102,105,120,116,117,114,101]
def contextHash2 : Bytes := [96,209,224,78,15,10,105,29,114,111,26,176,202,147,241,92,34,193,117,113,98,164,182,233,96,255,69,134,202,77,210,11]
def parents3 : Parents := ⟨(ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111"),(ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222"),(ascii "sha256:2534a9ccd9ecc93bc121a75e47c94b1b5c484735bfe24144faeec50fe72b7e14"),(ascii "sha256:aa7c0b3f9da0f3fcaf9ce430c0b72afefe917d3d7a4fcb6ff70650fea82b1ac2"),(ascii "sha256:5301813c9aa2cab9d5f8888776e37fb2f3d08f693cc481b0ec64f24b029d8d9e"),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii "")⟩
def candidate3 : NativePolicyBytes.Candidate := ⟨3,(ascii "sha256:67c4e17a75fc0998471b408dbe094b30aa2a238d23bc008099159268b4b63978"),(ascii "sha256:d9ba7cfbab18c0cc638bfff75cafeda604e9e81c71f1b698f6538cb6846bfdff"),1,0,NativeCandidateShape.value parents3,.pair (.number 3) (.pair (.text (ascii "sha256:67c4e17a75fc0998471b408dbe094b30aa2a238d23bc008099159268b4b63978")) (.pair (.text (ascii "sha256:d9ba7cfbab18c0cc638bfff75cafeda604e9e81c71f1b698f6538cb6846bfdff")) (.pair (.number 1) (.pair (.number 0) (.pair (NativeCandidateShape.value parents3) .end)))))⟩
def contextPre3 : Bytes := [100,101,108,116,97,114,101,100,117,99,101,46,118,111,116,101,45,99,111,110,116,101,120,116,46,101,99,46,118,49,0,0,0,0,0,0,0,0,71,115,104,97,50,53,54,58,50,53,51,52,97,57,99,99,100,57,101,99,99,57,51,98,99,49,50,49,97,55,53,101,52,55,99,57,52,98,49,98,53,99,52,56,52,55,51,53,98,102,101,50,52,49,52,52,102,97,101,101,99,53,48,102,101,55,50,98,55,101,49,52]
def contextHash3 : Bytes := [217,186,124,251,171,24,192,204,99,139,255,247,92,175,237,166,4,233,232,28,113,241,182,152,246,83,140,182,132,107,253,255]
def parents4 : Parents := ⟨(ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111"),(ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222"),(ascii "sha256:2534a9ccd9ecc93bc121a75e47c94b1b5c484735bfe24144faeec50fe72b7e14"),(ascii "sha256:aa7c0b3f9da0f3fcaf9ce430c0b72afefe917d3d7a4fcb6ff70650fea82b1ac2"),(ascii "sha256:5301813c9aa2cab9d5f8888776e37fb2f3d08f693cc481b0ec64f24b029d8d9e"),(ascii "sha256:5e22a57a95cef80ea86600ae9a87b75a9d7250164d7aabc2e4737d0e94fa962b"),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii "")⟩
def candidate4 : NativePolicyBytes.Candidate := ⟨4,(ascii "sha256:4580349215fc6b84d64fdf994c47283b08dbfa850927c8eb106a59fae9c812e2"),(ascii "sha256:7ccc5fd880d6ab0d4cb21d1e114d10995e1757b8372ef7547feefaa6d417edb2"),1,0,NativeCandidateShape.value parents4,.pair (.number 4) (.pair (.text (ascii "sha256:4580349215fc6b84d64fdf994c47283b08dbfa850927c8eb106a59fae9c812e2")) (.pair (.text (ascii "sha256:7ccc5fd880d6ab0d4cb21d1e114d10995e1757b8372ef7547feefaa6d417edb2")) (.pair (.number 1) (.pair (.number 0) (.pair (NativeCandidateShape.value parents4) .end)))))⟩
def contextPre4 : Bytes := [100,101,108,116,97,114,101,100,117,99,101,46,118,111,116,101,45,99,111,110,116,101,120,116,46,97,112,99,46,118,49,0,0,0,0,0,0,0,0,71,115,104,97,50,53,54,58,53,101,50,50,97,53,55,97,57,53,99,101,102,56,48,101,97,56,54,54,48,48,97,101,57,97,56,55,98,55,53,97,57,100,55,50,53,48,49,54,52,100,55,97,97,98,99,50,101,52,55,51,55,100,48,101,57,52,102,97,57,54,50,98]
def contextHash4 : Bytes := [124,204,95,216,128,214,171,13,76,178,29,30,17,77,16,153,94,23,87,184,55,46,247,84,127,238,250,166,212,23,237,178]
def parents5 : Parents := ⟨(ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111"),(ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222"),(ascii "sha256:2534a9ccd9ecc93bc121a75e47c94b1b5c484735bfe24144faeec50fe72b7e14"),(ascii "sha256:aa7c0b3f9da0f3fcaf9ce430c0b72afefe917d3d7a4fcb6ff70650fea82b1ac2"),(ascii ""),(ascii "sha256:5e22a57a95cef80ea86600ae9a87b75a9d7250164d7aabc2e4737d0e94fa962b"),(ascii "sha256:255dc9d74bba405a8db306acf36706aa0b2685f6d7ace1c3f42b006c11699aa4"),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii "domain-a"),(ascii "shard-a"),(ascii "")⟩
def candidate5 : NativePolicyBytes.Candidate := ⟨5,(ascii "sha256:64a104b7f8c820b6b3c48950af74c115f4d94787f7e5132950402a6adcd41645"),(ascii "PARAMETER:domain-a:shard-a"),1,0,NativeCandidateShape.value parents5,.pair (.number 5) (.pair (.text (ascii "sha256:64a104b7f8c820b6b3c48950af74c115f4d94787f7e5132950402a6adcd41645")) (.pair (.text (ascii "PARAMETER:domain-a:shard-a")) (.pair (.number 1) (.pair (.number 0) (.pair (NativeCandidateShape.value parents5) .end)))))⟩
def parents6 : Parents := ⟨(ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111"),(ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222"),(ascii "sha256:2534a9ccd9ecc93bc121a75e47c94b1b5c484735bfe24144faeec50fe72b7e14"),(ascii "sha256:aa7c0b3f9da0f3fcaf9ce430c0b72afefe917d3d7a4fcb6ff70650fea82b1ac2"),(ascii ""),(ascii "sha256:5e22a57a95cef80ea86600ae9a87b75a9d7250164d7aabc2e4737d0e94fa962b"),(ascii "sha256:255dc9d74bba405a8db306acf36706aa0b2685f6d7ace1c3f42b006c11699aa4"),(ascii "sha256:e5035addcb215f5ba4905d4cd5eaf8745919aa1f92d4f6e763bb0173d765b944"),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii "")⟩
def candidate6 : NativePolicyBytes.Candidate := ⟨6,(ascii "sha256:c5ec7f38bf6e199fd9d676f6e1b4a734624bc219a486c110fa5410f8f8fc2d28"),(ascii "sha256:08edbd495b3369f06d7d46dec477899485859ee01e58789eea42e61532a0cca1"),1,0,NativeCandidateShape.value parents6,.pair (.number 6) (.pair (.text (ascii "sha256:c5ec7f38bf6e199fd9d676f6e1b4a734624bc219a486c110fa5410f8f8fc2d28")) (.pair (.text (ascii "sha256:08edbd495b3369f06d7d46dec477899485859ee01e58789eea42e61532a0cca1")) (.pair (.number 1) (.pair (.number 0) (.pair (NativeCandidateShape.value parents6) .end)))))⟩
def contextPre6 : Bytes := [100,101,108,116,97,114,101,100,117,99,101,46,118,111,116,101,45,99,111,110,116,101,120,116,46,114,111,111,116,46,118,49,0,0,0,0,0,0,0,0,71,115,104,97,50,53,54,58,50,53,53,100,99,57,100,55,52,98,98,97,52,48,53,97,56,100,98,51,48,54,97,99,102,51,54,55,48,54,97,97,48,98,50,54,56,53,102,54,100,55,97,99,101,49,99,51,102,52,50,98,48,48,54,99,49,49,54,57,57,97,97,52]
def contextHash6 : Bytes := [8,237,189,73,91,51,105,240,109,125,70,222,196,119,137,148,133,133,158,224,30,88,120,158,234,66,230,21,50,160,204,161]
def parents7 : Parents := ⟨(ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111"),(ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222"),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii "sha256:06327c494519aa8f5077760d8081983ea24e403d2eb2c63a4739ca231b266c06"),(ascii "sha256:29ae9b636432fac1f85c8f4f353ced6b6aaa54e473a8e058c126feff029794bd"),(ascii "sha256:2bf5029d5500241ca9a548b5858bb142066512f4f1e3976e09c27b7e962ca01f"),(ascii ""),(ascii ""),(ascii ""),(ascii "")⟩
def candidate7 : NativePolicyBytes.Candidate := ⟨7,(ascii "sha256:2bf5029d5500241ca9a548b5858bb142066512f4f1e3976e09c27b7e962ca01f"),(ascii "sha256:7a21a3c4a2488f093311911563224fff2abf52557342bd33e4f469731c92d4e1"),1,0,NativeCandidateShape.value parents7,.pair (.number 7) (.pair (.text (ascii "sha256:2bf5029d5500241ca9a548b5858bb142066512f4f1e3976e09c27b7e962ca01f")) (.pair (.text (ascii "sha256:7a21a3c4a2488f093311911563224fff2abf52557342bd33e4f469731c92d4e1")) (.pair (.number 1) (.pair (.number 0) (.pair (NativeCandidateShape.value parents7) .end)))))⟩
def contextPre7 : Bytes := [100,101,108,116,97,114,101,100,117,99,101,46,118,111,116,101,45,99,111,110,116,101,120,116,46,97,112,112,108,121,46,118,49,0,0,0,0,0,0,0,0,71,115,104,97,50,53,54,58,48,54,51,50,55,99,52,57,52,53,49,57,97,97,56,102,53,48,55,55,55,54,48,100,56,48,56,49,57,56,51,101,97,50,52,101,52,48,51,100,50,101,98,50,99,54,51,97,52,55,51,57,99,97,50,51,49,98,50,54,54,99,48,54]
def contextHash7 : Bytes := [122,33,163,196,162,72,143,9,51,17,145,21,99,34,79,255,42,191,82,85,115,66,189,51,228,244,105,115,28,146,212,225]
def parents8 : Parents := ⟨(ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111"),(ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222"),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii "")⟩
def candidate8 : NativePolicyBytes.Candidate := ⟨8,(ascii "sha256:2ea13643cbd3d3ed7b0d860dc5c86c9cbfd945a0645de325ebd7a4f47da6b759"),(ascii "sha256:ee4385720a99be17cc6352b2cecbbb16bc33a45f86e3cea872cc8e6334af9bf9"),1,0,NativeCandidateShape.value parents8,.pair (.number 8) (.pair (.text (ascii "sha256:2ea13643cbd3d3ed7b0d860dc5c86c9cbfd945a0645de325ebd7a4f47da6b759")) (.pair (.text (ascii "sha256:ee4385720a99be17cc6352b2cecbbb16bc33a45f86e3cea872cc8e6334af9bf9")) (.pair (.number 1) (.pair (.number 0) (.pair (NativeCandidateShape.value parents8) .end)))))⟩
def contextPre8 : Bytes := [100,101,108,116,97,114,101,100,117,99,101,46,118,111,116,101,45,99,111,110,116,101,120,116,46,118,105,101,119,46,118,49,0,0,0,0,0,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45,102,105,120,116,117,114,101,0,0,0,0,0,0,0,0]
def contextHash8 : Bytes := [238,67,133,114,10,153,190,23,204,99,82,178,206,203,187,22,188,51,164,95,134,227,206,168,114,204,142,99,52,175,155,249]
def parents9 : Parents := ⟨(ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111"),(ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222"),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii ""),(ascii "HARD_DEADLINE")⟩
def candidate9 : NativePolicyBytes.Candidate := ⟨9,(ascii "sha256:7ae0b29609cc29c5be6fe78dd0d9201c065f1dc40074cd7a8ea73a8ee3c4b95f"),(ascii "sha256:25237c1323fbdae5feb16e5a60dfe9a12fb8881ed907b070adb8425c8a36ab9b"),1,0,NativeCandidateShape.value parents9,.pair (.number 9) (.pair (.text (ascii "sha256:7ae0b29609cc29c5be6fe78dd0d9201c065f1dc40074cd7a8ea73a8ee3c4b95f")) (.pair (.text (ascii "sha256:25237c1323fbdae5feb16e5a60dfe9a12fb8881ed907b070adb8425c8a36ab9b")) (.pair (.number 1) (.pair (.number 0) (.pair (NativeCandidateShape.value parents9) .end)))))⟩
def contextPre9 : Bytes := [100,101,108,116,97,114,101,100,117,99,101,46,118,111,116,101,45,99,111,110,116,101,120,116,46,97,98,111,114,116,46,118,49,0,0,0,0,0,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45,102,105,120,116,117,114,101]
def contextHash9 : Bytes := [37,35,124,19,35,251,218,229,254,177,110,90,96,223,233,161,47,184,136,30,217,7,176,112,173,184,66,92,138,54,171,155]
def sha (raw : Bytes) : Bytes :=
  if raw = contextPre1 then contextHash1 else
  if raw = contextPre2 then contextHash2 else
  if raw = contextPre3 then contextHash3 else
  if raw = contextPre4 then contextHash4 else
  if raw = contextPre6 then contextHash6 else
  if raw = contextPre7 then contextHash7 else
  if raw = contextPre8 then contextHash8 else
  if raw = contextPre9 then contextHash9 else NativeFailureAuthorityVectors.hash raw

-- These rows reuse earlier individually kernel-checked original fixture bodies.
-- Their simultaneous assembly is mathematical, not an original native snapshot.
def isc : NativeFinalizedIscSection.Bound :=
  ⟨policy,state,NativeSnapshotBaseVectors.base.schema,NativeSnapshotBaseVectors.base.arithmetic,
    [],[NativeIscCertificateVectors.tree],[NativeIscCertificateVectors.checked],
    [NativeIscCertificateVectors.qc]⟩
def norms : NativeNormSection.Bound :=
  ⟨isc,[NativeNormEvidenceVectors.tree],[NativeNormEvidenceVectors.checked]⟩
def ecs : NativeEligibilitySection.Bound :=
  ⟨norms,[NativeSeedTranscriptVectors.tree],[NativeSeedTranscriptVectors.checked],
    [NativeEligibilityVectors.bodyTree],[NativeEligibilityVectors.proposedEdge],
    [NativeEligibilityVectors.finalTree],[NativeEligibilityVectors.finalEdge],
    [NativeEligibilityVectors.qc]⟩
def plans : NativePlanSection.Bound :=
  ⟨ecs,NativeSnapshotBaseVectors.base.accumulator,[NativePlanVectors.bodyTree],
    [NativePlanVectors.proposedEdge],[NativePlanVectors.tree],[NativePlanVectors.finalEdge],
    [NativePlanVectors.qc]⟩
def parameters : NativeParameterSection.Bound :=
  ⟨plans,[],NativeParameterVectors.keys,[NativeParameterVectors.bodyTree],
    [NativeParameterVectors.proposedEdge],[NativeParameterVectors.tree],
    [NativeParameterVectors.finalizedEdge],[NativeParameterVectors.qc]⟩
def roots : NativeAggregateSection.Bound :=
  ⟨⟨parameters,[]⟩,[NativeAggregateVectors.bodyTree],[NativeAggregateVectors.proposedEdge],
    [NativeAggregateVectors.tree],[NativeAggregateVectors.finalizedEdge],[NativeAggregateVectors.qc]⟩
def applies : NativeApplySection.Bound :=
  ⟨roots,[NativeApplyCertificateVectors.profileTree],[NativeApplyCertificateVectors.checkedProfile],
    [NativeApplyCertificateVectors.candidateTree],[NativeApplyCertificateVectors.proposedEdge],
    [],[],[]⟩
def mixed : NativeSnapshotBase.Bound :=
  ⟨⟨applies,NativeFailureVectors.viewTail⟩,NativeSnapshotBaseVectors.base⟩
def abortMixed : NativeSnapshotBase.Bound :=
  {mixed with prior := {mixed.prior with tail := NativeFailureVectors.abortTail}}

theorem originalCandidate1 : NativePolicyBytes.candidate candidate1.source =
    some candidate1 := rfl
theorem shape1 : NativeCandidateShape.check policy candidate1 = some parents1 := by decide
theorem authority1 : Authority sha policy state mixed candidate1 parents1 := by decide
theorem accepted1 : check sha policy state mixed candidate1 = some ⟨candidate1,parents1⟩ :=
  fromComponents shape1 rfl rfl authority1
theorem wrongHeight1 :
    (check sha policy state mixed {candidate1 with height := 2}).isNone = true := by decide
theorem wrongContext1 : ¬ Authority sha policy state mixed
    {candidate1 with context := ascii "other"} parents1 := by decide

theorem originalCandidate2 : NativePolicyBytes.candidate candidate2.source =
    some candidate2 := rfl
theorem shape2 : NativeCandidateShape.check policy candidate2 = some parents2 := by decide
theorem authority2 : Authority sha policy state mixed candidate2 parents2 := by decide
theorem accepted2 : check sha policy state mixed candidate2 = some ⟨candidate2,parents2⟩ :=
  fromComponents shape2 rfl rfl authority2
theorem wrongHeight2 :
    (check sha policy state mixed {candidate2 with height := 2}).isNone = true := by decide
theorem wrongContext2 : ¬ Authority sha policy state mixed
    {candidate2 with context := ascii "other"} parents2 := by decide

theorem originalCandidate3 : NativePolicyBytes.candidate candidate3.source =
    some candidate3 := rfl
theorem shape3 : NativeCandidateShape.check policy candidate3 = some parents3 := by decide
theorem authority3 : Authority sha policy state mixed candidate3 parents3 := by decide
theorem accepted3 : check sha policy state mixed candidate3 = some ⟨candidate3,parents3⟩ :=
  fromComponents shape3 rfl rfl authority3
theorem wrongHeight3 :
    (check sha policy state mixed {candidate3 with height := 2}).isNone = true := by decide
theorem wrongContext3 : ¬ Authority sha policy state mixed
    {candidate3 with context := ascii "other"} parents3 := by decide

theorem originalCandidate4 : NativePolicyBytes.candidate candidate4.source =
    some candidate4 := rfl
theorem shape4 : NativeCandidateShape.check policy candidate4 = some parents4 := by decide
theorem authority4 : Authority sha policy state mixed candidate4 parents4 := by decide
theorem accepted4 : check sha policy state mixed candidate4 = some ⟨candidate4,parents4⟩ :=
  fromComponents shape4 rfl rfl authority4
theorem wrongHeight4 :
    (check sha policy state mixed {candidate4 with height := 2}).isNone = true := by decide
theorem wrongContext4 : ¬ Authority sha policy state mixed
    {candidate4 with context := ascii "other"} parents4 := by decide

theorem originalCandidate5 : NativePolicyBytes.candidate candidate5.source =
    some candidate5 := rfl
theorem shape5 : NativeCandidateShape.check policy candidate5 = some parents5 := by decide
theorem authority5 : Authority sha policy state mixed candidate5 parents5 := by decide
theorem accepted5 : check sha policy state mixed candidate5 = some ⟨candidate5,parents5⟩ :=
  fromComponents shape5 rfl rfl authority5
theorem wrongHeight5 :
    (check sha policy state mixed {candidate5 with height := 2}).isNone = true := by decide
theorem wrongContext5 : ¬ Authority sha policy state mixed
    {candidate5 with context := ascii "other"} parents5 := by decide

theorem originalCandidate6 : NativePolicyBytes.candidate candidate6.source =
    some candidate6 := rfl
theorem shape6 : NativeCandidateShape.check policy candidate6 = some parents6 := by decide
theorem authority6 : Authority sha policy state mixed candidate6 parents6 := by decide
theorem accepted6 : check sha policy state mixed candidate6 = some ⟨candidate6,parents6⟩ :=
  fromComponents shape6 rfl rfl authority6
theorem wrongHeight6 :
    (check sha policy state mixed {candidate6 with height := 2}).isNone = true := by decide
theorem wrongContext6 : ¬ Authority sha policy state mixed
    {candidate6 with context := ascii "other"} parents6 := by decide

theorem originalCandidate7 : NativePolicyBytes.candidate candidate7.source =
    some candidate7 := rfl
theorem shape7 : NativeCandidateShape.check policy candidate7 = some parents7 := by decide
theorem authority7 : Authority sha policy state mixed candidate7 parents7 := by decide
theorem accepted7 : check sha policy state mixed candidate7 = some ⟨candidate7,parents7⟩ :=
  fromComponents shape7 rfl rfl authority7
theorem wrongHeight7 :
    (check sha policy state mixed {candidate7 with height := 2}).isNone = true := by decide
theorem wrongContext7 : ¬ Authority sha policy state mixed
    {candidate7 with context := ascii "other"} parents7 := by decide

theorem originalCandidate8 : NativePolicyBytes.candidate candidate8.source =
    some candidate8 := rfl
theorem shape8 : NativeCandidateShape.check policy candidate8 = some parents8 := by decide
theorem authority8 : Authority sha policy state mixed candidate8 parents8 := by decide
theorem accepted8 : check sha policy state mixed candidate8 = some ⟨candidate8,parents8⟩ :=
  fromComponents shape8 rfl rfl authority8
theorem wrongHeight8 :
    (check sha policy state mixed {candidate8 with height := 2}).isNone = true := by decide
theorem wrongContext8 : ¬ Authority sha policy state mixed
    {candidate8 with context := ascii "other"} parents8 := by decide

theorem originalCandidate9 : NativePolicyBytes.candidate candidate9.source =
    some candidate9 := rfl
theorem shape9 : NativeCandidateShape.check policy candidate9 = some parents9 := by decide
theorem authority9 : Authority sha policy state abortMixed candidate9 parents9 := by decide
theorem accepted9 : check sha policy state abortMixed candidate9 = some ⟨candidate9,parents9⟩ :=
  fromComponents shape9 rfl rfl authority9
theorem wrongHeight9 :
    (check sha policy state abortMixed {candidate9 with height := 2}).isNone = true := by decide
theorem wrongContext9 : ¬ Authority sha policy state abortMixed
    {candidate9 with context := ascii "other"} parents9 := by decide

theorem wholeOriginalConfig :
    (bindPolicy NativeConfigAdmissionVectors.sha policy state).isSome = true := by decide
theorem wholeOriginalConfigBytes :
    (prepare NativeConfigAdmissionVectors.sha NativeConfigAdmissionVectors.policyRaw
      NativeConfigAdmissionVectors.stateRaw).isSome = true := by
  unfold prepare
  rw [NativeConfigAdmissionVectors.policyDecoded,NativeConfigAdmissionVectors.stateDecoded]
  exact wholeOriginalConfig
theorem authorityDoesNotPrematurelyRequireCurrent :
    NativeCandidateShape.Checks policy candidate1
      {parents1 with checkpoint := NativeSnapshotBaseVectors.base.schema} ∧
    Authority sha policy state mixed candidate1
      {parents1 with checkpoint := NativeSnapshotBaseVectors.base.schema} := by decide
theorem parameterContextIsOriginalAssignment :
    candidate5.context = NativeParameterVectors.body.voteContext := by decide
theorem missingBody :
    ¬ Authority sha policy state {mixed with prior := {mixed.prior with prior :=
      {applies with roots := {roots with bodies := []}}}} candidate6 parents6 := by decide
theorem missingFinalizedRoot :
    ¬ Authority sha policy state {mixed with prior := {mixed.prior with prior :=
      {applies with roots := {roots with finalized := []}}}} candidate7 parents7 := by decide
theorem changedNormParent : ¬ Authority sha policy state mixed candidate4
    {parents4 with norm := parents4.isc} := by decide
theorem changedSeedParent : ¬ Authority sha policy state mixed candidate5
    {parents5 with seed := parents5.plan} := by decide
theorem changedMatrix : ¬ Authority sha policy state mixed candidate6
    {parents6 with matrix := parents6.plan} := by decide
theorem changedApplyIdentity : ¬ Authority sha policy state mixed candidate7
    {parents7 with apply := parents7.root} := by decide
theorem changedCurrent : ¬ Authority sha policy
    {state with wire := {state.wire with parent := parents7.root}}
    mixed candidate7 parents7 := by decide
theorem missingClosed :
    ¬ Authority sha policy state {mixed with base := {mixed.base with closed := []}}
      candidate2 parents2 := by decide
theorem missingConfig :
    ¬ Authority sha policy state {mixed with base := {mixed.base with proposedConfigs := []}}
      candidate1 parents1 := by decide
theorem badAction : ¬ Authority sha policy state mixed
    {candidate1 with action := 0} parents1 := by decide
theorem missingTimeout : ¬ Authority sha policy state
    {mixed with prior := {mixed.prior with tail := {mixed.prior.tail with timeouts := []}}}
    candidate8 parents8 := by decide
theorem abortAfterApply : ¬ Authority sha policy state
    {abortMixed with prior := {abortMixed.prior with tail := {abortMixed.prior.tail with
      lineage := {abortMixed.prior.tail.lineage with applies := [candidate7.body]}}}}
    candidate9 parents9 := by decide
theorem rejectParent_config : ¬ NativeCandidateShape.Checks policy
    candidate1 {parents1 with config := []} := by decide
theorem rejectParent_checkpoint : ¬ NativeCandidateShape.Checks policy
    candidate1 {parents1 with checkpoint := []} := by decide
theorem rejectParent_isc : ¬ NativeCandidateShape.Checks policy
    candidate3 {parents3 with isc := []} := by decide
theorem rejectParent_seed : ¬ NativeCandidateShape.Checks policy
    candidate3 {parents3 with seed := []} := by decide
theorem rejectParent_norm : ¬ NativeCandidateShape.Checks policy
    candidate3 {parents3 with norm := []} := by decide
theorem rejectParent_ec : ¬ NativeCandidateShape.Checks policy
    candidate4 {parents4 with ec := []} := by decide
theorem rejectParent_plan : ¬ NativeCandidateShape.Checks policy
    candidate5 {parents5 with plan := []} := by decide
theorem rejectParent_matrix : ¬ NativeCandidateShape.Checks policy
    candidate6 {parents6 with matrix := []} := by decide
theorem rejectParent_root : ¬ NativeCandidateShape.Checks policy
    candidate7 {parents7 with root := []} := by decide
theorem rejectParent_profile : ¬ NativeCandidateShape.Checks policy
    candidate7 {parents7 with profile := []} := by decide
theorem rejectParent_apply : ¬ NativeCandidateShape.Checks policy
    candidate7 {parents7 with apply := []} := by decide
theorem rejectParent_last : ¬ NativeCandidateShape.Checks policy
    candidate1 {parents1 with last := policy.config} := by decide
theorem rejectParent_domain : ¬ NativeCandidateShape.Checks policy
    candidate5 {parents5 with domain := []} := by decide
theorem rejectParent_shard : ¬ NativeCandidateShape.Checks policy
    candidate5 {parents5 with shard := []} := by decide
theorem rejectParent_reason : ¬ NativeCandidateShape.Checks policy
    candidate9 {parents9 with reason := []} := by decide

theorem originalPairList :
    (checkAll sha policy state mixed [candidate1,candidate2]).isSome = true := by decide
theorem badSecondCannotBeSkipped :
    (checkAll sha policy state mixed [candidate1,{candidate2 with context := []}]).isNone = true :=
  by decide
theorem duplicateContextRejected :
    ¬ NativePolicyBytes.Canonical {policy with candidates := [candidate1,candidate1]} := by decide
theorem reversedOrderRejected :
    ¬ NativePolicyBytes.Canonical {policy with candidates := [candidate2,candidate1]} := by decide
end DeltaReduce.NativeCandidateAuthorityVectors
