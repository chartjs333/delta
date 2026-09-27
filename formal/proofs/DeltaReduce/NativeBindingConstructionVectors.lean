import DeltaReduce.NativeBindingConstruction

/-! Small synthetic codec examples exercise the general traversal. This byte
codec is NOT canonical JSON, cryptographic hashing or native authentication. -/
namespace DeltaReduce.NativeBindingConstructionVectors
open NativeBinding

def ref (n : UInt8) (kind : Kind) : Ref := ⟨List.replicate 32 n,kind,1⟩
def schema : Ref := ref 0 .schema
def model : Ref := ref 1 .model
def optimizer : Ref := ref 2 .optimizer
def profile : Ref := ref 3 .profile
def apc : Ref := ref 4 .apc
def ec : Ref := ref 5 .ec
def plan : Ref := ref 6 .plan
def isc : Ref := ref 7 .isc
def q : Ref := ref 8 .qShard
def root : Ref := ref 9 .authority
def context : Context := ⟨"r",1,0,"e",100,"parent"⟩
def authority : Authority := ⟨context,schema,profile,plan,model,optimizer,isc,ec,apc⟩
def scalar : StateVector := ⟨schema,⟨1,1⟩,[1]⟩
def profileValue : Profile := ⟨64,⟨1,1⟩,[⟨"d",⟨1,1⟩⟩],⟨1,1⟩,⟨0,1⟩,⟨0,1⟩,
  "HALF_TOWARD_POSITIVE",true,"FULL_SIGNED_INT64"⟩
def planValue : Plan := ⟨schema,profile,[⟨"t","d"⟩],[⟨"d","s","ctx",1,⟨1,1⟩,[⟨"t",⟨1,1⟩,q⟩]⟩]⟩
def payload : Bytes → Option Payload
  | [0] => some (.schema ["c"] [⟨"s",0,1⟩])
  | [1] => some (.model scalar)
  | [2] => some (.optimizer scalar)
  | [3] => some (.profile profileValue)
  | [4] => some (.apc ec plan)
  | [5] => some (.ec isc ["t"])
  | [6] => some (.plan planValue)
  | [7] => some (.isc ["t"] [⟨"t","d",[⟨"s",q⟩]⟩])
  | [8] => some (.qShard ⟨"t","d","s",schema,⟨1,1⟩,[2]⟩)
  | [9] => some (.authority authority)
  | _ => none
def codec : Codec := ⟨fun raw => List.replicate 32 (raw.headD 255),
  fun raw => raw.length == 1,payload,fun _ _ => []⟩
def store : Store := fun id =>
  if id = List.replicate 32 (id.headD 255) ∧ id.headD 255 < 10 then some [id.headD 255] else none

theorem leafAccepted : NativeGraphClosure.check codec store 1 schema = true := by decide
theorem completeGraphAccepted : NativeGraphClosure.check codec store 6 root = true := by decide
theorem insufficientDepthRejected : NativeGraphClosure.check codec store 5 root = false := by decide
theorem zeroDepthRejected : NativeGraphClosure.check codec store 0 root = false := rfl
theorem sharedGraphComplete : Complete codec store root := NativeGraphClosure.complete completeGraphAccepted
theorem missingQRejected : NativeGraphClosure.check codec
    (fun id => if id = q.id then none else store id) 6 root = false := by decide
theorem missingProfileRejected : NativeGraphClosure.check codec
    (fun id => if id = profile.id then none else store id) 6 root = false := by decide
theorem missingSchemaRejected : NativeGraphClosure.check codec
    (fun id => if id = schema.id then none else store id) 6 root = false := by decide
theorem alteredBytesRejected : NativeGraphClosure.check codec
    (fun id => if id = root.id then some [8] else store id) 6 root = false := by decide
theorem wrongLengthRejected : NativeGraphClosure.check codec store 6 { root with length := 2 } = false := by decide
theorem wrongKindRejected : NativeGraphClosure.check codec store 6 { root with kind := .model } = false := by decide
theorem noncanonicalRejected : NativeGraphClosure.check { codec with canonical := fun _ => false } store 6 root = false := by decide
theorem malformedIdRejected : NativeGraphClosure.check codec store 6 { root with id := [9] } = false := by decide
theorem missingDecodeRejected : NativeGraphClosure.check { codec with decode := fun _ => none } store 6 root = false := by decide
theorem badEdgeTypeRejected : NativeGraphClosure.check
    { codec with decode := fun raw => if raw = [1] then some (.model { scalar with schema := model }) else payload raw }
    store 6 root = false := by decide
theorem authorityOrder : (.authority authority : Payload).refs = [schema,profile,plan,model,optimizer,isc,ec,apc] := rfl
theorem swappedOrderChangesPath : (.authority { authority with model := optimizer, optimizer := model } : Payload).refs[3]? = some optimizer := rfl

def contextBytes : Bytes := [123,34,101,112,111,99,104,34,58,34,101,34,44,34,104,97,114,100,95,100,101,97,100,108,105,110,101,34,58,49,48,48,44,34,104,101,105,103,104,116,34,58,49,44,34,112,97,114,101,110,116,95,99,104,101,99,107,112,111,105,110,116,34,58,34,112,97,114,101,110,116,34,44,34,114,111,117,110,100,34,58,34,114,34,44,34,118,105,101,119,34,58,48,125]

