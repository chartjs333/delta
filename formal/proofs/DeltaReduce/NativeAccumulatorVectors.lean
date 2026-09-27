import DeltaReduce.NativeAccumulatorBinding
namespace DeltaReduce.NativeAccumulatorVectors
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ascii)
open NativeAccumulatorBinding
set_option maxRecDepth 10000
set_option maxHeartbeats 3000000
def configValue0 : Bytes := [54, 52]
theorem configValue0Valid : NativeQJson.ValueValid .natural configValue0 := by decide
def configField0 : Bytes := [34, 97, 99, 99, 117, 109, 117, 108, 97, 116, 111, 114, 95, 119, 105, 100, 116, 104, 95, 98, 105, 116, 115, 34, 58, 54, 52, 44]
theorem configField0Length : configField0.length = 28 := rfl
theorem configField0Encoded : NativeScaleBytes.memberBytes "accumulator_width_bits" .natural configValue0 44 = configField0 := rfl
def configValue1 : Bytes := [115, 104, 97, 50, 53, 54, 58, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49]
theorem configValue1Valid : NativeQJson.ValueValid .text configValue1 := by decide
def configField1 : Bytes := [34, 98, 97, 115, 101, 95, 114, 111, 117, 110, 100, 95, 99, 111, 110, 102, 105, 103, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 34, 44]
theorem configField1Length : configField1.length = 97 := rfl
theorem configField1Encoded : NativeScaleBytes.memberBytes "base_round_config_id" .text configValue1 44 = configField1 := rfl
def configValue2 : Bytes := [54, 53, 53, 51, 56]
theorem configValue2Valid : NativeQJson.ValueValid .text configValue2 := by decide
def configField2 : Bytes := [34, 99, 111, 101, 102, 102, 105, 99, 105, 101, 110, 116, 95, 97, 98, 115, 95, 109, 97, 120, 34, 58, 34, 54, 53, 53, 51, 56, 34, 44]
theorem configField2Length : configField2.length = 30 := rfl
theorem configField2Encoded : NativeScaleBytes.memberBytes "coefficient_abs_max" .text configValue2 44 = configField2 := rfl
def configValue3 : Bytes := [115, 104, 97, 50, 53, 54, 58, 99, 99, 57, 56, 102, 49, 53, 97, 99, 50, 48, 102, 99, 51, 101, 100, 50, 54, 53, 99, 98, 55, 54, 54, 56, 50, 99, 97, 49, 53, 97, 57, 51, 54, 101, 50, 52, 54, 54, 48, 97, 54, 53, 49, 101, 50, 98, 56, 102, 56, 49, 54, 51, 56, 97, 98, 98, 51, 50, 54, 53, 99, 98, 54]
theorem configValue3Valid : NativeQJson.ValueValid .text configValue3 := by decide
def configField3 : Bytes := [34, 102, 111, 114, 109, 97, 108, 95, 115, 101, 109, 97, 110, 116, 105, 99, 115, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 99, 99, 57, 56, 102, 49, 53, 97, 99, 50, 48, 102, 99, 51, 101, 100, 50, 54, 53, 99, 98, 55, 54, 54, 56, 50, 99, 97, 49, 53, 97, 57, 51, 54, 101, 50, 52, 54, 54, 48, 97, 54, 53, 49, 101, 50, 98, 56, 102, 56, 49, 54, 51, 56, 97, 98, 98, 51, 50, 54, 53, 99, 98, 54, 34, 44]
theorem configField3Length : configField3.length = 96 := rfl
theorem configField3Encoded : NativeScaleBytes.memberBytes "formal_semantics_id" .text configValue3 44 = configField3 := rfl
def configValue4 : Bytes := [52, 50, 57, 52, 57, 54, 55, 50, 57, 53]
theorem configValue4Valid : NativeQJson.ValueValid .text configValue4 := by decide
def configField4 : Bytes := [34, 109, 97, 120, 95, 101, 108, 105, 103, 105, 98, 108, 101, 95, 99, 111, 110, 116, 114, 105, 98, 117, 116, 105, 111, 110, 115, 34, 58, 34, 52, 50, 57, 52, 57, 54, 55, 50, 57, 53, 34, 44]
theorem configField4Length : configField4.length = 42 := rfl
theorem configField4Encoded : NativeScaleBytes.memberBytes "max_eligible_contributions" .text configValue4 44 = configField4 := rfl
def configValue5 : Bytes := [115, 104, 97, 50, 53, 54, 58, 102, 52, 51, 99, 48, 50, 53, 57, 55, 52, 57, 98, 49, 53, 97, 101, 48, 100, 48, 49, 53, 52, 97, 54, 101, 57, 48, 57, 52, 55, 55, 52, 99, 55, 101, 97, 54, 53, 101, 53, 53, 97, 100, 101, 102, 98, 97, 101, 97, 52, 48, 48, 97, 54, 50, 48, 49, 97, 99, 98, 54, 50, 51, 57]
theorem configValue5Valid : NativeQJson.ValueValid .text configValue5 := by decide
def configField5 : Bytes := [34, 112, 97, 114, 97, 109, 101, 116, 101, 114, 95, 115, 99, 104, 101, 109, 97, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 102, 52, 51, 99, 48, 50, 53, 57, 55, 52, 57, 98, 49, 53, 97, 101, 48, 100, 48, 49, 53, 52, 97, 54, 101, 57, 48, 57, 52, 55, 55, 52, 99, 55, 101, 97, 54, 53, 101, 53, 53, 97, 100, 101, 102, 98, 97, 101, 97, 52, 48, 48, 97, 54, 50, 48, 49, 97, 99, 98, 54, 50, 51, 57, 34, 44]
theorem configField5Length : configField5.length = 96 := rfl
theorem configField5Encoded : NativeScaleBytes.memberBytes "parameter_schema_id" .text configValue5 44 = configField5 := rfl
def configValue6 : Bytes := [115, 104, 97, 50, 53, 54, 58, 49, 55, 99, 56, 100, 50, 51, 55, 57, 48, 48, 52, 55, 57, 54, 54, 101, 52, 50, 102, 51, 50, 48, 52, 53, 48, 50, 54, 50, 51, 99, 55, 52, 97, 48, 102, 102, 48, 51, 56, 51, 51, 49, 57, 100, 50, 51, 101, 54, 55, 97, 98, 49, 53, 99, 102, 57, 50, 102, 101, 51, 101, 54, 49]
theorem configValue6Valid : NativeQJson.ValueValid .text configValue6 := by decide
def configField6 : Bytes := [34, 112, 114, 111, 102, 105, 108, 101, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 49, 55, 99, 56, 100, 50, 51, 55, 57, 48, 48, 52, 55, 57, 54, 54, 101, 52, 50, 102, 51, 50, 48, 52, 53, 48, 50, 54, 50, 51, 99, 55, 52, 97, 48, 102, 102, 48, 51, 56, 51, 51, 49, 57, 100, 50, 51, 101, 54, 55, 97, 98, 49, 53, 99, 102, 57, 50, 102, 101, 51, 101, 54, 49, 34, 44]
theorem configField6Length : configField6.length = 87 := rfl
theorem configField6Encoded : NativeScaleBytes.memberBytes "profile_id" .text configValue6 44 = configField6 := rfl
def configValue7 : Bytes := [51, 50, 55, 54, 55]
theorem configValue7Valid : NativeQJson.ValueValid .text configValue7 := by decide
def configField7 : Bytes := [34, 113, 95, 97, 98, 115, 95, 109, 97, 120, 34, 58, 34, 51, 50, 55, 54, 55, 34, 44]
theorem configField7Length : configField7.length = 20 := rfl
theorem configField7Encoded : NativeScaleBytes.memberBytes "q_abs_max" .text configValue7 44 = configField7 := rfl
def configValue8 : Bytes := [115, 104, 97, 50, 53, 54, 58, 52, 51, 52, 48, 57, 50, 102, 56, 50, 49, 56, 56, 51, 51, 55, 100, 48, 97, 50, 55, 51, 99, 100, 49, 51, 99, 57, 51, 101, 48, 54, 100, 101, 99, 53, 53, 97, 101, 56, 52, 50, 100, 102, 48, 52, 57, 56, 101, 52, 100, 53, 50, 99, 97, 97, 49, 100, 49, 56, 52, 52, 50, 48, 53]
theorem configValue8Valid : NativeQJson.ValueValid .text configValue8 := by decide
def configField8 : Bytes := [34, 115, 99, 97, 108, 101, 95, 116, 97, 98, 108, 101, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 52, 51, 52, 48, 57, 50, 102, 56, 50, 49, 56, 56, 51, 51, 55, 100, 48, 97, 50, 55, 51, 99, 100, 49, 51, 99, 57, 51, 101, 48, 54, 100, 101, 99, 53, 53, 97, 101, 56, 52, 50, 100, 102, 48, 52, 57, 56, 101, 52, 100, 53, 50, 99, 97, 97, 49, 100, 49, 56, 52, 52, 50, 48, 53, 34, 44]
theorem configField8Length : configField8.length = 91 := rfl
theorem configField8Encoded : NativeScaleBytes.memberBytes "scale_table_id" .text configValue8 44 = configField8 := rfl
def configValue9 : Bytes := [49, 46, 48, 46, 48]
theorem configValue9Valid : NativeQJson.ValueValid .text configValue9 := by decide
def configField9 : Bytes := [34, 115, 99, 104, 101, 109, 97, 95, 118, 101, 114, 115, 105, 111, 110, 34, 58, 34, 49, 46, 48, 46, 48, 34, 44]
theorem configField9Length : configField9.length = 25 := rfl
theorem configField9Encoded : NativeScaleBytes.memberBytes "schema_version" .text configValue9 44 = configField9 := rfl
def configValue10 : Bytes := [115, 104, 97, 50, 53, 54, 58, 52, 99, 54, 52, 52, 97, 51, 50, 53, 52, 101, 100, 98, 51, 100, 55, 98, 102, 102, 48, 48, 57, 98, 98, 101, 57, 49, 101, 101, 57, 57, 100, 102, 54, 48, 53, 49, 53, 49, 54, 51, 54, 50, 102, 97, 49, 97, 49, 101, 97, 99, 54, 102, 48, 97, 56, 48, 51, 97, 57, 99, 55, 97, 49]
theorem configValue10Valid : NativeQJson.ValueValid .text configValue10 := by decide
def configField10 : Bytes := [34, 115, 104, 97, 114, 100, 95, 112, 108, 97, 110, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 52, 99, 54, 52, 52, 97, 51, 50, 53, 52, 101, 100, 98, 51, 100, 55, 98, 102, 102, 48, 48, 57, 98, 98, 101, 57, 49, 101, 101, 57, 57, 100, 102, 54, 48, 53, 49, 53, 49, 54, 51, 54, 50, 102, 97, 49, 97, 49, 101, 97, 99, 54, 102, 48, 97, 56, 48, 51, 97, 57, 99, 55, 97, 49, 34, 44]
theorem configField10Length : configField10.length = 90 := rfl
theorem configField10Encoded : NativeScaleBytes.memberBytes "shard_plan_id" .text configValue10 44 = configField10 := rfl
def configValue11 : Bytes := [70, 73, 88, 69, 68, 80, 79, 73, 78, 84, 95, 82, 79, 85, 78, 68, 95, 67, 79, 78, 70, 73, 71]
theorem configValue11Valid : NativeQJson.ValueValid .text configValue11 := by decide
def configField11 : Bytes := [34, 116, 121, 112, 101, 95, 110, 97, 109, 101, 34, 58, 34, 70, 73, 88, 69, 68, 80, 79, 73, 78, 84, 95, 82, 79, 85, 78, 68, 95, 67, 79, 78, 70, 73, 71, 34, 125]
theorem configField11Length : configField11.length = 38 := rfl
theorem configField11Encoded : NativeScaleBytes.memberBytes "type_name" .text configValue11 125 = configField11 := rfl
def config : NativeAccumulatorBytes.Config := ⟨configValue0,configValue1,configValue2,configValue3,configValue4,configValue5,configValue6,configValue7,configValue8,configValue9,configValue10,configValue11⟩
theorem configSyntax : NativeAccumulatorBytes.ConfigSyntax config := ⟨configValue0Valid,configValue1Valid,configValue2Valid,configValue3Valid,configValue4Valid,configValue5Valid,configValue6Valid,configValue7Valid,configValue8Valid,configValue9Valid,configValue10Valid,configValue11Valid⟩
def configOriginal : Bytes := [123] ++ configField0 ++ configField1 ++ configField2 ++ configField3 ++ configField4 ++ configField5 ++ configField6 ++ configField7 ++ configField8 ++ configField9 ++ configField10 ++ configField11
theorem configLength : configOriginal.length = 741 := by
  simp only [configOriginal,List.length_append,List.length_cons,List.length_nil,configField0Length,configField1Length,configField2Length,configField3Length,configField4Length,configField5Length,configField6Length,configField7Length,configField8Length,configField9Length,configField10Length,configField11Length]
