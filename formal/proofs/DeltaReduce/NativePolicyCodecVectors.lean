import DeltaReduce.NativePolicyBytes

/-! Small mathematical codec examples; no native startup authority. -/
namespace DeltaReduce.NativePolicyCodecVectors
open NativePolicyCodec NativePolicySchema NativePolicyBytes NativeReceiptBytes
set_option maxRecDepth 10000
set_option maxHeartbeats 1000000

def tree : Value := .pair (.text []) (.pair (.text []) (.pair (.items [(.text [])]) (.pair (.number 1) (.pair (.text []) (.pair (.text []) (.pair (.text [72,65,82,68,95,68,69,65,68,76,73,78,69]) (.pair (.number 0) (.pair (.number 0) (.pair (.number 0) (.pair (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.pair (.items []) (.end)))))))))))))))))))))))))))))))))) (.pair (.items [(.pair (.number 1) (.pair (.text []) (.pair (.text []) (.pair (.number 0) (.pair (.number 0) (.pair (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.end)))))))))))))))) (.end)))))))]) (.end))))))))))))
def body : Bytes := [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,13,72,65,82,68,95,68,69,65,68,76,73,78,69,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
theorem exactEncoding : NativePolicyCodec.encode fmtPolicy tree = some body := by decide
theorem fullTreeInverse : NativePolicyCodec.decode fmtPolicy body = some tree :=
  NativePolicyCodec.encoded exactEncoding
theorem completeMinimalRead : (decodePolicy (NativePolicyBytes.header ++ body)).isSome = true := by decide
theorem emptyFrame : (decodePolicy []).isNone = true := by decide
theorem truncatedFrame : (decodePolicy ((NativePolicyBytes.header ++ body).take 32)).isNone = true := by decide
theorem trailingFrame : (decodePolicy (NativePolicyBytes.header ++ body ++ [0])).isNone = true := by decide
theorem wrongHeader : (decodePolicy ([0] ++ (NativePolicyBytes.header ++ body).drop 1)).isNone = true := by decide
theorem signedMinimum : signed64 (2^63) = -(2^63 : Int) := by decide
theorem signedMaximum : signed64 (2^63-1) = (2^63-1 : Int) := by decide
theorem signedMinusOne : signed64 (2^64-1) = -1 := by decide
theorem nonBoolean : (parse .boolean [2]).isNone = true := by decide
theorem asciiControl : (parse .text [0,0,0,1,31]).isNone = true := by decide
theorem asciiHigh : (parse .text [0,0,0,1,128]).isNone = true := by decide
theorem textTooLong : (parse .text [0,0,16,1]).isNone = true := by decide
theorem vectorTooLong : (parse (.vector 2 .boolean) [0,0,0,3,0,0,0]).isNone = true := by decide
theorem uintOverflow : (NativePolicyCodec.encode (.uint 4) (.number (2^32))).isNone = true := by decide
theorem uintMax : parse (.uint 8) [255,255,255,255,255,255,255,255] = some (.number (2^64-1),[]) := by rfl
theorem duplicatesRetained : parse (.vector 100000 .text) [0,0,0,2,0,0,0,1,97,0,0,0,1,97] = some (.items [.text [97],.text [97]],[]) := by rfl
theorem reverseOrderRetained : parse (.vector 100000 .text) [0,0,0,2,0,0,0,1,122,0,0,0,1,97] = some (.items [.text [122],.text [97]],[]) := by rfl
theorem rationalZeroRetained : (NativePolicyCodec.decode fmtRational (be 8 0 ++ be 8 0)).isSome = true := by decide
theorem asciiLexPrefix : bytesLT [97] [97,98] = true := by decide
theorem asciiLexReverse : bytesLT [122] [97] = false := by decide
theorem emptyValidators : strictly bytesLT ([] : List Bytes) = true := by decide
theorem duplicateValidators : strictly bytesLT [[97],[97]] = false := by decide
theorem invalidReason : ascii "NO_ABORT" ∉ reasons := by decide
theorem wrongRole : (decodePolicy [68,86,80,79,76,48,48,49,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,13,72,65,82,68,95,68,69,65,68,76,73,78,69,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]).isSome = false := by decide
theorem noValidators : (decodePolicy [68,86,80,79,76,48,48,49,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,13,72,65,82,68,95,68,69,65,68,76,73,78,69,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]).isSome = false := by decide
theorem noCandidates : (decodePolicy [68,86,80,79,76,48,48,49,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,13,72,65,82,68,95,68,69,65,68,76,73,78,69,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]).isSome = false := by decide
theorem wrongAction : (decodePolicy [68,86,80,79,76,48,48,49,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,13,72,65,82,68,95,68,69,65,68,76,73,78,69,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,10,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]).isSome = false := by decide
theorem unorderedDeadlineStillParses : (decodePolicy [68,86,80,79,76,48,48,49,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,13,72,65,82,68,95,68,69,65,68,76,73,78,69,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,10,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]).isSome = true := by decide
end DeltaReduce.NativePolicyCodecVectors
