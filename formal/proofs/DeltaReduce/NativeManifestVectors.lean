import DeltaReduce.NativeManifestBinding
import DeltaReduce.NativeShardPlanVectors
namespace DeltaReduce.NativeManifestVectors
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ascii)
open NativeManifestBinding
set_option maxRecDepth 10000
set_option maxHeartbeats 3000000
def bytes0 : Bytes := [52]
theorem valid0 : NativeVoteBytes.DecimalValid bytes0 := by decide
def bytes1 : Bytes := [48]
theorem valid1 : NativeVoteBytes.DecimalValid bytes1 := by decide
def bytes2 : Bytes := [57, 52, 57]
theorem valid2 : NativeVoteBytes.DecimalValid bytes2 := by decide
def bytes3 : Bytes := [115, 104, 97, 50, 53, 54, 58, 100, 51, 49, 101, 100, 98, 55, 56, 99, 48, 102, 97, 98, 53, 55, 53, 48, 49, 53, 99, 53, 48, 56, 53, 98, 99, 54, 100, 57, 53, 52, 57, 98, 52, 54, 99, 53, 100, 56, 48, 97, 102, 97, 48, 100, 53, 49, 98, 53, 50, 57, 55, 102, 101, 99, 101, 100, 53, 97, 49, 54, 54, 55, 98]
theorem valid3 : NativeQJson.TextValid bytes3 := by decide
def bytes4 : Bytes := [56]
theorem valid4 : NativeVoteBytes.DecimalValid bytes4 := by decide
def bytes5 : Bytes := [100, 101, 99, 111, 100, 101, 114, 46, 98, 105, 97, 115]
theorem valid5 : NativeQJson.TextValid bytes5 := by decide
def refWire0 : NativeManifestBytes.RefWire := ⟨bytes0,bytes1,bytes2,bytes3,bytes1,bytes4,bytes5,bytes1⟩
theorem refSyntax0 : NativeManifestBytes.RefSyntax refWire0 := ⟨valid0,valid1,valid2,valid3,valid1,valid4,valid5,valid1⟩
def ref0 : Ref := ⟨refWire0,NativeShardPlanVectors.plan.entries[0],949⟩
theorem refRead0 : readRef refWire0 = some ref0 := by decide
def bytes6 : Bytes := [57, 54, 49]
theorem valid6 : NativeVoteBytes.DecimalValid bytes6 := by decide
def bytes7 : Bytes := [115, 104, 97, 50, 53, 54, 58, 50, 57, 49, 50, 97, 57, 52, 53, 57, 99, 51, 55, 51, 50, 57, 98, 99, 51, 99, 55, 53, 54, 49, 101, 57, 102, 101, 99, 101, 100, 55, 51, 54, 51, 49, 102, 102, 54, 102, 97, 51, 101, 100, 101, 51, 98, 97, 55, 50, 49, 52, 102, 98, 101, 102, 50, 52, 49, 50, 97, 98, 57, 52, 99]
theorem valid7 : NativeQJson.TextValid bytes7 := by decide
def bytes8 : Bytes := [49]
theorem valid8 : NativeVoteBytes.DecimalValid bytes8 := by decide
def bytes9 : Bytes := [49, 54]
theorem valid9 : NativeVoteBytes.DecimalValid bytes9 := by decide
def bytes10 : Bytes := [101, 109, 98, 101, 100, 100, 105, 110, 103, 46, 119, 101, 105, 103, 104, 116]
theorem valid10 : NativeQJson.TextValid bytes10 := by decide
def refWire1 : NativeManifestBytes.RefWire := ⟨bytes4,bytes0,bytes6,bytes7,bytes8,bytes9,bytes10,bytes1⟩
theorem refSyntax1 : NativeManifestBytes.RefSyntax refWire1 := ⟨valid4,valid0,valid6,valid7,valid8,valid9,valid10,valid1⟩
def ref1 : Ref := ⟨refWire1,NativeShardPlanVectors.plan.entries[1],961⟩
theorem refRead1 : readRef refWire1 = some ref1 := by decide
def bytes11 : Bytes := [49, 50]
theorem valid11 : NativeVoteBytes.DecimalValid bytes11 := by decide
def bytes12 : Bytes := [57, 54, 50]
theorem valid12 : NativeVoteBytes.DecimalValid bytes12 := by decide
def bytes13 : Bytes := [115, 104, 97, 50, 53, 54, 58, 51, 55, 54, 57, 98, 53, 100, 54, 98, 101, 97, 48, 50, 54, 99, 100, 50, 100, 53, 54, 52, 57, 55, 100, 102, 57, 98, 55, 101, 49, 56, 102, 100, 98, 56, 99, 99, 97, 99, 52, 102, 100, 55, 53, 102, 100, 98, 51, 50, 101, 50, 50, 100, 99, 52, 52, 99, 98, 97, 100, 98, 48, 51, 98]
theorem valid13 : NativeQJson.TextValid bytes13 := by decide
def bytes14 : Bytes := [50]
theorem valid14 : NativeVoteBytes.DecimalValid bytes14 := by decide
def refWire2 : NativeManifestBytes.RefWire := ⟨bytes4,bytes11,bytes12,bytes13,bytes14,bytes9,bytes10,bytes4⟩
theorem refSyntax2 : NativeManifestBytes.RefSyntax refWire2 := ⟨valid4,valid11,valid12,valid13,valid14,valid9,valid10,valid4⟩
def ref2 : Ref := ⟨refWire2,NativeShardPlanVectors.plan.entries[2],962⟩
theorem refRead2 : readRef refWire2 = some ref2 := by decide
def bytes15 : Bytes := [50, 48]
theorem valid15 : NativeVoteBytes.DecimalValid bytes15 := by decide
def bytes16 : Bytes := [57, 54, 51]
theorem valid16 : NativeVoteBytes.DecimalValid bytes16 := by decide
def bytes17 : Bytes := [115, 104, 97, 50, 53, 54, 58, 98, 56, 51, 51, 54, 56, 50, 99, 53, 57, 52, 56, 102, 48, 51, 52, 50, 97, 98, 99, 101, 49, 53, 100, 97, 50, 52, 97, 100, 57, 51, 49, 98, 54, 55, 49, 49, 50, 102, 57, 97, 51, 55, 99, 99, 48, 51, 51, 101, 49, 98, 55, 56, 99, 51, 100, 101, 53, 50, 48, 99, 50, 102, 101]
theorem valid17 : NativeQJson.TextValid bytes17 := by decide
def bytes18 : Bytes := [51]
theorem valid18 : NativeVoteBytes.DecimalValid bytes18 := by decide
def refWire3 : NativeManifestBytes.RefWire := ⟨bytes4,bytes15,bytes16,bytes17,bytes18,bytes9,bytes10,bytes9⟩
theorem refSyntax3 : NativeManifestBytes.RefSyntax refWire3 := ⟨valid4,valid15,valid16,valid17,valid18,valid9,valid10,valid9⟩
def ref3 : Ref := ⟨refWire3,NativeShardPlanVectors.plan.entries[3],963⟩
theorem refRead3 : readRef refWire3 = some ref3 := by decide
def bytes19 : Bytes := [50, 56]
theorem valid19 : NativeVoteBytes.DecimalValid bytes19 := by decide
def bytes20 : Bytes := [115, 104, 97, 50, 53, 54, 58, 57, 56, 50, 97, 54, 56, 51, 49, 49, 48, 100, 56, 52, 55, 102, 54, 57, 101, 54, 101, 49, 56, 53, 50, 51, 99, 48, 51, 54, 97, 54, 54, 52, 53, 102, 98, 52, 100, 97, 51, 53, 49, 49, 98, 56, 101, 53, 56, 54, 97, 52, 48, 102, 48, 100, 102, 55, 53, 48, 97, 56, 100, 101, 100]
theorem valid20 : NativeQJson.TextValid bytes20 := by decide
def bytes21 : Bytes := [50, 52]
theorem valid21 : NativeVoteBytes.DecimalValid bytes21 := by decide
def refWire4 : NativeManifestBytes.RefWire := ⟨bytes4,bytes19,bytes16,bytes20,bytes0,bytes9,bytes10,bytes21⟩
theorem refSyntax4 : NativeManifestBytes.RefSyntax refWire4 := ⟨valid4,valid19,valid16,valid20,valid0,valid9,valid10,valid21⟩
def ref4 : Ref := ⟨refWire4,NativeShardPlanVectors.plan.entries[4],963⟩
theorem refRead4 : readRef refWire4 = some ref4 := by decide
def bytes22 : Bytes := [115, 104, 97, 50, 53, 54, 58, 101, 56, 48, 57, 49, 54, 97, 56, 101, 99, 55, 100, 54, 51, 52, 98, 52, 99, 51, 53, 50, 52, 100, 56, 55, 51, 99, 49, 51, 49, 52, 52, 98, 55, 55, 54, 48, 99, 55, 53, 53, 50, 101, 54, 55, 56, 56, 49, 51, 50, 97, 55, 53, 102, 99, 101, 53, 52, 53, 54, 50, 57, 54, 100]
theorem valid22 : NativeQJson.TextValid bytes22 := by decide
def bytes23 : Bytes := [100, 111, 109, 97, 105, 110, 45, 116, 101, 120, 116, 45, 101, 110]
theorem valid23 : NativeQJson.TextValid bytes23 := by decide
def bytes24 : Bytes := [115, 104, 97, 50, 53, 54, 58, 99, 99, 57, 56, 102, 49, 53, 97, 99, 50, 48, 102, 99, 51, 101, 100, 50, 54, 53, 99, 98, 55, 54, 54, 56, 50, 99, 97, 49, 53, 97, 57, 51, 54, 101, 50, 52, 54, 54, 48, 97, 54, 53, 49, 101, 50, 98, 56, 102, 56, 49, 54, 51, 56, 97, 98, 98, 51, 50, 54, 53, 99, 98, 54]
theorem valid24 : NativeQJson.TextValid bytes24 := by decide
def bytes25 : Bytes := [115, 104, 97, 50, 53, 54, 58, 102, 52, 51, 99, 48, 50, 53, 57, 55, 52, 57, 98, 49, 53, 97, 101, 48, 100, 48, 49, 53, 52, 97, 54, 101, 57, 48, 57, 52, 55, 55, 52, 99, 55, 101, 97, 54, 53, 101, 53, 53, 97, 100, 101, 102, 98, 97, 101, 97, 52, 48, 48, 97, 54, 50, 48, 49, 97, 99, 98, 54, 50, 51, 57]
theorem valid25 : NativeQJson.TextValid bytes25 := by decide
def bytes26 : Bytes := [115, 104, 97, 50, 53, 54, 58, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98]
theorem valid26 : NativeQJson.TextValid bytes26 := by decide
def bytes27 : Bytes := [115, 104, 97, 50, 53, 54, 58, 49, 55, 99, 56, 100, 50, 51, 55, 57, 48, 48, 52, 55, 57, 54, 54, 101, 52, 50, 102, 51, 50, 48, 52, 53, 48, 50, 54, 50, 51, 99, 55, 52, 97, 48, 102, 102, 48, 51, 56, 51, 51, 49, 57, 100, 50, 51, 101, 54, 55, 97, 98, 49, 53, 99, 102, 57, 50, 102, 101, 51, 101, 54, 49]
theorem valid27 : NativeQJson.TextValid bytes27 := by decide
def bytes28 : Bytes := [115, 104, 97, 50, 53, 54, 58, 57, 57, 51, 98, 52, 100, 53, 49, 48, 52, 56, 49, 48, 100, 100, 50, 54, 97, 51, 49, 53, 57, 98, 54, 48, 99, 102, 56, 102, 101, 57, 97, 102, 101, 54, 49, 53, 52, 99, 100, 99, 99, 97, 57, 48, 100, 50, 50, 98, 53, 55, 55, 97, 101, 49, 98, 54, 100, 49, 97, 99, 48, 55, 54]
theorem valid28 : NativeQJson.TextValid bytes28 := by decide
def bytes29 : Bytes := [115, 104, 97, 50, 53, 54, 58, 51, 52, 98, 99, 48, 56, 99, 51, 49, 54, 100, 102, 101, 50, 50, 101, 102, 101, 49, 53, 53, 101, 100, 49, 49, 98, 56, 54, 54, 98, 99, 99, 48, 100, 97, 102, 55, 101, 102, 56, 99, 51, 99, 55, 51, 56, 57, 99, 53, 54, 98, 50, 102, 50, 99, 55, 48, 55, 52, 52, 51, 54, 50, 57]
theorem valid29 : NativeQJson.TextValid bytes29 := by decide
def bytes30 : Bytes := [115, 104, 97, 50, 53, 54, 58, 52, 51, 52, 48, 57, 50, 102, 56, 50, 49, 56, 56, 51, 51, 55, 100, 48, 97, 50, 55, 51, 99, 100, 49, 51, 99, 57, 51, 101, 48, 54, 100, 101, 99, 53, 53, 97, 101, 56, 52, 50, 100, 102, 48, 52, 57, 56, 101, 52, 100, 53, 50, 99, 97, 97, 49, 100, 49, 56, 52, 52, 50, 48, 53]
theorem valid30 : NativeQJson.TextValid bytes30 := by decide
def bytes31 : Bytes := [49, 46, 48, 46, 48]
theorem valid31 : NativeQJson.TextValid bytes31 := by decide
def bytes32 : Bytes := [115, 104, 97, 50, 53, 54, 58, 52, 99, 54, 52, 52, 97, 51, 50, 53, 52, 101, 100, 98, 51, 100, 55, 98, 102, 102, 48, 48, 57, 98, 98, 101, 57, 49, 101, 101, 57, 57, 100, 102, 54, 48, 53, 49, 53, 49, 54, 51, 54, 50, 102, 97, 49, 97, 49, 101, 97, 99, 54, 102, 48, 97, 56, 48, 51, 97, 57, 99, 55, 97, 49]
theorem valid32 : NativeQJson.TextValid bytes32 := by decide
def bytes33 : Bytes := [116, 105, 99, 107, 101, 116, 45, 48, 48, 50, 45, 102, 105, 120, 116, 117, 114, 101]
theorem valid33 : NativeQJson.TextValid bytes33 := by decide
def bytes34 : Bytes := [51, 54]
theorem valid34 : NativeVoteBytes.DecimalValid bytes34 := by decide
def bytes35 : Bytes := [52, 55, 57, 56]
theorem valid35 : NativeVoteBytes.DecimalValid bytes35 := by decide
def bytes36 : Bytes := [55, 50]
theorem valid36 : NativeVoteBytes.DecimalValid bytes36 := by decide
def bytes37 : Bytes := [69, 78, 67, 79, 68, 69, 68, 95, 67, 79, 78, 84, 82, 73, 66, 85, 84, 73, 79, 78, 95, 77, 65, 78, 73, 70, 69, 83, 84]
theorem valid37 : NativeQJson.TextValid bytes37 := by decide
def wire : NativeManifestBytes.Wire := ⟨bytes14,bytes22,bytes23,bytes24,bytes25,bytes26,bytes27,bytes28,bytes29,bytes30,bytes31,bytes32,[refWire0,refWire1,refWire2,refWire3,refWire4],bytes33,bytes34,bytes35,bytes36,bytes37⟩
theorem wireSyntax : NativeManifestBytes.Syntax wire := by
  refine ⟨valid14,valid22,valid23,valid24,valid25,valid26,valid27,valid28,valid29,valid30,valid31,valid32,by decide,?_,valid33,valid34,valid35,valid36,valid37⟩
  change ∀ e ∈ [refWire0,refWire1,refWire2,refWire3,refWire4], NativeManifestBytes.RefSyntax e
  simp only [List.forall_mem_cons]
  exact ⟨refSyntax0,refSyntax1,refSyntax2,refSyntax3,refSyntax4,by simp⟩
