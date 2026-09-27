import DeltaReduce.NativeQHeader
import DeltaReduce.NativeQBytesVectors

/-! Original header bytes; no payload SHA, source graph or exporter authentication. -/
namespace DeltaReduce.NativeQHeaderVectors
open NativeVoteBytes (ascii ContentId)
open NativeQHeader
set_option maxRecDepth 4000
set_option maxHeartbeats 1000000

def bytes0 : NativeReceiptBytes.Bytes := [52]
theorem value0 : NativeQJson.ValueValid .natural bytes0 := by decide
def bytes1 : NativeReceiptBytes.Bytes := [48]
theorem value1 : NativeQJson.ValueValid .natural bytes1 := by decide
def bytes2 : NativeReceiptBytes.Bytes := [115,104,97,50,53,54,58,99,99,57,56,102,49,53,97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54,48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54]
theorem value2 : NativeQJson.ValueValid .text bytes2 := by decide
theorem id2 : ContentId bytes2 := by decide
def bytes3 : NativeReceiptBytes.Bytes := [115,104,97,50,53,54,58,102,52,51,99,48,50,53,57,55,52,57,98,49,53,97,101,48,100,48,49,53,52,97,54,101,57,48,57,52,55,55,52,99,55,101,97,54,53,101,53,53,97,100,101,102,98,97,101,97,52,48,48,97,54,50,48,49,97,99,98,54,50,51,57]
theorem value3 : NativeQJson.ValueValid .text bytes3 := by decide
theorem id3 : ContentId bytes3 := by decide
def bytes4 : NativeReceiptBytes.Bytes := [115,104,97,50,53,54,58,57,97,56,98,97,57,100,99,99,51,51,49,51,99,54,56,55,51,100,50,102,54,56,51,100,54,48,55,56,98,98,100,50,52,101,48,101,100,97,98,53,53,54,50,49,101,51,53,102,99,57,98,102,97,50,48,99,52,100,97,55,57,54,98]
theorem value4 : NativeQJson.ValueValid .text bytes4 := by decide
theorem id4 : ContentId bytes4 := by decide
def bytes5 : NativeReceiptBytes.Bytes := [115,104,97,50,53,54,58,49,55,99,56,100,50,51,55,57,48,48,52,55,57,54,54,101,52,50,102,51,50,48,52,53,48,50,54,50,51,99,55,52,97,48,102,102,48,51,56,51,51,49,57,100,50,51,101,54,55,97,98,49,53,99,102,57,50,102,101,51,101,54,49]
theorem value5 : NativeQJson.ValueValid .text bytes5 := by decide
theorem id5 : ContentId bytes5 := by decide
def bytes6 : NativeReceiptBytes.Bytes := [115,104,97,50,53,54,58,57,57,51,98,52,100,53,49,48,52,56,49,48,100,100,50,54,97,51,49,53,57,98,54,48,99,102,56,102,101,57,97,102,101,54,49,53,52,99,100,99,99,97,57,48,100,50,50,98,53,55,55,97,101,49,98,54,100,49,97,99,48,55,54]
theorem value6 : NativeQJson.ValueValid .text bytes6 := by decide
theorem id6 : ContentId bytes6 := by decide
def bytes7 : NativeReceiptBytes.Bytes := [115,104,97,50,53,54,58,51,52,98,99,48,56,99,51,49,54,100,102,101,50,50,101,102,101,49,53,53,101,100,49,49,98,56,54,54,98,99,99,48,100,97,102,55,101,102,56,99,51,99,55,51,56,57,99,53,54,98,50,102,50,99,55,48,55,52,52,51,54,50,57]
theorem value7 : NativeQJson.ValueValid .text bytes7 := by decide
theorem id7 : ContentId bytes7 := by decide
def bytes8 : NativeReceiptBytes.Bytes := [115,104,97,50,53,54,58,52,51,52,48,57,50,102,56,50,49,56,56,51,51,55,100,48,97,50,55,51,99,100,49,51,99,57,51,101,48,54,100,101,99,53,53,97,101,56,52,50,100,102,48,52,57,56,101,52,100,53,50,99,97,97,49,100,49,56,52,52,50,48,53]
theorem value8 : NativeQJson.ValueValid .text bytes8 := by decide
theorem id8 : ContentId bytes8 := by decide
def bytes9 : NativeReceiptBytes.Bytes := [100,101,99,111,100,101,114,46,98,105,97,115]
theorem value9 : NativeQJson.ValueValid .text bytes9 := by decide
theorem token9 : Token bytes9 := by decide
def bytes10 : NativeReceiptBytes.Bytes := [115,104,97,50,53,54,58,52,99,54,52,52,97,51,50,53,52,101,100,98,51,100,55,98,102,102,48,48,57,98,98,101,57,49,101,101,57,57,100,102,54,48,53,49,53,49,54,51,54,50,102,97,49,97,49,101,97,99,54,102,48,97,56,48,51,97,57,99,55,97,49]
theorem value10 : NativeQJson.ValueValid .text bytes10 := by decide
theorem id10 : ContentId bytes10 := by decide
def bytes11 : NativeReceiptBytes.Bytes := [116,105,99,107,101,116,45,48,48,50,45,102,105,120,116,117,114,101]
theorem value11 : NativeQJson.ValueValid .text bytes11 := by decide
theorem token11 : Token bytes11 := by decide
def bytes12 : NativeReceiptBytes.Bytes := [56]
theorem value12 : NativeQJson.ValueValid .natural bytes12 := by decide
def bytes13 : NativeReceiptBytes.Bytes := [49]
theorem value13 : NativeQJson.ValueValid .natural bytes13 := by decide
def bytes14 : NativeReceiptBytes.Bytes := [115,104,97,50,53,54,58,49,49,49,51,57,97,55,54,54,101,97,48,102,57,56,55,101,97,49,102,50,54,52,97,53,97,100,99,98,97,101,48,56,99,99,54,50,56,52,53,98,100,48,102,51,57,49,49,102,102,48,55,56,101,100,57,48,98,52,99,51,100,51,49]
theorem value14 : NativeQJson.ValueValid .text bytes14 := by decide
theorem id14 : ContentId bytes14 := by decide
def bytes15 : NativeReceiptBytes.Bytes := [101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116]
theorem value15 : NativeQJson.ValueValid .text bytes15 := by decide
theorem token15 : Token bytes15 := by decide
def bytes16 : NativeReceiptBytes.Bytes := [49,50]
theorem value16 : NativeQJson.ValueValid .natural bytes16 := by decide
def bytes17 : NativeReceiptBytes.Bytes := [50]
theorem value17 : NativeQJson.ValueValid .natural bytes17 := by decide
def bytes18 : NativeReceiptBytes.Bytes := [115,104,97,50,53,54,58,99,102,49,55,55,53,99,54,97,102,102,48,53,100,51,56,56,98,102,53,57,101,99,57,100,102,56,48,102,97,48,57,57,54,97,49,55,99,97,54,49,52,48,54,56,101,51,49,100,49,48,50,99,97,49,101,101,49,98,48,102,48,55,50]
theorem value18 : NativeQJson.ValueValid .text bytes18 := by decide
theorem id18 : ContentId bytes18 := by decide
def bytes19 : NativeReceiptBytes.Bytes := [50,48]
theorem value19 : NativeQJson.ValueValid .natural bytes19 := by decide
def bytes20 : NativeReceiptBytes.Bytes := [51]
theorem value20 : NativeQJson.ValueValid .natural bytes20 := by decide
def bytes21 : NativeReceiptBytes.Bytes := [115,104,97,50,53,54,58,54,98,97,56,54,54,53,50,48,100,53,98,52,49,56,53,51,54,50,55,102,102,57,97,50,56,51,49,51,55,98,99,51,97,52,49,48,56,50,57,55,102,57,97,99,102,97,51,99,98,100,53,99,53,102,57,98,50,55,50,101,48,57,99]
theorem value21 : NativeQJson.ValueValid .text bytes21 := by decide
theorem id21 : ContentId bytes21 := by decide
def bytes22 : NativeReceiptBytes.Bytes := [49,54]
theorem value22 : NativeQJson.ValueValid .natural bytes22 := by decide
def bytes23 : NativeReceiptBytes.Bytes := [50,56]
theorem value23 : NativeQJson.ValueValid .natural bytes23 := by decide
def bytes24 : NativeReceiptBytes.Bytes := [115,104,97,50,53,54,58,51,102,55,48,48,48,102,56,102,48,57,99,99,48,53,52,50,54,99,102,99,49,99,56,50,100,56,99,49,51,100,99,99,50,53,49,53,53,98,56,50,49,53,55,54,57,57,57,54,54,53,99,101,97,55,101,49,48,57,50,102,102,56,52]
theorem value24 : NativeQJson.ValueValid .text bytes24 := by decide
theorem id24 : ContentId bytes24 := by decide
def bytes25 : NativeReceiptBytes.Bytes := [50,52]
theorem value25 : NativeQJson.ValueValid .natural bytes25 := by decide
def bytes26 : NativeReceiptBytes.Bytes := [49,46,48,46,48]
theorem value26 : NativeQJson.ValueValid .text bytes26 := by decide
theorem token26 : Token bytes26 := by decide
def bytes27 : NativeReceiptBytes.Bytes := [69,78,67,79,68,69,68,95,73,78,84,49,54,95,83,72,65,82,68]
theorem value27 : NativeQJson.ValueValid .text bytes27 := by decide
theorem token27 : Token bytes27 := by decide
def wire0 : Wire := {
  countRaw := bytes0,
  startRaw := bytes1,
  semantics := bytes2,
  ordinalRaw := bytes1,
  schema := bytes3,
  payloadHash := bytes4,
  profile := bytes5,
  proof := bytes6,
  config := bytes7,
  scale := bytes8,
  segment := bytes9,
  offsetRaw := bytes1,
  plan := bytes10,
  ticket := bytes11
}
def header0 : Header := ⟨wire0,4,0,0,0⟩
theorem sourceBytes0 : encode wire0 = NativeQBytesVectors.header0 := by rfl
theorem fieldValues0 : ∀ f ∈ fields wire0, NativeQJson.ValueValid f.kind f.value := by
  simp only [fields, List.forall_mem_cons]
  exact ⟨value0, value1, value2, value1, value3, value4, value5, value6, value7, value8, value26, value9, value1, value10, value11, value27, by simp⟩
