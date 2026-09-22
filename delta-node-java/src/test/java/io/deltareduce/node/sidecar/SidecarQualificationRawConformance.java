package io.deltareduce.node.sidecar;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Fast exact-byte checks for the qualification canonical-JSON writer. */
public final class SidecarQualificationRawConformance {
  private SidecarQualificationRawConformance() {}

  public static void main(String[] arguments) throws Exception {
    require(arguments.length == 0, "SidecarQualificationRawConformance takes no arguments");
    var first = new LinkedHashMap<String, Object>();
    first.put("z", List.of(3, 2, 1));
    first.put("a", Map.of("y", true, "b", "value"));
    first.put("m", 7);
    var second = new LinkedHashMap<String, Object>();
    second.put("m", 7);
    second.put("a", Map.of("b", "value", "y", true));
    second.put("z", List.of(3, 2, 1));
    var expected =
        "{\"a\":{\"b\":\"value\",\"y\":true},\"m\":7,\"z\":[3,2,1]}"
            .getBytes(StandardCharsets.UTF_8);
    var firstBytes = SidecarQualificationRaw.canonicalBytes(first);
    var secondBytes = SidecarQualificationRaw.canonicalBytes(second);
    require(Arrays.equals(firstBytes, expected), "canonical JSON bytes are not lexicographic");
    require(Arrays.equals(firstBytes, secondBytes), "insertion order changed canonical JSON");

    var evidenceOne = SidecarQualificationRaw.evidence(Map.of("OBSERVED", true), first);
    var evidenceTwo = SidecarQualificationRaw.evidence(Map.of("OBSERVED", true), second);
    require(evidenceOne.sha256().equals(evidenceTwo.sha256()),
        "insertion order changed canonical evidence digest");

    var directory = Files.createTempDirectory("sidecar-raw-conformance-");
    var output = directory.resolve("raw.json");
    try {
      SidecarQualificationRaw.writeAtomically(output, first);
      var onDisk = Files.readAllBytes(output);
      var expectedWithNewline = Arrays.copyOf(expected, expected.length + 1);
      expectedWithNewline[expected.length] = (byte) '\n';
      require(Arrays.equals(onDisk, expectedWithNewline),
          "atomic raw output differs from canonical bytes plus LF");
    } finally {
      Files.deleteIfExists(output);
      Files.deleteIfExists(directory);
    }
    System.out.println("sidecar qualification raw JSON canonical ordering exact");
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalStateException(message);
    }
  }
}