def originalRef0 : Bytes := [123, 34, 101, 108, 101, 109, 101, 110, 116, 95, 99, 111, 117, 110, 116, 34, 58, 52, 44, 34, 101, 108, 101, 109, 101, 110, 116, 95, 115, 116, 97, 114, 116, 34, 58, 48, 44, 34, 101, 110, 118, 101, 108, 111, 112, 101, 95, 98, 121, 116, 101, 115, 34, 58, 57, 52, 57, 44, 34, 108, 101, 97, 102, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 100, 51, 49, 101, 100, 98, 55, 56, 99, 48, 102, 97, 98, 53, 55, 53, 48, 49, 53, 99, 53, 48, 56, 53, 98, 99, 54, 100, 57, 53, 52, 57, 98, 52, 54, 99, 53, 100, 56, 48, 97, 102, 97, 48, 100, 53, 49, 98, 53, 50, 57, 55, 102, 101, 99, 101, 100, 53, 97, 49, 54, 54, 55, 98, 34, 44, 34, 111, 114, 100, 105, 110, 97, 108, 34, 58, 48, 44, 34, 112, 97, 121, 108, 111, 97, 100, 95, 98, 121, 116, 101, 115, 34, 58, 56, 44, 34, 115, 101, 103, 109, 101, 110, 116, 95, 105, 100, 34, 58, 34, 100, 101, 99, 111, 100, 101, 114, 46, 98, 105, 97, 115, 34, 44, 34, 115, 101, 103, 109, 101, 110, 116, 95, 111, 102, 102, 115, 101, 116, 34, 58, 48, 125]
theorem originalRefLength0 : originalRef0.length = 219 := rfl
theorem originalRefEncoded0 : NativeManifestBytes.refBytes refWire0 = originalRef0 := rfl
def originalRef1 : Bytes := [123, 34, 101, 108, 101, 109, 101, 110, 116, 95, 99, 111, 117, 110, 116, 34, 58, 56, 44, 34, 101, 108, 101, 109, 101, 110, 116, 95, 115, 116, 97, 114, 116, 34, 58, 52, 44, 34, 101, 110, 118, 101, 108, 111, 112, 101, 95, 98, 121, 116, 101, 115, 34, 58, 57, 54, 49, 44, 34, 108, 101, 97, 102, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 50, 57, 49, 50, 97, 57, 52, 53, 57, 99, 51, 55, 51, 50, 57, 98, 99, 51, 99, 55, 53, 54, 49, 101, 57, 102, 101, 99, 101, 100, 55, 51, 54, 51, 49, 102, 102, 54, 102, 97, 51, 101, 100, 101, 51, 98, 97, 55, 50, 49, 52, 102, 98, 101, 102, 50, 52, 49, 50, 97, 98, 57, 52, 99, 34, 44, 34, 111, 114, 100, 105, 110, 97, 108, 34, 58, 49, 44, 34, 112, 97, 121, 108, 111, 97, 100, 95, 98, 121, 116, 101, 115, 34, 58, 49, 54, 44, 34, 115, 101, 103, 109, 101, 110, 116, 95, 105, 100, 34, 58, 34, 101, 109, 98, 101, 100, 100, 105, 110, 103, 46, 119, 101, 105, 103, 104, 116, 34, 44, 34, 115, 101, 103, 109, 101, 110, 116, 95, 111, 102, 102, 115, 101, 116, 34, 58, 48, 125]
theorem originalRefLength1 : originalRef1.length = 224 := rfl
theorem originalRefEncoded1 : NativeManifestBytes.refBytes refWire1 = originalRef1 := rfl
def originalRef2 : Bytes := [123, 34, 101, 108, 101, 109, 101, 110, 116, 95, 99, 111, 117, 110, 116, 34, 58, 56, 44, 34, 101, 108, 101, 109, 101, 110, 116, 95, 115, 116, 97, 114, 116, 34, 58, 49, 50, 44, 34, 101, 110, 118, 101, 108, 111, 112, 101, 95, 98, 121, 116, 101, 115, 34, 58, 57, 54, 50, 44, 34, 108, 101, 97, 102, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 51, 55, 54, 57, 98, 53, 100, 54, 98, 101, 97, 48, 50, 54, 99, 100, 50, 100, 53, 54, 52, 57, 55, 100, 102, 57, 98, 55, 101, 49, 56, 102, 100, 98, 56, 99, 99, 97, 99, 52, 102, 100, 55, 53, 102, 100, 98, 51, 50, 101, 50, 50, 100, 99, 52, 52, 99, 98, 97, 100, 98, 48, 51, 98, 34, 44, 34, 111, 114, 100, 105, 110, 97, 108, 34, 58, 50, 44, 34, 112, 97, 121, 108, 111, 97, 100, 95, 98, 121, 116, 101, 115, 34, 58, 49, 54, 44, 34, 115, 101, 103, 109, 101, 110, 116, 95, 105, 100, 34, 58, 34, 101, 109, 98, 101, 100, 100, 105, 110, 103, 46, 119, 101, 105, 103, 104, 116, 34, 44, 34, 115, 101, 103, 109, 101, 110, 116, 95, 111, 102, 102, 115, 101, 116, 34, 58, 56, 125]
theorem originalRefLength2 : originalRef2.length = 225 := rfl
theorem originalRefEncoded2 : NativeManifestBytes.refBytes refWire2 = originalRef2 := rfl
def originalRef3 : Bytes := [123, 34, 101, 108, 101, 109, 101, 110, 116, 95, 99, 111, 117, 110, 116, 34, 58, 56, 44, 34, 101, 108, 101, 109, 101, 110, 116, 95, 115, 116, 97, 114, 116, 34, 58, 50, 48, 44, 34, 101, 110, 118, 101, 108, 111, 112, 101, 95, 98, 121, 116, 101, 115, 34, 58, 57, 54, 51, 44, 34, 108, 101, 97, 102, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 98, 56, 51, 51, 54, 56, 50, 99, 53, 57, 52, 56, 102, 48, 51, 52, 50, 97, 98, 99, 101, 49, 53, 100, 97, 50, 52, 97, 100, 57, 51, 49, 98, 54, 55, 49, 49, 50, 102, 57, 97, 51, 55, 99, 99, 48, 51, 51, 101, 49, 98, 55, 56, 99, 51, 100, 101, 53, 50, 48, 99, 50, 102, 101, 34, 44, 34, 111, 114, 100, 105, 110, 97, 108, 34, 58, 51, 44, 34, 112, 97, 121, 108, 111, 97, 100, 95, 98, 121, 116, 101, 115, 34, 58, 49, 54, 44, 34, 115, 101, 103, 109, 101, 110, 116, 95, 105, 100, 34, 58, 34, 101, 109, 98, 101, 100, 100, 105, 110, 103, 46, 119, 101, 105, 103, 104, 116, 34, 44, 34, 115, 101, 103, 109, 101, 110, 116, 95, 111, 102, 102, 115, 101, 116, 34, 58, 49, 54, 125]
theorem originalRefLength3 : originalRef3.length = 226 := rfl
theorem originalRefEncoded3 : NativeManifestBytes.refBytes refWire3 = originalRef3 := rfl
def originalRef4 : Bytes := [123, 34, 101, 108, 101, 109, 101, 110, 116, 95, 99, 111, 117, 110, 116, 34, 58, 56, 44, 34, 101, 108, 101, 109, 101, 110, 116, 95, 115, 116, 97, 114, 116, 34, 58, 50, 56, 44, 34, 101, 110, 118, 101, 108, 111, 112, 101, 95, 98, 121, 116, 101, 115, 34, 58, 57, 54, 51, 44, 34, 108, 101, 97, 102, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 57, 56, 50, 97, 54, 56, 51, 49, 49, 48, 100, 56, 52, 55, 102, 54, 57, 101, 54, 101, 49, 56, 53, 50, 51, 99, 48, 51, 54, 97, 54, 54, 52, 53, 102, 98, 52, 100, 97, 51, 53, 49, 49, 98, 56, 101, 53, 56, 54, 97, 52, 48, 102, 48, 100, 102, 55, 53, 48, 97, 56, 100, 101, 100, 34, 44, 34, 111, 114, 100, 105, 110, 97, 108, 34, 58, 52, 44, 34, 112, 97, 121, 108, 111, 97, 100, 95, 98, 121, 116, 101, 115, 34, 58, 49, 54, 44, 34, 115, 101, 103, 109, 101, 110, 116, 95, 105, 100, 34, 58, 34, 101, 109, 98, 101, 100, 100, 105, 110, 103, 46, 119, 101, 105, 103, 104, 116, 34, 44, 34, 115, 101, 103, 109, 101, 110, 116, 95, 111, 102, 102, 115, 101, 116, 34, 58, 50, 52, 125]
theorem originalRefLength4 : originalRef4.length = 226 := rfl
theorem originalRefEncoded4 : NativeManifestBytes.refBytes refWire4 = originalRef4 := rfl
def originalRefs : Bytes := originalRef0 ++ [44] ++ originalRef1 ++ [44] ++ originalRef2 ++ [44] ++ originalRef3 ++ [44] ++ originalRef4 ++ [93]
theorem originalRefsEncoded : NativeManifestBytes.refsBytes wire.refs = originalRefs := by
  simp only [NativeManifestBytes.refsBytes,wire,NativeJsonSequence.encode,originalRefEncoded0,originalRefEncoded1,originalRefEncoded2,originalRefEncoded3,originalRefEncoded4,originalRefs,List.append_assoc]