theorem ids0 : ∀ b ∈ [wire0.semantics,wire0.schema,wire0.payloadHash,
    wire0.profile,wire0.proof,wire0.config,wire0.scale,wire0.plan], ContentId b := by
  simp only [List.forall_mem_cons]
  exact ⟨id2, id3, id4, id5, id6, id7, id8, id10, by simp⟩
theorem wireValid0 : WireValid wire0 := by
  refine ⟨fieldValues0, ?_, ids0, rfl, rfl, token9, token11⟩
  rw [sourceBytes0, NativeQBytesVectors.headerLength0]
  decide
theorem valid0 : Valid header0 := by
  exact ⟨wireValid0, by decide, by decide, by decide, by decide,
    by decide, by decide, by decide, by decide⟩
theorem decoded0 : decode NativeQBytesVectors.header0 = some header0 := by
  rw [← sourceBytes0]
  exact decodeEncoded header0 valid0
theorem joined0 : join NativeQBytesVectors.frame0 =
    some ⟨⟨NativeQBytesVectors.header0,NativeQBytesVectors.payload0,[1,-2,0,4]⟩,header0⟩ := by
  exact joinFromComputed NativeQBytesVectors.originalDecoded0 decoded0 rfl

def wire1 : Wire := {
  countRaw := bytes12,
  startRaw := bytes0,
  semantics := bytes2,
  ordinalRaw := bytes13,
  schema := bytes3,
  payloadHash := bytes14,
  profile := bytes5,
  proof := bytes6,
  config := bytes7,
  scale := bytes8,
  segment := bytes15,
  offsetRaw := bytes1,
  plan := bytes10,
  ticket := bytes11
}
def header1 : Header := ⟨wire1,8,4,1,0⟩
theorem sourceBytes1 : encode wire1 = NativeQBytesVectors.header1 := by rfl
theorem fieldValues1 : ∀ f ∈ fields wire1, NativeQJson.ValueValid f.kind f.value := by
  simp only [fields, List.forall_mem_cons]
  exact ⟨value12, value0, value2, value13, value3, value14, value5, value6, value7, value8, value26, value15, value1, value10, value11, value27, by simp⟩
