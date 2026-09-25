import DeltaReduce.NativeVoteBytes
import DeltaReduce.NativeReceiptVectors

/-! Finite native codec/hash samples; no admission or general SHA proof. -/
set_option maxRecDepth 8192
set_option maxHeartbeats 1000000
namespace DeltaReduce.NativeVoteCodecVectors
open NativeReceiptBytes NativeVoteBytes

theorem encodedText0 : textBytes (ascii "0") = [33,0,0,0,1,48] := by decide
theorem encodedText1 : textBytes (ascii "1") = [33,0,0,0,1,49] := by decide
theorem encodedText2 : textBytes (ascii "1.0.0") = [33,0,0,0,5,49,46,48,46,48] := by decide
theorem encodedText3 : textBytes (ascii "ABORT") = [33,0,0,0,5,65,66,79,82,84] := by decide
theorem encodedText4 : textBytes (ascii "AGGREGATE_ROOT") = [33,0,0,0,14,65,71,71,82,69,71,65,84,69,95,82,79,79,84] := by decide
theorem encodedText5 : textBytes (ascii "APC") = [33,0,0,0,3,65,80,67] := by decide
theorem encodedText6 : textBytes (ascii "APPLY") = [33,0,0,0,5,65,80,80,76,89] := by decide
theorem encodedText7 : textBytes (ascii "EC") = [33,0,0,0,2,69,67] := by decide
theorem encodedText8 : textBytes (ascii "ISC") = [33,0,0,0,3,73,83,67] := by decide
theorem encodedText9 : textBytes (ascii "PARAMETER") = [33,0,0,0,9,80,65,82,65,77,69,84,69,82] := by decide
theorem encodedText10 : textBytes (ascii "PARAMETER:domain-a:shard-a") = [33,0,0,0,26,80,65,82,65,77,69,84,69,82,58,100,111,109,97,105,110,45,97,58,115,104,97,114,100,45,97] := by decide
theorem encodedText11 : textBytes (ascii "ROUND_CONFIG") = [33,0,0,0,12,82,79,85,78,68,95,67,79,78,70,73,71] := by decide
theorem encodedText12 : textBytes (ascii "VIEW_CHANGE") = [33,0,0,0,11,86,73,69,87,95,67,72,65,78,71,69] := by decide
theorem encodedText13 : textBytes (ascii "VOTE") = [33,0,0,0,4,86,79,84,69] := by decide
theorem encodedText14 : textBytes (ascii "body_hash") = [33,0,0,0,9,98,111,100,121,95,104,97,115,104] := by decide
theorem encodedText15 : textBytes (ascii "context_id") = [33,0,0,0,10,99,111,110,116,101,120,116,95,105,100] := by decide
theorem encodedText16 : textBytes (ascii "durable_sequence") = [33,0,0,0,16,100,117,114,97,98,108,101,95,115,101,113,117,101,110,99,101] := by decide
theorem encodedText17 : textBytes (ascii "formal_semantics_id") = [33,0,0,0,19,102,111,114,109,97,108,95,115,101,109,97,110,116,105,99,115,95,105,100] := by decide
theorem encodedText18 : textBytes (ascii "height") = [33,0,0,0,6,104,101,105,103,104,116] := by decide
theorem encodedText19 : textBytes (ascii "kind") = [33,0,0,0,4,107,105,110,100] := by decide
theorem encodedText20 : textBytes (ascii "round-vote-fixture") = [33,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45,102,105,120,116,117,114,101] := by decide
theorem encodedText21 : textBytes (ascii "round_id") = [33,0,0,0,8,114,111,117,110,100,95,105,100] := by decide
theorem encodedText22 : textBytes (ascii "schema_version") = [33,0,0,0,14,115,99,104,101,109,97,95,118,101,114,115,105,111,110] := by decide
theorem encodedText23 : textBytes (ascii "sha256:08edbd495b3369f06d7d46dec477899485859ee01e58789eea42e61532a0cca1") = [33,0,0,0,71,115,104,97,50,53,54,58,48,56,101,100,98,100,52,57,53,98,51,51,54,57,102,48,54,100,55,100,52,54,100,101,99,52,55,55,56,57,57,52,56,53,56,53,57,101,101,48,49,101,53,56,55,56,57,101,101,97,52,50,101,54,49,53,51,50,97,48,99,99,97,49] := by decide
theorem encodedText24 : textBytes (ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111") = [33,0,0,0,71,115,104,97,50,53,54,58,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49] := by decide
theorem encodedText25 : textBytes (ascii "sha256:25237c1323fbdae5feb16e5a60dfe9a12fb8881ed907b070adb8425c8a36ab9b") = [33,0,0,0,71,115,104,97,50,53,54,58,50,53,50,51,55,99,49,51,50,51,102,98,100,97,101,53,102,101,98,49,54,101,53,97,54,48,100,102,101,57,97,49,50,102,98,56,56,56,49,101,100,57,48,55,98,48,55,48,97,100,98,56,52,50,53,99,56,97,51,54,97,98,57,98] := by decide
theorem encodedText26 : textBytes (ascii "sha256:2bf5029d5500241ca9a548b5858bb142066512f4f1e3976e09c27b7e962ca01f") = [33,0,0,0,71,115,104,97,50,53,54,58,50,98,102,53,48,50,57,100,53,53,48,48,50,52,49,99,97,57,97,53,52,56,98,53,56,53,56,98,98,49,52,50,48,54,54,53,49,50,102,52,102,49,101,51,57,55,54,101,48,57,99,50,55,98,55,101,57,54,50,99,97,48,49,102] := by decide
theorem encodedText27 : textBytes (ascii "sha256:2ea13643cbd3d3ed7b0d860dc5c86c9cbfd945a0645de325ebd7a4f47da6b759") = [33,0,0,0,71,115,104,97,50,53,54,58,50,101,97,49,51,54,52,51,99,98,100,51,100,51,101,100,55,98,48,100,56,54,48,100,99,53,99,56,54,99,57,99,98,102,100,57,52,53,97,48,54,52,53,100,101,51,50,53,101,98,100,55,97,52,102,52,55,100,97,54,98,55,53,57] := by decide
theorem encodedText28 : textBytes (ascii "sha256:33e327fe50bd52a92e0675c846fe2ee53671dde65350152380c82a99af21c27d") = [33,0,0,0,71,115,104,97,50,53,54,58,51,51,101,51,50,55,102,101,53,48,98,100,53,50,97,57,50,101,48,54,55,53,99,56,52,54,102,101,50,101,101,53,51,54,55,49,100,100,101,54,53,51,53,48,49,53,50,51,56,48,99,56,50,97,57,57,97,102,50,49,99,50,55,100] := by decide
theorem encodedText29 : textBytes (ascii "sha256:4580349215fc6b84d64fdf994c47283b08dbfa850927c8eb106a59fae9c812e2") = [33,0,0,0,71,115,104,97,50,53,54,58,52,53,56,48,51,52,57,50,49,53,102,99,54,98,56,52,100,54,52,102,100,102,57,57,52,99,52,55,50,56,51,98,48,56,100,98,102,97,56,53,48,57,50,55,99,56,101,98,49,48,54,97,53,57,102,97,101,57,99,56,49,50,101,50] := by decide
theorem encodedText30 : textBytes (ascii "sha256:5643f922e7810932c510057601fc59edf4817446d7fdce192abf6f86d93ef6e1") = [33,0,0,0,71,115,104,97,50,53,54,58,53,54,52,51,102,57,50,50,101,55,56,49,48,57,51,50,99,53,49,48,48,53,55,54,48,49,102,99,53,57,101,100,102,52,56,49,55,52,52,54,100,55,102,100,99,101,49,57,50,97,98,102,54,102,56,54,100,57,51,101,102,54,101,49] := by decide
theorem encodedText31 : textBytes (ascii "sha256:60d1e04e0f0a691d726f1ab0ca93f15c22c1757162a4b6e960ff4586ca4dd20b") = [33,0,0,0,71,115,104,97,50,53,54,58,54,48,100,49,101,48,52,101,48,102,48,97,54,57,49,100,55,50,54,102,49,97,98,48,99,97,57,51,102,49,53,99,50,50,99,49,55,53,55,49,54,50,97,52,98,54,101,57,54,48,102,102,52,53,56,54,99,97,52,100,100,50,48,98] := by decide
theorem encodedText32 : textBytes (ascii "sha256:64a104b7f8c820b6b3c48950af74c115f4d94787f7e5132950402a6adcd41645") = [33,0,0,0,71,115,104,97,50,53,54,58,54,52,97,49,48,52,98,55,102,56,99,56,50,48,98,54,98,51,99,52,56,57,53,48,97,102,55,52,99,49,49,53,102,52,100,57,52,55,56,55,102,55,101,53,49,51,50,57,53,48,52,48,50,97,54,97,100,99,100,52,49,54,52,53] := by decide
theorem encodedText33 : textBytes (ascii "sha256:67c4e17a75fc0998471b408dbe094b30aa2a238d23bc008099159268b4b63978") = [33,0,0,0,71,115,104,97,50,53,54,58,54,55,99,52,101,49,55,97,55,53,102,99,48,57,57,56,52,55,49,98,52,48,56,100,98,101,48,57,52,98,51,48,97,97,50,97,50,51,56,100,50,51,98,99,48,48,56,48,57,57,49,53,57,50,54,56,98,52,98,54,51,57,55,56] := by decide
theorem encodedText34 : textBytes (ascii "sha256:7a21a3c4a2488f093311911563224fff2abf52557342bd33e4f469731c92d4e1") = [33,0,0,0,71,115,104,97,50,53,54,58,55,97,50,49,97,51,99,52,97,50,52,56,56,102,48,57,51,51,49,49,57,49,49,53,54,51,50,50,52,102,102,102,50,97,98,102,53,50,53,53,55,51,52,50,98,100,51,51,101,52,102,52,54,57,55,51,49,99,57,50,100,52,101,49] := by decide
theorem encodedText35 : textBytes (ascii "sha256:7ae0b29609cc29c5be6fe78dd0d9201c065f1dc40074cd7a8ea73a8ee3c4b95f") = [33,0,0,0,71,115,104,97,50,53,54,58,55,97,101,48,98,50,57,54,48,57,99,99,50,57,99,53,98,101,54,102,101,55,56,100,100,48,100,57,50,48,49,99,48,54,53,102,49,100,99,52,48,48,55,52,99,100,55,97,56,101,97,55,51,97,56,101,101,51,99,52,98,57,53,102] := by decide
theorem encodedText36 : textBytes (ascii "sha256:7ccc5fd880d6ab0d4cb21d1e114d10995e1757b8372ef7547feefaa6d417edb2") = [33,0,0,0,71,115,104,97,50,53,54,58,55,99,99,99,53,102,100,56,56,48,100,54,97,98,48,100,52,99,98,50,49,100,49,101,49,49,52,100,49,48,57,57,53,101,49,55,53,55,98,56,51,55,50,101,102,55,53,52,55,102,101,101,102,97,97,54,100,52,49,55,101,100,98,50] := by decide
theorem encodedText37 : textBytes (ascii "sha256:c5ec7f38bf6e199fd9d676f6e1b4a734624bc219a486c110fa5410f8f8fc2d28") = [33,0,0,0,71,115,104,97,50,53,54,58,99,53,101,99,55,102,51,56,98,102,54,101,49,57,57,102,100,57,100,54,55,54,102,54,101,49,98,52,97,55,51,52,54,50,52,98,99,50,49,57,97,52,56,54,99,49,49,48,102,97,53,52,49,48,102,56,102,56,102,99,50,100,50,56] := by decide
theorem encodedText38 : textBytes (ascii "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6") = [33,0,0,0,71,115,104,97,50,53,54,58,99,99,57,56,102,49,53,97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54,48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54] := by decide
theorem encodedText39 : textBytes (ascii "sha256:d9ba7cfbab18c0cc638bfff75cafeda604e9e81c71f1b698f6538cb6846bfdff") = [33,0,0,0,71,115,104,97,50,53,54,58,100,57,98,97,55,99,102,98,97,98,49,56,99,48,99,99,54,51,56,98,102,102,102,55,53,99,97,102,101,100,97,54,48,52,101,57,101,56,49,99,55,49,102,49,98,54,57,56,102,54,53,51,56,99,98,54,56,52,54,98,102,100,102,102] := by decide
theorem encodedText40 : textBytes (ascii "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd") = [33,0,0,0,71,115,104,97,50,53,54,58,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100] := by decide
theorem encodedText41 : textBytes (ascii "sha256:ee4385720a99be17cc6352b2cecbbb16bc33a45f86e3cea872cc8e6334af9bf9") = [33,0,0,0,71,115,104,97,50,53,54,58,101,101,52,51,56,53,55,50,48,97,57,57,98,101,49,55,99,99,54,51,53,50,98,50,99,101,99,98,98,98,49,54,98,99,51,51,97,52,53,102,56,54,101,51,99,101,97,56,55,50,99,99,56,101,54,51,51,52,97,102,57,98,102,57] := by decide
theorem encodedText42 : textBytes (ascii "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee") = [33,0,0,0,71,115,104,97,50,53,54,58,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101] := by decide
theorem encodedText43 : textBytes (ascii "signature_id") = [33,0,0,0,12,115,105,103,110,97,116,117,114,101,95,105,100] := by decide
theorem encodedText44 : textBytes (ascii "type_name") = [33,0,0,0,9,116,121,112,101,95,110,97,109,101] := by decide
theorem encodedText45 : textBytes (ascii "validator-1") = [33,0,0,0,11,118,97,108,105,100,97,116,111,114,45,49] := by decide
theorem encodedText46 : textBytes (ascii "validator_epoch_id") = [33,0,0,0,18,118,97,108,105,100,97,116,111,114,95,101,112,111,99,104,95,105,100] := by decide
theorem encodedText47 : textBytes (ascii "validator_id") = [33,0,0,0,12,118,97,108,105,100,97,116,111,114,95,105,100] := by decide
theorem encodedText48 : textBytes (ascii "view") = [33,0,0,0,4,118,105,101,119] := by decide
def wire1 : WireVote := ⟨ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111", ascii "sha256:5643f922e7810932c510057601fc59edf4817446d7fdce192abf6f86d93ef6e1", ascii "1", ascii "1", ascii "ROUND_CONFIG", ascii "round-vote-fixture", ascii "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", ascii "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd", ascii "validator-1", ascii "0"⟩
def vote1 : Vote := ⟨wire1, 1, 1, 0⟩
theorem payloadBytes1 : payload wire1 = [49,0,0,0,13,33,0,0,0,9,98,111,100,121,95,104,97,115,104,33,0,0,0,71,115,104,97,50,53,54,58,49] ++ [49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49] ++ [49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,33] ++ [0,0,0,10,99,111,110,116,101,120,116,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,53,54,52,51,102,57] ++ [50,50,101,55,56,49,48,57,51,50,99,53,49,48,48,53,55,54,48,49,102,99,53,57,101,100,102,52,56,49,55,52] ++ [52,54,100,55,102,100,99,101,49,57,50,97,98,102,54,102,56,54,100,57,51,101,102,54,101,49,33,0,0,0,16,100] ++ [117,114,97,98,108,101,95,115,101,113,117,101,110,99,101,33,0,0,0,1,49,33,0,0,0,19,102,111,114,109,97,108] ++ [95,115,101,109,97,110,116,105,99,115,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,99,99,57,56,102,49,53] ++ [97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54] ++ [48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54,33,0,0,0,6,104,101] ++ [105,103,104,116,33,0,0,0,1,49,33,0,0,0,4,107,105,110,100,33,0,0,0,12,82,79,85,78,68,95,67,79] ++ [78,70,73,71,33,0,0,0,8,114,111,117,110,100,95,105,100,33,0,0,0,18,114,111,117,110,100,45,118,111,116,101] ++ [45,102,105,120,116,117,114,101,33,0,0,0,14,115,99,104,101,109,97,95,118,101,114,115,105,111,110,33,0,0,0,5] ++ [49,46,48,46,48,33,0,0,0,12,115,105,103,110,97,116,117,114,101,95,105,100,33,0,0,0,71,115,104,97,50,53] ++ [54,58,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101] ++ [101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101] ++ [101,101,33,0,0,0,9,116,121,112,101,95,110,97,109,101,33,0,0,0,4,86,79,84,69,33,0,0,0,18,118,97] ++ [108,105,100,97,116,111,114,95,101,112,111,99,104,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,100,100,100,100] ++ [100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100] ++ [100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,33,0,0,0] ++ [12,118,97,108,105,100,97,116,111,114,95,105,100,33,0,0,0,11,118,97,108,105,100,97,116,111,114,45,49,33,0,0] ++ [0,4,118,105,101,119,33,0,0,0,1,48] := by
  simp only [payload, fields, wire1, encodeFields, nativeSemantics, encodedText0, encodedText1, encodedText2, encodedText11, encodedText13, encodedText14, encodedText15, encodedText16, encodedText17, encodedText18, encodedText19, encodedText20, encodedText21, encodedText22, encodedText24, encodedText30, encodedText38, encodedText40, encodedText42, encodedText43, encodedText44, encodedText45, encodedText46, encodedText47, encodedText48]
  rfl
theorem nativeFrame1 : encodeFrame wire1 = NativeReceiptVectors.frame1 := by
  unfold encodeFrame; rw [payloadBytes1]; rfl
theorem frameValid1 : FrameValid wire1 := by
  constructor; · decide
  rw [nativeFrame1]; decide
theorem valid1 : VoteValid vote1 := by
  exact ⟨frameValid1, by decide, by decide, by decide, by decide, by decide⟩
theorem parsed1 : decodeFrame NativeReceiptVectors.frame1 = some vote1 := by
  exact decodeFrameFromEncoding vote1 NativeReceiptVectors.frame1 valid1 nativeFrame1
def fixtureSHA1 (b : Bytes) : Bytes := if b = votePreimage NativeReceiptVectors.frame1 then [92,85,47,180,84,17,56,73,225,110,221,170,218,123,202,75,58,167,252,122,210,146,238,62,161,48,174,87,8,141,142,34] else []
theorem hashBinding1 : voteId fixtureSHA1 NativeReceiptVectors.frame1 = some NativeReceiptVectors.receipt1.voteId := by
  simp only [voteId, fixtureSHA1, ↓reduceIte]; rfl
theorem linked1 : ReceiptLinked fixtureSHA1 NativeReceiptVectors.receipt1 vote1 := by
  exact ⟨rfl, rfl, rfl, hashBinding1⟩
theorem bound1 : bindReceipt fixtureSHA1 NativeReceiptVectors.receipt1 = some vote1 :=
  bindingFromComponents fixtureSHA1 NativeReceiptVectors.receipt1 vote1 parsed1 linked1
theorem fullReceipt1 : decodeReceipt fixtureSHA1 NativeReceiptVectors.nativeBytes1 = some (NativeReceiptVectors.receipt1,vote1) := by
  exact receiptFromNativeBytes fixtureSHA1 NativeReceiptVectors.receipt1 vote1 NativeReceiptVectors.nativeBytes1 NativeReceiptVectors.valid1 bound1 NativeReceiptVectors.exactBytes1
theorem sequenceMismatch1 : bindReceipt fixtureSHA1 {NativeReceiptVectors.receipt1 with sequence := 0} = none := by
  apply bindingRejectsMismatch fixtureSHA1 {NativeReceiptVectors.receipt1 with sequence := 0} vote1 parsed1
  intro h; have : (0:Nat) = 1 := h.1; contradiction
theorem contextMismatch1 : bindReceipt fixtureSHA1 {NativeReceiptVectors.receipt1 with context := []} = none := by
  apply bindingRejectsMismatch fixtureSHA1 {NativeReceiptVectors.receipt1 with context := []} vote1 parsed1
  intro h; have wrong := h.2.1
  have different : ([]:Bytes) ≠ vote1.wire.context := by decide
  exact different wrong
theorem actionMismatch1 : bindReceipt fixtureSHA1 {NativeReceiptVectors.receipt1 with action := 0} = none := by
  apply bindingRejectsMismatch fixtureSHA1 {NativeReceiptVectors.receipt1 with action := 0} vote1 parsed1
  intro h; have wrong := h.2.2.1
  have different : actionName 0 ≠ vote1.wire.kind := by decide
  exact different wrong
theorem idMismatch1 : bindReceipt fixtureSHA1 {NativeReceiptVectors.receipt1 with voteId := []} = none := by
  apply bindingRejectsMismatch fixtureSHA1 {NativeReceiptVectors.receipt1 with voteId := []} vote1 parsed1
  intro h; have wrong := h.2.2.2
  change voteId fixtureSHA1 NativeReceiptVectors.frame1 = some [] at wrong
  rw [hashBinding1] at wrong
  have different : NativeReceiptVectors.receipt1.voteId ≠ [] := by decide
  exact different (Option.some.inj wrong)

def wire2 : WireVote := ⟨ascii "sha256:33e327fe50bd52a92e0675c846fe2ee53671dde65350152380c82a99af21c27d", ascii "sha256:60d1e04e0f0a691d726f1ab0ca93f15c22c1757162a4b6e960ff4586ca4dd20b", ascii "1", ascii "1", ascii "ISC", ascii "round-vote-fixture", ascii "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", ascii "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd", ascii "validator-1", ascii "0"⟩
def vote2 : Vote := ⟨wire2, 1, 1, 0⟩
theorem payloadBytes2 : payload wire2 = [49,0,0,0,13,33,0,0,0,9,98,111,100,121,95,104,97,115,104,33,0,0,0,71,115,104,97,50,53,54,58,51] ++ [51,101,51,50,55,102,101,53,48,98,100,53,50,97,57,50,101,48,54,55,53,99,56,52,54,102,101,50,101,101,53,51] ++ [54,55,49,100,100,101,54,53,51,53,48,49,53,50,51,56,48,99,56,50,97,57,57,97,102,50,49,99,50,55,100,33] ++ [0,0,0,10,99,111,110,116,101,120,116,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,54,48,100,49,101,48] ++ [52,101,48,102,48,97,54,57,49,100,55,50,54,102,49,97,98,48,99,97,57,51,102,49,53,99,50,50,99,49,55,53] ++ [55,49,54,50,97,52,98,54,101,57,54,48,102,102,52,53,56,54,99,97,52,100,100,50,48,98,33,0,0,0,16,100] ++ [117,114,97,98,108,101,95,115,101,113,117,101,110,99,101,33,0,0,0,1,49,33,0,0,0,19,102,111,114,109,97,108] ++ [95,115,101,109,97,110,116,105,99,115,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,99,99,57,56,102,49,53] ++ [97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54] ++ [48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54,33,0,0,0,6,104,101] ++ [105,103,104,116,33,0,0,0,1,49,33,0,0,0,4,107,105,110,100,33,0,0,0,3,73,83,67,33,0,0,0,8] ++ [114,111,117,110,100,95,105,100,33,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45,102,105,120,116,117,114,101,33] ++ [0,0,0,14,115,99,104,101,109,97,95,118,101,114,115,105,111,110,33,0,0,0,5,49,46,48,46,48,33,0,0,0] ++ [12,115,105,103,110,97,116,117,114,101,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,101,101,101,101,101,101,101] ++ [101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101] ++ [101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,33,0,0,0,9,116,121] ++ [112,101,95,110,97,109,101,33,0,0,0,4,86,79,84,69,33,0,0,0,18,118,97,108,105,100,97,116,111,114,95,101] ++ [112,111,99,104,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,100,100,100,100,100,100,100,100,100,100,100,100,100] ++ [100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100] ++ [100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,33,0,0,0,12,118,97,108,105,100,97,116,111] ++ [114,95,105,100,33,0,0,0,11,118,97,108,105,100,97,116,111,114,45,49,33,0,0,0,4,118,105,101,119,33,0,0] ++ [0,1,48] := by
  simp only [payload, fields, wire2, encodeFields, nativeSemantics, encodedText0, encodedText1, encodedText2, encodedText8, encodedText13, encodedText14, encodedText15, encodedText16, encodedText17, encodedText18, encodedText19, encodedText20, encodedText21, encodedText22, encodedText28, encodedText31, encodedText38, encodedText40, encodedText42, encodedText43, encodedText44, encodedText45, encodedText46, encodedText47, encodedText48]
  rfl
theorem nativeFrame2 : encodeFrame wire2 = NativeReceiptVectors.frame2 := by
  unfold encodeFrame; rw [payloadBytes2]; rfl
theorem frameValid2 : FrameValid wire2 := by
  constructor; · decide
  rw [nativeFrame2]; decide
theorem valid2 : VoteValid vote2 := by
  exact ⟨frameValid2, by decide, by decide, by decide, by decide, by decide⟩
theorem parsed2 : decodeFrame NativeReceiptVectors.frame2 = some vote2 := by
  exact decodeFrameFromEncoding vote2 NativeReceiptVectors.frame2 valid2 nativeFrame2
def fixtureSHA2 (b : Bytes) : Bytes := if b = votePreimage NativeReceiptVectors.frame2 then [159,200,121,1,113,175,112,216,80,45,196,154,99,138,103,13,87,9,25,250,234,36,65,79,69,26,107,196,132,143,35,247] else []
theorem hashBinding2 : voteId fixtureSHA2 NativeReceiptVectors.frame2 = some NativeReceiptVectors.receipt2.voteId := by
  simp only [voteId, fixtureSHA2, ↓reduceIte]; rfl
theorem linked2 : ReceiptLinked fixtureSHA2 NativeReceiptVectors.receipt2 vote2 := by
  exact ⟨rfl, rfl, rfl, hashBinding2⟩
theorem bound2 : bindReceipt fixtureSHA2 NativeReceiptVectors.receipt2 = some vote2 :=
  bindingFromComponents fixtureSHA2 NativeReceiptVectors.receipt2 vote2 parsed2 linked2
theorem fullReceipt2 : decodeReceipt fixtureSHA2 NativeReceiptVectors.nativeBytes2 = some (NativeReceiptVectors.receipt2,vote2) := by
  exact receiptFromNativeBytes fixtureSHA2 NativeReceiptVectors.receipt2 vote2 NativeReceiptVectors.nativeBytes2 NativeReceiptVectors.valid2 bound2 NativeReceiptVectors.exactBytes2
theorem sequenceMismatch2 : bindReceipt fixtureSHA2 {NativeReceiptVectors.receipt2 with sequence := 0} = none := by
  apply bindingRejectsMismatch fixtureSHA2 {NativeReceiptVectors.receipt2 with sequence := 0} vote2 parsed2
  intro h; have : (0:Nat) = 1 := h.1; contradiction
theorem contextMismatch2 : bindReceipt fixtureSHA2 {NativeReceiptVectors.receipt2 with context := []} = none := by
  apply bindingRejectsMismatch fixtureSHA2 {NativeReceiptVectors.receipt2 with context := []} vote2 parsed2
  intro h; have wrong := h.2.1
  have different : ([]:Bytes) ≠ vote2.wire.context := by decide
  exact different wrong
theorem actionMismatch2 : bindReceipt fixtureSHA2 {NativeReceiptVectors.receipt2 with action := 0} = none := by
  apply bindingRejectsMismatch fixtureSHA2 {NativeReceiptVectors.receipt2 with action := 0} vote2 parsed2
  intro h; have wrong := h.2.2.1
  have different : actionName 0 ≠ vote2.wire.kind := by decide
  exact different wrong
theorem idMismatch2 : bindReceipt fixtureSHA2 {NativeReceiptVectors.receipt2 with voteId := []} = none := by
  apply bindingRejectsMismatch fixtureSHA2 {NativeReceiptVectors.receipt2 with voteId := []} vote2 parsed2
  intro h; have wrong := h.2.2.2
  change voteId fixtureSHA2 NativeReceiptVectors.frame2 = some [] at wrong
  rw [hashBinding2] at wrong
  have different : NativeReceiptVectors.receipt2.voteId ≠ [] := by decide
  exact different (Option.some.inj wrong)

def wire3 : WireVote := ⟨ascii "sha256:67c4e17a75fc0998471b408dbe094b30aa2a238d23bc008099159268b4b63978", ascii "sha256:d9ba7cfbab18c0cc638bfff75cafeda604e9e81c71f1b698f6538cb6846bfdff", ascii "1", ascii "1", ascii "EC", ascii "round-vote-fixture", ascii "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", ascii "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd", ascii "validator-1", ascii "0"⟩
def vote3 : Vote := ⟨wire3, 1, 1, 0⟩
theorem payloadBytes3 : payload wire3 = [49,0,0,0,13,33,0,0,0,9,98,111,100,121,95,104,97,115,104,33,0,0,0,71,115,104,97,50,53,54,58,54] ++ [55,99,52,101,49,55,97,55,53,102,99,48,57,57,56,52,55,49,98,52,48,56,100,98,101,48,57,52,98,51,48,97] ++ [97,50,97,50,51,56,100,50,51,98,99,48,48,56,48,57,57,49,53,57,50,54,56,98,52,98,54,51,57,55,56,33] ++ [0,0,0,10,99,111,110,116,101,120,116,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,100,57,98,97,55,99] ++ [102,98,97,98,49,56,99,48,99,99,54,51,56,98,102,102,102,55,53,99,97,102,101,100,97,54,48,52,101,57,101,56] ++ [49,99,55,49,102,49,98,54,57,56,102,54,53,51,56,99,98,54,56,52,54,98,102,100,102,102,33,0,0,0,16,100] ++ [117,114,97,98,108,101,95,115,101,113,117,101,110,99,101,33,0,0,0,1,49,33,0,0,0,19,102,111,114,109,97,108] ++ [95,115,101,109,97,110,116,105,99,115,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,99,99,57,56,102,49,53] ++ [97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54] ++ [48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54,33,0,0,0,6,104,101] ++ [105,103,104,116,33,0,0,0,1,49,33,0,0,0,4,107,105,110,100,33,0,0,0,2,69,67,33,0,0,0,8,114] ++ [111,117,110,100,95,105,100,33,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45,102,105,120,116,117,114,101,33,0] ++ [0,0,14,115,99,104,101,109,97,95,118,101,114,115,105,111,110,33,0,0,0,5,49,46,48,46,48,33,0,0,0,12] ++ [115,105,103,110,97,116,117,114,101,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,101,101,101,101,101,101,101,101] ++ [101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101] ++ [101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,33,0,0,0,9,116,121,112] ++ [101,95,110,97,109,101,33,0,0,0,4,86,79,84,69,33,0,0,0,18,118,97,108,105,100,97,116,111,114,95,101,112] ++ [111,99,104,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,100,100,100,100,100,100,100,100,100,100,100,100,100,100] ++ [100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100] ++ [100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,33,0,0,0,12,118,97,108,105,100,97,116,111,114] ++ [95,105,100,33,0,0,0,11,118,97,108,105,100,97,116,111,114,45,49,33,0,0,0,4,118,105,101,119,33,0,0,0] ++ [1,48] := by
  simp only [payload, fields, wire3, encodeFields, nativeSemantics, encodedText0, encodedText1, encodedText2, encodedText7, encodedText13, encodedText14, encodedText15, encodedText16, encodedText17, encodedText18, encodedText19, encodedText20, encodedText21, encodedText22, encodedText33, encodedText38, encodedText39, encodedText40, encodedText42, encodedText43, encodedText44, encodedText45, encodedText46, encodedText47, encodedText48]
  rfl
theorem nativeFrame3 : encodeFrame wire3 = NativeReceiptVectors.frame3 := by
  unfold encodeFrame; rw [payloadBytes3]; rfl
theorem frameValid3 : FrameValid wire3 := by
  constructor; · decide
  rw [nativeFrame3]; decide
theorem valid3 : VoteValid vote3 := by
  exact ⟨frameValid3, by decide, by decide, by decide, by decide, by decide⟩
theorem parsed3 : decodeFrame NativeReceiptVectors.frame3 = some vote3 := by
  exact decodeFrameFromEncoding vote3 NativeReceiptVectors.frame3 valid3 nativeFrame3
def fixtureSHA3 (b : Bytes) : Bytes := if b = votePreimage NativeReceiptVectors.frame3 then [64,186,56,229,74,11,218,201,253,34,65,183,59,36,17,219,73,90,197,8,5,27,98,56,112,212,128,38,173,215,140,168] else []
theorem hashBinding3 : voteId fixtureSHA3 NativeReceiptVectors.frame3 = some NativeReceiptVectors.receipt3.voteId := by
  simp only [voteId, fixtureSHA3, ↓reduceIte]; rfl
theorem linked3 : ReceiptLinked fixtureSHA3 NativeReceiptVectors.receipt3 vote3 := by
  exact ⟨rfl, rfl, rfl, hashBinding3⟩
theorem bound3 : bindReceipt fixtureSHA3 NativeReceiptVectors.receipt3 = some vote3 :=
  bindingFromComponents fixtureSHA3 NativeReceiptVectors.receipt3 vote3 parsed3 linked3
theorem fullReceipt3 : decodeReceipt fixtureSHA3 NativeReceiptVectors.nativeBytes3 = some (NativeReceiptVectors.receipt3,vote3) := by
  exact receiptFromNativeBytes fixtureSHA3 NativeReceiptVectors.receipt3 vote3 NativeReceiptVectors.nativeBytes3 NativeReceiptVectors.valid3 bound3 NativeReceiptVectors.exactBytes3
theorem sequenceMismatch3 : bindReceipt fixtureSHA3 {NativeReceiptVectors.receipt3 with sequence := 0} = none := by
  apply bindingRejectsMismatch fixtureSHA3 {NativeReceiptVectors.receipt3 with sequence := 0} vote3 parsed3
  intro h; have : (0:Nat) = 1 := h.1; contradiction
theorem contextMismatch3 : bindReceipt fixtureSHA3 {NativeReceiptVectors.receipt3 with context := []} = none := by
  apply bindingRejectsMismatch fixtureSHA3 {NativeReceiptVectors.receipt3 with context := []} vote3 parsed3
  intro h; have wrong := h.2.1
  have different : ([]:Bytes) ≠ vote3.wire.context := by decide
  exact different wrong
theorem actionMismatch3 : bindReceipt fixtureSHA3 {NativeReceiptVectors.receipt3 with action := 0} = none := by
  apply bindingRejectsMismatch fixtureSHA3 {NativeReceiptVectors.receipt3 with action := 0} vote3 parsed3
  intro h; have wrong := h.2.2.1
  have different : actionName 0 ≠ vote3.wire.kind := by decide
  exact different wrong
theorem idMismatch3 : bindReceipt fixtureSHA3 {NativeReceiptVectors.receipt3 with voteId := []} = none := by
  apply bindingRejectsMismatch fixtureSHA3 {NativeReceiptVectors.receipt3 with voteId := []} vote3 parsed3
  intro h; have wrong := h.2.2.2
  change voteId fixtureSHA3 NativeReceiptVectors.frame3 = some [] at wrong
  rw [hashBinding3] at wrong
  have different : NativeReceiptVectors.receipt3.voteId ≠ [] := by decide
  exact different (Option.some.inj wrong)

def wire4 : WireVote := ⟨ascii "sha256:4580349215fc6b84d64fdf994c47283b08dbfa850927c8eb106a59fae9c812e2", ascii "sha256:7ccc5fd880d6ab0d4cb21d1e114d10995e1757b8372ef7547feefaa6d417edb2", ascii "1", ascii "1", ascii "APC", ascii "round-vote-fixture", ascii "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", ascii "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd", ascii "validator-1", ascii "0"⟩
def vote4 : Vote := ⟨wire4, 1, 1, 0⟩
theorem payloadBytes4 : payload wire4 = [49,0,0,0,13,33,0,0,0,9,98,111,100,121,95,104,97,115,104,33,0,0,0,71,115,104,97,50,53,54,58,52] ++ [53,56,48,51,52,57,50,49,53,102,99,54,98,56,52,100,54,52,102,100,102,57,57,52,99,52,55,50,56,51,98,48] ++ [56,100,98,102,97,56,53,48,57,50,55,99,56,101,98,49,48,54,97,53,57,102,97,101,57,99,56,49,50,101,50,33] ++ [0,0,0,10,99,111,110,116,101,120,116,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,55,99,99,99,53,102] ++ [100,56,56,48,100,54,97,98,48,100,52,99,98,50,49,100,49,101,49,49,52,100,49,48,57,57,53,101,49,55,53,55] ++ [98,56,51,55,50,101,102,55,53,52,55,102,101,101,102,97,97,54,100,52,49,55,101,100,98,50,33,0,0,0,16,100] ++ [117,114,97,98,108,101,95,115,101,113,117,101,110,99,101,33,0,0,0,1,49,33,0,0,0,19,102,111,114,109,97,108] ++ [95,115,101,109,97,110,116,105,99,115,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,99,99,57,56,102,49,53] ++ [97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54] ++ [48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54,33,0,0,0,6,104,101] ++ [105,103,104,116,33,0,0,0,1,49,33,0,0,0,4,107,105,110,100,33,0,0,0,3,65,80,67,33,0,0,0,8] ++ [114,111,117,110,100,95,105,100,33,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45,102,105,120,116,117,114,101,33] ++ [0,0,0,14,115,99,104,101,109,97,95,118,101,114,115,105,111,110,33,0,0,0,5,49,46,48,46,48,33,0,0,0] ++ [12,115,105,103,110,97,116,117,114,101,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,101,101,101,101,101,101,101] ++ [101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101] ++ [101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,33,0,0,0,9,116,121] ++ [112,101,95,110,97,109,101,33,0,0,0,4,86,79,84,69,33,0,0,0,18,118,97,108,105,100,97,116,111,114,95,101] ++ [112,111,99,104,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,100,100,100,100,100,100,100,100,100,100,100,100,100] ++ [100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100] ++ [100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,33,0,0,0,12,118,97,108,105,100,97,116,111] ++ [114,95,105,100,33,0,0,0,11,118,97,108,105,100,97,116,111,114,45,49,33,0,0,0,4,118,105,101,119,33,0,0] ++ [0,1,48] := by
  simp only [payload, fields, wire4, encodeFields, nativeSemantics, encodedText0, encodedText1, encodedText2, encodedText5, encodedText13, encodedText14, encodedText15, encodedText16, encodedText17, encodedText18, encodedText19, encodedText20, encodedText21, encodedText22, encodedText29, encodedText36, encodedText38, encodedText40, encodedText42, encodedText43, encodedText44, encodedText45, encodedText46, encodedText47, encodedText48]
  rfl
theorem nativeFrame4 : encodeFrame wire4 = NativeReceiptVectors.frame4 := by
  unfold encodeFrame; rw [payloadBytes4]; rfl
theorem frameValid4 : FrameValid wire4 := by
  constructor; · decide
  rw [nativeFrame4]; decide
theorem valid4 : VoteValid vote4 := by
  exact ⟨frameValid4, by decide, by decide, by decide, by decide, by decide⟩
theorem parsed4 : decodeFrame NativeReceiptVectors.frame4 = some vote4 := by
  exact decodeFrameFromEncoding vote4 NativeReceiptVectors.frame4 valid4 nativeFrame4
def fixtureSHA4 (b : Bytes) : Bytes := if b = votePreimage NativeReceiptVectors.frame4 then [15,133,45,107,86,4,219,255,187,239,163,81,234,202,42,192,105,166,53,152,197,53,163,107,177,178,19,237,97,215,129,238] else []
theorem hashBinding4 : voteId fixtureSHA4 NativeReceiptVectors.frame4 = some NativeReceiptVectors.receipt4.voteId := by
  simp only [voteId, fixtureSHA4, ↓reduceIte]; rfl
theorem linked4 : ReceiptLinked fixtureSHA4 NativeReceiptVectors.receipt4 vote4 := by
  exact ⟨rfl, rfl, rfl, hashBinding4⟩
theorem bound4 : bindReceipt fixtureSHA4 NativeReceiptVectors.receipt4 = some vote4 :=
  bindingFromComponents fixtureSHA4 NativeReceiptVectors.receipt4 vote4 parsed4 linked4
theorem fullReceipt4 : decodeReceipt fixtureSHA4 NativeReceiptVectors.nativeBytes4 = some (NativeReceiptVectors.receipt4,vote4) := by
  exact receiptFromNativeBytes fixtureSHA4 NativeReceiptVectors.receipt4 vote4 NativeReceiptVectors.nativeBytes4 NativeReceiptVectors.valid4 bound4 NativeReceiptVectors.exactBytes4
theorem sequenceMismatch4 : bindReceipt fixtureSHA4 {NativeReceiptVectors.receipt4 with sequence := 0} = none := by
  apply bindingRejectsMismatch fixtureSHA4 {NativeReceiptVectors.receipt4 with sequence := 0} vote4 parsed4
  intro h; have : (0:Nat) = 1 := h.1; contradiction
theorem contextMismatch4 : bindReceipt fixtureSHA4 {NativeReceiptVectors.receipt4 with context := []} = none := by
  apply bindingRejectsMismatch fixtureSHA4 {NativeReceiptVectors.receipt4 with context := []} vote4 parsed4
  intro h; have wrong := h.2.1
  have different : ([]:Bytes) ≠ vote4.wire.context := by decide
  exact different wrong
theorem actionMismatch4 : bindReceipt fixtureSHA4 {NativeReceiptVectors.receipt4 with action := 0} = none := by
  apply bindingRejectsMismatch fixtureSHA4 {NativeReceiptVectors.receipt4 with action := 0} vote4 parsed4
  intro h; have wrong := h.2.2.1
  have different : actionName 0 ≠ vote4.wire.kind := by decide
  exact different wrong
theorem idMismatch4 : bindReceipt fixtureSHA4 {NativeReceiptVectors.receipt4 with voteId := []} = none := by
  apply bindingRejectsMismatch fixtureSHA4 {NativeReceiptVectors.receipt4 with voteId := []} vote4 parsed4
  intro h; have wrong := h.2.2.2
  change voteId fixtureSHA4 NativeReceiptVectors.frame4 = some [] at wrong
  rw [hashBinding4] at wrong
  have different : NativeReceiptVectors.receipt4.voteId ≠ [] := by decide
  exact different (Option.some.inj wrong)

def wire5 : WireVote := ⟨ascii "sha256:64a104b7f8c820b6b3c48950af74c115f4d94787f7e5132950402a6adcd41645", ascii "PARAMETER:domain-a:shard-a", ascii "1", ascii "1", ascii "PARAMETER", ascii "round-vote-fixture", ascii "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", ascii "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd", ascii "validator-1", ascii "0"⟩
def vote5 : Vote := ⟨wire5, 1, 1, 0⟩
theorem payloadBytes5 : payload wire5 = [49,0,0,0,13,33,0,0,0,9,98,111,100,121,95,104,97,115,104,33,0,0,0,71,115,104,97,50,53,54,58,54] ++ [52,97,49,48,52,98,55,102,56,99,56,50,48,98,54,98,51,99,52,56,57,53,48,97,102,55,52,99,49,49,53,102] ++ [52,100,57,52,55,56,55,102,55,101,53,49,51,50,57,53,48,52,48,50,97,54,97,100,99,100,52,49,54,52,53,33] ++ [0,0,0,10,99,111,110,116,101,120,116,95,105,100,33,0,0,0,26,80,65,82,65,77,69,84,69,82,58,100,111,109] ++ [97,105,110,45,97,58,115,104,97,114,100,45,97,33,0,0,0,16,100,117,114,97,98,108,101,95,115,101,113,117,101,110] ++ [99,101,33,0,0,0,1,49,33,0,0,0,19,102,111,114,109,97,108,95,115,101,109,97,110,116,105,99,115,95,105,100] ++ [33,0,0,0,71,115,104,97,50,53,54,58,99,99,57,56,102,49,53,97,99,50,48,102,99,51,101,100,50,54,53,99] ++ [98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54,48,97,54,53,49,101,50,98,56,102,56,49,54] ++ [51,56,97,98,98,51,50,54,53,99,98,54,33,0,0,0,6,104,101,105,103,104,116,33,0,0,0,1,49,33,0,0] ++ [0,4,107,105,110,100,33,0,0,0,9,80,65,82,65,77,69,84,69,82,33,0,0,0,8,114,111,117,110,100,95,105] ++ [100,33,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45,102,105,120,116,117,114,101,33,0,0,0,14,115,99,104] ++ [101,109,97,95,118,101,114,115,105,111,110,33,0,0,0,5,49,46,48,46,48,33,0,0,0,12,115,105,103,110,97,116] ++ [117,114,101,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,101,101,101,101,101,101,101,101,101,101,101,101,101,101] ++ [101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101] ++ [101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,33,0,0,0,9,116,121,112,101,95,110,97,109,101] ++ [33,0,0,0,4,86,79,84,69,33,0,0,0,18,118,97,108,105,100,97,116,111,114,95,101,112,111,99,104,95,105,100] ++ [33,0,0,0,71,115,104,97,50,53,54,58,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100] ++ [100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100] ++ [100,100,100,100,100,100,100,100,100,100,100,100,33,0,0,0,12,118,97,108,105,100,97,116,111,114,95,105,100,33,0,0] ++ [0,11,118,97,108,105,100,97,116,111,114,45,49,33,0,0,0,4,118,105,101,119,33,0,0,0,1,48] := by
  simp only [payload, fields, wire5, encodeFields, nativeSemantics, encodedText0, encodedText1, encodedText2, encodedText9, encodedText10, encodedText13, encodedText14, encodedText15, encodedText16, encodedText17, encodedText18, encodedText19, encodedText20, encodedText21, encodedText22, encodedText32, encodedText38, encodedText40, encodedText42, encodedText43, encodedText44, encodedText45, encodedText46, encodedText47, encodedText48]
  rfl
theorem nativeFrame5 : encodeFrame wire5 = NativeReceiptVectors.frame5 := by
  unfold encodeFrame; rw [payloadBytes5]; rfl
theorem frameValid5 : FrameValid wire5 := by
  constructor; · decide
  rw [nativeFrame5]; decide
theorem valid5 : VoteValid vote5 := by
  exact ⟨frameValid5, by decide, by decide, by decide, by decide, by decide⟩
theorem parsed5 : decodeFrame NativeReceiptVectors.frame5 = some vote5 := by
  exact decodeFrameFromEncoding vote5 NativeReceiptVectors.frame5 valid5 nativeFrame5
def fixtureSHA5 (b : Bytes) : Bytes := if b = votePreimage NativeReceiptVectors.frame5 then [236,202,126,150,173,161,231,134,118,76,71,141,143,57,190,14,168,158,191,72,240,42,227,100,241,163,134,72,227,227,228,157] else []
theorem hashBinding5 : voteId fixtureSHA5 NativeReceiptVectors.frame5 = some NativeReceiptVectors.receipt5.voteId := by
  simp only [voteId, fixtureSHA5, ↓reduceIte]; rfl
theorem linked5 : ReceiptLinked fixtureSHA5 NativeReceiptVectors.receipt5 vote5 := by
  exact ⟨rfl, rfl, rfl, hashBinding5⟩
theorem bound5 : bindReceipt fixtureSHA5 NativeReceiptVectors.receipt5 = some vote5 :=
  bindingFromComponents fixtureSHA5 NativeReceiptVectors.receipt5 vote5 parsed5 linked5
theorem fullReceipt5 : decodeReceipt fixtureSHA5 NativeReceiptVectors.nativeBytes5 = some (NativeReceiptVectors.receipt5,vote5) := by
  exact receiptFromNativeBytes fixtureSHA5 NativeReceiptVectors.receipt5 vote5 NativeReceiptVectors.nativeBytes5 NativeReceiptVectors.valid5 bound5 NativeReceiptVectors.exactBytes5
theorem sequenceMismatch5 : bindReceipt fixtureSHA5 {NativeReceiptVectors.receipt5 with sequence := 0} = none := by
  apply bindingRejectsMismatch fixtureSHA5 {NativeReceiptVectors.receipt5 with sequence := 0} vote5 parsed5
  intro h; have : (0:Nat) = 1 := h.1; contradiction
theorem contextMismatch5 : bindReceipt fixtureSHA5 {NativeReceiptVectors.receipt5 with context := []} = none := by
  apply bindingRejectsMismatch fixtureSHA5 {NativeReceiptVectors.receipt5 with context := []} vote5 parsed5
  intro h; have wrong := h.2.1
  have different : ([]:Bytes) ≠ vote5.wire.context := by decide
  exact different wrong
theorem actionMismatch5 : bindReceipt fixtureSHA5 {NativeReceiptVectors.receipt5 with action := 0} = none := by
  apply bindingRejectsMismatch fixtureSHA5 {NativeReceiptVectors.receipt5 with action := 0} vote5 parsed5
  intro h; have wrong := h.2.2.1
  have different : actionName 0 ≠ vote5.wire.kind := by decide
  exact different wrong
theorem idMismatch5 : bindReceipt fixtureSHA5 {NativeReceiptVectors.receipt5 with voteId := []} = none := by
  apply bindingRejectsMismatch fixtureSHA5 {NativeReceiptVectors.receipt5 with voteId := []} vote5 parsed5
  intro h; have wrong := h.2.2.2
  change voteId fixtureSHA5 NativeReceiptVectors.frame5 = some [] at wrong
  rw [hashBinding5] at wrong
  have different : NativeReceiptVectors.receipt5.voteId ≠ [] := by decide
  exact different (Option.some.inj wrong)

def wire6 : WireVote := ⟨ascii "sha256:c5ec7f38bf6e199fd9d676f6e1b4a734624bc219a486c110fa5410f8f8fc2d28", ascii "sha256:08edbd495b3369f06d7d46dec477899485859ee01e58789eea42e61532a0cca1", ascii "1", ascii "1", ascii "AGGREGATE_ROOT", ascii "round-vote-fixture", ascii "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", ascii "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd", ascii "validator-1", ascii "0"⟩
def vote6 : Vote := ⟨wire6, 1, 1, 0⟩
theorem payloadBytes6 : payload wire6 = [49,0,0,0,13,33,0,0,0,9,98,111,100,121,95,104,97,115,104,33,0,0,0,71,115,104,97,50,53,54,58,99] ++ [53,101,99,55,102,51,56,98,102,54,101,49,57,57,102,100,57,100,54,55,54,102,54,101,49,98,52,97,55,51,52,54] ++ [50,52,98,99,50,49,57,97,52,56,54,99,49,49,48,102,97,53,52,49,48,102,56,102,56,102,99,50,100,50,56,33] ++ [0,0,0,10,99,111,110,116,101,120,116,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,48,56,101,100,98,100] ++ [52,57,53,98,51,51,54,57,102,48,54,100,55,100,52,54,100,101,99,52,55,55,56,57,57,52,56,53,56,53,57,101] ++ [101,48,49,101,53,56,55,56,57,101,101,97,52,50,101,54,49,53,51,50,97,48,99,99,97,49,33,0,0,0,16,100] ++ [117,114,97,98,108,101,95,115,101,113,117,101,110,99,101,33,0,0,0,1,49,33,0,0,0,19,102,111,114,109,97,108] ++ [95,115,101,109,97,110,116,105,99,115,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,99,99,57,56,102,49,53] ++ [97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54] ++ [48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54,33,0,0,0,6,104,101] ++ [105,103,104,116,33,0,0,0,1,49,33,0,0,0,4,107,105,110,100,33,0,0,0,14,65,71,71,82,69,71,65,84] ++ [69,95,82,79,79,84,33,0,0,0,8,114,111,117,110,100,95,105,100,33,0,0,0,18,114,111,117,110,100,45,118,111] ++ [116,101,45,102,105,120,116,117,114,101,33,0,0,0,14,115,99,104,101,109,97,95,118,101,114,115,105,111,110,33,0,0] ++ [0,5,49,46,48,46,48,33,0,0,0,12,115,105,103,110,97,116,117,114,101,95,105,100,33,0,0,0,71,115,104,97] ++ [50,53,54,58,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101] ++ [101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101] ++ [101,101,101,101,33,0,0,0,9,116,121,112,101,95,110,97,109,101,33,0,0,0,4,86,79,84,69,33,0,0,0,18] ++ [118,97,108,105,100,97,116,111,114,95,101,112,111,99,104,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,100,100] ++ [100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100] ++ [100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,33,0] ++ [0,0,12,118,97,108,105,100,97,116,111,114,95,105,100,33,0,0,0,11,118,97,108,105,100,97,116,111,114,45,49,33] ++ [0,0,0,4,118,105,101,119,33,0,0,0,1,48] := by
  simp only [payload, fields, wire6, encodeFields, nativeSemantics, encodedText0, encodedText1, encodedText2, encodedText4, encodedText13, encodedText14, encodedText15, encodedText16, encodedText17, encodedText18, encodedText19, encodedText20, encodedText21, encodedText22, encodedText23, encodedText37, encodedText38, encodedText40, encodedText42, encodedText43, encodedText44, encodedText45, encodedText46, encodedText47, encodedText48]
  rfl
theorem nativeFrame6 : encodeFrame wire6 = NativeReceiptVectors.frame6 := by
  unfold encodeFrame; rw [payloadBytes6]; rfl
theorem frameValid6 : FrameValid wire6 := by
  constructor; · decide
  rw [nativeFrame6]; decide
theorem valid6 : VoteValid vote6 := by
  exact ⟨frameValid6, by decide, by decide, by decide, by decide, by decide⟩
theorem parsed6 : decodeFrame NativeReceiptVectors.frame6 = some vote6 := by
  exact decodeFrameFromEncoding vote6 NativeReceiptVectors.frame6 valid6 nativeFrame6
def fixtureSHA6 (b : Bytes) : Bytes := if b = votePreimage NativeReceiptVectors.frame6 then [194,74,23,196,232,76,183,225,102,165,138,111,58,103,185,146,244,138,73,56,67,173,196,242,206,18,15,156,53,186,43,34] else []
theorem hashBinding6 : voteId fixtureSHA6 NativeReceiptVectors.frame6 = some NativeReceiptVectors.receipt6.voteId := by
  simp only [voteId, fixtureSHA6, ↓reduceIte]; rfl
theorem linked6 : ReceiptLinked fixtureSHA6 NativeReceiptVectors.receipt6 vote6 := by
  exact ⟨rfl, rfl, rfl, hashBinding6⟩
theorem bound6 : bindReceipt fixtureSHA6 NativeReceiptVectors.receipt6 = some vote6 :=
  bindingFromComponents fixtureSHA6 NativeReceiptVectors.receipt6 vote6 parsed6 linked6
theorem fullReceipt6 : decodeReceipt fixtureSHA6 NativeReceiptVectors.nativeBytes6 = some (NativeReceiptVectors.receipt6,vote6) := by
  exact receiptFromNativeBytes fixtureSHA6 NativeReceiptVectors.receipt6 vote6 NativeReceiptVectors.nativeBytes6 NativeReceiptVectors.valid6 bound6 NativeReceiptVectors.exactBytes6
theorem sequenceMismatch6 : bindReceipt fixtureSHA6 {NativeReceiptVectors.receipt6 with sequence := 0} = none := by
  apply bindingRejectsMismatch fixtureSHA6 {NativeReceiptVectors.receipt6 with sequence := 0} vote6 parsed6
  intro h; have : (0:Nat) = 1 := h.1; contradiction
theorem contextMismatch6 : bindReceipt fixtureSHA6 {NativeReceiptVectors.receipt6 with context := []} = none := by
  apply bindingRejectsMismatch fixtureSHA6 {NativeReceiptVectors.receipt6 with context := []} vote6 parsed6
  intro h; have wrong := h.2.1
  have different : ([]:Bytes) ≠ vote6.wire.context := by decide
  exact different wrong
theorem actionMismatch6 : bindReceipt fixtureSHA6 {NativeReceiptVectors.receipt6 with action := 0} = none := by
  apply bindingRejectsMismatch fixtureSHA6 {NativeReceiptVectors.receipt6 with action := 0} vote6 parsed6
  intro h; have wrong := h.2.2.1
  have different : actionName 0 ≠ vote6.wire.kind := by decide
  exact different wrong
theorem idMismatch6 : bindReceipt fixtureSHA6 {NativeReceiptVectors.receipt6 with voteId := []} = none := by
  apply bindingRejectsMismatch fixtureSHA6 {NativeReceiptVectors.receipt6 with voteId := []} vote6 parsed6
  intro h; have wrong := h.2.2.2
  change voteId fixtureSHA6 NativeReceiptVectors.frame6 = some [] at wrong
  rw [hashBinding6] at wrong
  have different : NativeReceiptVectors.receipt6.voteId ≠ [] := by decide
  exact different (Option.some.inj wrong)

def wire7 : WireVote := ⟨ascii "sha256:2bf5029d5500241ca9a548b5858bb142066512f4f1e3976e09c27b7e962ca01f", ascii "sha256:7a21a3c4a2488f093311911563224fff2abf52557342bd33e4f469731c92d4e1", ascii "1", ascii "1", ascii "APPLY", ascii "round-vote-fixture", ascii "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", ascii "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd", ascii "validator-1", ascii "0"⟩
def vote7 : Vote := ⟨wire7, 1, 1, 0⟩
theorem payloadBytes7 : payload wire7 = [49,0,0,0,13,33,0,0,0,9,98,111,100,121,95,104,97,115,104,33,0,0,0,71,115,104,97,50,53,54,58,50] ++ [98,102,53,48,50,57,100,53,53,48,48,50,52,49,99,97,57,97,53,52,56,98,53,56,53,56,98,98,49,52,50,48] ++ [54,54,53,49,50,102,52,102,49,101,51,57,55,54,101,48,57,99,50,55,98,55,101,57,54,50,99,97,48,49,102,33] ++ [0,0,0,10,99,111,110,116,101,120,116,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,55,97,50,49,97,51] ++ [99,52,97,50,52,56,56,102,48,57,51,51,49,49,57,49,49,53,54,51,50,50,52,102,102,102,50,97,98,102,53,50] ++ [53,53,55,51,52,50,98,100,51,51,101,52,102,52,54,57,55,51,49,99,57,50,100,52,101,49,33,0,0,0,16,100] ++ [117,114,97,98,108,101,95,115,101,113,117,101,110,99,101,33,0,0,0,1,49,33,0,0,0,19,102,111,114,109,97,108] ++ [95,115,101,109,97,110,116,105,99,115,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,99,99,57,56,102,49,53] ++ [97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54] ++ [48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54,33,0,0,0,6,104,101] ++ [105,103,104,116,33,0,0,0,1,49,33,0,0,0,4,107,105,110,100,33,0,0,0,5,65,80,80,76,89,33,0,0] ++ [0,8,114,111,117,110,100,95,105,100,33,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45,102,105,120,116,117,114] ++ [101,33,0,0,0,14,115,99,104,101,109,97,95,118,101,114,115,105,111,110,33,0,0,0,5,49,46,48,46,48,33,0] ++ [0,0,12,115,105,103,110,97,116,117,114,101,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,101,101,101,101,101] ++ [101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101] ++ [101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,33,0,0,0,9] ++ [116,121,112,101,95,110,97,109,101,33,0,0,0,4,86,79,84,69,33,0,0,0,18,118,97,108,105,100,97,116,111,114] ++ [95,101,112,111,99,104,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,100,100,100,100,100,100,100,100,100,100,100] ++ [100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100] ++ [100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,33,0,0,0,12,118,97,108,105,100,97] ++ [116,111,114,95,105,100,33,0,0,0,11,118,97,108,105,100,97,116,111,114,45,49,33,0,0,0,4,118,105,101,119,33] ++ [0,0,0,1,48] := by
  simp only [payload, fields, wire7, encodeFields, nativeSemantics, encodedText0, encodedText1, encodedText2, encodedText6, encodedText13, encodedText14, encodedText15, encodedText16, encodedText17, encodedText18, encodedText19, encodedText20, encodedText21, encodedText22, encodedText26, encodedText34, encodedText38, encodedText40, encodedText42, encodedText43, encodedText44, encodedText45, encodedText46, encodedText47, encodedText48]
  rfl
theorem nativeFrame7 : encodeFrame wire7 = NativeReceiptVectors.frame7 := by
  unfold encodeFrame; rw [payloadBytes7]; rfl
theorem frameValid7 : FrameValid wire7 := by
  constructor; · decide
  rw [nativeFrame7]; decide
theorem valid7 : VoteValid vote7 := by
  exact ⟨frameValid7, by decide, by decide, by decide, by decide, by decide⟩
theorem parsed7 : decodeFrame NativeReceiptVectors.frame7 = some vote7 := by
  exact decodeFrameFromEncoding vote7 NativeReceiptVectors.frame7 valid7 nativeFrame7
def fixtureSHA7 (b : Bytes) : Bytes := if b = votePreimage NativeReceiptVectors.frame7 then [61,148,132,206,173,47,155,34,251,228,130,112,38,42,168,80,222,103,195,55,63,168,123,71,201,156,175,161,77,201,230,221] else []
theorem hashBinding7 : voteId fixtureSHA7 NativeReceiptVectors.frame7 = some NativeReceiptVectors.receipt7.voteId := by
  simp only [voteId, fixtureSHA7, ↓reduceIte]; rfl
theorem linked7 : ReceiptLinked fixtureSHA7 NativeReceiptVectors.receipt7 vote7 := by
  exact ⟨rfl, rfl, rfl, hashBinding7⟩
theorem bound7 : bindReceipt fixtureSHA7 NativeReceiptVectors.receipt7 = some vote7 :=
  bindingFromComponents fixtureSHA7 NativeReceiptVectors.receipt7 vote7 parsed7 linked7
theorem fullReceipt7 : decodeReceipt fixtureSHA7 NativeReceiptVectors.nativeBytes7 = some (NativeReceiptVectors.receipt7,vote7) := by
  exact receiptFromNativeBytes fixtureSHA7 NativeReceiptVectors.receipt7 vote7 NativeReceiptVectors.nativeBytes7 NativeReceiptVectors.valid7 bound7 NativeReceiptVectors.exactBytes7
theorem sequenceMismatch7 : bindReceipt fixtureSHA7 {NativeReceiptVectors.receipt7 with sequence := 0} = none := by
  apply bindingRejectsMismatch fixtureSHA7 {NativeReceiptVectors.receipt7 with sequence := 0} vote7 parsed7
  intro h; have : (0:Nat) = 1 := h.1; contradiction
theorem contextMismatch7 : bindReceipt fixtureSHA7 {NativeReceiptVectors.receipt7 with context := []} = none := by
  apply bindingRejectsMismatch fixtureSHA7 {NativeReceiptVectors.receipt7 with context := []} vote7 parsed7
  intro h; have wrong := h.2.1
  have different : ([]:Bytes) ≠ vote7.wire.context := by decide
  exact different wrong
theorem actionMismatch7 : bindReceipt fixtureSHA7 {NativeReceiptVectors.receipt7 with action := 0} = none := by
  apply bindingRejectsMismatch fixtureSHA7 {NativeReceiptVectors.receipt7 with action := 0} vote7 parsed7
  intro h; have wrong := h.2.2.1
  have different : actionName 0 ≠ vote7.wire.kind := by decide
  exact different wrong
theorem idMismatch7 : bindReceipt fixtureSHA7 {NativeReceiptVectors.receipt7 with voteId := []} = none := by
  apply bindingRejectsMismatch fixtureSHA7 {NativeReceiptVectors.receipt7 with voteId := []} vote7 parsed7
  intro h; have wrong := h.2.2.2
  change voteId fixtureSHA7 NativeReceiptVectors.frame7 = some [] at wrong
  rw [hashBinding7] at wrong
  have different : NativeReceiptVectors.receipt7.voteId ≠ [] := by decide
  exact different (Option.some.inj wrong)

def wire8 : WireVote := ⟨ascii "sha256:2ea13643cbd3d3ed7b0d860dc5c86c9cbfd945a0645de325ebd7a4f47da6b759", ascii "sha256:ee4385720a99be17cc6352b2cecbbb16bc33a45f86e3cea872cc8e6334af9bf9", ascii "1", ascii "1", ascii "VIEW_CHANGE", ascii "round-vote-fixture", ascii "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", ascii "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd", ascii "validator-1", ascii "0"⟩
def vote8 : Vote := ⟨wire8, 1, 1, 0⟩
theorem payloadBytes8 : payload wire8 = [49,0,0,0,13,33,0,0,0,9,98,111,100,121,95,104,97,115,104,33,0,0,0,71,115,104,97,50,53,54,58,50] ++ [101,97,49,51,54,52,51,99,98,100,51,100,51,101,100,55,98,48,100,56,54,48,100,99,53,99,56,54,99,57,99,98] ++ [102,100,57,52,53,97,48,54,52,53,100,101,51,50,53,101,98,100,55,97,52,102,52,55,100,97,54,98,55,53,57,33] ++ [0,0,0,10,99,111,110,116,101,120,116,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,101,101,52,51,56,53] ++ [55,50,48,97,57,57,98,101,49,55,99,99,54,51,53,50,98,50,99,101,99,98,98,98,49,54,98,99,51,51,97,52] ++ [53,102,56,54,101,51,99,101,97,56,55,50,99,99,56,101,54,51,51,52,97,102,57,98,102,57,33,0,0,0,16,100] ++ [117,114,97,98,108,101,95,115,101,113,117,101,110,99,101,33,0,0,0,1,49,33,0,0,0,19,102,111,114,109,97,108] ++ [95,115,101,109,97,110,116,105,99,115,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,99,99,57,56,102,49,53] ++ [97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54] ++ [48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54,33,0,0,0,6,104,101] ++ [105,103,104,116,33,0,0,0,1,49,33,0,0,0,4,107,105,110,100,33,0,0,0,11,86,73,69,87,95,67,72,65] ++ [78,71,69,33,0,0,0,8,114,111,117,110,100,95,105,100,33,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45] ++ [102,105,120,116,117,114,101,33,0,0,0,14,115,99,104,101,109,97,95,118,101,114,115,105,111,110,33,0,0,0,5,49] ++ [46,48,46,48,33,0,0,0,12,115,105,103,110,97,116,117,114,101,95,105,100,33,0,0,0,71,115,104,97,50,53,54] ++ [58,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101] ++ [101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101] ++ [101,33,0,0,0,9,116,121,112,101,95,110,97,109,101,33,0,0,0,4,86,79,84,69,33,0,0,0,18,118,97,108] ++ [105,100,97,116,111,114,95,101,112,111,99,104,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,100,100,100,100,100] ++ [100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100] ++ [100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,33,0,0,0,12] ++ [118,97,108,105,100,97,116,111,114,95,105,100,33,0,0,0,11,118,97,108,105,100,97,116,111,114,45,49,33,0,0,0] ++ [4,118,105,101,119,33,0,0,0,1,48] := by
  simp only [payload, fields, wire8, encodeFields, nativeSemantics, encodedText0, encodedText1, encodedText2, encodedText12, encodedText13, encodedText14, encodedText15, encodedText16, encodedText17, encodedText18, encodedText19, encodedText20, encodedText21, encodedText22, encodedText27, encodedText38, encodedText40, encodedText41, encodedText42, encodedText43, encodedText44, encodedText45, encodedText46, encodedText47, encodedText48]
  rfl
theorem nativeFrame8 : encodeFrame wire8 = NativeReceiptVectors.frame8 := by
  unfold encodeFrame; rw [payloadBytes8]; rfl
theorem frameValid8 : FrameValid wire8 := by
  constructor; · decide
  rw [nativeFrame8]; decide
theorem valid8 : VoteValid vote8 := by
  exact ⟨frameValid8, by decide, by decide, by decide, by decide, by decide⟩
theorem parsed8 : decodeFrame NativeReceiptVectors.frame8 = some vote8 := by
  exact decodeFrameFromEncoding vote8 NativeReceiptVectors.frame8 valid8 nativeFrame8
def fixtureSHA8 (b : Bytes) : Bytes := if b = votePreimage NativeReceiptVectors.frame8 then [238,245,233,55,52,143,25,95,41,152,79,110,232,203,213,138,177,72,71,218,163,6,247,64,99,148,176,159,38,70,17,240] else []
theorem hashBinding8 : voteId fixtureSHA8 NativeReceiptVectors.frame8 = some NativeReceiptVectors.receipt8.voteId := by
  simp only [voteId, fixtureSHA8, ↓reduceIte]; rfl
theorem linked8 : ReceiptLinked fixtureSHA8 NativeReceiptVectors.receipt8 vote8 := by
  exact ⟨rfl, rfl, rfl, hashBinding8⟩
theorem bound8 : bindReceipt fixtureSHA8 NativeReceiptVectors.receipt8 = some vote8 :=
  bindingFromComponents fixtureSHA8 NativeReceiptVectors.receipt8 vote8 parsed8 linked8
theorem fullReceipt8 : decodeReceipt fixtureSHA8 NativeReceiptVectors.nativeBytes8 = some (NativeReceiptVectors.receipt8,vote8) := by
  exact receiptFromNativeBytes fixtureSHA8 NativeReceiptVectors.receipt8 vote8 NativeReceiptVectors.nativeBytes8 NativeReceiptVectors.valid8 bound8 NativeReceiptVectors.exactBytes8
theorem sequenceMismatch8 : bindReceipt fixtureSHA8 {NativeReceiptVectors.receipt8 with sequence := 0} = none := by
  apply bindingRejectsMismatch fixtureSHA8 {NativeReceiptVectors.receipt8 with sequence := 0} vote8 parsed8
  intro h; have : (0:Nat) = 1 := h.1; contradiction
theorem contextMismatch8 : bindReceipt fixtureSHA8 {NativeReceiptVectors.receipt8 with context := []} = none := by
  apply bindingRejectsMismatch fixtureSHA8 {NativeReceiptVectors.receipt8 with context := []} vote8 parsed8
  intro h; have wrong := h.2.1
  have different : ([]:Bytes) ≠ vote8.wire.context := by decide
  exact different wrong
theorem actionMismatch8 : bindReceipt fixtureSHA8 {NativeReceiptVectors.receipt8 with action := 0} = none := by
  apply bindingRejectsMismatch fixtureSHA8 {NativeReceiptVectors.receipt8 with action := 0} vote8 parsed8
  intro h; have wrong := h.2.2.1
  have different : actionName 0 ≠ vote8.wire.kind := by decide
  exact different wrong
theorem idMismatch8 : bindReceipt fixtureSHA8 {NativeReceiptVectors.receipt8 with voteId := []} = none := by
  apply bindingRejectsMismatch fixtureSHA8 {NativeReceiptVectors.receipt8 with voteId := []} vote8 parsed8
  intro h; have wrong := h.2.2.2
  change voteId fixtureSHA8 NativeReceiptVectors.frame8 = some [] at wrong
  rw [hashBinding8] at wrong
  have different : NativeReceiptVectors.receipt8.voteId ≠ [] := by decide
  exact different (Option.some.inj wrong)

def wire9 : WireVote := ⟨ascii "sha256:7ae0b29609cc29c5be6fe78dd0d9201c065f1dc40074cd7a8ea73a8ee3c4b95f", ascii "sha256:25237c1323fbdae5feb16e5a60dfe9a12fb8881ed907b070adb8425c8a36ab9b", ascii "1", ascii "1", ascii "ABORT", ascii "round-vote-fixture", ascii "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", ascii "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd", ascii "validator-1", ascii "0"⟩
def vote9 : Vote := ⟨wire9, 1, 1, 0⟩
theorem payloadBytes9 : payload wire9 = [49,0,0,0,13,33,0,0,0,9,98,111,100,121,95,104,97,115,104,33,0,0,0,71,115,104,97,50,53,54,58,55] ++ [97,101,48,98,50,57,54,48,57,99,99,50,57,99,53,98,101,54,102,101,55,56,100,100,48,100,57,50,48,49,99,48] ++ [54,53,102,49,100,99,52,48,48,55,52,99,100,55,97,56,101,97,55,51,97,56,101,101,51,99,52,98,57,53,102,33] ++ [0,0,0,10,99,111,110,116,101,120,116,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,50,53,50,51,55,99] ++ [49,51,50,51,102,98,100,97,101,53,102,101,98,49,54,101,53,97,54,48,100,102,101,57,97,49,50,102,98,56,56,56] ++ [49,101,100,57,48,55,98,48,55,48,97,100,98,56,52,50,53,99,56,97,51,54,97,98,57,98,33,0,0,0,16,100] ++ [117,114,97,98,108,101,95,115,101,113,117,101,110,99,101,33,0,0,0,1,49,33,0,0,0,19,102,111,114,109,97,108] ++ [95,115,101,109,97,110,116,105,99,115,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,99,99,57,56,102,49,53] ++ [97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54] ++ [48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54,33,0,0,0,6,104,101] ++ [105,103,104,116,33,0,0,0,1,49,33,0,0,0,4,107,105,110,100,33,0,0,0,5,65,66,79,82,84,33,0,0] ++ [0,8,114,111,117,110,100,95,105,100,33,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45,102,105,120,116,117,114] ++ [101,33,0,0,0,14,115,99,104,101,109,97,95,118,101,114,115,105,111,110,33,0,0,0,5,49,46,48,46,48,33,0] ++ [0,0,12,115,105,103,110,97,116,117,114,101,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,101,101,101,101,101] ++ [101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101] ++ [101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,33,0,0,0,9] ++ [116,121,112,101,95,110,97,109,101,33,0,0,0,4,86,79,84,69,33,0,0,0,18,118,97,108,105,100,97,116,111,114] ++ [95,101,112,111,99,104,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,100,100,100,100,100,100,100,100,100,100,100] ++ [100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100] ++ [100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,33,0,0,0,12,118,97,108,105,100,97] ++ [116,111,114,95,105,100,33,0,0,0,11,118,97,108,105,100,97,116,111,114,45,49,33,0,0,0,4,118,105,101,119,33] ++ [0,0,0,1,48] := by
  simp only [payload, fields, wire9, encodeFields, nativeSemantics, encodedText0, encodedText1, encodedText2, encodedText3, encodedText13, encodedText14, encodedText15, encodedText16, encodedText17, encodedText18, encodedText19, encodedText20, encodedText21, encodedText22, encodedText25, encodedText35, encodedText38, encodedText40, encodedText42, encodedText43, encodedText44, encodedText45, encodedText46, encodedText47, encodedText48]
  rfl
theorem nativeFrame9 : encodeFrame wire9 = NativeReceiptVectors.frame9 := by
  unfold encodeFrame; rw [payloadBytes9]; rfl
theorem frameValid9 : FrameValid wire9 := by
  constructor; · decide
  rw [nativeFrame9]; decide
theorem valid9 : VoteValid vote9 := by
  exact ⟨frameValid9, by decide, by decide, by decide, by decide, by decide⟩
theorem parsed9 : decodeFrame NativeReceiptVectors.frame9 = some vote9 := by
  exact decodeFrameFromEncoding vote9 NativeReceiptVectors.frame9 valid9 nativeFrame9
def fixtureSHA9 (b : Bytes) : Bytes := if b = votePreimage NativeReceiptVectors.frame9 then [223,55,248,199,101,210,211,113,66,49,148,10,5,83,243,114,0,68,102,234,141,63,149,131,95,67,159,226,118,45,164,19] else []
theorem hashBinding9 : voteId fixtureSHA9 NativeReceiptVectors.frame9 = some NativeReceiptVectors.receipt9.voteId := by
  simp only [voteId, fixtureSHA9, ↓reduceIte]; rfl
theorem linked9 : ReceiptLinked fixtureSHA9 NativeReceiptVectors.receipt9 vote9 := by
  exact ⟨rfl, rfl, rfl, hashBinding9⟩
theorem bound9 : bindReceipt fixtureSHA9 NativeReceiptVectors.receipt9 = some vote9 :=
  bindingFromComponents fixtureSHA9 NativeReceiptVectors.receipt9 vote9 parsed9 linked9
theorem fullReceipt9 : decodeReceipt fixtureSHA9 NativeReceiptVectors.nativeBytes9 = some (NativeReceiptVectors.receipt9,vote9) := by
  exact receiptFromNativeBytes fixtureSHA9 NativeReceiptVectors.receipt9 vote9 NativeReceiptVectors.nativeBytes9 NativeReceiptVectors.valid9 bound9 NativeReceiptVectors.exactBytes9
theorem sequenceMismatch9 : bindReceipt fixtureSHA9 {NativeReceiptVectors.receipt9 with sequence := 0} = none := by
  apply bindingRejectsMismatch fixtureSHA9 {NativeReceiptVectors.receipt9 with sequence := 0} vote9 parsed9
  intro h; have : (0:Nat) = 1 := h.1; contradiction
theorem contextMismatch9 : bindReceipt fixtureSHA9 {NativeReceiptVectors.receipt9 with context := []} = none := by
  apply bindingRejectsMismatch fixtureSHA9 {NativeReceiptVectors.receipt9 with context := []} vote9 parsed9
  intro h; have wrong := h.2.1
  have different : ([]:Bytes) ≠ vote9.wire.context := by decide
  exact different wrong
theorem actionMismatch9 : bindReceipt fixtureSHA9 {NativeReceiptVectors.receipt9 with action := 0} = none := by
  apply bindingRejectsMismatch fixtureSHA9 {NativeReceiptVectors.receipt9 with action := 0} vote9 parsed9
  intro h; have wrong := h.2.2.1
  have different : actionName 0 ≠ vote9.wire.kind := by decide
  exact different wrong
theorem idMismatch9 : bindReceipt fixtureSHA9 {NativeReceiptVectors.receipt9 with voteId := []} = none := by
  apply bindingRejectsMismatch fixtureSHA9 {NativeReceiptVectors.receipt9 with voteId := []} vote9 parsed9
  intro h; have wrong := h.2.2.2
  change voteId fixtureSHA9 NativeReceiptVectors.frame9 = some [] at wrong
  rw [hashBinding9] at wrong
  have different : NativeReceiptVectors.receipt9.voteId ≠ [] := by decide
  exact different (Option.some.inj wrong)

theorem decimal_zero : parseDecimal (ascii "0") = some 0 := by decide
theorem decimal_maximum : parseDecimal (ascii "18446744073709551615") = some 18446744073709551615 := by decide
theorem decimal_overflow : parseDecimal (ascii "18446744073709551616") = none := by decide
theorem decimal_empty : parseDecimal (ascii "") = none := by decide
theorem decimal_leadingZero : parseDecimal (ascii "01") = none := by decide
theorem decimal_twoZeros : parseDecimal (ascii "00") = none := by decide
theorem decimal_sign : parseDecimal (ascii "+1") = none := by decide
theorem decimal_negative : parseDecimal (ascii "-1") = none := by decide
theorem decimal_space : parseDecimal (ascii "1 ") = none := by decide
theorem decimal_nondigit : parseDecimal (ascii "1x") = none := by decide
theorem badHashWidth : voteId (fun _ => [0]) [] = none := by decide
theorem printableBoundary : readText (textBytes [32,126]) = some ([32,126],[]) := by decide
theorem textControlReject : readText (textBytes [31]) = none := by decide
theorem textDeleteReject : readText (textBytes [127]) = none := by decide
theorem textTagReject : readText [32,0,0,0,0] = none := by decide
theorem structuralCountercheckNowRejects : decodeReceipt (fun _ => []) (encode NativeReceiptVectors.unauthenticated) = none := by
  simp only [decodeReceipt, NativeReceiptVectors.structuralDoesNotAuthenticate, bind, Option.bind]
  decide
end DeltaReduce.NativeVoteCodecVectors