def originalField0 : Bytes := [34, 97, 103, 103, 114, 101, 103, 97, 116, 105, 111, 110, 95, 115, 116, 101, 112, 115, 34, 58, 50, 44]
theorem originalFieldLength0 : originalField0.length = 22 := rfl
theorem originalFieldEncoded0 : NativeScaleBytes.memberBytes "aggregation_steps" .natural wire.steps 44 = originalField0 := rfl
def originalField1 : Bytes := [34, 99, 111, 109, 109, 105, 116, 109, 101, 110, 116, 95, 114, 111, 111, 116, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 101, 56, 48, 57, 49, 54, 97, 56, 101, 99, 55, 100, 54, 51, 52, 98, 52, 99, 51, 53, 50, 52, 100, 56, 55, 51, 99, 49, 51, 49, 52, 52, 98, 55, 55, 54, 48, 99, 55, 53, 53, 50, 101, 54, 55, 56, 56, 49, 51, 50, 97, 55, 53, 102, 99, 101, 53, 52, 53, 54, 50, 57, 54, 100, 34, 44]
theorem originalFieldLength1 : originalField1.length = 92 := rfl
theorem originalFieldEncoded1 : NativeScaleBytes.memberBytes "commitment_root" .text wire.root 44 = originalField1 := rfl
def originalField2 : Bytes := [34, 100, 111, 109, 97, 105, 110, 95, 105, 100, 34, 58, 34, 100, 111, 109, 97, 105, 110, 45, 116, 101, 120, 116, 45, 101, 110, 34, 44]
theorem originalFieldLength2 : originalField2.length = 29 := rfl
theorem originalFieldEncoded2 : NativeScaleBytes.memberBytes "domain_id" .text wire.domain 44 = originalField2 := rfl
def originalField3 : Bytes := [34, 102, 111, 114, 109, 97, 108, 95, 115, 101, 109, 97, 110, 116, 105, 99, 115, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 99, 99, 57, 56, 102, 49, 53, 97, 99, 50, 48, 102, 99, 51, 101, 100, 50, 54, 53, 99, 98, 55, 54, 54, 56, 50, 99, 97, 49, 53, 97, 57, 51, 54, 101, 50, 52, 54, 54, 48, 97, 54, 53, 49, 101, 50, 98, 56, 102, 56, 49, 54, 51, 56, 97, 98, 98, 51, 50, 54, 53, 99, 98, 54, 34, 44]
theorem originalFieldLength3 : originalField3.length = 96 := rfl
theorem originalFieldEncoded3 : NativeScaleBytes.memberBytes "formal_semantics_id" .text wire.semantics 44 = originalField3 := rfl
def originalField4 : Bytes := [34, 112, 97, 114, 97, 109, 101, 116, 101, 114, 95, 115, 99, 104, 101, 109, 97, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 102, 52, 51, 99, 48, 50, 53, 57, 55, 52, 57, 98, 49, 53, 97, 101, 48, 100, 48, 49, 53, 52, 97, 54, 101, 57, 48, 57, 52, 55, 55, 52, 99, 55, 101, 97, 54, 53, 101, 53, 53, 97, 100, 101, 102, 98, 97, 101, 97, 52, 48, 48, 97, 54, 50, 48, 49, 97, 99, 98, 54, 50, 51, 57, 34, 44]
theorem originalFieldLength4 : originalField4.length = 96 := rfl
theorem originalFieldEncoded4 : NativeScaleBytes.memberBytes "parameter_schema_id" .text wire.schema 44 = originalField4 := rfl
def originalField5 : Bytes := [34, 112, 97, 114, 101, 110, 116, 95, 99, 104, 101, 99, 107, 112, 111, 105, 110, 116, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 34, 44]
theorem originalFieldLength5 : originalField5.length = 97 := rfl
theorem originalFieldEncoded5 : NativeScaleBytes.memberBytes "parent_checkpoint_id" .text wire.parent 44 = originalField5 := rfl
def originalField6 : Bytes := [34, 112, 114, 111, 102, 105, 108, 101, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 49, 55, 99, 56, 100, 50, 51, 55, 57, 48, 48, 52, 55, 57, 54, 54, 101, 52, 50, 102, 51, 50, 48, 52, 53, 48, 50, 54, 50, 51, 99, 55, 52, 97, 48, 102, 102, 48, 51, 56, 51, 51, 49, 57, 100, 50, 51, 101, 54, 55, 97, 98, 49, 53, 99, 102, 57, 50, 102, 101, 51, 101, 54, 49, 34, 44]
theorem originalFieldLength6 : originalField6.length = 87 := rfl
theorem originalFieldEncoded6 : NativeScaleBytes.memberBytes "profile_id" .text wire.profile 44 = originalField6 := rfl
def originalField7 : Bytes := [34, 112, 114, 111, 111, 102, 95, 105, 110, 115, 116, 97, 110, 99, 101, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 57, 57, 51, 98, 52, 100, 53, 49, 48, 52, 56, 49, 48, 100, 100, 50, 54, 97, 51, 49, 53, 57, 98, 54, 48, 99, 102, 56, 102, 101, 57, 97, 102, 101, 54, 49, 53, 52, 99, 100, 99, 99, 97, 57, 48, 100, 50, 50, 98, 53, 55, 55, 97, 101, 49, 98, 54, 100, 49, 97, 99, 48, 55, 54, 34, 44]
theorem originalFieldLength7 : originalField7.length = 94 := rfl
theorem originalFieldEncoded7 : NativeScaleBytes.memberBytes "proof_instance_id" .text wire.proof 44 = originalField7 := rfl
def originalField8 : Bytes := [34, 114, 111, 117, 110, 100, 95, 99, 111, 110, 102, 105, 103, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 51, 52, 98, 99, 48, 56, 99, 51, 49, 54, 100, 102, 101, 50, 50, 101, 102, 101, 49, 53, 53, 101, 100, 49, 49, 98, 56, 54, 54, 98, 99, 99, 48, 100, 97, 102, 55, 101, 102, 56, 99, 51, 99, 55, 51, 56, 57, 99, 53, 54, 98, 50, 102, 50, 99, 55, 48, 55, 52, 52, 51, 54, 50, 57, 34, 44]
theorem originalFieldLength8 : originalField8.length = 92 := rfl
theorem originalFieldEncoded8 : NativeScaleBytes.memberBytes "round_config_id" .text wire.config 44 = originalField8 := rfl
def originalField9 : Bytes := [34, 115, 99, 97, 108, 101, 95, 116, 97, 98, 108, 101, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 52, 51, 52, 48, 57, 50, 102, 56, 50, 49, 56, 56, 51, 51, 55, 100, 48, 97, 50, 55, 51, 99, 100, 49, 51, 99, 57, 51, 101, 48, 54, 100, 101, 99, 53, 53, 97, 101, 56, 52, 50, 100, 102, 48, 52, 57, 56, 101, 52, 100, 53, 50, 99, 97, 97, 49, 100, 49, 56, 52, 52, 50, 48, 53, 34, 44]
theorem originalFieldLength9 : originalField9.length = 91 := rfl
theorem originalFieldEncoded9 : NativeScaleBytes.memberBytes "scale_table_id" .text wire.scale 44 = originalField9 := rfl
def originalField10 : Bytes := [34, 115, 99, 104, 101, 109, 97, 95, 118, 101, 114, 115, 105, 111, 110, 34, 58, 34, 49, 46, 48, 46, 48, 34, 44]
theorem originalFieldLength10 : originalField10.length = 25 := rfl
theorem originalFieldEncoded10 : NativeScaleBytes.memberBytes "schema_version" .text wire.version 44 = originalField10 := rfl
def originalField11 : Bytes := [34, 115, 104, 97, 114, 100, 95, 112, 108, 97, 110, 95, 105, 100, 34, 58, 34, 115, 104, 97, 50, 53, 54, 58, 52, 99, 54, 52, 52, 97, 51, 50, 53, 52, 101, 100, 98, 51, 100, 55, 98, 102, 102, 48, 48, 57, 98, 98, 101, 57, 49, 101, 101, 57, 57, 100, 102, 54, 48, 53, 49, 53, 49, 54, 51, 54, 50, 102, 97, 49, 97, 49, 101, 97, 99, 54, 102, 48, 97, 56, 48, 51, 97, 57, 99, 55, 97, 49, 34, 44]
theorem originalFieldLength11 : originalField11.length = 90 := rfl
theorem originalFieldEncoded11 : NativeScaleBytes.memberBytes "shard_plan_id" .text wire.plan 44 = originalField11 := rfl
def originalField13 : Bytes := [34, 116, 105, 99, 107, 101, 116, 95, 105, 100, 34, 58, 34, 116, 105, 99, 107, 101, 116, 45, 48, 48, 50, 45, 102, 105, 120, 116, 117, 114, 101, 34, 44]
theorem originalFieldLength13 : originalField13.length = 33 := rfl
theorem originalFieldEncoded13 : NativeScaleBytes.memberBytes "ticket_id" .text wire.ticket 44 = originalField13 := rfl
def originalField14 : Bytes := [34, 116, 111, 116, 97, 108, 95, 101, 108, 101, 109, 101, 110, 116, 115, 34, 58, 51, 54, 44]
theorem originalFieldLength14 : originalField14.length = 20 := rfl
theorem originalFieldEncoded14 : NativeScaleBytes.memberBytes "total_elements" .natural wire.total 44 = originalField14 := rfl
def originalField15 : Bytes := [34, 116, 111, 116, 97, 108, 95, 101, 110, 118, 101, 108, 111, 112, 101, 95, 98, 121, 116, 101, 115, 34, 58, 52, 55, 57, 56, 44]
theorem originalFieldLength15 : originalField15.length = 28 := rfl
theorem originalFieldEncoded15 : NativeScaleBytes.memberBytes "total_envelope_bytes" .natural wire.envelopes 44 = originalField15 := rfl
def originalField16 : Bytes := [34, 116, 111, 116, 97, 108, 95, 112, 97, 121, 108, 111, 97, 100, 95, 98, 121, 116, 101, 115, 34, 58, 55, 50, 44]
theorem originalFieldLength16 : originalField16.length = 25 := rfl
theorem originalFieldEncoded16 : NativeScaleBytes.memberBytes "total_payload_bytes" .natural wire.payloads 44 = originalField16 := rfl
def originalField17 : Bytes := [34, 116, 121, 112, 101, 95, 110, 97, 109, 101, 34, 58, 34, 69, 78, 67, 79, 68, 69, 68, 95, 67, 79, 78, 84, 82, 73, 66, 85, 84, 73, 79, 78, 95, 77, 65, 78, 73, 70, 69, 83, 84, 34, 125]
theorem originalFieldLength17 : originalField17.length = 44 := rfl
theorem originalFieldEncoded17 : NativeScaleBytes.memberBytes "type_name" .text wire.kind 125 = originalField17 := rfl
def original : Bytes := [123] ++ originalField0 ++ originalField1 ++ originalField2 ++ originalField3 ++ originalField4 ++ originalField5 ++ originalField6 ++ originalField7 ++ originalField8 ++ originalField9 ++ originalField10 ++ originalField11 ++ ascii "\"shards\":[" ++ originalRefs ++ [44] ++ originalField13 ++ originalField14 ++ originalField15 ++ originalField16 ++ originalField17
theorem originalLength : original.length = 2198 := by
  simp only [original,originalRefs,List.length_append,List.length_cons,List.length_nil,originalRefLength0,originalRefLength1,originalRefLength2,originalRefLength3,originalRefLength4,originalFieldLength0,originalFieldLength1,originalFieldLength2,originalFieldLength3,originalFieldLength4,originalFieldLength5,originalFieldLength6,originalFieldLength7,originalFieldLength8,originalFieldLength9,originalFieldLength10,originalFieldLength11,originalFieldLength13,originalFieldLength14,originalFieldLength15,originalFieldLength16,originalFieldLength17]
  rfl
