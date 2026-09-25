import DeltaReduce.PublicArithmeticInputs

-- Generated from independently pinned fixture a768ce4a038c3413d21a41df634a2c643e237e80855232820144a604258353fa.
-- Mathematical image/codec example, not native producer authentication.
namespace DeltaReduce.PublicArithmeticInputsVectors
open NativeBinding NativeInputProjection PublicState PublicArithmeticInputs
set_option Elab.async false
set_option maxRecDepth 16000
set_option maxHeartbeats 5000000

def vocabulary : Vocabulary := {
  ticket := fun n => if n == "t0000" then some "t1" else none
  domain := fun n => if n == "d1" then some "d1" else none
  shard := fun n => if n == "s1" then some "shard1" else if n == "s2" then some "shard2" else none
  tickets := ["t1"], domains := ["d1"], shards := ["shard1","shard2"]
  models := ["t1","d1","shard1","shard2"] }

def nativeProfile : Profile := {
  accumulatorBits := 64
  applyQuantum := ⟨1,1⟩
  domainWeights := [⟨"d1",⟨1,1⟩⟩]
  learningRate := ⟨1,2⟩, momentum := ⟨1,2⟩
  weightDecay := ⟨0,1⟩
  rounding := "HALF_TOWARD_POSITIVE", nesterov := true
  outputRange := "FULL_SIGNED_INT64" }

def fixtureImage : Image := {
  tickets := [⟨"t0000","d1",⟨1,1⟩,[1,(-2)]⟩]
  domains := [⟨"d1",1,[⟨1,2⟩,⟨1,2⟩]⟩]
  shards := ["s1","s2"], profile := nativeProfile
  mixtureDenominator := 1
  model := [("s1",20),("s2",(-20))], optimizer := [("s1",2),("s2",(-2))], limit := 127 }

def expectedASCII : String := "[\"fun\",[[[\"str\",\"applyD\"],[\"int\",\"1\"]],[[\"str\",\"applyN\"],[\"int\",\"1\"]],[[\"str\",\"denominator\"],[\"fun\",[[[\"model\",\"d1\"],[\"int\",\"1\"]]]]],[[\"str\",\"domainOrder\"],[\"fun\",[[[\"int\",\"1\"],[\"model\",\"d1\"]]]]],[[\"str\",\"limit\"],[\"int\",\"127\"]],[[\"str\",\"lrD\"],[\"int\",\"2\"]],[[\"str\",\"lrN\"],[\"int\",\"1\"]],[[\"str\",\"mixtureD\"],[\"int\",\"1\"]],[[\"str\",\"model\"],[\"fun\",[[[\"model\",\"shard1\"],[\"int\",\"20\"]],[[\"model\",\"shard2\"],[\"int\",\"-20\"]]]]],[[\"str\",\"muD\"],[\"int\",\"2\"]],[[\"str\",\"muN\"],[\"int\",\"1\"]],[[\"str\",\"optimizer\"],[\"fun\",[[[\"model\",\"shard1\"],[\"int\",\"2\"]],[[\"model\",\"shard2\"],[\"int\",\"-2\"]]]]],[[\"str\",\"piD\"],[\"fun\",[[[\"model\",\"d1\"],[\"int\",\"1\"]]]]],[[\"str\",\"piN\"],[\"fun\",[[[\"model\",\"d1\"],[\"int\",\"1\"]]]]],[[\"str\",\"q\"],[\"fun\",[[[\"model\",\"t1\"],[\"fun\",[[[\"model\",\"shard1\"],[\"int\",\"1\"]],[[\"model\",\"shard2\"],[\"int\",\"-2\"]]]]]]]],[[\"str\",\"qD\"],[\"fun\",[[[\"model\",\"d1\"],[\"fun\",[[[\"model\",\"shard1\"],[\"int\",\"2\"]],[[\"model\",\"shard2\"],[\"int\",\"2\"]]]]]]]],[[\"str\",\"qN\"],[\"fun\",[[[\"model\",\"d1\"],[\"fun\",[[[\"model\",\"shard1\"],[\"int\",\"1\"]],[[\"model\",\"shard2\"],[\"int\",\"1\"]]]]]]]],[[\"str\",\"ticketDomain\"],[\"fun\",[[[\"model\",\"t1\"],[\"model\",\"d1\"]]]]],[[\"str\",\"ticketOrder\"],[\"fun\",[[[\"int\",\"1\"],[\"model\",\"t1\"]]]]],[[\"str\",\"wdD\"],[\"int\",\"1\"]],[[\"str\",\"wdN\"],[\"int\",\"0\"]],[[\"str\",\"weightD\"],[\"fun\",[[[\"model\",\"t1\"],[\"int\",\"1\"]]]]],[[\"str\",\"weightN\"],[\"fun\",[[[\"model\",\"t1\"],[\"int\",\"1\"]]]]]]]"