theorem ids1 : ∀ b ∈ [wire1.semantics,wire1.schema,wire1.payloadHash,
    wire1.profile,wire1.proof,wire1.config,wire1.scale,wire1.plan], ContentId b := by
  simp only [List.forall_mem_cons]
  exact ⟨id2, id3, id14, id5, id6, id7, id8, id10, by simp⟩
theorem wireValid1 : WireValid wire1 := by
  refine ⟨fieldValues1, ?_, ids1, rfl, rfl, token15, token11⟩
  rw [sourceBytes1, NativeQBytesVectors.headerLength1]
  decide
theorem valid1 : Valid header1 := by
  exact ⟨wireValid1, by decide, by decide, by decide, by decide,
    by decide, by decide, by decide, by decide⟩
theorem decoded1 : decode NativeQBytesVectors.header1 = some header1 := by
  rw [← sourceBytes1]
  exact decodeEncoded header1 valid1
theorem joined1 : join NativeQBytesVectors.frame1 =
    some ⟨⟨NativeQBytesVectors.header1,NativeQBytesVectors.payload1,[-16,-15,-14,-13,-12,-11,-10,-9]⟩,header1⟩ := by
  exact joinFromComputed NativeQBytesVectors.originalDecoded1 decoded1 rfl

def wire2 : Wire := {
  countRaw := bytes12,
  startRaw := bytes16,
  semantics := bytes2,
  ordinalRaw := bytes17,
  schema := bytes3,
  payloadHash := bytes18,
  profile := bytes5,
  proof := bytes6,
  config := bytes7,
  scale := bytes8,
  segment := bytes15,
  offsetRaw := bytes12,
  plan := bytes10,
  ticket := bytes11
}
def header2 : Header := ⟨wire2,8,12,2,8⟩
theorem sourceBytes2 : encode wire2 = NativeQBytesVectors.header2 := by rfl
theorem fieldValues2 : ∀ f ∈ fields wire2, NativeQJson.ValueValid f.kind f.value := by
  simp only [fields, List.forall_mem_cons]
  exact ⟨value12, value16, value2, value17, value3, value18, value5, value6, value7, value8, value26, value15, value12, value10, value11, value27, by simp⟩