theorem originalEncoded : NativeManifestBytes.encode wire = original := by
  simp only [NativeManifestBytes.encode,originalFieldEncoded0,originalFieldEncoded1,originalFieldEncoded2,originalFieldEncoded3,originalFieldEncoded4,originalFieldEncoded5,originalFieldEncoded6,originalFieldEncoded7,originalFieldEncoded8,originalFieldEncoded9,originalFieldEncoded10,originalFieldEncoded11,originalFieldEncoded13,originalFieldEncoded14,originalFieldEncoded15,originalFieldEncoded16,originalFieldEncoded17,originalRefsEncoded,original]
theorem decodedWire : NativeManifestBytes.decode original = some wire := by
  rw [← originalEncoded]
  apply NativeManifestBytes.decodeEncoded wire wireSyntax
  rw [originalEncoded,originalLength]; decide
def manifest : Manifest := ⟨wire,[ref0,ref1,ref2,ref3,ref4],2,36,4798,72⟩
theorem interpretedManifest : interpret wire = some manifest := by
  apply interpretFromSource
  refine ⟨rfl,?_,by decide,by decide,by decide,by decide⟩
  change readRefs [refWire0,refWire1,refWire2,refWire3,refWire4] = some [ref0,ref1,ref2,ref3,ref4]
  simp only [readRefs,refRead0,refRead1,refRead2,refRead3,refRead4,Bind.bind,Option.bind]
