package io.deltareduce.node.sidecar;

/** Qualification-only entry point for the sealed PR50 scheduler/environment diagnostic. */
public final class SidecarDiagnosticCapture {
  private SidecarDiagnosticCapture() {}

  public static void main(String[] arguments) throws Throwable {
    SidecarComparisonCapture.runDiagnostic(arguments);
  }
}