def table0 : Value := (.function (entries [((.model "t1"),(.model "d1"))]))
theorem computed0 : ticketDomains vocabulary fixtureImage = some table0 := by decide +kernel

def table1 : Value := (.function (entries [((.model "t1"),(.function (entries [((.model "shard1"),(.integer 1)),((.model "shard2"),(.integer (-2)))])))]))
theorem computed1 : qTable vocabulary fixtureImage = some table1 := by decide +kernel

def table2 : Value := (.function (entries [((.model "t1"),(.integer 1))]))
theorem computed2 : weightTable Rational.numerator vocabulary fixtureImage = some table2 := by decide +kernel

def table3 : Value := (.function (entries [((.model "t1"),(.integer 1))]))
theorem computed3 : weightTable Rational.denominator vocabulary fixtureImage = some table3 := by decide +kernel

def table4 : Value := (.function (entries [((.model "d1"),(.integer 1))]))
theorem computed4 : denominatorTable vocabulary fixtureImage = some table4 := by decide +kernel

def table5 : Value := (.function (entries [((.model "d1"),(.function (entries [((.model "shard1"),(.integer 1)),((.model "shard2"),(.integer 1))])))]))
theorem computed5 : quantumTable Rational.numerator vocabulary fixtureImage = some table5 := by decide +kernel

def table6 : Value := (.function (entries [((.model "d1"),(.function (entries [((.model "shard1"),(.integer 2)),((.model "shard2"),(.integer 2))])))]))
theorem computed6 : quantumTable Rational.denominator vocabulary fixtureImage = some table6 := by decide +kernel

def table7 : Value := (.function (entries [((.model "d1"),(.integer 1))]))
theorem computed7 : mixtureTable Rational.numerator vocabulary fixtureImage = some table7 := by decide +kernel

def table8 : Value := (.function (entries [((.model "d1"),(.integer 1))]))
theorem computed8 : mixtureTable Rational.denominator vocabulary fixtureImage = some table8 := by decide +kernel

def table9 : Value := (.function (entries [((.model "shard1"),(.integer 20)),((.model "shard2"),(.integer (-20)))]))
theorem computed9 : currentTable vocabulary.shard fixtureImage.model = some table9 := by decide +kernel

def table10 : Value := (.function (entries [((.model "shard1"),(.integer 2)),((.model "shard2"),(.integer (-2)))]))
theorem computed10 : currentTable vocabulary.shard fixtureImage.optimizer = some table10 := by decide +kernel

def fixtureComponents : Components vocabulary fixtureImage := {
  ticketNames := ["t1"], tickets := by decide +kernel
  domainNames := ["d1"], domains := by decide +kernel
  values := [table0,table1,table2,table3,table4,table5,table6,table7,table8,table9,table10]
  computed := by simp only [computed0,computed1,computed2,computed3,computed4,computed5,computed6,computed7,computed8,computed9,computed10,collect,id,Bind.bind,Option.bind]
  size := by decide +kernel
  ticketSet := by decide +kernel
  domainSet := by decide +kernel
  shardSet := by decide +kernel }