def hashInput0 : Bytes := NativeSchemaVectors.original
def hashOutput0 : Bytes := ascii "sha256:f43c0259749b15ae0d0154a6e9094774c7ea65e55adefbaea400a6201acb6239"
theorem hashLength0 : hashInput0.length = 376 := rfl
def hashInput1 : Bytes := NativeScaleBinding.hashInput NativeScaleVectors.original
def hashOutput1 : Bytes := ascii "sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205"
theorem hashLength1 : hashInput1.length = 674 := rfl
def hashInput2 : Bytes := NativeShardPlanBinding.hashInput NativeShardPlanVectors.original
def hashOutput2 : Bytes := ascii "sha256:4c644a3254edb3d7bff009bbe91ee99df6051516362fa1a1eac6f0a803a9c7a1"
theorem hashLength2 : hashInput2.length = 1109 := rfl
def hashInput3 : Bytes := manifestInput original
def hashOutput3 : Bytes := ascii "sha256:6b24994dde9f03ccde6acb42abb080ec9dcc2e111a81d781948a3ac1d10446ec"
theorem hashLength3 : hashInput3.length = 2226 := rfl
def hashInput4 : Bytes := NativeScaleVectors.bound0.block.frame.payload
def hashOutput4 : Bytes := ascii "sha256:9a8ba9dcc3313c6873d2f683d6078bbd24e0edab55621e35fc9bfa20c4da796b"
theorem hashLength4 : hashInput4.length = 8 := rfl
def hashInput5 : Bytes := leafInput NativeQBytesVectors.frame0
def hashOutput5 : Bytes := ascii "sha256:d31edb78c0fab575015c5085bc6d9549b46c5d80afa0d51b5297feced5a1667b"
theorem hashLength5 : hashInput5.length = 979 := rfl
def hashInput6 : Bytes := NativeScaleVectors.bound1.block.frame.payload
def hashOutput6 : Bytes := ascii "sha256:11139a766ea0f987ea1f264a5adcbae08cc62845bd0f3911ff078ed90b4c3d31"
theorem hashLength6 : hashInput6.length = 16 := rfl
def hashInput7 : Bytes := leafInput NativeQBytesVectors.frame1
def hashOutput7 : Bytes := ascii "sha256:2912a9459c37329bc3c7561e9feced73631ff6fa3ede3ba7214fbef2412ab94c"
theorem hashLength7 : hashInput7.length = 991 := rfl
def hashInput8 : Bytes := NativeScaleVectors.bound2.block.frame.payload
def hashOutput8 : Bytes := ascii "sha256:cf1775c6aff05d388bf59ec9df80fa0996a17ca614068e31d102ca1ee1b0f072"
theorem hashLength8 : hashInput8.length = 16 := rfl
def hashInput9 : Bytes := leafInput NativeQBytesVectors.frame2
def hashOutput9 : Bytes := ascii "sha256:3769b5d6bea026cd2d56497df9b7e18fdb8ccac4fd75fdb32e22dc44cbadb03b"
theorem hashLength9 : hashInput9.length = 992 := rfl
def hashInput10 : Bytes := NativeScaleVectors.bound3.block.frame.payload
def hashOutput10 : Bytes := ascii "sha256:6ba866520d5b41853627ff9a283137bc3a4108297f9acfa3cbd5c5f9b272e09c"
theorem hashLength10 : hashInput10.length = 16 := rfl
def hashInput11 : Bytes := leafInput NativeQBytesVectors.frame3
def hashOutput11 : Bytes := ascii "sha256:b833682c5948f0342abce15da24ad931b67112f9a37cc033e1b78c3de520c2fe"
theorem hashLength11 : hashInput11.length = 993 := rfl
def hashInput12 : Bytes := NativeScaleVectors.bound4.block.frame.payload
def hashOutput12 : Bytes := ascii "sha256:3f7000f8f09cc05426cfc1c82d8c13dcc25155b821576999665cea7e1092ff84"
theorem hashLength12 : hashInput12.length = 16 := rfl
def hashInput13 : Bytes := leafInput NativeQBytesVectors.frame4
def hashOutput13 : Bytes := ascii "sha256:982a683110d847f69e6e18523c036a6645fb4da3511b8e586a40f0df750a8ded"
theorem hashLength13 : hashInput13.length = 993 := rfl
def hashInput14 : Bytes := [100, 101, 108, 116, 97, 114, 101, 100, 117, 99, 101, 46, 48, 48, 52, 46, 109, 101, 114, 107, 108, 101, 45, 110, 111, 100, 101, 46, 118, 49, 0, 211, 30, 219, 120, 192, 250, 181, 117, 1, 92, 80, 133, 188, 109, 149, 73, 180, 108, 93, 128, 175, 160, 213, 27, 82, 151, 254, 206, 213, 161, 102, 123, 41, 18, 169, 69, 156, 55, 50, 155, 195, 199, 86, 30, 159, 236, 237, 115, 99, 31, 246, 250, 62, 222, 59, 167, 33, 79, 190, 242, 65, 42, 185, 76]
def hashOutput14 : Bytes := ascii "sha256:6fb2bfe2dfcafa6e16fb525362bb19f60b1fdf4f0049755275a843404f5842a8"
theorem hashLength14 : hashInput14.length = 95 := rfl
def hashInput15 : Bytes := [100, 101, 108, 116, 97, 114, 101, 100, 117, 99, 101, 46, 48, 48, 52, 46, 109, 101, 114, 107, 108, 101, 45, 110, 111, 100, 101, 46, 118, 49, 0, 55, 105, 181, 214, 190, 160, 38, 205, 45, 86, 73, 125, 249, 183, 225, 143, 219, 140, 202, 196, 253, 117, 253, 179, 46, 34, 220, 68, 203, 173, 176, 59, 184, 51, 104, 44, 89, 72, 240, 52, 42, 188, 225, 93, 162, 74, 217, 49, 182, 113, 18, 249, 163, 124, 192, 51, 225, 183, 140, 61, 229, 32, 194, 254]
def hashOutput15 : Bytes := ascii "sha256:b0fda27acef7816928b931ecbfacb338481db518611fd6f98bd8fb159a0656f2"
theorem hashLength15 : hashInput15.length = 95 := rfl
def hashInput16 : Bytes := [100, 101, 108, 116, 97, 114, 101, 100, 117, 99, 101, 46, 48, 48, 52, 46, 109, 101, 114, 107, 108, 101, 45, 110, 111, 100, 101, 46, 118, 49, 0, 152, 42, 104, 49, 16, 216, 71, 246, 158, 110, 24, 82, 60, 3, 106, 102, 69, 251, 77, 163, 81, 27, 142, 88, 106, 64, 240, 223, 117, 10, 141, 237, 152, 42, 104, 49, 16, 216, 71, 246, 158, 110, 24, 82, 60, 3, 106, 102, 69, 251, 77, 163, 81, 27, 142, 88, 106, 64, 240, 223, 117, 10, 141, 237]
def hashOutput16 : Bytes := ascii "sha256:1407dc7895b66fdeacb11981d3dccbfae48ac0a389379af8a34cf6537bb1aa0b"
theorem hashLength16 : hashInput16.length = 95 := rfl
def hashInput17 : Bytes := [100, 101, 108, 116, 97, 114, 101, 100, 117, 99, 101, 46, 48, 48, 52, 46, 109, 101, 114, 107, 108, 101, 45, 110, 111, 100, 101, 46, 118, 49, 0, 111, 178, 191, 226, 223, 202, 250, 110, 22, 251, 82, 83, 98, 187, 25, 246, 11, 31, 223, 79, 0, 73, 117, 82, 117, 168, 67, 64, 79, 88, 66, 168, 176, 253, 162, 122, 206, 247, 129, 105, 40, 185, 49, 236, 191, 172, 179, 56, 72, 29, 181, 24, 97, 31, 214, 249, 139, 216, 251, 21, 154, 6, 86, 242]
def hashOutput17 : Bytes := ascii "sha256:44698e87c695ecb608925ac745d40cff871c70edb4ee8c3d021cdef941ba3e85"
theorem hashLength17 : hashInput17.length = 95 := rfl
def hashInput18 : Bytes := [100, 101, 108, 116, 97, 114, 101, 100, 117, 99, 101, 46, 48, 48, 52, 46, 109, 101, 114, 107, 108, 101, 45, 110, 111, 100, 101, 46, 118, 49, 0, 20, 7, 220, 120, 149, 182, 111, 222, 172, 177, 25, 129, 211, 220, 203, 250, 228, 138, 192, 163, 137, 55, 154, 248, 163, 76, 246, 83, 123, 177, 170, 11, 20, 7, 220, 120, 149, 182, 111, 222, 172, 177, 25, 129, 211, 220, 203, 250, 228, 138, 192, 163, 137, 55, 154, 248, 163, 76, 246, 83, 123, 177, 170, 11]
def hashOutput18 : Bytes := ascii "sha256:d5da7e6ce16e92c4e1a3aa17cea6722a898b590e5e86359df31b36bcdd49414f"
theorem hashLength18 : hashInput18.length = 95 := rfl
def hashInput19 : Bytes := [100, 101, 108, 116, 97, 114, 101, 100, 117, 99, 101, 46, 48, 48, 52, 46, 109, 101, 114, 107, 108, 101, 45, 110, 111, 100, 101, 46, 118, 49, 0, 68, 105, 142, 135, 198, 149, 236, 182, 8, 146, 90, 199, 69, 212, 12, 255, 135, 28, 112, 237, 180, 238, 140, 61, 2, 28, 222, 249, 65, 186, 62, 133, 213, 218, 126, 108, 225, 110, 146, 196, 225, 163, 170, 23, 206, 166, 114, 42, 137, 139, 89, 14, 94, 134, 53, 157, 243, 27, 54, 188, 221, 73, 65, 79]
def hashOutput19 : Bytes := ascii "sha256:e80916a8ec7d634b4c3524d873c13144b7760c7552e6788132a75fce5456296d"
theorem hashLength19 : hashInput19.length = 95 := rfl
/-- Finite exact-preimage SYNTHETIC adapter. NOT SHA or source authority. -/
@[irreducible]
def fixtureHash (raw : Bytes) : Bytes :=
  if raw.length = 376 then
    if raw = hashInput0 then hashOutput0 else
    []
  else
  if raw.length = 674 then
    if raw = hashInput1 then hashOutput1 else
    []
  else
  if raw.length = 1109 then
    if raw = hashInput2 then hashOutput2 else
    []
  else
  if raw.length = 2226 then
    if raw = hashInput3 then hashOutput3 else
    []
  else
  if raw.length = 8 then
    if raw = hashInput4 then hashOutput4 else
    []
  else
  if raw.length = 979 then
    if raw = hashInput5 then hashOutput5 else
    []
  else
  if raw.length = 16 then
    if raw = hashInput6 then hashOutput6 else
    if raw = hashInput8 then hashOutput8 else
    if raw = hashInput10 then hashOutput10 else
    if raw = hashInput12 then hashOutput12 else
    []
  else
  if raw.length = 991 then
    if raw = hashInput7 then hashOutput7 else
    []
  else
  if raw.length = 992 then
    if raw = hashInput9 then hashOutput9 else
    []
  else
  if raw.length = 993 then
    if raw = hashInput11 then hashOutput11 else
    if raw = hashInput13 then hashOutput13 else
    []
  else
  if raw.length = 95 then
    if raw = hashInput14 then hashOutput14 else
    if raw = hashInput15 then hashOutput15 else
    if raw = hashInput16 then hashOutput16 else
    if raw = hashInput17 then hashOutput17 else
    if raw = hashInput18 then hashOutput18 else
    if raw = hashInput19 then hashOutput19 else
    []
  else
    []
theorem hashChecked0 : fixtureHash (NativeSchemaVectors.original) = hashOutput0 := by
  change fixtureHash hashInput0 = hashOutput0
  unfold fixtureHash
  rw [hashLength0]
  rw [if_pos rfl]
  rw [if_pos rfl]
theorem hashChecked1 : fixtureHash (NativeScaleBinding.hashInput NativeScaleVectors.original) = hashOutput1 := by
  change fixtureHash hashInput1 = hashOutput1
  unfold fixtureHash
  rw [hashLength1]
  rw [if_neg (by decide : ¬ (674 = 376))]
  rw [if_pos rfl]
  rw [if_pos rfl]
theorem hashChecked2 : fixtureHash (NativeShardPlanBinding.hashInput NativeShardPlanVectors.original) = hashOutput2 := by
  change fixtureHash hashInput2 = hashOutput2
  unfold fixtureHash
  rw [hashLength2]
  rw [if_neg (by decide : ¬ (1109 = 376))]
  rw [if_neg (by decide : ¬ (1109 = 674))]
  rw [if_pos rfl]
  rw [if_pos rfl]
theorem hashChecked3 : fixtureHash (manifestInput original) = hashOutput3 := by
  change fixtureHash hashInput3 = hashOutput3
  unfold fixtureHash
  rw [hashLength3]
  rw [if_neg (by decide : ¬ (2226 = 376))]
  rw [if_neg (by decide : ¬ (2226 = 674))]
  rw [if_neg (by decide : ¬ (2226 = 1109))]
  rw [if_pos rfl]
  rw [if_pos rfl]
theorem hashChecked4 : fixtureHash (NativeScaleVectors.bound0.block.frame.payload) = hashOutput4 := by
  change fixtureHash hashInput4 = hashOutput4
  unfold fixtureHash
  rw [hashLength4]
  rw [if_neg (by decide : ¬ (8 = 376))]
  rw [if_neg (by decide : ¬ (8 = 674))]
  rw [if_neg (by decide : ¬ (8 = 1109))]
  rw [if_neg (by decide : ¬ (8 = 2226))]
  rw [if_pos rfl]
  rw [if_pos rfl]
theorem hashChecked5 : fixtureHash (leafInput NativeQBytesVectors.frame0) = hashOutput5 := by
  change fixtureHash hashInput5 = hashOutput5
  unfold fixtureHash
  rw [hashLength5]
  rw [if_neg (by decide : ¬ (979 = 376))]
  rw [if_neg (by decide : ¬ (979 = 674))]
  rw [if_neg (by decide : ¬ (979 = 1109))]
  rw [if_neg (by decide : ¬ (979 = 2226))]
  rw [if_neg (by decide : ¬ (979 = 8))]
  rw [if_pos rfl]
  rw [if_pos rfl]
theorem hashChecked6 : fixtureHash (NativeScaleVectors.bound1.block.frame.payload) = hashOutput6 := by
  change fixtureHash hashInput6 = hashOutput6
  unfold fixtureHash
  rw [hashLength6]
  rw [if_neg (by decide : ¬ (16 = 376))]
  rw [if_neg (by decide : ¬ (16 = 674))]
  rw [if_neg (by decide : ¬ (16 = 1109))]
  rw [if_neg (by decide : ¬ (16 = 2226))]
  rw [if_neg (by decide : ¬ (16 = 8))]
  rw [if_neg (by decide : ¬ (16 = 979))]
  rw [if_pos rfl]
  rw [if_pos rfl]
theorem hashChecked7 : fixtureHash (leafInput NativeQBytesVectors.frame1) = hashOutput7 := by
  change fixtureHash hashInput7 = hashOutput7
  unfold fixtureHash
  rw [hashLength7]
  rw [if_neg (by decide : ¬ (991 = 376))]
  rw [if_neg (by decide : ¬ (991 = 674))]
  rw [if_neg (by decide : ¬ (991 = 1109))]
  rw [if_neg (by decide : ¬ (991 = 2226))]
  rw [if_neg (by decide : ¬ (991 = 8))]
  rw [if_neg (by decide : ¬ (991 = 979))]
  rw [if_neg (by decide : ¬ (991 = 16))]
  rw [if_pos rfl]
  rw [if_pos rfl]
