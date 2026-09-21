import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;

/** Standalone TEST_FIXTURE byte/hash consumer; it has no node-runtime authority. */
public final class FoundationFixtureConsumer {
  private static final String[] ARTIFACT_NAMES = {
      "arm", "attestation", "definition", "evidence_manifest", "evidence_node", "result",
      "run_manifest"
  };
  private static final String[] EXPECTED_IDS = {
      "sha256:476b466992370b989ac24ef63569bb179b1c3ac9e215b8ce01fe68054c5c9b73",
      "sha256:0ce29dfbdab797db41850031ec6ee4fdd01fe8ea34ec1e4e0a63ba31ced39892",
      "sha256:32c8e884d1d93a3de77881d30df2bf78ed45d59017b38ca1318664e77485a449",
      "sha256:4ae1806f1ce4fb165d698f6d28648e4287b47689332c8859df008695ad8b6308",
      "sha256:50c42bee228b98c5bb58238251ef897fdc2a2286027f4f2f011dfc86b6e8efbb",
      "sha256:1f29322d968fd99538395765dafea1cc37c6d052cdb5160ca543b289d7b95faa",
      "sha256:e837f264cc59a92a1537aa24d44cefe9410008f2c826a5c50e3172455309e2cc"
  };
  private static final String EXPECTED_CANONICAL =
      "{\"adapter_id\":\"sha256:4c2b37696dd07c8b7defff21cd9248e987b5d4a397a65bd59540a8e2723756c6\","
          + "\"arm_kind\":\"DELTAREDUCE\",\"authority_scope\":\"BENCHMARK_GOVERNANCE_ONLY\","
          + "\"deployment_profile\":\"EMBEDDED_FFM\",\"evidence_class\":\"TEST_FIXTURE\","
          + "\"formal_semantics_id\":\"sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6\","
          + "\"gate_eligible\":false,\"model_mode\":\"QLORA_ADAPTER\","
          + "\"primary_eligible\":false,\"schema_version\":\"1.0.0\","
          + "\"topology\":\"HIERARCHICAL\",\"type_name\":\"BENCHMARK_ARM\"}";

  private FoundationFixtureConsumer() {}

  public static void main(String[] args) throws Exception {
    if (args.length != 1) {
      throw new IllegalArgumentException("fixture path required");
    }
    String fixture = Files.readString(Path.of(args[0]), StandardCharsets.UTF_8);
    for (int index = 0; index < ARTIFACT_NAMES.length; index++) {
      String prefix = "\"" + ARTIFACT_NAMES[index] + "\":{\"bytes_hex\":\"";
      int start = fixture.indexOf(prefix);
      if (start < 0) {
        throw new IllegalStateException(ARTIFACT_NAMES[index] + " vector missing");
      }
      start += prefix.length();
      int end = fixture.indexOf('"', start);
      byte[] canonical = HexFormat.of().parseHex(fixture.substring(start, end));
      if (index == 0 && !EXPECTED_CANONICAL.equals(new String(canonical, StandardCharsets.UTF_8))) {
        throw new IllegalStateException("canonical bytes differ");
      }
      String digest = "sha256:" + HexFormat.of().formatHex(
          MessageDigest.getInstance("SHA-256").digest(canonical));
      if (!EXPECTED_IDS[index].equals(digest)) {
        throw new IllegalStateException(ARTIFACT_NAMES[index] + " content ID differs");
      }
      String storedPrefix = ",\"content_id\":\"";
      int storedStart = fixture.indexOf(storedPrefix, end);
      if (storedStart < 0) {
        throw new IllegalStateException(ARTIFACT_NAMES[index] + " stored content ID missing");
      }
      storedStart += storedPrefix.length();
      int storedEnd = fixture.indexOf('"', storedStart);
      if (!digest.equals(fixture.substring(storedStart, storedEnd))) {
        throw new IllegalStateException(ARTIFACT_NAMES[index] + " stored content ID differs");
      }
    }
    System.out.println(EXPECTED_IDS[0]);
  }
}