def expectedValue : Value := (.function (entries [((.text "applyD"),(.integer 1)),((.text "applyN"),(.integer 1)),((.text "denominator"),(.function (entries [((.model "d1"),(.integer 1))]))),((.text "domainOrder"),(.function (entries [((.integer 1),(.model "d1"))]))),((.text "limit"),(.integer 127)),((.text "lrD"),(.integer 2)),((.text "lrN"),(.integer 1)),((.text "mixtureD"),(.integer 1)),((.text "model"),(.function (entries [((.model "shard1"),(.integer 20)),((.model "shard2"),(.integer (-20)))]))),((.text "muD"),(.integer 2)),((.text "muN"),(.integer 1)),((.text "optimizer"),(.function (entries [((.model "shard1"),(.integer 2)),((.model "shard2"),(.integer (-2)))]))),((.text "piD"),(.function (entries [((.model "d1"),(.integer 1))]))),((.text "piN"),(.function (entries [((.model "d1"),(.integer 1))]))),((.text "q"),(.function (entries [((.model "t1"),(.function (entries [((.model "shard1"),(.integer 1)),((.model "shard2"),(.integer (-2)))])))]))),((.text "qD"),(.function (entries [((.model "d1"),(.function (entries [((.model "shard1"),(.integer 2)),((.model "shard2"),(.integer 2))])))]))),((.text "qN"),(.function (entries [((.model "d1"),(.function (entries [((.model "shard1"),(.integer 1)),((.model "shard2"),(.integer 1))])))]))),((.text "ticketDomain"),(.function (entries [((.model "t1"),(.model "d1"))]))),((.text "ticketOrder"),(.function (entries [((.integer 1),(.model "t1"))]))),((.text "wdD"),(.integer 1)),((.text "wdN"),(.integer 0)),((.text "weightD"),(.function (entries [((.model "t1"),(.integer 1))]))),((.text "weightN"),(.function (entries [((.model "t1"),(.integer 1))])))]))

theorem computedFields :
    Value.function (entries (fixtureComponents.fields.map (fun (k,x) => (.text k,x)))) = expectedValue := by rfl

theorem expectedCanonical : canonical vocabulary.models expectedValue = true := by decide +kernel

def fixtureEncoded : Encoded vocabulary fixtureImage :=
  ⟨fixtureComponents,by rw [computedFields]; exact expectedCanonical⟩

theorem encodedValue : fixtureEncoded.value = expectedValue := computedFields


def rawField0 : Bytes := asciiBytes "[[\"str\",\"applyD\"],[\"int\",\"1\"]]"
theorem fieldEncoding0 : [91] ++ encode (.text "applyD") ++ [44] ++ encode (.integer 1) ++ [93] = rawField0 := by decide +kernel

def rawField1 : Bytes := asciiBytes "[[\"str\",\"applyN\"],[\"int\",\"1\"]]"
theorem fieldEncoding1 : [91] ++ encode (.text "applyN") ++ [44] ++ encode (.integer 1) ++ [93] = rawField1 := by decide +kernel

def rawField2 : Bytes := asciiBytes "[[\"str\",\"denominator\"],[\"fun\",[[[\"model\",\"d1\"],[\"int\",\"1\"]]]]]"
theorem fieldEncoding2 : [91] ++ encode (.text "denominator") ++ [44] ++ encode (.function (entries [((.model "d1"),(.integer 1))])) ++ [93] = rawField2 := by decide +kernel

def rawField3 : Bytes := asciiBytes "[[\"str\",\"domainOrder\"],[\"fun\",[[[\"int\",\"1\"],[\"model\",\"d1\"]]]]]"
theorem fieldEncoding3 : [91] ++ encode (.text "domainOrder") ++ [44] ++ encode (.function (entries [((.integer 1),(.model "d1"))])) ++ [93] = rawField3 := by decide +kernel

