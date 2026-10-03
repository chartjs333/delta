package io.deltareduce.node.sidecar;

/** Fast, non-qualifying self-test for the Feature-010 comparison capture harness. */
public final class SidecarComparisonCaptureDryRun {
  private SidecarComparisonCaptureDryRun() {}

  public static void main(String[] arguments) throws Exception {
    if (arguments.length != 0) {
      throw new IllegalArgumentException("SidecarComparisonCaptureDryRun takes no arguments");
    }
    SidecarComparisonCapture.selfTest();
    System.out.println(
        "{\"execution_class\":\"NON_QUALIFYING_SELF_TEST\","
            + "\"status\":\"PASS\","
            + "\"type_name\":\"FEATURE010_SIDECAR_CAPTURE_DRY_RUN\"}");
  }
}