theorem configEncoded : NativeAccumulatorBytes.encodeConfig config = configOriginal := by
  simp only [NativeAccumulatorBytes.encodeConfig,config,configField0Encoded,configField1Encoded,configField2Encoded,configField3Encoded,configField4Encoded,configField5Encoded,configField6Encoded,configField7Encoded,configField8Encoded,configField9Encoded,configField10Encoded,configField11Encoded,configOriginal]
theorem configDecoded : NativeAccumulatorBytes.decodeConfig configOriginal = some config := by
  rw [← configEncoded]
  apply NativeAccumulatorBytes.decodeConfigEncoded _ configSyntax
  rw [configEncoded,configLength]; decide
def proofValue0 : Bytes := [54, 53, 53, 51, 56]
theorem proofValue0Valid : NativeQJson.ValueValid .text proofValue0 := by decide
def proofField0 : Bytes := [34, 99, 111, 101, 102, 102, 105, 99, 105, 101, 110, 116, 95, 97, 98, 115, 95, 109, 97, 120, 34, 58, 34, 54, 53, 53, 51, 56, 34, 44]
theorem proofField0Length : proofField0.length = 30 := rfl
theorem proofField0Encoded : NativeScaleBytes.memberBytes "coefficient_abs_max" .text proofValue0 44 = proofField0 := rfl
def proofValue1 : Bytes := [49]
theorem proofValue1Valid : NativeQJson.ValueValid .text proofValue1 := by decide
def proofField1 : Bytes := [34, 99, 111, 109, 109, 111, 110, 95, 100, 101, 110, 111, 109, 105, 110, 97, 116, 111, 114, 34, 58, 34, 49, 34, 44]
theorem proofField1Length : proofField1.length = 25 := rfl
theorem proofField1Encoded : NativeScaleBytes.memberBytes "common_denominator" .text proofValue1 44 = proofField1 := rfl
def proofValue2 : Bytes := [115, 104, 97, 50, 53, 54, 58, 51, 52, 98, 99, 48, 56, 99, 51, 49, 54, 100, 102, 101, 50, 50, 101, 102, 101, 49, 53, 53, 101, 100, 49, 49, 98, 56, 54, 54, 98, 99, 99, 48, 100, 97, 102, 55, 101, 102, 56, 99, 51, 99, 55, 51, 56, 57, 99, 53, 54, 98, 50, 102, 50, 99, 55, 48, 55, 52, 52, 51, 54, 50, 57]
theorem proofValue2Valid : NativeQJson.ValueValid .text proofValue2 := by decide
def proofField2 : Bytes := [34, 99, 111, 110, 102, 105, 103, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 51, 52, 98, 99, 48, 56, 99, 51, 49, 54, 100, 102, 101, 50, 50, 101, 102, 101, 49, 53, 53, 101, 100, 49, 49, 98, 56, 54, 54, 98, 99, 99, 48, 100, 97, 102, 55, 101, 102, 56, 99, 51, 99, 55, 51, 56, 57, 99, 53, 54, 98, 50, 102, 50, 99, 55, 48, 55, 52, 52, 51, 54, 50, 57, 34, 44]
theorem proofField2Length : proofField2.length = 86 := rfl
theorem proofField2Encoded : NativeScaleBytes.memberBytes "config_id" .text proofValue2 44 = proofField2 := rfl
def proofValue3 : Bytes := [57, 50, 50, 51, 51, 55, 50, 48, 50, 54, 49, 49, 55, 51, 53, 55, 53, 55, 48]
theorem proofValue3Valid : NativeQJson.ValueValid .text proofValue3 := by decide
def proofField3 : Bytes := [34, 102, 105, 110, 97, 108, 95, 97, 98, 115, 95, 98, 111, 117, 110, 100, 34, 58, 34, 57, 50, 50, 51, 51, 55, 50, 48, 50, 54, 49, 49, 55, 51, 53, 55, 53, 55, 48, 34, 44]
theorem proofField3Length : proofField3.length = 40 := rfl
theorem proofField3Encoded : NativeScaleBytes.memberBytes "final_abs_bound" .text proofValue3 44 = proofField3 := rfl
def proofValue4 : Bytes := [115, 104, 97, 50, 53, 54, 58, 99, 99, 57, 56, 102, 49, 53, 97, 99, 50, 48, 102, 99, 51, 101, 100, 50, 54, 53, 99, 98, 55, 54, 54, 56, 50, 99, 97, 49, 53, 97, 57, 51, 54, 101, 50, 52, 54, 54, 48, 97, 54, 53, 49, 101, 50, 98, 56, 102, 56, 49, 54, 51, 56, 97, 98, 98, 51, 50, 54, 53, 99, 98, 54]
theorem proofValue4Valid : NativeQJson.ValueValid .text proofValue4 := by decide
def proofField4 : Bytes := [34, 102, 111, 114, 109, 97, 108, 95, 115, 101, 109, 97, 110, 116, 105, 99, 115, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 99, 99, 57, 56, 102, 49, 53, 97, 99, 50, 48, 102, 99, 51, 101, 100, 50, 54, 53, 99, 98, 55, 54, 54, 56, 50, 99, 97, 49, 53, 97, 57, 51, 54, 101, 50, 52, 54, 54, 48, 97, 54, 53, 49, 101, 50, 98, 56, 102, 56, 49, 54, 51, 56, 97, 98, 98, 51, 50, 54, 53, 99, 98, 54, 34, 44]
theorem proofField4Length : proofField4.length = 96 := rfl
theorem proofField4Encoded : NativeScaleBytes.memberBytes "formal_semantics_id" .text proofValue4 44 = proofField4 := rfl
def proofValue5 : Bytes := [115, 104, 97, 50, 53, 54, 58, 54, 100, 56, 99, 55, 49, 53, 101, 97, 99, 102, 53, 53, 102, 57, 57, 97, 50, 98, 98, 99, 53, 102, 99, 97, 55, 50, 52, 50, 54, 49, 48, 100, 56, 55, 49, 97, 49, 101, 102, 55, 54, 97, 101, 53, 56, 100, 53, 49, 51, 48, 53, 98, 56, 49, 101, 54, 54, 51, 54, 52, 55, 51, 54]
theorem proofValue5Valid : NativeQJson.ValueValid .text proofValue5 := by decide
def proofField5 : Bytes := [34, 108, 101, 97, 110, 95, 97, 114, 116, 105, 102, 97, 99, 116, 95, 115, 104, 97, 50, 53, 54, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 54, 100, 56, 99, 55, 49, 53, 101, 97, 99, 102, 53, 53, 102, 57, 57, 97, 50, 98, 98, 99, 53, 102, 99, 97, 55, 50, 52, 50, 54, 49, 48, 100, 56, 55, 49, 97, 49, 101, 102, 55, 54, 97, 101, 53, 56, 100, 53, 49, 51, 48, 53, 98, 56, 49, 101, 54, 54, 51, 54, 52, 55, 51, 54, 34, 44]
theorem proofField5Length : proofField5.length = 97 := rfl
theorem proofField5Encoded : NativeScaleBytes.memberBytes "lean_artifact_sha256" .text proofValue5 44 = proofField5 := rfl
def proofValue6 : Bytes := [52, 50, 57, 52, 57, 54, 55, 50, 57, 53]
theorem proofValue6Valid : NativeQJson.ValueValid .text proofValue6 := by decide
def proofField6 : Bytes := [34, 109, 97, 120, 95, 101, 108, 105, 103, 105, 98, 108, 101, 95, 99, 111, 110, 116, 114, 105, 98, 117, 116, 105, 111, 110, 115, 34, 58, 34, 52, 50, 57, 52, 57, 54, 55, 50, 57, 53, 34, 44]
theorem proofField6Length : proofField6.length = 42 := rfl
theorem proofField6Encoded : NativeScaleBytes.memberBytes "max_eligible_contributions" .text proofValue6 44 = proofField6 := rfl
def proofValue7 : Bytes := [57, 50, 50, 51, 51, 55, 50, 48, 50, 54, 49, 49, 55, 51, 53, 55, 53, 55, 48]
theorem proofValue7Valid : NativeQJson.ValueValid .text proofValue7 := by decide
def proofField7 : Bytes := [34, 109, 97, 120, 95, 105, 110, 99, 114, 101, 109, 101, 110, 116, 97, 108, 95, 112, 114, 101, 102, 105, 120, 95, 97, 98, 115, 34, 58, 34, 57, 50, 50, 51, 51, 55, 50, 48, 50, 54, 49, 49, 55, 51, 53, 55, 53, 55, 48, 34, 44]
theorem proofField7Length : proofField7.length = 51 := rfl
theorem proofField7Encoded : NativeScaleBytes.memberBytes "max_incremental_prefix_abs" .text proofValue7 44 = proofField7 := rfl
def proofValue8 : Bytes := [50, 49, 52, 55, 52, 56, 51, 54, 52, 54]
theorem proofValue8Valid : NativeQJson.ValueValid .text proofValue8 := by decide
def proofField8 : Bytes := [34, 112, 114, 111, 100, 117, 99, 116, 95, 97, 98, 115, 95, 98, 111, 117, 110, 100, 34, 58, 34, 50, 49, 52, 55, 52, 56, 51, 54, 52, 54, 34, 44]
theorem proofField8Length : proofField8.length = 33 := rfl
theorem proofField8Encoded : NativeScaleBytes.memberBytes "product_abs_bound" .text proofValue8 44 = proofField8 := rfl
def proofValue9 : Bytes := [54, 52]
theorem proofValue9Valid : NativeQJson.ValueValid .natural proofValue9 := by decide
def proofField9 : Bytes := [34, 112, 114, 111, 100, 117, 99, 116, 95, 119, 105, 100, 116, 104, 95, 98, 105, 116, 115, 34, 58, 54, 52, 44]
theorem proofField9Length : proofField9.length = 24 := rfl
theorem proofField9Encoded : NativeScaleBytes.memberBytes "product_width_bits" .natural proofValue9 44 = proofField9 := rfl
def proofValue10 : Bytes := [115, 104, 97, 50, 53, 54, 58, 49, 55, 99, 56, 100, 50, 51, 55, 57, 48, 48, 52, 55, 57, 54, 54, 101, 52, 50, 102, 51, 50, 48, 52, 53, 48, 50, 54, 50, 51, 99, 55, 52, 97, 48, 102, 102, 48, 51, 56, 51, 51, 49, 57, 100, 50, 51, 101, 54, 55, 97, 98, 49, 53, 99, 102, 57, 50, 102, 101, 51, 101, 54, 49]
theorem proofValue10Valid : NativeQJson.ValueValid .text proofValue10 := by decide
def proofField10 : Bytes := [34, 112, 114, 111, 102, 105, 108, 101, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 49, 55, 99, 56, 100, 50, 51, 55, 57, 48, 48, 52, 55, 57, 54, 54, 101, 52, 50, 102, 51, 50, 48, 52, 53, 48, 50, 54, 50, 51, 99, 55, 52, 97, 48, 102, 102, 48, 51, 56, 51, 51, 49, 57, 100, 50, 51, 101, 54, 55, 97, 98, 49, 53, 99, 102, 57, 50, 102, 101, 51, 101, 54, 49, 34, 44]
theorem proofField10Length : proofField10.length = 87 := rfl
theorem proofField10Encoded : NativeScaleBytes.memberBytes "profile_id" .text proofValue10 44 = proofField10 := rfl
def proofValue11 : Bytes := [51, 50, 55, 54, 55]
theorem proofValue11Valid : NativeQJson.ValueValid .text proofValue11 := by decide
def proofField11 : Bytes := [34, 113, 95, 97, 98, 115, 95, 109, 97, 120, 34, 58, 34, 51, 50, 55, 54, 55, 34, 44]
theorem proofField11Length : proofField11.length = 20 := rfl
theorem proofField11Encoded : NativeScaleBytes.memberBytes "q_abs_max" .text proofValue11 44 = proofField11 := rfl
def proofValue12 : Bytes := [80, 65, 83, 83]
theorem proofValue12Valid : NativeQJson.ValueValid .text proofValue12 := by decide
def proofField12 : Bytes := [34, 114, 101, 115, 117, 108, 116, 34, 58, 34, 80, 65, 83, 83, 34, 44]
theorem proofField12Length : proofField12.length = 16 := rfl
theorem proofField12Encoded : NativeScaleBytes.memberBytes "result" .text proofValue12 44 = proofField12 := rfl
def proofValue13 : Bytes := [115, 104, 97, 50, 53, 54, 58, 52, 51, 52, 48, 57, 50, 102, 56, 50, 49, 56, 56, 51, 51, 55, 100, 48, 97, 50, 55, 51, 99, 100, 49, 51, 99, 57, 51, 101, 48, 54, 100, 101, 99, 53, 53, 97, 101, 56, 52, 50, 100, 102, 48, 52, 57, 56, 101, 52, 100, 53, 50, 99, 97, 97, 49, 100, 49, 56, 52, 52, 50, 48, 53]
theorem proofValue13Valid : NativeQJson.ValueValid .text proofValue13 := by decide
def proofField13 : Bytes := [34, 115, 99, 97, 108, 101, 95, 116, 97, 98, 108, 101, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 52, 51, 52, 48, 57, 50, 102, 56, 50, 49, 56, 56, 51, 51, 55, 100, 48, 97, 50, 55, 51, 99, 100, 49, 51, 99, 57, 51, 101, 48, 54, 100, 101, 99, 53, 53, 97, 101, 56, 52, 50, 100, 102, 48, 52, 57, 56, 101, 52, 100, 53, 50, 99, 97, 97, 49, 100, 49, 56, 52, 52, 50, 48, 53, 34, 44]
theorem proofField13Length : proofField13.length = 91 := rfl
theorem proofField13Encoded : NativeScaleBytes.memberBytes "scale_table_id" .text proofValue13 44 = proofField13 := rfl
def proofValue14 : Bytes := [49, 46, 48, 46, 48]
theorem proofValue14Valid : NativeQJson.ValueValid .text proofValue14 := by decide
def proofField14 : Bytes := [34, 115, 99, 104, 101, 109, 97, 95, 118, 101, 114, 115, 105, 111, 110, 34, 58, 34, 49, 46, 48, 46, 48, 34, 44]
theorem proofField14Length : proofField14.length = 25 := rfl
theorem proofField14Encoded : NativeScaleBytes.memberBytes "schema_version" .text proofValue14 44 = proofField14 := rfl
def proofValue15 : Bytes := [54, 52]
theorem proofValue15Valid : NativeQJson.ValueValid .natural proofValue15 := by decide
def proofField15 : Bytes := [34, 115, 101, 108, 101, 99, 116, 101, 100, 95, 97, 99, 99, 117, 109, 117, 108, 97, 116, 111, 114, 95, 119, 105, 100, 116, 104, 95, 98, 105, 116, 115, 34, 58, 54, 52, 44]
theorem proofField15Length : proofField15.length = 37 := rfl
theorem proofField15Encoded : NativeScaleBytes.memberBytes "selected_accumulator_width_bits" .natural proofValue15 44 = proofField15 := rfl
def proofValue16 : Bytes := [65, 67, 67, 85, 77, 85, 76, 65, 84, 79, 82, 95, 80, 82, 79, 79, 70, 95, 73, 78, 83, 84, 65, 78, 67, 69]
theorem proofValue16Valid : NativeQJson.ValueValid .text proofValue16 := by decide
theorem theoremLength : NativeAccumulatorBytes.theoremBytes.length = 674 := rfl
def proofField16 : Bytes := [34, 116, 121, 112, 101, 95, 110, 97, 109, 101, 34, 58, 34, 65, 67, 67, 85, 77, 85, 76, 65, 84, 79, 82, 95, 80, 82, 79, 79, 70, 95, 73, 78, 83, 84, 65, 78, 67, 69, 34, 125]
theorem proofField16Length : proofField16.length = 41 := rfl
theorem proofField16Encoded : NativeScaleBytes.memberBytes "type_name" .text proofValue16 125 = proofField16 := rfl
def proof : NativeAccumulatorBytes.Proof := ⟨proofValue0,proofValue1,proofValue2,proofValue3,proofValue4,proofValue5,proofValue6,proofValue7,proofValue8,proofValue9,proofValue10,proofValue11,proofValue12,proofValue13,proofValue14,proofValue15,proofValue16⟩
theorem proofSyntax : NativeAccumulatorBytes.ProofSyntax proof := ⟨proofValue0Valid,proofValue1Valid,proofValue2Valid,proofValue3Valid,proofValue4Valid,proofValue5Valid,proofValue6Valid,proofValue7Valid,proofValue8Valid,proofValue9Valid,proofValue10Valid,proofValue11Valid,proofValue12Valid,proofValue13Valid,proofValue14Valid,proofValue15Valid,proofValue16Valid⟩
def proofOriginal : Bytes := [123] ++ proofField0 ++ proofField1 ++ proofField2 ++ proofField3 ++ proofField4 ++ proofField5 ++ proofField6 ++ proofField7 ++ proofField8 ++ proofField9 ++ proofField10 ++ proofField11 ++ proofField12 ++ proofField13 ++ proofField14 ++ proofField15 ++ NativeAccumulatorBytes.theoremBytes ++ proofField16
theorem proofLength : proofOriginal.length = 1516 := by
  simp only [proofOriginal,List.length_append,List.length_cons,List.length_nil,proofField0Length,proofField1Length,proofField2Length,proofField3Length,proofField4Length,proofField5Length,proofField6Length,proofField7Length,proofField8Length,proofField9Length,proofField10Length,proofField11Length,proofField12Length,proofField13Length,proofField14Length,proofField15Length,theoremLength,proofField16Length]