theorem ids2 : ∀ b ∈ [wire2.semantics,wire2.schema,wire2.payloadHash,
    wire2.profile,wire2.proof,wire2.config,wire2.scale,wire2.plan], ContentId b := by
  simp only [List.forall_mem_cons]
  exact ⟨id2, id3, id18, id5, id6, id7, id8, id10, by simp⟩
theorem wireValid2 : WireValid wire2 := by
  refine ⟨fieldValues2, ?_, ids2, rfl, rfl, token15, token11⟩
  rw [sourceBytes2, NativeQBytesVectors.headerLength2]
  decide
theorem valid2 : Valid header2 := by
  exact ⟨wireValid2, by decide, by decide, by decide, by decide,
    by decide, by decide, by decide, by decide⟩
theorem decoded2 : decode NativeQBytesVectors.header2 = some header2 := by
  rw [← sourceBytes2]
  exact decodeEncoded header2 valid2
theorem joined2 : join NativeQBytesVectors.frame2 =
    some ⟨⟨NativeQBytesVectors.header2,NativeQBytesVectors.payload2,[-8,-7,-6,-5,-4,-3,-2,-1]⟩,header2⟩ := by
  exact joinFromComputed NativeQBytesVectors.originalDecoded2 decoded2 rfl

def wire3 : Wire := {
  countRaw := bytes12,
  startRaw := bytes19,
  semantics := bytes2,
  ordinalRaw := bytes20,
  schema := bytes3,
  payloadHash := bytes21,
  profile := bytes5,
  proof := bytes6,
  config := bytes7,
  scale := bytes8,
  segment := bytes15,
  offsetRaw := bytes22,
  plan := bytes10,
  ticket := bytes11
}
def header3 : Header := ⟨wire3,8,20,3,16⟩
theorem sourceBytes3 : encode wire3 = NativeQBytesVectors.header3 := by rfl
theorem fieldValues3 : ∀ f ∈ fields wire3, NativeQJson.ValueValid f.kind f.value := by
  simp only [fields, List.forall_mem_cons]
  exact ⟨value12, value19, value2, value20, value3, value21, value5, value6, value7, value8, value26, value15, value22, value10, value11, value27, by simp⟩
