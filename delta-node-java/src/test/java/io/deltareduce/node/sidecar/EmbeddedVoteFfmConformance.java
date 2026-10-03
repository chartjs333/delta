package io.deltareduce.node.sidecar;

import java.nio.file.Path;

/** Short real-FFM RECORD_VOTE/restart/replay conformance check. */
public final class EmbeddedVoteFfmConformance {
  private EmbeddedVoteFfmConformance() {}

  public static void main(String[] arguments) throws Throwable {
    if (arguments.length != 3) {
      throw new IllegalArgumentException(
          "usage: EmbeddedVoteFfmConformance <delta-ffi-library> "
              + "<durable-directory> <native-vote-fixture>");
    }
    SidecarComparisonCapture.embeddedVoteConformance(
        Path.of(arguments[0]), Path.of(arguments[1]), Path.of(arguments[2]));
    System.out.println(
        "{\"profile_id\":\"EMBEDDED_FFM\",\"status\":\"PASS\","
            + "\"type_name\":\"DELTA_EMBEDDED_VOTE_FFM_CONFORMANCE\"}");
  }
}