theorem proofEncoded : NativeAccumulatorBytes.encodeProof proof = proofOriginal := by
  simp only [NativeAccumulatorBytes.encodeProof,proof,proofField0Encoded,proofField1Encoded,proofField2Encoded,proofField3Encoded,proofField4Encoded,proofField5Encoded,proofField6Encoded,proofField7Encoded,proofField8Encoded,proofField9Encoded,proofField10Encoded,proofField11Encoded,proofField12Encoded,proofField13Encoded,proofField14Encoded,proofField15Encoded,proofField16Encoded,proofOriginal]
theorem proofDecoded : NativeAccumulatorBytes.decodeProof proofOriginal = some proof := by
  rw [← proofEncoded]
  apply NativeAccumulatorBytes.decodeProofEncoded _ proofSyntax
  rw [proofEncoded,proofLength]; decide
theorem profileLength : workerProfileBytes.length = 752 := rfl
def numbers : Numbers := ⟨65538,4294967295,1,2147483646,9223372026117357570,9223372026117357570,64,64⟩
theorem numericValid : NumericValid numbers := by decide
theorem numericDecoded : readNumbers proof = some numbers := by
  apply numbersFromSource
  exact ⟨by decide,by decide,by decide,by decide,by decide,by decide,by decide,by decide,numericValid⟩