theorem ids3 : ∀ b ∈ [wire3.semantics,wire3.schema,wire3.payloadHash,
    wire3.profile,wire3.proof,wire3.config,wire3.scale,wire3.plan], ContentId b := by
  simp only [List.forall_mem_cons]
  exact ⟨id2, id3, id21, id5, id6, id7, id8, id10, by simp⟩
theorem wireValid3 : WireValid wire3 := by
  refine ⟨fieldValues3, ?_, ids3, rfl, rfl, token15, token11⟩
  rw [sourceBytes3, NativeQBytesVectors.headerLength3]
  decide
theorem valid3 : Valid header3 := by
  exact ⟨wireValid3, by decide, by decide, by decide, by decide,
    by decide, by decide, by decide, by decide⟩
theorem decoded3 : decode NativeQBytesVectors.header3 = some header3 := by
  rw [← sourceBytes3]
  exact decodeEncoded header3 valid3
theorem joined3 : join NativeQBytesVectors.frame3 =
    some ⟨⟨NativeQBytesVectors.header3,NativeQBytesVectors.payload3,[0,1,2,3,4,5,6,7]⟩,header3⟩ := by
  exact joinFromComputed NativeQBytesVectors.originalDecoded3 decoded3 rfl

def wire4 : Wire := {
  countRaw := bytes12,
  startRaw := bytes23,
  semantics := bytes2,
  ordinalRaw := bytes0,
  schema := bytes3,
  payloadHash := bytes24,
  profile := bytes5,
  proof := bytes6,
  config := bytes7,
  scale := bytes8,
  segment := bytes15,
  offsetRaw := bytes25,
  plan := bytes10,
  ticket := bytes11
}
def header4 : Header := ⟨wire4,8,28,4,24⟩
theorem sourceBytes4 : encode wire4 = NativeQBytesVectors.header4 := by rfl
theorem fieldValues4 : ∀ f ∈ fields wire4, NativeQJson.ValueValid f.kind f.value := by
  simp only [fields, List.forall_mem_cons]
  exact ⟨value12, value23, value2, value0, value3, value24, value5, value6, value7, value8, value26, value15, value25, value10, value11, value27, by simp⟩
theorem ids4 : ∀ b ∈ [wire4.semantics,wire4.schema,wire4.payloadHash,
    wire4.profile,wire4.proof,wire4.config,wire4.scale,wire4.plan], ContentId b := by
  simp only [List.forall_mem_cons]
  exact ⟨id2, id3, id24, id5, id6, id7, id8, id10, by simp⟩
theorem wireValid4 : WireValid wire4 := by
  refine ⟨fieldValues4, ?_, ids4, rfl, rfl, token15, token11⟩
  rw [sourceBytes4, NativeQBytesVectors.headerLength4]
  decide
theorem valid4 : Valid header4 := by
  exact ⟨wireValid4, by decide, by decide, by decide, by decide,
    by decide, by decide, by decide, by decide⟩
