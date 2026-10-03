package io.deltareduce.node.sidecar;

/** Deterministic parser/arithmetic check; it never starts a diagnostic campaign. */
public final class SidecarDiagnosticCaptureDryRun {
  private SidecarDiagnosticCaptureDryRun() {}

  public static void main(String[] arguments) {
    if (arguments.length != 0) {
      throw new IllegalArgumentException("diagnostic dry-run accepts no arguments");
    }
    SidecarComparisonCapture.diagnosticSelfTest();
    System.out.println(
        "{\"authority\":\"DIAGNOSTIC_ONLY\",\"available_processors\":"
            + Runtime.getRuntime().availableProcessors()
            + ",\"offers_per_second\":100,"
            + "\"status\":\"PASS\",\"type_name\":\"FEATURE010_SIDECAR_DIAGNOSTIC_DRY_RUN\"}");
  }
}