theorem metadata : Metadata config proof := by decide
def bound : Bound := ⟨config,proof,numbers⟩
def input0 : Bytes := configInput configOriginal
def id0 : Bytes := [115, 104, 97, 50, 53, 54, 58, 51, 52, 98, 99, 48, 56, 99, 51, 49, 54, 100, 102, 101, 50, 50, 101, 102, 101, 49, 53, 53, 101, 100, 49, 49, 98, 56, 54, 54, 98, 99, 99, 48, 100, 97, 102, 55, 101, 102, 56, 99, 51, 99, 55, 51, 56, 57, 99, 53, 54, 98, 50, 102, 50, 99, 55, 48, 55, 52, 52, 51, 54, 50, 57]
theorem inputLength0 : input0.length = 778 := by
  simp only [input0,configInput,List.length_append,List.length_cons,List.length_nil,configLength]
  rfl
def input1 : Bytes := proofInput proofOriginal
def id1 : Bytes := [115, 104, 97, 50, 53, 54, 58, 57, 57, 51, 98, 52, 100, 53, 49, 48, 52, 56, 49, 48, 100, 100, 50, 54, 97, 51, 49, 53, 57, 98, 54, 48, 99, 102, 56, 102, 101, 57, 97, 102, 101, 54, 49, 53, 52, 99, 100, 99, 99, 97, 57, 48, 100, 50, 50, 98, 53, 55, 55, 97, 101, 49, 98, 54, 100, 49, 97, 99, 48, 55, 54]
theorem inputLength1 : input1.length = 1550 := by
  simp only [input1,proofInput,List.length_append,List.length_cons,List.length_nil,proofLength]
  rfl
