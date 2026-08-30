package io.deltareduce.node.benchmark;

import java.util.LinkedHashMap;
import java.util.Map;

/** Captures exact Java/native/Python identities for BenchmarkDefinition admission. */
public final class RuntimeIdentityCollector {
  public Map<String, String> collect(
      String nativeBuildId,
      String abiDescriptorId,
      String jdkProfileId,
      String nettyProfileId,
      String pythonProfileId,
      String deploymentProfile) {
    BenchmarkContracts.requireContentId(nativeBuildId, "native build ID");
    BenchmarkContracts.requireContentId(abiDescriptorId, "ABI descriptor ID");
    BenchmarkContracts.requireContentId(jdkProfileId, "JDK profile ID");
    BenchmarkContracts.requireContentId(nettyProfileId, "Netty profile ID");
    BenchmarkContracts.requireContentId(pythonProfileId, "Python profile ID");
    BenchmarkContracts.require(
        deploymentProfile.equals("EMBEDDED_FFM")
            || deploymentProfile.equals("ISOLATED_SIDECAR"),
        "invalid deployment profile");
    var result = new LinkedHashMap<String, String>();
    result.put("abi_descriptor_id", abiDescriptorId);
    result.put("deployment_profile", deploymentProfile);
    result.put("formal_semantics_id", BenchmarkContracts.FORMAL_SEMANTICS_ID);
    result.put("jdk_profile_id", jdkProfileId);
    result.put("native_build_id", nativeBuildId);
    result.put("netty_profile_id", nettyProfileId);
    result.put("python_profile_id", pythonProfileId);
    return Map.copyOf(result);
  }
}
