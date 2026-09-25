import DeltaReduce.PublicScalarNumbers

namespace DeltaReduce.PublicScalarNumbersExamples
open NativeBinding PublicState PublicScalarNumbers
set_option Elab.async false
set_option maxRecDepth 20000
set_option maxHeartbeats 8000000

def symbols : String → Option Value
  | "s1" => some (.model "shard1")
  | "s2" => some (.model "shard2")
  | _ => none

def numericTable (a b : Int) : Value := .function
  (.cons (.model "shard1") (.integer a) (.cons (.model "shard2") (.integer b) .nil))

def vectorValue (kind : String) (a b : Int) : Value := .function
  (.cons (.text "kind") (.text kind) (.cons (.text "schema") (.model "schema1")
    (.cons (.text "values") (numericTable a b) .nil)))

def applyBody (model optimizer : Value) : Value := .function
  (.cons (.text "nextModelHash") model (.cons (.text "nextOptimizerHash") optimizer .nil))

theorem tableAcceptsCompleteValues :
    (checkTable symbols [("s1",19),("s2",-19)] (numericTable 19 (-19))).isSome = true := by decide

theorem changedCoordinateRejected :
    (checkTable symbols [("s1",19),("s2",-19)] (numericTable 19 19)).isNone = true := by decide

theorem missingAliasRejected :
    (checkTable (fun _ => none) [("s1",19)] (numericTable 19 (-19))).isNone = true := by decide

theorem duplicateAliasRejected :
    (checkTable (fun _ => some (.model "x")) [("s1",19),("s2",-19)]
      (.function (.cons (.model "x") (.integer 19) (.cons (.model "x") (.integer (-19)) .nil)))).isNone = true := by decide

theorem extraPublicCoordinateRejected :
    (checkTable symbols [("s1",19)] (numericTable 19 (-19))).isNone = true := by decide

theorem missingPublicCoordinateRejected :
    (checkTable symbols [("s1",19),("s2",-19)]
      (.function (.cons (.model "shard1") (.integer 19) .nil))).isNone = true := by decide

theorem duplicatePublicCoordinateRejected :
    (checkTable symbols [("s1",19),("s2",-19)]
      (.function (.cons (.model "shard1") (.integer 19) (.cons (.model "shard1") (.integer 19) .nil)))).isNone = true := by decide

theorem wrongNumericTagRejected :
    (checkTable symbols [("s1",19)] (.function (.cons (.model "shard1") (.text "19") .nil))).isNone = true := by decide

theorem wrongModelKindRejected :
    (checkVectorValue symbols "MODEL" (.model "schema1") [("s1",19),("s2",-19)]
      (vectorValue "OPTIMIZER" 19 (-19))).isNone = true := by decide

theorem wrongSchemaRejected :
    (checkVectorValue symbols "MODEL" (.model "other") [("s1",19),("s2",-19)]
      (vectorValue "MODEL" 19 (-19))).isNone = true := by decide

theorem nativeHashStringIsNotAbstractVector :
    (checkVectorValue symbols "MODEL" (.model "schema1") [("s1",19),("s2",-19)]
      (.text "sha256:example")).isNone = true := by decide

theorem correctModelRecordAccepted :
    (checkVectorValue symbols "MODEL" (.model "schema1") [("s1",19),("s2",-19)]
      (vectorValue "MODEL" 19 (-19))).isSome = true := by decide

theorem correctOptimizerRecordAccepted :
    (checkVectorValue symbols "OPTIMIZER" (.model "schema1") [("s1",2),("s2",-2)]
      (vectorValue "OPTIMIZER" 2 (-2))).isSome = true := by decide

theorem changedOptimizerRecordRejected :
    (checkVectorValue symbols "OPTIMIZER" (.model "schema1") [("s1",2),("s2",-2)]
      (vectorValue "OPTIMIZER" 0 0)).isNone = true := by decide

-- Deliberate scope countercheck: two individually valid numerical records fit
-- a body with no authority/parent fields. This is not ValidApplyBody.
theorem numericTablesDoNotCheckWholeBody :
    let body := applyBody (vectorValue "MODEL" 19 (-19)) (vectorValue "OPTIMIZER" 2 (-2))
    readField body "authority" = none ∧ readField body "parent" = none ∧
    (readField body "nextModelHash").map (fun v => (checkVectorValue symbols "MODEL" (.model "schema1")
      [("s1",19),("s2",-19)] v).isSome) = some true ∧
    (readField body "nextOptimizerHash").map (fun v => (checkVectorValue symbols "OPTIMIZER" (.model "schema1")
      [("s1",2),("s2",-2)] v).isSome) = some true := by decide

end DeltaReduce.PublicScalarNumbersExamples
