package io.deltareduce.node.benchmark;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Duration;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.Objects;
import java.util.concurrent.TimeUnit;

/** Bounded local-IPC benchmark path with explicit native-process crash containment. */
public final class SidecarRunner implements ProcessProfileRunner {
  public interface SidecarEndpoint {
    byte[] execute(String requestId, byte[] canonicalBytes);

    void crash();

    void restart();
  }

  /** Real local child-process endpoint using a bounded line protocol and persistent replay journal. */
  public static final class ExternalEndpoint implements SidecarEndpoint, AutoCloseable {
    private final Path executable;
    private final Path journal;
    private final int maximumPayloadBytes;
    private Process process;
    private BufferedWriter writer;
    private BufferedReader reader;

    public ExternalEndpoint(Path executable, Path journal, int maximumPayloadBytes) {
      this.executable = Objects.requireNonNull(executable, "executable").toAbsolutePath();
      this.journal = Objects.requireNonNull(journal, "journal").toAbsolutePath();
      BenchmarkContracts.require(maximumPayloadBytes > 0, "invalid sidecar payload bound");
      this.maximumPayloadBytes = maximumPayloadBytes;
      start();
    }

    @Override
    public synchronized byte[] execute(String requestId, byte[] canonicalBytes) {
      BenchmarkContracts.require(
          canonicalBytes != null && canonicalBytes.length <= maximumPayloadBytes,
          "sidecar request too large");
      try {
        writer.write("ECHO " + requestId + " " + HexFormat.of().formatHex(canonicalBytes));
        writer.newLine();
        writer.flush();
        String response = reader.readLine();
        if (response == null || !response.startsWith("OK ")) {
          throw new IllegalStateException("sidecar response invalid: " + response);
        }
        String[] fields = response.split(" ", 4);
        if (fields.length != 4) {
          throw new IllegalStateException("sidecar response malformed");
        }
        return HexFormat.of().parseHex(fields[3]);
      } catch (IOException error) {
        throw new IllegalStateException("sidecar I/O failed", error);
      }
    }

    @Override
    public synchronized void crash() {
      try {
        writer.write("CRASH");
        writer.newLine();
        writer.flush();
        if (!process.waitFor(Duration.ofSeconds(5).toMillis(), TimeUnit.MILLISECONDS)) {
          process.destroyForcibly();
          throw new IllegalStateException("sidecar did not crash within bound");
        }
      } catch (IOException error) {
        throw new IllegalStateException("sidecar crash injection failed", error);
      } catch (InterruptedException error) {
        Thread.currentThread().interrupt();
        throw new IllegalStateException("sidecar crash wait interrupted", error);
      }
    }

    @Override
    public synchronized void restart() {
      BenchmarkContracts.require(!process.isAlive(), "sidecar still running");
      start();
    }

    private void start() {
      try {
        process =
            new ProcessBuilder(
                    executable.toString(), journal.toString(), Integer.toString(maximumPayloadBytes))
                .redirectError(ProcessBuilder.Redirect.INHERIT)
                .start();
        writer =
            new BufferedWriter(
                new OutputStreamWriter(process.getOutputStream(), StandardCharsets.US_ASCII));
        reader =
            new BufferedReader(
                new InputStreamReader(process.getInputStream(), StandardCharsets.US_ASCII));
      } catch (IOException error) {
        throw new IllegalStateException("sidecar start failed", error);
      }
    }

    @Override
    public synchronized void close() {
      process.destroy();
      try {
        if (!process.waitFor(Duration.ofSeconds(5).toMillis(), TimeUnit.MILLISECONDS)) {
          process.destroyForcibly();
        }
      } catch (InterruptedException error) {
        Thread.currentThread().interrupt();
        process.destroyForcibly();
      }
    }
  }

  private final SidecarEndpoint endpoint;
  private final int maximumPayloadBytes;

  public SidecarRunner(SidecarEndpoint endpoint, int maximumPayloadBytes) {
    this.endpoint = Objects.requireNonNull(endpoint, "endpoint");
    BenchmarkContracts.require(maximumPayloadBytes > 0, "invalid sidecar payload bound");
    this.maximumPayloadBytes = maximumPayloadBytes;
  }

  @Override
  public Result run(Request request) {
    byte[] input = request.canonicalBytes();
    BenchmarkContracts.require(input.length <= maximumPayloadBytes, "sidecar request too large");
    long firstStart = System.nanoTime();
    byte[] first = endpoint.execute(request.requestId(), input.clone());
    long firstMicros = elapsedMicros(firstStart);
    long restartStart = System.nanoTime();
    endpoint.crash();
    endpoint.restart();
    long restartMicros = elapsedMicros(restartStart);
    long replayStart = System.nanoTime();
    byte[] replay = endpoint.execute(request.requestId(), input.clone());
    long replayMicros = elapsedMicros(replayStart);
    return new Result(
        "ISOLATED_SIDECAR",
        BenchmarkContracts.sha256(first),
        firstMicros,
        replayMicros,
        restartMicros,
        input.length,
        first.length,
        true,
        Arrays.equals(first, replay));
  }

  private static long elapsedMicros(long startNanos) {
    return Math.max(1, (System.nanoTime() - startNanos + 999) / 1_000);
  }
}