theorem decoded4 : decode NativeQBytesVectors.header4 = some header4 := by
  rw [← sourceBytes4]
  exact decodeEncoded header4 valid4
theorem joined4 : join NativeQBytesVectors.frame4 =
    some ⟨⟨NativeQBytesVectors.header4,NativeQBytesVectors.payload4,[8,9,10,11,12,13,14,15]⟩,header4⟩ := by
  exact joinFromComputed NativeQBytesVectors.originalDecoded4 decoded4 rfl

theorem leadingZero : NativeQJson.readValue .natural 44 (ascii "00,") = none := by decide
theorem negativeZero : NativeQJson.readValue .natural 44 (ascii "-0,") = none := by decide
theorem negativeOne : NativeQJson.readValue .natural 44 (ascii "-1,") = none := by decide
theorem plusSign : NativeQJson.readValue .natural 44 (ascii "+1,") = none := by decide
theorem fractionalNumber : NativeQJson.readValue .natural 44 (ascii "1.0,") = none := by decide
theorem exponentNumber : NativeQJson.readValue .natural 44 (ascii "1e0,") = none := by decide
theorem booleanNumber : NativeQJson.readValue .natural 44 (ascii "true,") = none := by decide
theorem overflowNumber : NativeQJson.readValue .natural 44 (ascii "18446744073709551616,") = none := by decide
theorem maximumUint64 : NativeQJson.readValue .natural 44 (ascii "18446744073709551615,") = some (ascii "18446744073709551615",[]) := by decide
theorem escapedText : NativeQJson.readValue .text 44 [34,92,117,48,48,54,49,34,44] = none := by decide
theorem controlText : NativeQJson.readValue .text 44 [34,10,34,44] = none := by decide
theorem nonAsciiText : NativeQJson.readValue .text 44 [34,255,34,44] = none := by decide
theorem missingQuote : NativeQJson.readValue .text 44 [34,97,44] = none := by decide
theorem nonJsonHeaderRejected : decode [255] = none := by decide
theorem badNumericWire : interpret {wire0 with countRaw := ascii "01"} = none := by decide
theorem overflowOffsetWire : interpret {wire0 with offsetRaw := ascii "18446744073709551616"} = none := by decide
theorem wrongVersion : fromValues (((fields wire0).map NativeQJson.Field.value).set 10 (ascii "2.0.0")) = none := by decide
theorem wrongType : fromValues (((fields wire0).map NativeQJson.Field.value).set 15 (ascii "Q_SHARD")) = none := by decide
theorem invalidTokenEscape : ¬ Token (ascii "a\\b") := by decide
theorem invalidTokenSpace : ¬ Token (ascii "a b") := by decide
theorem upperHexNotContentId : ¬ ContentId (ascii "sha256:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA") := by decide
theorem duplicateKey : readWire (ascii "{\"element_count\":1,\"element_count\":2}") = none := by decide
theorem extraFirstKey : readWire (ascii "{\"extra\":1,\"element_count\":1}") = none := by decide
theorem wrongFirstOrder : readWire (ascii "{\"element_start\":0,\"element_count\":1}") = none := by decide
theorem outerWhitespace : readWire (ascii " {\"element_count\":1}") = none := by decide
theorem quotedNumber : readWire (ascii "{\"element_count\":\"1\"}") = none := by decide
theorem missingFields : readWire (ascii "{\"element_count\":1}") = none := by decide

/-- Metadata/count interpretation still does not authenticate payload SHA. -/
theorem changedPayloadWithOldShaStillAccepted :
    join (NativeQBytes.encodeFrame NativeQBytesVectors.header0 [2,0,254,255,0,0,4,0]) =
      some ⟨⟨NativeQBytesVectors.header0,[2,0,254,255,0,0,4,0],[2,-2,0,4]⟩,header0⟩ := by
  exact joinFromComputed NativeQBytesVectors.changedPayloadWithOldHeaderAccepted decoded0 rfl

end DeltaReduce.NativeQHeaderVectors