def rawField4 : Bytes := asciiBytes "[[\"str\",\"limit\"],[\"int\",\"127\"]]"
theorem fieldEncoding4 : [91] ++ encode (.text "limit") ++ [44] ++ encode (.integer 127) ++ [93] = rawField4 := by decide +kernel

def rawField5 : Bytes := asciiBytes "[[\"str\",\"lrD\"],[\"int\",\"2\"]]"
theorem fieldEncoding5 : [91] ++ encode (.text "lrD") ++ [44] ++ encode (.integer 2) ++ [93] = rawField5 := by decide +kernel

def rawField6 : Bytes := asciiBytes "[[\"str\",\"lrN\"],[\"int\",\"1\"]]"
theorem fieldEncoding6 : [91] ++ encode (.text "lrN") ++ [44] ++ encode (.integer 1) ++ [93] = rawField6 := by decide +kernel

def rawField7 : Bytes := asciiBytes "[[\"str\",\"mixtureD\"],[\"int\",\"1\"]]"
theorem fieldEncoding7 : [91] ++ encode (.text "mixtureD") ++ [44] ++ encode (.integer 1) ++ [93] = rawField7 := by decide +kernel

def rawField8 : Bytes := asciiBytes "[[\"str\",\"model\"],[\"fun\",[[[\"model\",\"shard1\"],[\"int\",\"20\"]],[[\"model\",\"shard2\"],[\"int\",\"-20\"]]]]]"
theorem fieldEncoding8 : [91] ++ encode (.text "model") ++ [44] ++ encode (.function (entries [((.model "shard1"),(.integer 20)),((.model "shard2"),(.integer (-20)))])) ++ [93] = rawField8 := by decide +kernel

def rawField9 : Bytes := asciiBytes "[[\"str\",\"muD\"],[\"int\",\"2\"]]"
theorem fieldEncoding9 : [91] ++ encode (.text "muD") ++ [44] ++ encode (.integer 2) ++ [93] = rawField9 := by decide +kernel

def rawField10 : Bytes := asciiBytes "[[\"str\",\"muN\"],[\"int\",\"1\"]]"
theorem fieldEncoding10 : [91] ++ encode (.text "muN") ++ [44] ++ encode (.integer 1) ++ [93] = rawField10 := by decide +kernel

def rawField11 : Bytes := asciiBytes "[[\"str\",\"optimizer\"],[\"fun\",[[[\"model\",\"shard1\"],[\"int\",\"2\"]],[[\"model\",\"shard2\"],[\"int\",\"-2\"]]]]]"
theorem fieldEncoding11 : [91] ++ encode (.text "optimizer") ++ [44] ++ encode (.function (entries [((.model "shard1"),(.integer 2)),((.model "shard2"),(.integer (-2)))])) ++ [93] = rawField11 := by decide +kernel

def rawField12 : Bytes := asciiBytes "[[\"str\",\"piD\"],[\"fun\",[[[\"model\",\"d1\"],[\"int\",\"1\"]]]]]"
theorem fieldEncoding12 : [91] ++ encode (.text "piD") ++ [44] ++ encode (.function (entries [((.model "d1"),(.integer 1))])) ++ [93] = rawField12 := by decide +kernel

def rawField13 : Bytes := asciiBytes "[[\"str\",\"piN\"],[\"fun\",[[[\"model\",\"d1\"],[\"int\",\"1\"]]]]]"
theorem fieldEncoding13 : [91] ++ encode (.text "piN") ++ [44] ++ encode (.function (entries [((.model "d1"),(.integer 1))])) ++ [93] = rawField13 := by decide +kernel

def rawField14 : Bytes := asciiBytes "[[\"str\",\"q\"],[\"fun\",[[[\"model\",\"t1\"],[\"fun\",[[[\"model\",\"shard1\"],[\"int\",\"1\"]],[[\"model\",\"shard2\"],[\"int\",\"-2\"]]]]]]]]"
theorem fieldEncoding14 : [91] ++ encode (.text "q") ++ [44] ++ encode (.function (entries [((.model "t1"),(.function (entries [((.model "shard1"),(.integer 1)),((.model "shard2"),(.integer (-2)))])))])) ++ [93] = rawField14 := by decide +kernel