def input2 : Bytes := profileInput workerProfileBytes
def id2 : Bytes := [115, 104, 97, 50, 53, 54, 58, 49, 55, 99, 56, 100, 50, 51, 55, 57, 48, 48, 52, 55, 57, 54, 54, 101, 52, 50, 102, 51, 50, 48, 52, 53, 48, 50, 54, 50, 51, 99, 55, 52, 97, 48, 102, 102, 48, 51, 56, 51, 51, 49, 57, 100, 50, 51, 101, 54, 55, 97, 98, 49, 53, 99, 102, 57, 50, 102, 101, 51, 101, 54, 49]
theorem inputLength2 : input2.length = 779 := by
  simp only [input2,profileInput,List.length_append,List.length_cons,List.length_nil,profileLength]
  rfl
@[irreducible]
def fixtureHash (raw : Bytes) : Bytes :=
  if raw.length = 778 then (if raw = input0 then id0 else []) else
  if raw.length = 1550 then (if raw = input1 then id1 else []) else
  if raw.length = 779 then (if raw = input2 then id2 else []) else
  []
theorem hash0 : fixtureHash input0 = id0 := by
  simp only [fixtureHash,inputLength0]
  simp
theorem hash1 : fixtureHash input1 = id1 := by
  simp only [fixtureHash,inputLength1]
  simp