theorem hashChecked8 : fixtureHash (NativeScaleVectors.bound2.block.frame.payload) = hashOutput8 := by
  change fixtureHash hashInput8 = hashOutput8
  unfold fixtureHash
  rw [hashLength8]
  rw [if_neg (by decide : ¬ (16 = 376))]
  rw [if_neg (by decide : ¬ (16 = 674))]
  rw [if_neg (by decide : ¬ (16 = 1109))]
  rw [if_neg (by decide : ¬ (16 = 2226))]
  rw [if_neg (by decide : ¬ (16 = 8))]
  rw [if_neg (by decide : ¬ (16 = 979))]
  rw [if_pos rfl]
  rw [if_neg (show hashInput8 ≠ hashInput6 from by decide)]
  rw [if_pos rfl]
theorem hashChecked9 : fixtureHash (leafInput NativeQBytesVectors.frame2) = hashOutput9 := by
  change fixtureHash hashInput9 = hashOutput9
  unfold fixtureHash
  rw [hashLength9]
  rw [if_neg (by decide : ¬ (992 = 376))]
  rw [if_neg (by decide : ¬ (992 = 674))]
  rw [if_neg (by decide : ¬ (992 = 1109))]
  rw [if_neg (by decide : ¬ (992 = 2226))]
  rw [if_neg (by decide : ¬ (992 = 8))]
  rw [if_neg (by decide : ¬ (992 = 979))]
  rw [if_neg (by decide : ¬ (992 = 16))]
  rw [if_neg (by decide : ¬ (992 = 991))]
  rw [if_pos rfl]
  rw [if_pos rfl]
theorem hashChecked10 : fixtureHash (NativeScaleVectors.bound3.block.frame.payload) = hashOutput10 := by
  change fixtureHash hashInput10 = hashOutput10
  unfold fixtureHash
  rw [hashLength10]
  rw [if_neg (by decide : ¬ (16 = 376))]
  rw [if_neg (by decide : ¬ (16 = 674))]
  rw [if_neg (by decide : ¬ (16 = 1109))]
  rw [if_neg (by decide : ¬ (16 = 2226))]
  rw [if_neg (by decide : ¬ (16 = 8))]
  rw [if_neg (by decide : ¬ (16 = 979))]
  rw [if_pos rfl]
  rw [if_neg (show hashInput10 ≠ hashInput6 from by decide)]
  rw [if_neg (show hashInput10 ≠ hashInput8 from by decide)]
  rw [if_pos rfl]
theorem hashChecked11 : fixtureHash (leafInput NativeQBytesVectors.frame3) = hashOutput11 := by
  change fixtureHash hashInput11 = hashOutput11
  unfold fixtureHash
  rw [hashLength11]
  rw [if_neg (by decide : ¬ (993 = 376))]
  rw [if_neg (by decide : ¬ (993 = 674))]
  rw [if_neg (by decide : ¬ (993 = 1109))]
  rw [if_neg (by decide : ¬ (993 = 2226))]
  rw [if_neg (by decide : ¬ (993 = 8))]
  rw [if_neg (by decide : ¬ (993 = 979))]
  rw [if_neg (by decide : ¬ (993 = 16))]
  rw [if_neg (by decide : ¬ (993 = 991))]
  rw [if_neg (by decide : ¬ (993 = 992))]
  rw [if_pos rfl]
  rw [if_pos rfl]
theorem hashChecked12 : fixtureHash (NativeScaleVectors.bound4.block.frame.payload) = hashOutput12 := by
  change fixtureHash hashInput12 = hashOutput12
  unfold fixtureHash
  rw [hashLength12]
  rw [if_neg (by decide : ¬ (16 = 376))]
  rw [if_neg (by decide : ¬ (16 = 674))]
  rw [if_neg (by decide : ¬ (16 = 1109))]
  rw [if_neg (by decide : ¬ (16 = 2226))]
  rw [if_neg (by decide : ¬ (16 = 8))]
  rw [if_neg (by decide : ¬ (16 = 979))]
  rw [if_pos rfl]
  rw [if_neg (show hashInput12 ≠ hashInput6 from by decide)]
  rw [if_neg (show hashInput12 ≠ hashInput8 from by decide)]
  rw [if_neg (show hashInput12 ≠ hashInput10 from by decide)]
  rw [if_pos rfl]
theorem hashChecked13 : fixtureHash (leafInput NativeQBytesVectors.frame4) = hashOutput13 := by
  change fixtureHash hashInput13 = hashOutput13
  unfold fixtureHash
  rw [hashLength13]
  rw [if_neg (by decide : ¬ (993 = 376))]
  rw [if_neg (by decide : ¬ (993 = 674))]
  rw [if_neg (by decide : ¬ (993 = 1109))]
  rw [if_neg (by decide : ¬ (993 = 2226))]
  rw [if_neg (by decide : ¬ (993 = 8))]
  rw [if_neg (by decide : ¬ (993 = 979))]
  rw [if_neg (by decide : ¬ (993 = 16))]
  rw [if_neg (by decide : ¬ (993 = 991))]
  rw [if_neg (by decide : ¬ (993 = 992))]
  rw [if_pos rfl]
  rw [if_neg (show hashInput13 ≠ hashInput11 from by decide)]
  rw [if_pos rfl]
theorem hashChecked14 : fixtureHash ([100, 101, 108, 116, 97, 114, 101, 100, 117, 99, 101, 46, 48, 48, 52, 46, 109, 101, 114, 107, 108, 101, 45, 110, 111, 100, 101, 46, 118, 49, 0, 211, 30, 219, 120, 192, 250, 181, 117, 1, 92, 80, 133, 188, 109, 149, 73, 180, 108, 93, 128, 175, 160, 213, 27, 82, 151, 254, 206, 213, 161, 102, 123, 41, 18, 169, 69, 156, 55, 50, 155, 195, 199, 86, 30, 159, 236, 237, 115, 99, 31, 246, 250, 62, 222, 59, 167, 33, 79, 190, 242, 65, 42, 185, 76]) = hashOutput14 := by
  change fixtureHash hashInput14 = hashOutput14
  unfold fixtureHash
  rw [hashLength14]
  rw [if_neg (by decide : ¬ (95 = 376))]
  rw [if_neg (by decide : ¬ (95 = 674))]
  rw [if_neg (by decide : ¬ (95 = 1109))]
  rw [if_neg (by decide : ¬ (95 = 2226))]
  rw [if_neg (by decide : ¬ (95 = 8))]
  rw [if_neg (by decide : ¬ (95 = 979))]
  rw [if_neg (by decide : ¬ (95 = 16))]
  rw [if_neg (by decide : ¬ (95 = 991))]
  rw [if_neg (by decide : ¬ (95 = 992))]
  rw [if_neg (by decide : ¬ (95 = 993))]
  rw [if_pos rfl]
  rw [if_pos rfl]
theorem hashChecked15 : fixtureHash ([100, 101, 108, 116, 97, 114, 101, 100, 117, 99, 101, 46, 48, 48, 52, 46, 109, 101, 114, 107, 108, 101, 45, 110, 111, 100, 101, 46, 118, 49, 0, 55, 105, 181, 214, 190, 160, 38, 205, 45, 86, 73, 125, 249, 183, 225, 143, 219, 140, 202, 196, 253, 117, 253, 179, 46, 34, 220, 68, 203, 173, 176, 59, 184, 51, 104, 44, 89, 72, 240, 52, 42, 188, 225, 93, 162, 74, 217, 49, 182, 113, 18, 249, 163, 124, 192, 51, 225, 183, 140, 61, 229, 32, 194, 254]) = hashOutput15 := by
  change fixtureHash hashInput15 = hashOutput15
  unfold fixtureHash
  rw [hashLength15]
  rw [if_neg (by decide : ¬ (95 = 376))]
  rw [if_neg (by decide : ¬ (95 = 674))]
  rw [if_neg (by decide : ¬ (95 = 1109))]
  rw [if_neg (by decide : ¬ (95 = 2226))]
  rw [if_neg (by decide : ¬ (95 = 8))]
  rw [if_neg (by decide : ¬ (95 = 979))]
  rw [if_neg (by decide : ¬ (95 = 16))]
  rw [if_neg (by decide : ¬ (95 = 991))]
  rw [if_neg (by decide : ¬ (95 = 992))]
  rw [if_neg (by decide : ¬ (95 = 993))]
  rw [if_pos rfl]
  rw [if_neg (show hashInput15 ≠ hashInput14 from by decide)]
  rw [if_pos rfl]
theorem hashChecked16 : fixtureHash ([100, 101, 108, 116, 97, 114, 101, 100, 117, 99, 101, 46, 48, 48, 52, 46, 109, 101, 114, 107, 108, 101, 45, 110, 111, 100, 101, 46, 118, 49, 0, 152, 42, 104, 49, 16, 216, 71, 246, 158, 110, 24, 82, 60, 3, 106, 102, 69, 251, 77, 163, 81, 27, 142, 88, 106, 64, 240, 223, 117, 10, 141, 237, 152, 42, 104, 49, 16, 216, 71, 246, 158, 110, 24, 82, 60, 3, 106, 102, 69, 251, 77, 163, 81, 27, 142, 88, 106, 64, 240, 223, 117, 10, 141, 237]) = hashOutput16 := by
  change fixtureHash hashInput16 = hashOutput16
  unfold fixtureHash
  rw [hashLength16]
  rw [if_neg (by decide : ¬ (95 = 376))]
  rw [if_neg (by decide : ¬ (95 = 674))]
  rw [if_neg (by decide : ¬ (95 = 1109))]
  rw [if_neg (by decide : ¬ (95 = 2226))]
  rw [if_neg (by decide : ¬ (95 = 8))]
  rw [if_neg (by decide : ¬ (95 = 979))]
  rw [if_neg (by decide : ¬ (95 = 16))]
  rw [if_neg (by decide : ¬ (95 = 991))]
  rw [if_neg (by decide : ¬ (95 = 992))]
  rw [if_neg (by decide : ¬ (95 = 993))]
  rw [if_pos rfl]
  rw [if_neg (show hashInput16 ≠ hashInput14 from by decide)]
  rw [if_neg (show hashInput16 ≠ hashInput15 from by decide)]
  rw [if_pos rfl]
theorem hashChecked17 : fixtureHash ([100, 101, 108, 116, 97, 114, 101, 100, 117, 99, 101, 46, 48, 48, 52, 46, 109, 101, 114, 107, 108, 101, 45, 110, 111, 100, 101, 46, 118, 49, 0, 111, 178, 191, 226, 223, 202, 250, 110, 22, 251, 82, 83, 98, 187, 25, 246, 11, 31, 223, 79, 0, 73, 117, 82, 117, 168, 67, 64, 79, 88, 66, 168, 176, 253, 162, 122, 206, 247, 129, 105, 40, 185, 49, 236, 191, 172, 179, 56, 72, 29, 181, 24, 97, 31, 214, 249, 139, 216, 251, 21, 154, 6, 86, 242]) = hashOutput17 := by
  change fixtureHash hashInput17 = hashOutput17
  unfold fixtureHash
  rw [hashLength17]
  rw [if_neg (by decide : ¬ (95 = 376))]
  rw [if_neg (by decide : ¬ (95 = 674))]
  rw [if_neg (by decide : ¬ (95 = 1109))]
  rw [if_neg (by decide : ¬ (95 = 2226))]
  rw [if_neg (by decide : ¬ (95 = 8))]
  rw [if_neg (by decide : ¬ (95 = 979))]
  rw [if_neg (by decide : ¬ (95 = 16))]
  rw [if_neg (by decide : ¬ (95 = 991))]
  rw [if_neg (by decide : ¬ (95 = 992))]
  rw [if_neg (by decide : ¬ (95 = 993))]
  rw [if_pos rfl]
  rw [if_neg (show hashInput17 ≠ hashInput14 from by decide)]
  rw [if_neg (show hashInput17 ≠ hashInput15 from by decide)]
  rw [if_neg (show hashInput17 ≠ hashInput16 from by decide)]
  rw [if_pos rfl]