def rawField15 : Bytes := asciiBytes "[[\"str\",\"qD\"],[\"fun\",[[[\"model\",\"d1\"],[\"fun\",[[[\"model\",\"shard1\"],[\"int\",\"2\"]],[[\"model\",\"shard2\"],[\"int\",\"2\"]]]]]]]]"
theorem fieldEncoding15 : [91] ++ encode (.text "qD") ++ [44] ++ encode (.function (entries [((.model "d1"),(.function (entries [((.model "shard1"),(.integer 2)),((.model "shard2"),(.integer 2))])))])) ++ [93] = rawField15 := by decide +kernel

def rawField16 : Bytes := asciiBytes "[[\"str\",\"qN\"],[\"fun\",[[[\"model\",\"d1\"],[\"fun\",[[[\"model\",\"shard1\"],[\"int\",\"1\"]],[[\"model\",\"shard2\"],[\"int\",\"1\"]]]]]]]]"
theorem fieldEncoding16 : [91] ++ encode (.text "qN") ++ [44] ++ encode (.function (entries [((.model "d1"),(.function (entries [((.model "shard1"),(.integer 1)),((.model "shard2"),(.integer 1))])))])) ++ [93] = rawField16 := by decide +kernel

def rawField17 : Bytes := asciiBytes "[[\"str\",\"ticketDomain\"],[\"fun\",[[[\"model\",\"t1\"],[\"model\",\"d1\"]]]]]"
theorem fieldEncoding17 : [91] ++ encode (.text "ticketDomain") ++ [44] ++ encode (.function (entries [((.model "t1"),(.model "d1"))])) ++ [93] = rawField17 := by decide +kernel

def rawField18 : Bytes := asciiBytes "[[\"str\",\"ticketOrder\"],[\"fun\",[[[\"int\",\"1\"],[\"model\",\"t1\"]]]]]"
theorem fieldEncoding18 : [91] ++ encode (.text "ticketOrder") ++ [44] ++ encode (.function (entries [((.integer 1),(.model "t1"))])) ++ [93] = rawField18 := by decide +kernel

def rawField19 : Bytes := asciiBytes "[[\"str\",\"wdD\"],[\"int\",\"1\"]]"
theorem fieldEncoding19 : [91] ++ encode (.text "wdD") ++ [44] ++ encode (.integer 1) ++ [93] = rawField19 := by decide +kernel

def rawField20 : Bytes := asciiBytes "[[\"str\",\"wdN\"],[\"int\",\"0\"]]"
theorem fieldEncoding20 : [91] ++ encode (.text "wdN") ++ [44] ++ encode (.integer 0) ++ [93] = rawField20 := by decide +kernel

def rawField21 : Bytes := asciiBytes "[[\"str\",\"weightD\"],[\"fun\",[[[\"model\",\"t1\"],[\"int\",\"1\"]]]]]"
theorem fieldEncoding21 : [91] ++ encode (.text "weightD") ++ [44] ++ encode (.function (entries [((.model "t1"),(.integer 1))])) ++ [93] = rawField21 := by decide +kernel

def rawField22 : Bytes := asciiBytes "[[\"str\",\"weightN\"],[\"fun\",[[[\"model\",\"t1\"],[\"int\",\"1\"]]]]]"
theorem fieldEncoding22 : [91] ++ encode (.text "weightN") ++ [44] ++ encode (.function (entries [((.model "t1"),(.integer 1))])) ++ [93] = rawField22 := by decide +kernel

