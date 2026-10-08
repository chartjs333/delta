import RetentionSource

set_option maxRecDepth 4096
set_option maxHeartbeats 2000000

namespace DeltaReduce.RetentionSource
open NativeVoteBytes (ascii)

-- diagnostic-1; original raw E may contain binary bytes.
example : decode (ascii "{\"obligation_ref\":{\"byte_length\":\"17\",\"sha256\":\"6f2c1107c99ce2d4c9d8b13d898853221bc8a1b4e64265465d27ef2a7def0a91\"},\"retention_epoch_id\":\"retention-1\",\"schema_version\":\"1.0.0\",\"type_name\":\"STORAGE_RETENTION_POLICY_SOURCE\"}") =
  some ⟨ ascii "17", ascii "6f2c1107c99ce2d4c9d8b13d898853221bc8a1b4e64265465d27ef2a7def0a91",
     ascii "retention-1"⟩ := by decide

-- diagnostic-2; original raw E may contain binary bytes.
example : decode (ascii "{\"obligation_ref\":{\"byte_length\":\"6\",\"sha256\":\"8ab1d708b7af1c2380f11097d29278a90281f43b29a0dfbb1559de6103af40b4\"},\"retention_epoch_id\":\"epoch-2\",\"schema_version\":\"1.0.0\",\"type_name\":\"STORAGE_RETENTION_POLICY_SOURCE\"}") =
  some ⟨ ascii "6", ascii "8ab1d708b7af1c2380f11097d29278a90281f43b29a0dfbb1559de6103af40b4",
     ascii "epoch-2"⟩ := by decide

-- diagnostic-3; original raw E may contain binary bytes.
example : decode (ascii "{\"obligation_ref\":{\"byte_length\":\"1\",\"sha256\":\"2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881\"},\"retention_epoch_id\":\"zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz\",\"schema_version\":\"1.0.0\",\"type_name\":\"STORAGE_RETENTION_POLICY_SOURCE\"}") =
  some ⟨ ascii "1", ascii "2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881",
     ascii "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"⟩ := by decide

example : decode (ascii "{\"obligation_ref\":{\"byte_length\":\"1\",\"byte_length\":\"1\"}}") = none := by decide

end DeltaReduce.RetentionSource