theorem hashChecked18 : fixtureHash ([100, 101, 108, 116, 97, 114, 101, 100, 117, 99, 101, 46, 48, 48, 52, 46, 109, 101, 114, 107, 108, 101, 45, 110, 111, 100, 101, 46, 118, 49, 0, 20, 7, 220, 120, 149, 182, 111, 222, 172, 177, 25, 129, 211, 220, 203, 250, 228, 138, 192, 163, 137, 55, 154, 248, 163, 76, 246, 83, 123, 177, 170, 11, 20, 7, 220, 120, 149, 182, 111, 222, 172, 177, 25, 129, 211, 220, 203, 250, 228, 138, 192, 163, 137, 55, 154, 248, 163, 76, 246, 83, 123, 177, 170, 11]) = hashOutput18 := by
  change fixtureHash hashInput18 = hashOutput18
  unfold fixtureHash
  rw [hashLength18]
  rw [if_neg (by decide : ¬ (95 = 376))]
  rw [if_neg (by decide : ¬ (95 = 674))]
  rw [if_neg (by decide : ¬ (95 = 1109))]
  rw [if_neg (by decide : ¬ (95 = 2226))]
  rw [if_neg (by decide : ¬ (95 = 8))]
  rw [if_neg (by decide : ¬ (95 = 979))]
  rw [if_neg (by decide : ¬ (95 = 16))]
  rw [if_neg (by decide : ¬ (95 = 991))]
  rw [if_neg (by decide : ¬ (95 = 992))]
  rw [if_neg (by decide : ¬ (95 = 993))]
  rw [if_pos rfl]
  rw [if_neg (show hashInput18 ≠ hashInput14 from by decide)]
  rw [if_neg (show hashInput18 ≠ hashInput15 from by decide)]
  rw [if_neg (show hashInput18 ≠ hashInput16 from by decide)]
  rw [if_neg (show hashInput18 ≠ hashInput17 from by decide)]
  rw [if_pos rfl]
theorem hashChecked19 : fixtureHash ([100, 101, 108, 116, 97, 114, 101, 100, 117, 99, 101, 46, 48, 48, 52, 46, 109, 101, 114, 107, 108, 101, 45, 110, 111, 100, 101, 46, 118, 49, 0, 68, 105, 142, 135, 198, 149, 236, 182, 8, 146, 90, 199, 69, 212, 12, 255, 135, 28, 112, 237, 180, 238, 140, 61, 2, 28, 222, 249, 65, 186, 62, 133, 213, 218, 126, 108, 225, 110, 146, 196, 225, 163, 170, 23, 206, 166, 114, 42, 137, 139, 89, 14, 94, 134, 53, 157, 243, 27, 54, 188, 221, 73, 65, 79]) = hashOutput19 := by
  change fixtureHash hashInput19 = hashOutput19
  unfold fixtureHash
  rw [hashLength19]
  rw [if_neg (by decide : ¬ (95 = 376))]
  rw [if_neg (by decide : ¬ (95 = 674))]
  rw [if_neg (by decide : ¬ (95 = 1109))]
  rw [if_neg (by decide : ¬ (95 = 2226))]
  rw [if_neg (by decide : ¬ (95 = 8))]
  rw [if_neg (by decide : ¬ (95 = 979))]
  rw [if_neg (by decide : ¬ (95 = 16))]
  rw [if_neg (by decide : ¬ (95 = 991))]
  rw [if_neg (by decide : ¬ (95 = 992))]
  rw [if_neg (by decide : ¬ (95 = 993))]
  rw [if_pos rfl]
  rw [if_neg (show hashInput19 ≠ hashInput14 from by decide)]
  rw [if_neg (show hashInput19 ≠ hashInput15 from by decide)]
  rw [if_neg (show hashInput19 ≠ hashInput16 from by decide)]
  rw [if_neg (show hashInput19 ≠ hashInput17 from by decide)]
  rw [if_neg (show hashInput19 ≠ hashInput18 from by decide)]
  rw [if_pos rfl]
theorem pairChecked14 : NativeManifestMerkle.pair fixtureHash hashOutput5 hashOutput7 = some hashOutput14 :=
  NativeManifestMerkle.pairFromSource (da := [211, 30, 219, 120, 192, 250, 181, 117, 1, 92, 80, 133, 188, 109, 149, 73, 180, 108, 93, 128, 175, 160, 213, 27, 82, 151, 254, 206, 213, 161, 102, 123]) (db := [41, 18, 169, 69, 156, 55, 50, 155, 195, 199, 86, 30, 159, 236, 237, 115, 99, 31, 246, 250, 62, 222, 59, 167, 33, 79, 190, 242, 65, 42, 185, 76]) (by decide) (by decide) hashChecked14 (by decide)
theorem pairChecked15 : NativeManifestMerkle.pair fixtureHash hashOutput9 hashOutput11 = some hashOutput15 :=
  NativeManifestMerkle.pairFromSource (da := [55, 105, 181, 214, 190, 160, 38, 205, 45, 86, 73, 125, 249, 183, 225, 143, 219, 140, 202, 196, 253, 117, 253, 179, 46, 34, 220, 68, 203, 173, 176, 59]) (db := [184, 51, 104, 44, 89, 72, 240, 52, 42, 188, 225, 93, 162, 74, 217, 49, 182, 113, 18, 249, 163, 124, 192, 51, 225, 183, 140, 61, 229, 32, 194, 254]) (by decide) (by decide) hashChecked15 (by decide)
theorem pairChecked16 : NativeManifestMerkle.pair fixtureHash hashOutput13 hashOutput13 = some hashOutput16 :=
  NativeManifestMerkle.pairFromSource (da := [152, 42, 104, 49, 16, 216, 71, 246, 158, 110, 24, 82, 60, 3, 106, 102, 69, 251, 77, 163, 81, 27, 142, 88, 106, 64, 240, 223, 117, 10, 141, 237]) (db := [152, 42, 104, 49, 16, 216, 71, 246, 158, 110, 24, 82, 60, 3, 106, 102, 69, 251, 77, 163, 81, 27, 142, 88, 106, 64, 240, 223, 117, 10, 141, 237]) (by decide) (by decide) hashChecked16 (by decide)
theorem pairChecked17 : NativeManifestMerkle.pair fixtureHash hashOutput14 hashOutput15 = some hashOutput17 :=
  NativeManifestMerkle.pairFromSource (da := [111, 178, 191, 226, 223, 202, 250, 110, 22, 251, 82, 83, 98, 187, 25, 246, 11, 31, 223, 79, 0, 73, 117, 82, 117, 168, 67, 64, 79, 88, 66, 168]) (db := [176, 253, 162, 122, 206, 247, 129, 105, 40, 185, 49, 236, 191, 172, 179, 56, 72, 29, 181, 24, 97, 31, 214, 249, 139, 216, 251, 21, 154, 6, 86, 242]) (by decide) (by decide) hashChecked17 (by decide)
theorem pairChecked18 : NativeManifestMerkle.pair fixtureHash hashOutput16 hashOutput16 = some hashOutput18 :=
  NativeManifestMerkle.pairFromSource (da := [20, 7, 220, 120, 149, 182, 111, 222, 172, 177, 25, 129, 211, 220, 203, 250, 228, 138, 192, 163, 137, 55, 154, 248, 163, 76, 246, 83, 123, 177, 170, 11]) (db := [20, 7, 220, 120, 149, 182, 111, 222, 172, 177, 25, 129, 211, 220, 203, 250, 228, 138, 192, 163, 137, 55, 154, 248, 163, 76, 246, 83, 123, 177, 170, 11]) (by decide) (by decide) hashChecked18 (by decide)
theorem pairChecked19 : NativeManifestMerkle.pair fixtureHash hashOutput17 hashOutput18 = some hashOutput19 :=
  NativeManifestMerkle.pairFromSource (da := [68, 105, 142, 135, 198, 149, 236, 182, 8, 146, 90, 199, 69, 212, 12, 255, 135, 28, 112, 237, 180, 238, 140, 61, 2, 28, 222, 249, 65, 186, 62, 133]) (db := [213, 218, 126, 108, 225, 110, 146, 196, 225, 163, 170, 23, 206, 166, 114, 42, 137, 139, 89, 14, 94, 134, 53, 157, 243, 27, 54, 188, 221, 73, 65, 79]) (by decide) (by decide) hashChecked19 (by decide)
theorem levelChecked0 : NativeManifestMerkle.level fixtureHash [hashOutput5,hashOutput7,hashOutput9,hashOutput11,hashOutput13] = some [hashOutput14,hashOutput15,hashOutput16] := by
  simp only [NativeManifestMerkle.level,pairChecked14,pairChecked15,pairChecked16,Bind.bind,Option.bind,Option.map]
theorem levelChecked1 : NativeManifestMerkle.level fixtureHash [hashOutput14,hashOutput15,hashOutput16] = some [hashOutput17,hashOutput18] := by
  simp only [NativeManifestMerkle.level,pairChecked17,pairChecked18,Bind.bind,Option.bind,Option.map]
theorem levelChecked2 : NativeManifestMerkle.level fixtureHash [hashOutput17,hashOutput18] = some [hashOutput19] := by
  simp only [NativeManifestMerkle.level,pairChecked19,Bind.bind,Option.bind]
def planBound := NativeShardPlanVectors.bound
theorem boundPlan : NativeShardPlanBinding.bind fixtureHash NativeSchemaVectors.original
    NativeScaleVectors.original NativeShardPlanVectors.original = some planBound := by
  apply NativeShardPlanBinding.bindFromSource
  refine ⟨?_,NativeShardPlanVectors.decodedWire,NativeShardPlanVectors.interpretedPlan,
    NativeShardPlanVectors.computedPlan,?_⟩
  · apply NativeSchemaBinding.bindFromSource
    exact ⟨NativeSchemaVectors.decodedSchema,NativeScaleVectors.decodedTable,hashChecked0,by decide,by decide⟩
  · exact ⟨rfl,rfl,rfl,rfl,rfl,hashChecked1.symm,rfl,by decide⟩