def expectedBytes : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [rawField0,rawField1,rawField2,rawField3,rawField4,rawField5,rawField6,rawField7,rawField8,rawField9,rawField10,rawField11,rawField12,rawField13,rawField14,rawField15,rawField16,rawField17,rawField18,rawField19,rawField20,rawField21,rawField22] ++ [93,93]
theorem expectedEncoding : encode expectedValue = expectedBytes := by
  have parts := (congrPair List.cons fieldEncoding0 (congrPair List.cons fieldEncoding1 (congrPair List.cons fieldEncoding2 (congrPair List.cons fieldEncoding3 (congrPair List.cons fieldEncoding4 (congrPair List.cons fieldEncoding5 (congrPair List.cons fieldEncoding6 (congrPair List.cons fieldEncoding7 (congrPair List.cons fieldEncoding8 (congrPair List.cons fieldEncoding9 (congrPair List.cons fieldEncoding10 (congrPair List.cons fieldEncoding11 (congrPair List.cons fieldEncoding12 (congrPair List.cons fieldEncoding13 (congrPair List.cons fieldEncoding14 (congrPair List.cons fieldEncoding15 (congrPair List.cons fieldEncoding16 (congrPair List.cons fieldEncoding17 (congrPair List.cons fieldEncoding18 (congrPair List.cons fieldEncoding19 (congrPair List.cons fieldEncoding20 (congrPair List.cons fieldEncoding21 (congrPair List.cons fieldEncoding22 (Eq.refl ([] : List Bytes)))))))))))))))))))))))))
  exact congrArg (fun xs : List Bytes => asciiBytes "[\"fun\",[" ++ List.intercalate [44] xs ++ [93,93]) parts

theorem fullCanonicalInputBytes :
    (encodeImage vocabulary fixtureImage).map (fun e => e.preimage) =
      some expectedBytes := by
  rw [encodeImageFromComputed fixtureEncoded]
  simp only [Option.map_some,Encoded.preimage,encodedValue,expectedEncoding]

theorem missingTicketAliasRejected :
    (encodeImage {vocabulary with ticket := fun _ => none} fixtureImage).isNone = true := by decide +kernel

theorem extraConfiguredTicketRejected :
    (encodeImage {vocabulary with tickets := ["t1","t2"]} fixtureImage).isNone = true := by decide +kernel

theorem extraConfiguredDomainRejected :
    (encodeImage {vocabulary with domains := ["d1","d2"]} fixtureImage).isNone = true := by decide +kernel

theorem missingConfiguredShardRejected :
    (encodeImage {vocabulary with shards := ["shard1"]} fixtureImage).isNone = true := by decide +kernel

theorem duplicateShardAliasRejected :
    (encodeImage {vocabulary with shard := fun _ => some "shard1"} fixtureImage).isNone = true := by decide +kernel

theorem unknownModelNameRejected :
    canonical ["t1","d1","shard1"] table1 = false := by decide +kernel

theorem missingCoordinateDoesNotZipAway :
    vectorTable vocabulary.shard ["s1","s2"] [1] = none := by decide +kernel

theorem extraCoordinateDoesNotZipAway :
    vectorTable vocabulary.shard ["s1","s2"] [1,2,3] = none := by decide +kernel

theorem changedProfileChangesField :
    ({nativeProfile with learningRate := ⟨1,1⟩}).learningRate ≠ nativeProfile.learningRate := by decide +kernel

theorem changedQuantumChangesTable :
    quantumTable Rational.denominator vocabulary {fixtureImage with domains := [⟨"d1",1,[⟨1,1⟩,⟨1,2⟩]⟩]} ≠
      some table6 := by decide +kernel

theorem changedOptimizerChangesTable :
    currentTable vocabulary.shard [("s1",0),("s2",0)] ≠ some table10 := by decide +kernel

theorem completeFieldCount : PublicArithmeticInputs.fieldNames.length = 23 := by decide +kernel

theorem longSequenceUsesCanonicalKeyOrder :
    PublicState.canonical [] (sequence ((List.range 12).map (fun n => .integer (Int.ofNat n)))) = true := by decide +kernel

end DeltaReduce.PublicArithmeticInputsVectors