theorem hash2 : fixtureHash input2 = id2 := by
  simp only [fixtureHash,inputLength2]
  simp
theorem loaded : load fixtureHash configOriginal proofOriginal workerProfileBytes id1 = some bound := by
  apply loadFromSource
  refine ⟨configDecoded,proofDecoded,numericDecoded,metadata,rfl,?_,?_,by decide,hash1⟩
  · exact hash2
  · exact hash0
theorem exactInferredHeadroom : headroom numbers = 0 := by decide
theorem actualComputedBounds : numbers.product = 2147483646 ∧ numbers.prefixBound = 9223372026117357570 := ⟨rfl,rfl⟩
theorem signed128Endpoint : number i128 (ascii "170141183460469231731687303715884105727") = some i128 := by decide
theorem signed128Overflow : number i128 (ascii "170141183460469231731687303715884105728") = none := by decide
theorem unsigned64Endpoint : number u64 (ascii "18446744073709551615") = some u64 := by decide
theorem unsigned64Overflow : number u64 (ascii "18446744073709551616") = none := by decide
theorem leadingZero : number i128 (ascii "01") = none := by decide
theorem negativeZero : number i128 (ascii "-0") = none := by decide
theorem negativeAlternate : number i128 (ascii "-01") = none := by decide
theorem plusSign : number i128 (ascii "+1") = none := by decide
theorem emptyNumber : number i128 [] = none := by decide
theorem badWidth : ¬ NumericValid { numbers with accumulatorBits := 65 } := by decide
theorem wrongProduct : ¬ NumericValid { numbers with product := numbers.product+1 } := by decide
theorem wrongPrefix : ¬ NumericValid { numbers with prefixBound := numbers.prefixBound+1 } := by decide
theorem zeroCoefficient : ¬ NumericValid { numbers with coefficient := 0 } := by decide
theorem zeroCount : ¬ NumericValid { numbers with count := 0 } := by decide
theorem zeroDenominator : ¬ NumericValid { numbers with denominator := 0 } := by decide
theorem exactDenominatorNotLCM : NumericValid { numbers with denominator := 7 } := by decide
theorem finalBelowPrefix : ¬ NumericValid { numbers with finalBound := numbers.prefixBound-1 } := by decide
theorem nonzeroHeadroom : NumericValid { numbers with finalBound := numbers.finalBound+1 } := by decide
theorem inclusive64Final : NumericValid { numbers with finalBound := i64 } := by decide
theorem separateAccumulatorWidth : ¬ NumericValid { numbers with finalBound := i64+1, productBits := 128 } := by decide
theorem wideProductNarrowAccumulator : ¬ NumericValid ⟨i64,1,1,32767*i64,32767*i64,32767*i64,128,64⟩ := by decide
theorem narrowProductWideAccumulator : ¬ NumericValid ⟨i64,1,1,32767*i64,32767*i64,32767*i64,64,128⟩ := by decide
theorem wideBoth : NumericValid ⟨i64,1,1,32767*i64,32767*i64,32767*i64,128,128⟩ := by decide
theorem missingAuthorityReference : ¬ Metadata { config with base := [] } proof := by decide
theorem wrongConfigCount : ¬ Metadata { config with count := ascii "1" } proof := by decide
theorem wrongHistoricalLean : ¬ Metadata config { proof with lean := [] } := by decide
theorem passStringInsufficient : readNumbers { proof with product := ascii "0" } = none := by decide
theorem unknownMetadata : NativeAccumulatorBytes.decodeConfig (ascii "{}") = none := by decide
theorem missingTheorems : NativeReceiptBytes.consume NativeAccumulatorBytes.theoremBytes (ascii "\"theorems\":[],") = none := by decide
end DeltaReduce.NativeAccumulatorVectors