set_option maxRecDepth 4096 in
theorem contextCanonical : NativeAuthorityProjection.encodeContext context = contextBytes := by decide

def schemaBytes : Bytes := [123,34,105,100,34,58,34,115,104,97,50,53,54,58,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,34,44,34,107,105,110,100,34,58,34,83,67,72,69,77,65,34,44,34,108,101,110,103,116,104,34,58,49,125]

set_option maxRecDepth 4096 in
theorem schemaCanonical : NativeIscProjection.encodeRef "SCHEMA" schema = schemaBytes := by decide

def modelBytes : Bytes := [123,34,105,100,34,58,34,115,104,97,50,53,54,58,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,34,44,34,107,105,110,100,34,58,34,77,79,68,69,76,34,44,34,108,101,110,103,116,104,34,58,49,125]

set_option maxRecDepth 4096 in
theorem modelCanonical : NativeIscProjection.encodeRef "MODEL" model = modelBytes := by decide

def optimizerBytes : Bytes := [123,34,105,100,34,58,34,115,104,97,50,53,54,58,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,48,50,34,44,34,107,105,110,100,34,58,34,79,80,84,73,77,73,90,69,82,34,44,34,108,101,110,103,116,104,34,58,49,125]

set_option maxRecDepth 4096 in
theorem optimizerCanonical : NativeIscProjection.encodeRef "OPTIMIZER" optimizer = optimizerBytes := by decide

def profileBytes : Bytes := [123,34,105,100,34,58,34,115,104,97,50,53,54,58,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,48,51,34,44,34,107,105,110,100,34,58,34,80,82,79,70,73,76,69,34,44,34,108,101,110,103,116,104,34,58,49,125]

set_option maxRecDepth 4096 in
theorem profileCanonical : NativeIscProjection.encodeRef "PROFILE" profile = profileBytes := by decide

def apcBytes : Bytes := [123,34,105,100,34,58,34,115,104,97,50,53,54,58,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,48,52,34,44,34,107,105,110,100,34,58,34,65,80,67,95,80,82,79,74,69,67,84,73,79,78,34,44,34,108,101,110,103,116,104,34,58,49,125]

set_option maxRecDepth 4096 in
theorem apcCanonical : NativeIscProjection.encodeRef "APC_PROJECTION" apc = apcBytes := by decide

def ecBytes : Bytes := [123,34,105,100,34,58,34,115,104,97,50,53,54,58,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,48,53,34,44,34,107,105,110,100,34,58,34,69,67,95,80,82,79,74,69,67,84,73,79,78,34,44,34,108,101,110,103,116,104,34,58,49,125]

set_option maxRecDepth 4096 in
theorem ecCanonical : NativeIscProjection.encodeRef "EC_PROJECTION" ec = ecBytes := by decide

def planBytes : Bytes := [123,34,105,100,34,58,34,115,104,97,50,53,54,58,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,48,54,34,44,34,107,105,110,100,34,58,34,80,76,65,78,34,44,34,108,101,110,103,116,104,34,58,49,125]

set_option maxRecDepth 4096 in
theorem planCanonical : NativeIscProjection.encodeRef "PLAN" plan = planBytes := by decide

def iscBytes : Bytes := [123,34,105,100,34,58,34,115,104,97,50,53,54,58,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,48,55,34,44,34,107,105,110,100,34,58,34,73,83,67,95,80,82,79,74,69,67,84,73,79,78,34,44,34,108,101,110,103,116,104,34,58,49,125]

set_option maxRecDepth 4096 in
theorem iscCanonical : NativeIscProjection.encodeRef "ISC_PROJECTION" isc = iscBytes := by decide

def authorityBytes : Bytes :=
  [123,34,107,105,110,100,34,58,34,65,85,84,72,79,82,73,84,89,34,44,34,112,97,121,108,111,97,100,34,58,123,34,99,111,110,116,101,120,116,34,58] ++
  contextBytes ++
  [44,34,109,111,100,101,108,34,58] ++
  modelBytes ++
  [44,34,111,112,116,105,109,105,122,101,114,34,58] ++
  optimizerBytes ++
  [44,34,112,97,114,101,110,116,115,34,58,123,34,97,112,99,34,58] ++
  apcBytes ++
  [44,34,101,99,34,58] ++
  ecBytes ++
  [44,34,105,115,99,34,58] ++
  iscBytes ++
  [125,44,34,112,108,97,110,34,58] ++
  planBytes ++
  [44,34,112,114,111,102,105,108,101,34,58] ++
  profileBytes ++
  [44,34,115,99,104,101,109,97,34,58] ++
  schemaBytes ++
  [125,125]

theorem authorityCanonical : NativeAuthorityProjection.encode authority = authorityBytes := by
  simp only [NativeAuthorityProjection.encode,authority,contextCanonical,schemaCanonical,modelCanonical,optimizerCanonical,profileCanonical,apcCanonical,ecCanonical,planCanonical,iscCanonical]
  rfl

end DeltaReduce.NativeBindingConstructionVectors