theorem scaleQ0 : NativeScaleBinding.bind fixtureHash NativeScaleVectors.original
    NativeQBytesVectors.frame0 = some NativeScaleVectors.bound0 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined0,
    by decide,hashChecked1,rfl,rfl,rfl,by decide,by decide⟩
theorem leafLinks0 : LeafLinks fixtureHash planBound wire ref0
    NativeQBytesVectors.frame0 NativeScaleVectors.bound0 := by
  refine ⟨rfl,?_,by decide,by decide,by decide,hashChecked5⟩
  unfold expectedHeader
  rw [hashChecked4]
  rfl
theorem scaleQ1 : NativeScaleBinding.bind fixtureHash NativeScaleVectors.original
    NativeQBytesVectors.frame1 = some NativeScaleVectors.bound1 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined1,
    by decide,hashChecked1,rfl,rfl,rfl,by decide,by decide⟩
theorem leafLinks1 : LeafLinks fixtureHash planBound wire ref1
    NativeQBytesVectors.frame1 NativeScaleVectors.bound1 := by
  refine ⟨rfl,?_,by decide,by decide,by decide,hashChecked7⟩
  unfold expectedHeader
  rw [hashChecked6]
  rfl
theorem scaleQ2 : NativeScaleBinding.bind fixtureHash NativeScaleVectors.original
    NativeQBytesVectors.frame2 = some NativeScaleVectors.bound2 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined2,
    by decide,hashChecked1,rfl,rfl,rfl,by decide,by decide⟩
theorem leafLinks2 : LeafLinks fixtureHash planBound wire ref2
    NativeQBytesVectors.frame2 NativeScaleVectors.bound2 := by
  refine ⟨rfl,?_,by decide,by decide,by decide,hashChecked9⟩
  unfold expectedHeader
  rw [hashChecked8]
  rfl
theorem scaleQ3 : NativeScaleBinding.bind fixtureHash NativeScaleVectors.original
    NativeQBytesVectors.frame3 = some NativeScaleVectors.bound3 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined3,
    by decide,hashChecked1,rfl,rfl,rfl,by decide,by decide⟩
theorem leafLinks3 : LeafLinks fixtureHash planBound wire ref3
    NativeQBytesVectors.frame3 NativeScaleVectors.bound3 := by
  refine ⟨rfl,?_,by decide,by decide,by decide,hashChecked11⟩
  unfold expectedHeader
  rw [hashChecked10]
  rfl
theorem scaleQ4 : NativeScaleBinding.bind fixtureHash NativeScaleVectors.original
    NativeQBytesVectors.frame4 = some NativeScaleVectors.bound4 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined4,
    by decide,hashChecked1,rfl,rfl,rfl,by decide,by decide⟩
theorem leafLinks4 : LeafLinks fixtureHash planBound wire ref4
    NativeQBytesVectors.frame4 NativeScaleVectors.bound4 := by
  refine ⟨rfl,?_,by decide,by decide,by decide,hashChecked13⟩
  unfold expectedHeader
  rw [hashChecked12]
  rfl
def raws : List Bytes := [NativeQBytesVectors.frame0,NativeQBytesVectors.frame1,NativeQBytesVectors.frame2,NativeQBytesVectors.frame3,NativeQBytesVectors.frame4]
def blocks : List NativeScaleBinding.Bound := [NativeScaleVectors.bound0,NativeScaleVectors.bound1,NativeScaleVectors.bound2,NativeScaleVectors.bound3,NativeScaleVectors.bound4]
theorem corpusChecked : corpus fixtureHash NativeScaleVectors.original planBound wire manifest.refs raws = some blocks := by
  apply corpusFromSource
  exact .cons scaleQ0 leafLinks0 (.cons scaleQ1 leafLinks1 (.cons scaleQ2 leafLinks2 (.cons scaleQ3 leafLinks3 (.cons scaleQ4 leafLinks4 (.nil)))))
theorem manifestLinks : Links fixtureHash NativeShardPlanVectors.original planBound manifest := by
  refine ⟨rfl,rfl,rfl,rfl,rfl,rfl,hashChecked2.symm,?_⟩
  decide
theorem rootChecked : NativeManifestMerkle.root fixtureHash (manifest.refs.map (fun r => r.wire.leaf)) = some wire.root := by
  unfold NativeManifestMerkle.root
  rw [if_pos (by decide)]
  change NativeManifestMerkle.tree fixtureHash 13 [hashOutput5,hashOutput7,hashOutput9,hashOutput11,hashOutput13] = some wire.root
  rw [NativeManifestMerkle.tree,levelChecked0]
  dsimp only [Bind.bind,Option.bind]
  rw [NativeManifestMerkle.tree,levelChecked1]
  dsimp only [Bind.bind,Option.bind]
  rw [NativeManifestMerkle.tree,levelChecked2]
  dsimp only [Bind.bind,Option.bind]
  rw [NativeManifestMerkle.tree,if_pos (by decide)]
  rfl
def bound : Bound := ⟨planBound,manifest,blocks⟩
theorem wholeManifest : bind fixtureHash NativeSchemaVectors.original NativeScaleVectors.original
    NativeShardPlanVectors.original original hashOutput3 raws = some bound :=
  bindFromSource ⟨boundPlan,decodedWire,interpretedManifest,manifestLinks,
    ⟨by decide,hashChecked3⟩,corpusChecked,rootChecked⟩
theorem exactCompleteSizes : manifest.envelopes = (raws.map List.length).sum ∧
    manifest.payloads = (blocks.map (fun q => q.block.frame.payload.length)).sum ∧
    manifest.total = (blocks.map (fun q => q.block.frame.values.length)).sum := exactTotals wholeManifest
theorem emptyManifest : NativeManifestBytes.decode [] = none := by decide
theorem trailingComma : NativeManifestBytes.readRefs (ascii ",]") = none := by decide
theorem emptyTree : NativeManifestMerkle.root fixtureHash [] = none := by decide
theorem fuelExhausted : NativeManifestMerkle.tree fixtureHash 0 [wire.root] = none := by decide
theorem singletonTree : NativeManifestMerkle.root (fun _ => []) [wire.root] = some wire.root := by decide
theorem rawDigestLength : (NativeManifestMerkle.digest hashOutput5).map List.length = some 32 := by decide
theorem oddHex : NativeManifestMerkle.unhex (ascii "a") = none := by decide
theorem upperHex : NativeManifestMerkle.unhex (ascii "AA") = none := by decide
theorem invalidHashOutput : NativeManifestMerkle.pair (fun _ => []) hashOutput5 hashOutput7 = none := by decide
theorem wrongEnvelope : ¬ LeafLinks fixtureHash planBound wire {ref0 with envelope := 950} NativeQBytesVectors.frame0 NativeScaleVectors.bound0 := by
  intro h
  rcases h with ⟨_,_,_,_,bad,_⟩
  revert bad; decide
theorem wrongTicket : ¬ LeafLinks fixtureHash planBound {wire with ticket := ascii "wrong"} ref0 NativeQBytesVectors.frame0 NativeScaleVectors.bound0 := by
  intro h
  rcases h with ⟨_,bad,_,_,_,_⟩
  have mismatch := congrArg NativeQHeader.Wire.ticket bad
  revert mismatch; decide
theorem wrongProof : ¬ LeafLinks fixtureHash planBound {wire with proof := wire.config} ref0 NativeQBytesVectors.frame0 NativeScaleVectors.bound0 := by
  intro h
  rcases h with ⟨_,bad,_,_,_,_⟩
  have mismatch := congrArg NativeQHeader.Wire.proof bad
  revert mismatch; decide
theorem wrongConfig : ¬ LeafLinks fixtureHash planBound {wire with config := wire.proof} ref0 NativeQBytesVectors.frame0 NativeScaleVectors.bound0 := by
  intro h
  rcases h with ⟨_,bad,_,_,_,_⟩
  have mismatch := congrArg NativeQHeader.Wire.config bad
  revert mismatch; decide
theorem wrongLeaf : ¬ LeafLinks fixtureHash planBound wire {ref0 with wire := {refWire0 with leaf := wire.root}} NativeQBytesVectors.frame0 NativeScaleVectors.bound0 := by
  intro h
  rcases h with ⟨_,_,_,_,_,bad⟩
  rw [hashChecked5] at bad
  revert bad; decide
theorem wrongCount : ¬ LeafLinks fixtureHash planBound wire {ref0 with entry := {ref0.entry with count := 5}} NativeQBytesVectors.frame0 NativeScaleVectors.bound0 := by
  intro h
  rcases h with ⟨_,_,bad,_,_,_⟩
  revert bad; decide
theorem missingRef : ¬ Links fixtureHash NativeShardPlanVectors.original planBound {manifest with refs := manifest.refs.drop 1} := by
  intro h
  rcases h with ⟨_,_,_,_,_,_,_,_,_,_,_,_,bad,_,_,_,_,_⟩
  revert bad; decide
theorem extraRef : ¬ Links fixtureHash NativeShardPlanVectors.original planBound {manifest with refs := manifest.refs ++ [ref0]} := by
  intro h
  rcases h with ⟨_,_,_,_,_,_,_,_,_,_,_,_,bad,_,_,_,_,_⟩
  revert bad; decide
theorem reorderedRefs : ¬ Links fixtureHash NativeShardPlanVectors.original planBound {manifest with refs := manifest.refs.reverse} := by
  intro h
  rcases h with ⟨_,_,_,_,_,_,_,_,_,_,_,_,bad,_,_,_,_,_⟩
  revert bad; decide
theorem wrongByteTotal : ¬ Links fixtureHash NativeShardPlanVectors.original planBound {manifest with envelopes := 4799} := by
  intro h
  rcases h with ⟨_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,bad⟩
  revert bad; decide
theorem wrongPayloadTotal : ¬ Links fixtureHash NativeShardPlanVectors.original planBound {manifest with payloads := 73} := by
  intro h
  rcases h with ⟨_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,bad,_,_⟩
  revert bad; decide
theorem wrongElementTotal : ¬ Links fixtureHash NativeShardPlanVectors.original planBound {manifest with total := 35} := by
  intro h
  rcases h with ⟨_,_,_,_,_,_,_,_,_,_,_,_,_,_,bad,_,_,_⟩
  revert bad; decide
theorem zeroAggregation : ¬ Links fixtureHash NativeShardPlanVectors.original planBound {manifest with steps := 0} := by
  intro h
  rcases h with ⟨_,_,_,_,_,_,_,_,_,_,bad,_,_,_,_,_,_,_⟩
  revert bad; decide
theorem wideAggregation : ¬ Links fixtureHash NativeShardPlanVectors.original planBound {manifest with steps := 2^32} := by
  intro h
  rcases h with ⟨_,_,_,_,_,_,_,_,_,_,_,bad,_,_,_,_,_,_⟩
  revert bad; decide
theorem missingCorpusTail : corpus fixtureHash [] planBound wire [ref0] [] = none := by decide
theorem extraCorpusTail : corpus fixtureHash [] planBound wire [] [[]] = none := by decide
end DeltaReduce.NativeManifestVectors
