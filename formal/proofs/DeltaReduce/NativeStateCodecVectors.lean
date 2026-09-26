import DeltaReduce.NativeStateBytes
import DeltaReduce.NativeWalScanVectors
set_option maxRecDepth 32768
set_option maxHeartbeats 1000000
namespace DeltaReduce.NativeStateCodecVectors
open NativeReceiptBytes NativeVoteBytes NativeStateBytes
theorem text0 : textBytes (ascii "0") = [33,0,0,0,1,48] := by decide
theorem text1 : textBytes (ascii "1") = [33,0,0,0,1,49] := by decide
theorem text2 : textBytes (ascii "1.0.0") = [33,0,0,0,5,49,46,48,46,48] := by decide
theorem text3 : textBytes (ascii "11") = [33,0,0,0,2,49,49] := by decide
theorem text4 : textBytes (ascii "AVAILABLE") = [33,0,0,0,9,65,86,65,73,76,65,66,76,69] := by decide
theorem text5 : textBytes (ascii "COMMAND") = [33,0,0,0,7,67,79,77,77,65,78,68] := by decide
theorem text6 : textBytes (ascii "ELIGIBLE") = [33,0,0,0,8,69,76,73,71,73,66,76,69] := by decide
theorem text7 : textBytes (ascii "FINALIZE_INPUT_FREEZE") = [33,0,0,0,21,70,73,78,65,76,73,90,69,95,73,78,80,85,84,95,70,82,69,69,90,69] := by decide
theorem text8 : textBytes (ascii "ROUND_STATE") = [33,0,0,0,11,82,79,85,78,68,95,83,84,65,84,69] := by decide
theorem text9 : textBytes (ascii "actor_id") = [33,0,0,0,8,97,99,116,111,114,95,105,100] := by decide
theorem text10 : textBytes (ascii "available_ticket_count") = [33,0,0,0,22,97,118,97,105,108,97,98,108,101,95,116,105,99,107,101,116,95,99,111,117,110,116] := by decide
theorem text11 : textBytes (ascii "body_hash") = [33,0,0,0,9,98,111,100,121,95,104,97,115,104] := by decide
theorem text12 : textBytes (ascii "command_kind") = [33,0,0,0,12,99,111,109,109,97,110,100,95,107,105,110,100] := by decide
theorem text13 : textBytes (ascii "committed_ticket_count") = [33,0,0,0,22,99,111,109,109,105,116,116,101,100,95,116,105,99,107,101,116,95,99,111,117,110,116] := by decide
theorem text14 : textBytes (ascii "config_id") = [33,0,0,0,9,99,111,110,102,105,103,95,105,100] := by decide
theorem text15 : textBytes (ascii "durable_sequence") = [33,0,0,0,16,100,117,114,97,98,108,101,95,115,101,113,117,101,110,99,101] := by decide
theorem text16 : textBytes (ascii "formal_semantics_id") = [33,0,0,0,19,102,111,114,109,97,108,95,115,101,109,97,110,116,105,99,115,95,105,100] := by decide
theorem text17 : textBytes (ascii "freeze-after-isc") = [33,0,0,0,16,102,114,101,101,122,101,45,97,102,116,101,114,45,105,115,99] := by decide
theorem text18 : textBytes (ascii "height") = [33,0,0,0,6,104,101,105,103,104,116] := by decide
theorem text19 : textBytes (ascii "logical_tick") = [33,0,0,0,12,108,111,103,105,99,97,108,95,116,105,99,107] := by decide
theorem text20 : textBytes (ascii "parent_checkpoint_id") = [33,0,0,0,20,112,97,114,101,110,116,95,99,104,101,99,107,112,111,105,110,116,95,105,100] := by decide
theorem text21 : textBytes (ascii "phase") = [33,0,0,0,5,112,104,97,115,101] := by decide
theorem text22 : textBytes (ascii "request_id") = [33,0,0,0,10,114,101,113,117,101,115,116,95,105,100] := by decide
theorem text23 : textBytes (ascii "round-vote-fixture") = [33,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45,102,105,120,116,117,114,101] := by decide
theorem text24 : textBytes (ascii "round_id") = [33,0,0,0,8,114,111,117,110,100,95,105,100] := by decide
theorem text25 : textBytes (ascii "schema_version") = [33,0,0,0,14,115,99,104,101,109,97,95,118,101,114,115,105,111,110] := by decide
theorem text26 : textBytes (ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111") = [33,0,0,0,71,115,104,97,50,53,54,58,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49] := by decide
theorem text27 : textBytes (ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222") = [33,0,0,0,71,115,104,97,50,53,54,58,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50] := by decide
theorem text28 : textBytes (ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333") = [33,0,0,0,71,115,104,97,50,53,54,58,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51] := by decide
theorem text29 : textBytes (ascii "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6") = [33,0,0,0,71,115,104,97,50,53,54,58,99,99,57,56,102,49,53,97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54,48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54] := by decide
theorem text30 : textBytes (ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc") = [33,0,0,0,71,115,104,97,50,53,54,58,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99] := by decide
theorem text31 : textBytes (ascii "state_root") = [33,0,0,0,10,115,116,97,116,101,95,114,111,111,116] := by decide
theorem text32 : textBytes (ascii "ticket_count") = [33,0,0,0,12,116,105,99,107,101,116,95,99,111,117,110,116] := by decide
theorem text33 : textBytes (ascii "type_name") = [33,0,0,0,9,116,121,112,101,95,110,97,109,101] := by decide
theorem text34 : textBytes (ascii "validator-1") = [33,0,0,0,11,118,97,108,105,100,97,116,111,114,45,49] := by decide
theorem text35 : textBytes (ascii "view") = [33,0,0,0,4,118,105,101,119] := by decide
def wire1 : WireCommand := ⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_INPUT_FREEZE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩
def value1 : Command := ⟨wire1,1,11,0⟩
def raw1 : Bytes := NativeWalVectors.command3
theorem payload1 : NativeStateBytes.payload (commandFields wire1) = [49,0,0,0,11,33,0,0,0,8,97,99,116,111,114,95,105,100,33,0,0,0,11,118,97,108,105,100,97,116,111,114,45,49,33,0,0,0,9,98,111,100,121,95,104,97,115,104,33,0,0,0,71,115,104,97,50,53,54,58,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,33,0,0,0,12,99,111,109,109,97,110,100,95,107,105,110,100,33,0,0,0,21,70,73,78,65,76,73,90,69,95,73,78,80,85,84,95,70,82,69,69,90,69,33,0,0,0,19,102,111,114,109,97,108,95,115,101,109,97,110,116,105,99,115,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,99,99,57,56,102,49,53,97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54,48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54,33,0,0,0,6,104,101,105,103,104,116,33,0,0,0,1,49,33,0,0,0,12,108,111,103,105,99,97,108,95,116,105,99,107,33,0,0,0,2,49,49,33,0,0,0,10,114,101,113,117,101,115,116,95,105,100,33,0,0,0,16,102,114,101,101,122,101,45,97,102,116,101,114,45,105,115,99,33,0,0,0,8,114,111,117,110,100,95,105,100,33,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45,102,105,120,116,117,114,101,33,0,0,0,14,115,99,104,101,109,97,95,118,101,114,115,105,111,110,33,0,0,0,5,49,46,48,46,48,33,0,0,0,9,116,121,112,101,95,110,97,109,101,33,0,0,0,7,67,79,77,77,65,78,68,33,0,0,0,4,118,105,101,119,33,0,0,0,1,48] := by
  simp only [NativeStateBytes.payload,commandFields,wire1,NativeStateBytes.encodeFields,scalarBytes,nativeSemantics,text0,text1,text2,text3,text5,text7,text9,text11,text12,text16,text17,text18,text19,text22,text23,text24,text25,text29,text30,text33,text34,text35]
  rfl
theorem bytes1 : encodeCommand wire1 = raw1 := by
  unfold encodeCommand encodeEnvelope; rw [payload1]; rfl
theorem frame1 : EnvelopeValid 6 (commandFields wire1) := by
  constructor; · decide
  change (encodeCommand wire1).length ≤ maxEnvelope; rw [bytes1]; decide
theorem valid1 : CommandValid value1 := ⟨frame1,by decide,by decide,by decide,by decide,by decide,by decide,by decide,by decide⟩
theorem parsed1 : decodeCommand raw1 = some value1 :=
  commandFromBytes value1 raw1 valid1 bytes1
def sha1 (b : Bytes) : Bytes := if b = contentPreimage commandDomain raw1 then [247,6,234,55,26,158,241,207,15,221,74,63,2,195,236,57,24,236,49,74,11,54,136,234,198,106,131,182,46,201,2,15] else []
theorem nativeId1 : contentId sha1 commandDomain raw1 = some (ascii "sha256:f706ea371a9ef1cf0fdd4a3f02c3ec3918ec314a0b3688eac66a83b62ec9020f") := by
  simp only [contentId,sha1,↓reduceIte]; rfl
def wire2 : WireState := ⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ELIGIBLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩
def value2 : State := ⟨wire2,1,1,0⟩
def raw2 : Bytes := NativeWalVectors.state3
theorem payload2 : NativeStateBytes.payload (stateFields wire2) = [49,0,0,0,14,33,0,0,0,22,97,118,97,105,108,97,98,108,101,95,116,105,99,107,101,116,95,99,111,117,110,116,16,0,0,0,0,0,0,0,1,33,0,0,0,22,99,111,109,109,105,116,116,101,100,95,116,105,99,107,101,116,95,99,111,117,110,116,16,0,0,0,0,0,0,0,1,33,0,0,0,9,99,111,110,102,105,103,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,33,0,0,0,16,100,117,114,97,98,108,101,95,115,101,113,117,101,110,99,101,33,0,0,0,1,49,33,0,0,0,19,102,111,114,109,97,108,95,115,101,109,97,110,116,105,99,115,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,99,99,57,56,102,49,53,97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54,48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54,33,0,0,0,6,104,101,105,103,104,116,33,0,0,0,1,49,33,0,0,0,20,112,97,114,101,110,116,95,99,104,101,99,107,112,111,105,110,116,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,33,0,0,0,5,112,104,97,115,101,33,0,0,0,8,69,76,73,71,73,66,76,69,33,0,0,0,8,114,111,117,110,100,95,105,100,33,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45,102,105,120,116,117,114,101,33,0,0,0,14,115,99,104,101,109,97,95,118,101,114,115,105,111,110,33,0,0,0,5,49,46,48,46,48,33,0,0,0,10,115,116,97,116,101,95,114,111,111,116,33,0,0,0,71,115,104,97,50,53,54,58,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,33,0,0,0,12,116,105,99,107,101,116,95,99,111,117,110,116,16,0,0,0,0,0,0,0,1,33,0,0,0,9,116,121,112,101,95,110,97,109,101,33,0,0,0,11,82,79,85,78,68,95,83,84,65,84,69,33,0,0,0,4,118,105,101,119,33,0,0,0,1,48] := by
  simp only [NativeStateBytes.payload,stateFields,wire2,NativeStateBytes.encodeFields,scalarBytes,nativeSemantics,text0,text1,text2,text6,text8,text10,text13,text14,text15,text16,text18,text20,text21,text23,text24,text25,text26,text27,text28,text29,text31,text32,text33,text35]
  rfl
theorem bytes2 : encodeState wire2 = raw2 := by
  unfold encodeState encodeEnvelope; rw [payload2]; rfl
theorem frame2 : EnvelopeValid 5 (stateFields wire2) := by
  constructor; · decide
  change (encodeState wire2).length ≤ maxEnvelope; rw [bytes2]; decide
theorem valid2 : StateValid value2 := ⟨frame2,by decide,by decide,by decide,by decide,by decide,by decide,by decide,by decide,by decide,by decide,by decide⟩
theorem parsed2 : decodeState raw2 = some value2 :=
  stateFromBytes value2 raw2 valid2 bytes2
def sha2 (b : Bytes) : Bytes := if b = contentPreimage stateDomain raw2 then [95,166,46,15,47,181,230,48,121,65,205,81,1,93,56,0,216,132,47,221,78,231,206,240,213,195,32,123,16,63,225,125] else []
theorem nativeId2 : contentId sha2 stateDomain raw2 = some (ascii "sha256:5fa62e0f2fb5e6307941cd51015d3800d8842fdd4ee7cef0d5c3207b103fe17d") := by
  simp only [contentId,sha2,↓reduceIte]; rfl
def wire3 : WireState := ⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩
def value3 : State := ⟨wire3,0,1,0⟩
def raw3 : Bytes := [68,82,67,49,1,0,0,5,0,0,2,151,49,0,0,0,14,33,0,0,0,22,97,118,97,105,108,97,98,108,101,95,116,105,99,107,101,116,95,99,111,117,110,116,16,0,0,0,0,0,0,0,1,33,0,0,0,22,99,111,109,109,105,116,116,101,100,95,116,105,99,107,101,116,95,99,111,117,110,116,16,0,0,0,0,0,0,0,1,33,0,0,0,9,99,111,110,102,105,103,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,33,0,0,0,16,100,117,114,97,98,108,101,95,115,101,113,117,101,110,99,101,33,0,0,0,1,48,33,0,0,0,19,102,111,114,109,97,108,95,115,101,109,97,110,116,105,99,115,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,99,99,57,56,102,49,53,97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54,48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54,33,0,0,0,6,104,101,105,103,104,116,33,0,0,0,1,49,33,0,0,0,20,112,97,114,101,110,116,95,99,104,101,99,107,112,111,105,110,116,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,33,0,0,0,5,112,104,97,115,101,33,0,0,0,9,65,86,65,73,76,65,66,76,69,33,0,0,0,8,114,111,117,110,100,95,105,100,33,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45,102,105,120,116,117,114,101,33,0,0,0,14,115,99,104,101,109,97,95,118,101,114,115,105,111,110,33,0,0,0,5,49,46,48,46,48,33,0,0,0,10,115,116,97,116,101,95,114,111,111,116,33,0,0,0,71,115,104,97,50,53,54,58,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,33,0,0,0,12,116,105,99,107,101,116,95,99,111,117,110,116,16,0,0,0,0,0,0,0,1,33,0,0,0,9,116,121,112,101,95,110,97,109,101,33,0,0,0,11,82,79,85,78,68,95,83,84,65,84,69,33,0,0,0,4,118,105,101,119,33,0,0,0,1,48]
theorem payload3 : NativeStateBytes.payload (stateFields wire3) = [49,0,0,0,14,33,0,0,0,22,97,118,97,105,108,97,98,108,101,95,116,105,99,107,101,116,95,99,111,117,110,116,16,0,0,0,0,0,0,0,1,33,0,0,0,22,99,111,109,109,105,116,116,101,100,95,116,105,99,107,101,116,95,99,111,117,110,116,16,0,0,0,0,0,0,0,1,33,0,0,0,9,99,111,110,102,105,103,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,49,33,0,0,0,16,100,117,114,97,98,108,101,95,115,101,113,117,101,110,99,101,33,0,0,0,1,48,33,0,0,0,19,102,111,114,109,97,108,95,115,101,109,97,110,116,105,99,115,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,99,99,57,56,102,49,53,97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54,48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54,33,0,0,0,6,104,101,105,103,104,116,33,0,0,0,1,49,33,0,0,0,20,112,97,114,101,110,116,95,99,104,101,99,107,112,111,105,110,116,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,33,0,0,0,5,112,104,97,115,101,33,0,0,0,9,65,86,65,73,76,65,66,76,69,33,0,0,0,8,114,111,117,110,100,95,105,100,33,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45,102,105,120,116,117,114,101,33,0,0,0,14,115,99,104,101,109,97,95,118,101,114,115,105,111,110,33,0,0,0,5,49,46,48,46,48,33,0,0,0,10,115,116,97,116,101,95,114,111,111,116,33,0,0,0,71,115,104,97,50,53,54,58,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,51,33,0,0,0,12,116,105,99,107,101,116,95,99,111,117,110,116,16,0,0,0,0,0,0,0,1,33,0,0,0,9,116,121,112,101,95,110,97,109,101,33,0,0,0,11,82,79,85,78,68,95,83,84,65,84,69,33,0,0,0,4,118,105,101,119,33,0,0,0,1,48] := by
  simp only [NativeStateBytes.payload,stateFields,wire3,NativeStateBytes.encodeFields,scalarBytes,nativeSemantics,text0,text1,text2,text4,text8,text10,text13,text14,text15,text16,text18,text20,text21,text23,text24,text25,text26,text27,text28,text29,text31,text32,text33,text35]
  rfl
theorem bytes3 : encodeState wire3 = raw3 := by
  unfold encodeState encodeEnvelope; rw [payload3]; rfl
theorem frame3 : EnvelopeValid 5 (stateFields wire3) := by
  constructor; · decide
  change (encodeState wire3).length ≤ maxEnvelope; rw [bytes3]; decide
theorem valid3 : StateValid value3 := ⟨frame3,by decide,by decide,by decide,by decide,by decide,by decide,by decide,by decide,by decide,by decide,by decide⟩
theorem parsed3 : decodeState raw3 = some value3 :=
  stateFromBytes value3 raw3 valid3 bytes3
def sha3 (b : Bytes) : Bytes := if b = contentPreimage stateDomain raw3 then [7,219,248,225,40,142,9,19,91,121,173,199,157,56,236,178,129,241,101,248,62,217,46,5,135,95,198,180,237,235,41,121] else []
theorem nativeId3 : contentId sha3 stateDomain raw3 = some (ascii "sha256:07dbf8e1288e09135b79adc79d38ecb281f165f83ed92e05875fc6b4edeb2979") := by
  simp only [contentId,sha3,↓reduceIte]; rfl
theorem nativeEntryParsed : inspectEntry NativeWalVectors.entry3 = some (value1,value2) :=
  entryFromComponents NativeWalVectors.entry3 value1 value2 rfl parsed1 parsed2
theorem nativeAllEntrySequence : NativeWalVectors.entry3.sequence = 2 ∧ value2.sequence = 1 := by decide
theorem scannedOriginalCommand : NativeWalVectors.entry3.sequence = 2 ∧ NativeWalVectors.entry3.kind = 1 ∧
    NativeWalBytes.encode NativeWalScanVectors.sha NativeWalVectors.entry3 = NativeWalVectors.raw3 ∧
    encodeCommand value1.wire = NativeWalVectors.entry3.command ∧ encodeState value2.wire = NativeWalVectors.entry3.state :=
  scannedCommandOrigin NativeWalScanVectors.sha NativeWalScanVectors.stream NativeWalScanVectors.fullResult
    1 ⟨NativeWalVectors.entry3,NativeWalVectors.raw3⟩ value1 value2 NativeWalScanVectors.checkedNativeStream rfl nativeEntryParsed
theorem nativeVoteCannotBeStateCommand : inspectEntry NativeWalVectors.entry2 = none := by decide
theorem commandReject0 : interpretCommand {wire1 with actor := []} = none := by decide
theorem commandReject1 : interpretCommand {wire1 with commandKind := []} = none := by decide
theorem commandReject2 : interpretCommand {wire1 with request := []} = none := by decide
theorem commandReject3 : interpretCommand {wire1 with round := []} = none := by decide
theorem commandReject4 : interpretCommand {wire1 with height := ascii "00"} = none := by decide
theorem commandReject5 : interpretCommand {wire1 with tick := ascii "-1"} = none := by decide
theorem commandReject6 : interpretCommand {wire1 with view := ascii "18446744073709551616"} = none := by decide
theorem commandReject7 : interpretCommand {wire1 with body := ascii "sha256:bad"} = none := by decide
theorem stateReject0 : interpretState {wire2 with available := 2} = none := by decide
theorem stateReject1 : interpretState {wire2 with committed := 0} = none := by decide
theorem stateReject2 : interpretState {wire2 with total := 0} = none := by decide
theorem stateReject3 : interpretState {wire2 with total := 256^4} = none := by decide
theorem stateReject4 : interpretState {wire2 with phase := ascii "UNKNOWN"} = none := by decide
theorem stateReject5 : interpretState {wire2 with round := []} = none := by decide
theorem stateReject6 : interpretState {wire2 with sequence := ascii "01"} = none := by decide
theorem stateReject7 : interpretState {wire2 with view := ascii "18446744073709551616"} = none := by decide
theorem stateReject8 : interpretState {wire2 with parent := []} = none := by decide
theorem stateReject9 : interpretState {wire2 with config := []} = none := by decide
theorem stateReject10 : interpretState {wire2 with root := []} = none := by decide
theorem commandKindIsNotAdmission : (interpretCommand {wire1 with commandKind := ascii "UNKNOWN_COMMAND"}).isSome = true := by decide
theorem changedRootCanParse : (interpretState {wire2 with root := ascii "sha256:0000000000000000000000000000000000000000000000000000000000000000"}).isSome = true := by decide
theorem maximumTime : (interpretCommand {wire1 with tick := ascii "18446744073709551615"}).isSome = true := by decide
theorem maximumCount : (interpretState {wire2 with total := 256^4-1}).isSome = true := by decide
theorem zeroStateSequenceAllowed : (interpretState {wire2 with sequence := ascii "0"}).isSome = true := by decide
theorem unsignedTagRequired : readScalar .uint (textBytes (ascii "1")) = none := by decide
theorem unsignedUsesEightBytes : readScalar .uint ([16]++be 8 4294967296) = some (.uint 4294967296,[]) := by decide
theorem truncatedUnsigned : readScalar .uint ([16]++be 4 1) = none := by decide
theorem wrongCommandType : readCommand (header 5 ++ sizedBytes (NativeStateBytes.payload (commandFields wire1))) = none := by decide
theorem commandTrailingByte : decodeCommand (raw1++[0]) = none := by decide
theorem stateTrailingByte : decodeState (raw2++[0]) = none := by decide
theorem commandFieldsWrongConstants : commandValues ((commandFields wire1).map Prod.snd |>.set 3 (.text [])) = none := by decide
theorem stateFieldsWrongConstants : stateValues ((stateFields wire2).map Prod.snd |>.set 4 (.text [])) = none := by decide
end DeltaReduce.NativeStateCodecVectors
