package io.deltareduce.node.sidecar;

import static java.lang.foreign.ValueLayout.ADDRESS;
import static java.lang.foreign.ValueLayout.JAVA_BYTE;
import static java.lang.foreign.ValueLayout.JAVA_INT;
import static java.lang.foreign.ValueLayout.JAVA_LONG;
import static java.lang.foreign.ValueLayout.JAVA_SHORT;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.BufferedWriter;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.Reader;
import java.io.StringReader;
import java.lang.foreign.Arena;
import java.lang.foreign.FunctionDescriptor;
import java.lang.foreign.Linker;
import java.lang.foreign.MemoryLayout;
import java.lang.foreign.MemorySegment;
import java.lang.foreign.SymbolLookup;
import java.lang.invoke.MethodHandle;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.nio.channels.Channels;
import java.nio.channels.FileChannel;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.locks.LockSupport;
import java.util.regex.Pattern;

/**
 * Executable raw-capture harness for the frozen Feature-010 embedded/sidecar comparison.
 *
 * <p>One invocation admits exactly one deployment profile. The harness consumes the same
 * {@code DLTSTRC1} corpus in either profile, executes the immutable production schedule, and emits
 * the canonical {@code FEATURE010_SIDECAR_PROFILE_RUN_RAW} document accepted by
 * {@code assemble_sidecar_comparison.py}. Crash/restart observations and the projected formal
 * trace are deliberately supplied as independently captured artifacts: this class never invents
 * a crash, recovery, Java-survival, or gate observation.
 *
 * <p>{@code request_order} is the complete validated order of the immutable input corpus, not a
 * claim that both profiles completed the same number of saturation operations. Each execution is
 * a sequential prefix of that common order; the profile-specific prefix length is retained in the
 * saturation measurement evidence. This preserves the frozen identical-input invariant while the
 * completed-operation counts remain the measured throughput signal. The projected-trace input is
 * a canonical receipt, not an opaque blob: it binds source commit/tree, corpus digest, exact
 * warm-up/fixed ordinal range, a digest of those DLTSTRC1 records, and a schema-checked formal
 * trace whose request IDs and initial/terminal roots are verified against the actual run.
 *
 * <p>Use {@link SidecarComparisonCaptureDryRun} for a fast parser/serializer self-test. This main
 * class has no schedule-shortening switch; every successful output therefore represents exactly
 * 1,000 warm-ups, ten 6,000-operation fixed blocks at 100/s, and ten 60-second saturation blocks.
 */
public final class SidecarComparisonCapture {
  private static final String SCHEMA_VERSION = "1.0.0";
  private static final String EXECUTION_CLASS =
      "NON_PRIMARY_RUNTIME_PROFILE_QUALIFICATION";
  private static final String RUN_TYPE = "FEATURE010_SIDECAR_PROFILE_RUN_RAW";
  private static final String DESIGN_RAW_SHA256 =
      "sha256:dc031e7fb413d9ef1ed33b2d4fe1fedb170100e2782f636e7162b40cabbeb4c8";
  private static final String DESIGN_CANONICAL_ID =
      "sha256:080074ff7de58d7ba025b8156ceafb0085937bb6ed74485d217af664d0ecf6ef";
  private static final String FORMAL_SEMANTICS_ID =
      "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
  private static final String BUILD_ID =
      "sha256:1616161616161616161616161616161616161616161616161616161616161616";
  private static final String SCHEMA_SET_ID =
      "sha256:1717171717171717171717171717171717171717171717171717171717171717";
  private static final String PROTOCOL_VERSION = "003.1.0";
  private static final Pattern GIT_OBJECT = Pattern.compile("[0-9a-f]{40}");
  private static final Pattern CONTENT_ID = Pattern.compile("sha256:[0-9a-f]{64}");
  private static final byte[] CORPUS_MAGIC =
      "DLTSTRC1".getBytes(StandardCharsets.US_ASCII);
  private static final int CORPUS_MAJOR = 1;
  private static final int CORPUS_MINOR = 0;
  private static final int WARMUP_OPERATIONS = 1_000;
  private static final int FIXED_BLOCKS = 10;
  private static final int FIXED_OPERATIONS_PER_BLOCK = 6_000;
  private static final int FIXED_RATE_PER_SECOND = 100;
  private static final int SATURATION_BLOCKS = 10;
  private static final long SATURATION_OFFERS_PER_BLOCK = 10_000_000L;
  private static final int WINDOW_SECONDS = 60;
  private static final long FIXED_INTERVAL_NANOS = 10_000_000L;
  private static final long WINDOW_NANOS = 60_000_000_000L;
  private static final int ABI_DESCRIPTOR_SIZE = 64;
  private static final int ABI_OPEN_OPTIONS_SIZE = 128;
  private static final int ABI_OUTPUT_SIZE = 32;
  private static final int ABI_VOTE_RECEIPT_V1_SIZE = 40;
  private static final int ABI_SUBMIT_RECEIPT_V1_SIZE = 48;
  private static final long ABI_FEATURE_SUBMIT_RECEIPT_V1 = 16L;
  private static final int ABI_OK = 0;
  private static final String ROUND_STATE_DOMAIN = "deltareduce:003:round-state:v1";
  private static final String EFFECT_BATCH_DOMAIN = "deltareduce:003:effect-batch:v1";
  private static final List<String> COPY_COUNTERS =
      List.of(
          "INLINE_INGRESS_BYTES",
          "INLINE_EGRESS_BYTES",
          "SHARED_MEMORY_INGRESS_BYTES",
          "SHARED_MEMORY_EGRESS_BYTES",
          "STAGING_FALLBACK_INGRESS_BYTES",
          "STAGING_FALLBACK_EGRESS_BYTES",
          "ZERO_COPY_ELIGIBLE_COUNT",
          "ZERO_COPY_HIT_COUNT");
  private static final List<String> TRANSCRIPT_IDS =
      List.of(
          "CANONICAL_STATUS_BYTES",
          "CANONICAL_EFFECT_BYTES",
          "STATE_ROOTS",
          "WAL_RECEIPTS_AND_DURABLE_SEQUENCES",
          "REPLAY_EFFECT_IDENTITIES",
          "PROJECTED_FORMAL_TRACE_BYTES_AFTER_STUTTER_ERASURE",
          "CANONICAL_VOTE_RECEIPT_BYTES");
  private static final List<String> MEASUREMENT_IDS =
      List.of(
          "END_TO_END_LATENCY_NS",
          "PHASE_LATENCY_NS",
          "FIXED_LOAD_THROUGHPUT_OPS_PER_WINDOW",
          "SATURATION_THROUGHPUT_OPS_PER_WINDOW",
          "RESTART_TO_READY_NS",
          "JAVA_PROCESS_SURVIVAL",
          "STATE_EFFECT_WAL_REPLAY_IDENTITY",
          "RETRY_COUNT",
          "DUPLICATE_RESPONSE_COUNT",
          "STALE_RESPONSE_COUNT",
          "REJECTED_FRAME_COUNT");

  private static final MemoryLayout ABI_VIEW = MemoryLayout.structLayout(ADDRESS, JAVA_LONG);
  private static final MemoryLayout ABI_OUTPUT =
      MemoryLayout.structLayout(ADDRESS, JAVA_LONG, JAVA_LONG, JAVA_LONG);
  private static final MemoryLayout ABI_VOTE_RECEIPT_V1 =
      MemoryLayout.structLayout(JAVA_INT, JAVA_INT, ABI_OUTPUT);
  private static final MemoryLayout ABI_SUBMIT_RECEIPT_V1 =
      MemoryLayout.structLayout(
          JAVA_INT, JAVA_INT, JAVA_LONG, ADDRESS, JAVA_LONG, JAVA_LONG, JAVA_LONG);
  private static final MemoryLayout ABI_DESCRIPTOR =
      MemoryLayout.structLayout(
          JAVA_INT,
          JAVA_SHORT,
          JAVA_SHORT,
          JAVA_LONG,
          ADDRESS,
          ADDRESS,
          ADDRESS,
          ADDRESS,
          ADDRESS,
          ADDRESS);
  private static final MemoryLayout ABI_OPEN_OPTIONS =
      MemoryLayout.structLayout(
          JAVA_INT,
          JAVA_INT,
          ABI_VIEW,
          ABI_VIEW,
          JAVA_SHORT,
          JAVA_SHORT,
          JAVA_INT,
          ABI_VIEW,
          ABI_VIEW,
          ABI_VIEW,
          ABI_VIEW,
          ABI_VIEW);

  private SidecarComparisonCapture() {}

  public static void main(String[] arguments) throws Throwable {
    var options = Options.parse(arguments);
    new Capture(options).run();
  }

  static void selfTest() throws Exception {
    require(ABI_DESCRIPTOR.byteSize() == ABI_DESCRIPTOR_SIZE, "descriptor ABI size changed");
    require(ABI_OPEN_OPTIONS.byteSize() == ABI_OPEN_OPTIONS_SIZE, "open-options ABI size changed");
    require(ABI_OUTPUT.byteSize() == ABI_OUTPUT_SIZE, "output ABI size changed");
    require(
        ABI_VOTE_RECEIPT_V1.byteSize() == ABI_VOTE_RECEIPT_V1_SIZE,
        "vote-receipt-v1 ABI size changed");
    require(
        ABI_SUBMIT_RECEIPT_V1.byteSize() == ABI_SUBMIT_RECEIPT_V1_SIZE,
        "submit-receipt-v1 ABI size changed");
    require(
        sha256Id(new byte[0])
            .equals("sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
        "SHA-256 empty-vector self-test failed");
    var designPath =
        Path.of("specs/010-wan-benchmark-and-quality/sidecar-refinement-design.json");
    if (Files.isRegularFile(designPath)) {
      FrozenDesign.load(designPath.toAbsolutePath());
    }

    var sample = new TreeMap<String, Object>();
    sample.put("a", List.of(1L, true, "x\nπ"));
    sample.put("z", null);
    var encoded = Json.bytes(sample);
    require(
        Arrays.equals(encoded, Json.bytes(Json.parse(encoded))),
        "canonical JSON round-trip self-test failed");

    var selfTestBody = "sha256:" + "a".repeat(64);
    var initial =
        CanonicalEnvelope.encodeMap(
            5,
            Map.of(
                "committed_ticket_count", 0L,
                "durable_sequence", "7",
                "height", "1",
                "phase", "TICKETING_OPEN",
                "round_id", "self-test-round",
                "ticket_count", 1L,
                "view", "0"));
    var command =
        CanonicalEnvelope.encodeTextMap(
            6,
            Map.of(
                "actor_id", "worker-self-test",
                "body_hash", selfTestBody,
                "command_kind", "ACCEPT_COMMITMENT",
                "height", "1",
                "request_id", "sidecar-benchmark-00000000000000000000",
                "round_id", "self-test-round",
                "view", "0"));
    var trace = Files.createTempFile("delta-sidecar-capture-self-test-", ".bin");
    try {
      try (var output =
          new DataOutputStream(new BufferedOutputStream(Files.newOutputStream(trace)))) {
        output.write(CORPUS_MAGIC);
        output.writeShort(CORPUS_MAJOR);
        output.writeShort(CORPUS_MINOR);
        output.writeLong(1);
        output.writeInt(initial.length);
        output.write(initial);
        output.writeLong(0);
        output.writeInt(command.length);
        output.write(command);
        output.write(sha256(command));
      }
      try (var corpus = new Corpus(trace)) {
        require(corpus.initialDurableSequence() == 7, "corpus initial sequence self-test failed");
        var record = corpus.next();
        require(record.ordinal() == 0, "corpus ordinal self-test failed");
        require(
            record.requestId().equals("sidecar-benchmark-00000000000000000000"),
            "corpus request-ID self-test failed");
      }
    } finally {
      Files.deleteIfExists(trace);
    }

    var voteFixturePath = Files.createTempFile("delta-vote-fixture-snapshot-self-test-", ".json");
    try {
      var original =
          Json.bytes(
              Map.of(
                  "expected_receipt_hex", "04",
                  "formal_semantics_id", FORMAL_SEMANTICS_ID,
                  "initial_state_hex", "01",
                  "schema_version", SCHEMA_VERSION,
                  "type_name", VoteFixture.TYPE_NAME,
                  "vote_hex", "03",
                  "vote_policy_hex", "02"));
      Files.write(voteFixturePath, original);
      var snapshot = FileSnapshot.read(voteFixturePath, "vote fixture snapshot self-test");
      var record = new TreeMap<String, Object>();
      record.put("artifact_id", "VOTE_FIXTURE");
      record.put("path", voteFixturePath.toAbsolutePath().normalize().toString());
      record.put("sha256", snapshot.sha256());
      record.put("size_bytes", snapshot.sizeBytes());

      Files.write(voteFixturePath, Json.bytes(Map.of("replacement", true)));
      InputProvenance.verifyFileRecord(
          record, voteFixturePath, "vote fixture snapshot self-test", snapshot);
      var fixture = VoteFixture.load(snapshot);
      require(
          Arrays.equals(fixture.initialState(), new byte[] {1})
              && Arrays.equals(fixture.votePolicy(), new byte[] {2})
              && Arrays.equals(fixture.vote(), new byte[] {3})
              && Arrays.equals(fixture.expectedReceipt(), new byte[] {4})
              && fixture.sha256().equals(snapshot.sha256()),
          "vote fixture execution bytes were not bound to the verified one-read snapshot");
      require(
          !sha256Id(Files.readAllBytes(voteFixturePath)).equals(snapshot.sha256()),
          "vote fixture snapshot self-test did not replace the backing path");
    } finally {
      Files.deleteIfExists(voteFixturePath);
    }
  }

  /** Runs one real embedded RECORD_VOTE, restarts, and proves exact durable replay. */
  static void embeddedVoteConformance(
      Path nativeLibrary, Path durableDirectory, Path voteFixturePath) throws Throwable {
    var library = nativeLibrary.toAbsolutePath().normalize();
    var durable = durableDirectory.toAbsolutePath().normalize();
    var fixturePath = voteFixturePath.toAbsolutePath().normalize();
    requireRegular(library, "embedded native library");
    requireRegular(fixturePath, "native vote fixture");
    require(!Files.exists(durable), "embedded vote durable directory already exists");
    var parent = durable.getParent();
    require(parent != null && Files.isDirectory(parent), "embedded vote durable parent is absent");
    Files.createDirectory(durable);

    var descriptor = RuntimeDescriptor.frozen();
    var fixture = VoteFixture.load(fixturePath);
    var wal = durable.resolve("runtime.wal");
    byte[] accepted;
    try (var adapter =
        new EmbeddedAdapter(
            library,
            durable,
            fixture.initialState(),
            fixture.votePolicy(),
            descriptor)) {
      accepted = adapter.recordVote(fixture.vote());
      require(
          Arrays.equals(accepted, fixture.expectedReceipt()),
          "embedded vote receipt differs from the frozen fixture");
      requireRegular(wal, "embedded vote WAL");
      require(Files.size(wal) > 0, "embedded vote returned before a non-empty WAL existed");
    }
    var acceptedWal = new WalArtifact(sha256Id(wal), Files.size(wal));

    byte[] replay;
    try (var adapter =
        new EmbeddedAdapter(
            library,
            durable,
            fixture.initialState(),
            fixture.votePolicy(),
            descriptor)) {
      require(
          new WalArtifact(sha256Id(wal), Files.size(wal)).equals(acceptedWal),
          "embedded vote WAL changed while reopening recovered state");
      replay = adapter.recordVote(fixture.vote());
      require(
          Arrays.equals(replay, fixture.expectedReceipt()),
          "embedded vote replay differs from the frozen fixture");
      require(
          new WalArtifact(sha256Id(wal), Files.size(wal)).equals(acceptedWal),
          "embedded vote replay appended or rewrote durable state");
    }
    require(Arrays.equals(replay, accepted), "embedded vote replay changed receipt bytes");
    require(
        new WalArtifact(sha256Id(wal), Files.size(wal)).equals(acceptedWal),
        "embedded vote WAL changed while closing recovered state");
  }

  /** Executes the separately sealed, assembler-ineligible 100/s diagnostic lane. */
  static void runDiagnostic(String[] arguments) throws Throwable {
    new DiagnosticCapture(DiagnosticOptions.parse(arguments)).run();
  }

  static void diagnosticSelfTest() {
    var root = Path.of(".").toAbsolutePath().normalize().toString();
    var options =
        DiagnosticOptions.parse(
            new String[] {
              "--profile", "EMBEDDED_FFM",
              "--corpus", root + "/corpus.bin",
              "--event-log", root + "/events.jsonl",
              "--durable-directory", root + "/durable",
              "--source-root", root,
              "--duration-seconds", "60",
              "--offers-per-second", "100",
              "--native-library", root + "/libdelta_ffi.so"
            });
    require(options.offersPerSecond() == 100, "diagnostic self-test changed 100/s rate");
    require(options.durationSeconds() == 60, "diagnostic self-test changed duration");
    var rateRejected = false;
    try {
      DiagnosticOptions.parse(
          new String[] {
            "--profile", "EMBEDDED_FFM",
            "--corpus", root + "/corpus.bin",
            "--event-log", root + "/events.jsonl",
            "--durable-directory", root + "/durable",
            "--source-root", root,
            "--duration-seconds", "60",
            "--offers-per-second", "99",
            "--native-library", root + "/libdelta_ffi.so"
          });
    } catch (CaptureException expected) {
      rateRejected = true;
    }
    require(rateRejected, "diagnostic self-test admitted a lowered offer rate");
    var delta = deltaValue(10L, 15L);
    require(delta.get("status").equals("AVAILABLE"), "diagnostic CPU delta is unavailable");
    require(delta.get("value").equals(5L), "diagnostic CPU delta is incorrect");
  }

  private record DiagnosticOptions(
      Profile profile,
      Path corpus,
      Path eventLog,
      Path durableDirectory,
      Path sourceRoot,
      int durationSeconds,
      int offersPerSecond,
      Path nativeLibrary,
      Path sidecarExecutable) {
    private static final Set<String> NAMES =
        Set.of(
            "--profile",
            "--corpus",
            "--event-log",
            "--durable-directory",
            "--source-root",
            "--duration-seconds",
            "--offers-per-second",
            "--native-library",
            "--sidecar-executable");

    private DiagnosticOptions {
      Objects.requireNonNull(profile, "profile");
      Objects.requireNonNull(corpus, "corpus");
      Objects.requireNonNull(eventLog, "eventLog");
      Objects.requireNonNull(durableDirectory, "durableDirectory");
      Objects.requireNonNull(sourceRoot, "sourceRoot");
      require(durationSeconds > 0 && durationSeconds <= 3_600, "invalid diagnostic duration");
      require(offersPerSecond == 100, "diagnostic offer rate must remain exactly 100/s");
      if (profile == Profile.EMBEDDED_FFM) {
        require(nativeLibrary != null, "EMBEDDED_FFM requires --native-library");
        require(sidecarExecutable == null, "EMBEDDED_FFM forbids --sidecar-executable");
      } else {
        require(sidecarExecutable != null, "ISOLATED_SIDECAR requires --sidecar-executable");
        require(nativeLibrary == null, "ISOLATED_SIDECAR forbids --native-library");
      }
    }

    private static DiagnosticOptions parse(String[] arguments) {
      require(arguments.length % 2 == 0, usage());
      var values = new LinkedHashMap<String, String>();
      for (var index = 0; index < arguments.length; index += 2) {
        var name = arguments[index];
        require(NAMES.contains(name), "unknown diagnostic option " + name + "\n" + usage());
        require(!arguments[index + 1].isEmpty(), "empty diagnostic option " + name);
        require(values.put(name, arguments[index + 1]) == null, "duplicate diagnostic option " + name);
      }
      for (var name : NAMES) {
        if (!name.equals("--native-library") && !name.equals("--sidecar-executable")) {
          require(values.containsKey(name), "missing diagnostic option " + name + "\n" + usage());
        }
      }
      Profile profile;
      try {
        profile = Profile.valueOf(values.get("--profile"));
      } catch (IllegalArgumentException error) {
        throw new CaptureException("invalid diagnostic profile", error);
      }
      return new DiagnosticOptions(
          profile,
          Path.of(values.get("--corpus")).toAbsolutePath().normalize(),
          Path.of(values.get("--event-log")).toAbsolutePath().normalize(),
          Path.of(values.get("--durable-directory")).toAbsolutePath().normalize(),
          Path.of(values.get("--source-root")).toAbsolutePath().normalize(),
          parsePositiveInt(values.get("--duration-seconds"), "diagnostic duration"),
          parsePositiveInt(values.get("--offers-per-second"), "diagnostic offer rate"),
          optionalPath(values.get("--native-library")),
          optionalPath(values.get("--sidecar-executable")));
    }

    private static int parsePositiveInt(String value, String label) {
      try {
        var parsed = Integer.parseInt(value);
        require(parsed > 0, label + " is not positive");
        return parsed;
      } catch (NumberFormatException error) {
        throw new CaptureException(label + " is not an integer", error);
      }
    }

    private static Path optionalPath(String value) {
      return value == null ? null : Path.of(value).toAbsolutePath().normalize();
    }

    private static String usage() {
      return "usage: SidecarDiagnosticCapture --profile EMBEDDED_FFM|ISOLATED_SIDECAR "
          + "--corpus FILE --event-log FILE --durable-directory DIR --source-root DIR "
          + "--duration-seconds N --offers-per-second 100 "
          + "(--native-library FILE | --sidecar-executable FILE)";
    }
  }

  private static final class DiagnosticCapture {
    private static final long NANOS_PER_SECOND = 1_000_000_000L;
    private final DiagnosticOptions options;

    private DiagnosticCapture(DiagnosticOptions options) {
      this.options = options;
    }

    private void run() throws Throwable {
      requireRegular(options.corpus(), "diagnostic corpus");
      require(Files.isDirectory(options.sourceRoot()), "diagnostic source root is not a directory");
      require(!Files.exists(options.eventLog()), "diagnostic event log already exists");
      require(!Files.exists(options.durableDirectory()), "diagnostic durable directory already exists");
      var parent = options.eventLog().getParent();
      require(parent != null && Files.isDirectory(parent), "diagnostic event-log parent is absent");
      Files.createDirectory(options.durableDirectory());
      var operationCount = Math.multiplyExact(options.durationSeconds(), options.offersPerSecond());
      var interval = NANOS_PER_SECOND / options.offersPerSecond();
      require(
          interval * options.offersPerSecond() == NANOS_PER_SECOND,
          "diagnostic rate does not divide one second exactly");
      var descriptor = RuntimeDescriptor.frozen();
      try (var corpus = new Corpus(options.corpus());
          var writer = new DiagnosticWriter(options.eventLog())) {
        require(
            corpus.operationCount() >= Math.addExact(WARMUP_OPERATIONS, operationCount),
            "diagnostic corpus is too short");
        var cursor =
            new StateCursor(
                contentId(ROUND_STATE_DOMAIN, corpus.initialState()), corpus.initialDurableSequence());
        var adapter = openDiagnosticAdapter(descriptor, corpus.initialState());
        try (adapter) {
          executeWarmup(adapter, corpus, cursor);
          writer.write(laneStartEvent(cursor));
          executeSchedule(adapter, corpus, cursor, writer, operationCount, interval);
          verifyState(adapter.state(), cursor);
          writer.write(laneEndEvent(operationCount, cursor));
        }
      }
    }

    private void executeWarmup(Adapter adapter, Corpus corpus, StateCursor cursor) throws Throwable {
      for (var index = 0; index < WARMUP_OPERATIONS; ++index) {
        var command = corpus.next();
        validateNewOperation(command, adapter.execute(command), cursor);
      }
    }

    private Map<String, Object> laneStartEvent(StateCursor cursor) {
      var monotonicAnchor = System.nanoTime();
      var wallAnchor = wallTimeNanos();
      var event = new TreeMap<String, Object>();
      event.put("available_processors", (long) Runtime.getRuntime().availableProcessors());
      event.put("duration_seconds", (long) options.durationSeconds());
      event.put("event_type", "LANE_START");
      event.put("initial_durable_sequence", cursor.durableSequence());
      event.put("initial_state_root", cursor.stateRoot());
      event.put("monotonic_anchor_ns", monotonicAnchor);
      event.put("offers_per_second", (long) options.offersPerSecond());
      event.put("process_id", ProcessHandle.current().pid());
      event.put("profile_id", options.profile().name());
      event.put("source_root", options.sourceRoot().toString());
      event.put("wall_anchor_ns", wallAnchor);
      event.put("warmup_completed_operations", (long) WARMUP_OPERATIONS);
      return event;
    }

    private Map<String, Object> laneEndEvent(int operationCount, StateCursor cursor) {
      var event = new TreeMap<String, Object>();
      event.put("completed_operations", (long) operationCount);
      event.put("event_type", "LANE_END");
      event.put("final_durable_sequence", cursor.durableSequence());
      event.put("final_state_root", cursor.stateRoot());
      event.put("monotonic_ns", System.nanoTime());
      event.put("profile_id", options.profile().name());
      event.put("terminal_state_validated", true);
      event.put("wall_time_ns", wallTimeNanos());
      return event;
    }

    private Adapter openDiagnosticAdapter(RuntimeDescriptor descriptor, byte[] initialState)
        throws Throwable {
      return switch (options.profile()) {
        case EMBEDDED_FFM ->
            new EmbeddedAdapter(
                Objects.requireNonNull(options.nativeLibrary()),
                options.durableDirectory(),
                initialState,
                null,
                descriptor);
        case ISOLATED_SIDECAR ->
            new IsolatedAdapter(
                Objects.requireNonNull(options.sidecarExecutable()),
                options.durableDirectory(),
                initialState,
                null,
                descriptor);
      };
    }

    private void executeSchedule(
        Adapter adapter,
        Corpus corpus,
        StateCursor cursor,
        DiagnosticWriter writer,
        int operationCount,
        long interval)
        throws Throwable {
      var pending = new ArrayList<DiagnosticPending>(operationCount);
      var previousCpu = CpuObservation.capture();
      var start = Math.addExact(System.nanoTime(), interval);
      for (var ordinal = 0; ordinal < operationCount; ++ordinal) {
        var scheduled = Math.addExact(start, Math.multiplyExact((long) ordinal, interval));
        await(scheduled);
        var wakeup = System.nanoTime();
        var wakeupLateness = checkedElapsed(wakeup, scheduled, "diagnostic wake-up lateness");
        var currentCpu = CpuObservation.capture();
        var command = corpus.next();
        var walBefore = WalObservation.capture(options.durableDirectory().resolve("runtime.wal"));
        // Keep the adapter-offer timestamp adjacent to the real bounded-ingress call.  Everything
        // above is diagnostic preparation and is reported separately so it cannot be hidden as
        // runtime demand.
        var actualWall = wallTimeNanos();
        var actual = System.nanoTime();
        var submission = adapter.tryExecute(command, actual);
        var lateness = checkedElapsed(actual, scheduled, "diagnostic scheduler lateness");
        var preparationLatency = checkedElapsed(actual, wakeup, "diagnostic preparation latency");
        writer.write(
            offerEvent(
                ordinal,
                command.requestId(),
                scheduled,
                wakeup,
                actual,
                actualWall,
                lateness,
                wakeupLateness,
                preparationLatency,
                interval,
                previousCpu,
                currentCpu,
                walBefore,
                submission.accepted()));
        require(submission.accepted(), "diagnostic bounded ingress rejected an exact 100/s offer");
        pending.add(
            new DiagnosticPending(
                ordinal, command, submission, scheduled, actual, lateness, walBefore));
        previousCpu = currentCpu;
      }
      for (var item : pending) {
        var timed = awaitSubmission(item.submission());
        var result = validateNewOperation(item.command(), timed.operation(), cursor);
        var walAfter = WalObservation.capture(options.durableDirectory().resolve("runtime.wal"));
        writer.write(completionEvent(item, timed, result, walAfter));
      }
    }

    private Map<String, Object> offerEvent(
        int ordinal,
        String requestId,
        long scheduled,
        long wakeup,
        long actual,
        long actualWall,
        long lateness,
        long wakeupLateness,
        long preparationLatency,
        long interval,
        CpuObservation previousCpu,
        CpuObservation currentCpu,
        WalObservation walBefore,
        boolean accepted) {
      var event = new TreeMap<String, Object>();
      event.put("actual_offer_ns", actual);
      event.put("actual_wall_time_ns", actualWall);
      event.put("admission_accepted", accepted);
      event.put("event_type", "OFFER");
      event.put(
          "harness_preparation_overran_slot",
          lateness >= interval && wakeupLateness < interval);
      event.put("missed_slot", lateness >= interval);
      event.put("offer_ordinal", (long) ordinal);
      event.put("preparation_latency_ns", preparationLatency);
      event.put("process_cpu_delta_ns", deltaValue(previousCpu.processCpu(), currentCpu.processCpu()));
      event.put("profile_id", options.profile().name());
      event.put("request_id", requestId);
      event.put("scheduled_offer_ns", scheduled);
      event.put("scheduler_lateness_ns", lateness);
      event.put(
          "scheduler_thread_cpu_delta_ns",
          deltaValue(previousCpu.threadCpu(), currentCpu.threadCpu()));
      event.put("schedstat_delta", schedstatDelta(previousCpu.schedstat(), currentCpu.schedstat()));
      event.put("wal_before", walBefore.asEvidence());
      event.put("wakeup_lateness_ns", wakeupLateness);
      event.put("wakeup_ns", wakeup);
      return event;
    }

    private Map<String, Object> completionEvent(
        DiagnosticPending item,
        TimedOperation timed,
        ValidatedOperation result,
        WalObservation walAfter) {
      var event = new TreeMap<String, Object>();
      event.put("completed_at_ns", timed.completedAtNanos());
      event.put("completed_wall_time_ns", wallTimeNanos());
      event.put("durable_sequence", result.durableSequence());
      event.put("event_type", "COMPLETION");
      event.put("native_phase_latency_ns", result.phaseLatencyNanos());
      event.put("next_state_root", result.nextStateRoot());
      event.put("offer_ordinal", (long) item.ordinal());
      event.put("operation_latency_ns", result.totalLatencyNanos());
      event.put("prior_state_root", result.priorStateRoot());
      event.put("profile_id", options.profile().name());
      event.put("request_id", item.command().requestId());
      event.put("wal_after", walAfter.asEvidence());
      return event;
    }
  }

  private record DiagnosticPending(
      int ordinal,
      CorpusRecord command,
      Submission submission,
      long scheduledOfferNanos,
      long actualOfferNanos,
      long schedulerLatenessNanos,
      WalObservation walBefore) {}

  private record SchedstatObservation(long runningNanos, long waitingNanos, long timeslices) {
    private static SchedstatObservation capture() {
      if (!System.getProperty("os.name").toLowerCase(java.util.Locale.ROOT).contains("linux")) {
        return null;
      }
      try {
        var values = Files.readString(Path.of("/proc/self/schedstat"), StandardCharsets.US_ASCII)
            .trim()
            .split("\\s+");
        require(values.length >= 3, "Linux schedstat has fewer than three counters");
        return new SchedstatObservation(
            Long.parseLong(values[0]), Long.parseLong(values[1]), Long.parseLong(values[2]));
      } catch (IOException | NumberFormatException | CaptureException ignored) {
        return null;
      }
    }
  }

  private record CpuObservation(Long processCpu, Long threadCpu, SchedstatObservation schedstat) {
    private static CpuObservation capture() {
      Long process =
          ProcessHandle.current().info().totalCpuDuration().map(Duration::toNanos).orElse(null);
      var bean = ManagementFactory.getThreadMXBean();
      Long thread = null;
      if (bean.isCurrentThreadCpuTimeSupported()) {
        var value = bean.getCurrentThreadCpuTime();
        if (value >= 0) {
          thread = value;
        }
      }
      return new CpuObservation(process, thread, SchedstatObservation.capture());
    }
  }

  private record WalObservation(
      boolean present, long sizeBytes, long modifiedTimeMillis, long observedAtNanos) {
    private static WalObservation capture(Path path) {
      try {
        if (!Files.isRegularFile(path)) {
          return new WalObservation(false, 0, 0, System.nanoTime());
        }
        return new WalObservation(
            true, Files.size(path), Files.getLastModifiedTime(path).toMillis(), System.nanoTime());
      } catch (IOException ignored) {
        return new WalObservation(false, 0, 0, System.nanoTime());
      }
    }

    private Map<String, Object> asEvidence() {
      return Map.of(
          "modified_time_millis", modifiedTimeMillis,
          "observed_at_ns", observedAtNanos,
          "present", present,
          "size_bytes", sizeBytes);
    }
  }

  private static final class DiagnosticWriter implements AutoCloseable {
    private final FileChannel channel;
    private final BufferedWriter writer;

    private DiagnosticWriter(Path path) throws IOException {
      channel = FileChannel.open(path, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
      writer =
          new BufferedWriter(
              Channels.newWriter(channel, StandardCharsets.UTF_8),
              64 * 1024);
    }

    private void write(Map<String, Object> event) throws IOException {
      Json.write(event, writer);
      writer.write('\n');
    }

    @Override
    public void close() throws IOException {
      writer.flush();
      channel.force(true);
      writer.close();
    }
  }

  private static Map<String, Object> deltaValue(Long before, Long after) {
    if (before == null || after == null || after < before) {
      return Map.of(
          "reason", "counter unavailable or non-monotonic",
          "status", "NOT_AVAILABLE");
    }
    return Map.of("status", "AVAILABLE", "value", after - before);
  }

  private static Map<String, Object> schedstatDelta(
      SchedstatObservation before, SchedstatObservation after) {
    if (before == null
        || after == null
        || after.runningNanos() < before.runningNanos()
        || after.waitingNanos() < before.waitingNanos()
        || after.timeslices() < before.timeslices()) {
      return Map.of("reason", "Linux schedstat unavailable", "status", "NOT_AVAILABLE");
    }
    return Map.of(
        "status",
        "AVAILABLE",
        "value",
        Map.of(
            "running_ns", after.runningNanos() - before.runningNanos(),
            "timeslices", after.timeslices() - before.timeslices(),
            "waiting_ns", after.waitingNanos() - before.waitingNanos()));
  }

  private static long wallTimeNanos() {
    var now = Instant.now();
    return Math.addExact(Math.multiplyExact(now.getEpochSecond(), 1_000_000_000L), now.getNano());
  }

  private enum Profile {
    EMBEDDED_FFM,
    ISOLATED_SIDECAR
  }

  private record Options(
      Profile profile,
      Path corpus,
      Path design,
      Path output,
      Path durableDirectory,
      String sourceCommit,
      String sourceTree,
      Path hardwareAllocation,
      Path toolchains,
      Path nativeCore,
      Path faultTrace,
      Path projectedFormalTrace,
      Path crashObservations,
      Path voteFixture,
      Path inputProvenance,
      Path nativeLibrary,
      Path sidecarExecutable,
      List<String> rawArguments) {
    private static final Set<String> NAMES =
        Set.of(
            "--profile",
            "--corpus",
            "--design",
            "--output",
            "--durable-directory",
            "--source-commit",
            "--source-tree",
            "--hardware-allocation",
            "--toolchains",
            "--native-core",
            "--fault-trace",
            "--projected-formal-trace",
            "--crash-observations",
            "--vote-fixture",
            "--input-provenance",
            "--native-library",
            "--sidecar-executable");

    private Options {
      Objects.requireNonNull(profile, "profile");
      Objects.requireNonNull(corpus, "corpus");
      Objects.requireNonNull(design, "design");
      Objects.requireNonNull(output, "output");
      Objects.requireNonNull(durableDirectory, "durableDirectory");
      Objects.requireNonNull(sourceCommit, "sourceCommit");
      Objects.requireNonNull(sourceTree, "sourceTree");
      Objects.requireNonNull(hardwareAllocation, "hardwareAllocation");
      Objects.requireNonNull(toolchains, "toolchains");
      Objects.requireNonNull(nativeCore, "nativeCore");
      Objects.requireNonNull(faultTrace, "faultTrace");
      Objects.requireNonNull(projectedFormalTrace, "projectedFormalTrace");
      Objects.requireNonNull(crashObservations, "crashObservations");
      Objects.requireNonNull(voteFixture, "voteFixture");
      Objects.requireNonNull(inputProvenance, "inputProvenance");
      rawArguments = List.copyOf(rawArguments);
      require(GIT_OBJECT.matcher(sourceCommit).matches(), "source commit is not lowercase Git SHA-1");
      require(GIT_OBJECT.matcher(sourceTree).matches(), "source tree is not lowercase Git SHA-1");
      if (profile == Profile.EMBEDDED_FFM) {
        require(nativeLibrary != null, "EMBEDDED_FFM requires --native-library");
        require(sidecarExecutable == null, "EMBEDDED_FFM forbids --sidecar-executable");
      } else {
        require(sidecarExecutable != null, "ISOLATED_SIDECAR requires --sidecar-executable");
        require(nativeLibrary == null, "ISOLATED_SIDECAR forbids --native-library");
      }
    }

    private static Options parse(String[] arguments) {
      require(arguments.length % 2 == 0, usage());
      var values = new LinkedHashMap<String, String>();
      for (var index = 0; index < arguments.length; index += 2) {
        var name = arguments[index];
        require(NAMES.contains(name), "unknown option " + name + "\n" + usage());
        require(!arguments[index + 1].isEmpty(), "empty value for " + name);
        require(values.put(name, arguments[index + 1]) == null, "duplicate option " + name);
      }
      for (var name : NAMES) {
        if (!name.equals("--native-library") && !name.equals("--sidecar-executable")) {
          require(values.containsKey(name), "missing " + name + "\n" + usage());
        }
      }
      Profile profile;
      try {
        profile = Profile.valueOf(values.get("--profile"));
      } catch (IllegalArgumentException error) {
        throw new CaptureException("profile must be EMBEDDED_FFM or ISOLATED_SIDECAR", error);
      }
      return new Options(
          profile,
          Path.of(values.get("--corpus")).toAbsolutePath(),
          Path.of(values.get("--design")).toAbsolutePath(),
          Path.of(values.get("--output")).toAbsolutePath(),
          Path.of(values.get("--durable-directory")).toAbsolutePath(),
          values.get("--source-commit"),
          values.get("--source-tree"),
          Path.of(values.get("--hardware-allocation")).toAbsolutePath(),
          Path.of(values.get("--toolchains")).toAbsolutePath(),
          Path.of(values.get("--native-core")).toAbsolutePath(),
          Path.of(values.get("--fault-trace")).toAbsolutePath(),
          Path.of(values.get("--projected-formal-trace")).toAbsolutePath(),
          Path.of(values.get("--crash-observations")).toAbsolutePath(),
          Path.of(values.get("--vote-fixture")).toAbsolutePath(),
          Path.of(values.get("--input-provenance")).toAbsolutePath(),
          optionalPath(values.get("--native-library")),
          optionalPath(values.get("--sidecar-executable")),
          List.of(arguments));
    }

    private static Path optionalPath(String value) {
      return value == null ? null : Path.of(value).toAbsolutePath();
    }

    private static String usage() {
      return "usage: SidecarComparisonCapture --profile <EMBEDDED_FFM|ISOLATED_SIDECAR> "
          + "--corpus <DLTSTRC1> --design <sidecar-refinement-design.json> --output <raw.json> "
          + "--durable-directory <dir> --source-commit <sha1> --source-tree <sha1> "
          + "--hardware-allocation <artifact> --toolchains <artifact> --native-core <artifact> "
          + "--fault-trace <artifact> --projected-formal-trace <artifact> "
          + "--crash-observations <canonical-json> --vote-fixture <canonical-json> "
          + "--input-provenance <canonical-json> "
          + "(--native-library <delta-ffi> | --sidecar-executable <sidecar>)";
    }
  }

  /** One immutable file read shared by provenance verification and execution parsing. */
  private record FileSnapshot(Path path, byte[] bytes, long sizeBytes, String sha256) {
    private FileSnapshot {
      path = Objects.requireNonNull(path, "path").toAbsolutePath().normalize();
      bytes = Arrays.copyOf(Objects.requireNonNull(bytes, "bytes"), bytes.length);
      require(sizeBytes == bytes.length, "file snapshot size differs from its bytes");
      requireContentId(sha256, "file snapshot digest");
      require(sha256Id(bytes).equals(sha256), "file snapshot digest differs from its bytes");
    }

    private static FileSnapshot read(Path path, String label) throws IOException {
      var normalized = Objects.requireNonNull(path, "path").toAbsolutePath().normalize();
      var raw = readRegularFile(normalized, label);
      return new FileSnapshot(normalized, raw, raw.length, sha256Id(raw));
    }

    @Override
    public byte[] bytes() {
      return Arrays.copyOf(bytes, bytes.length);
    }
  }

  /** Opaque native-generated RECORD_VOTE fixture used identically by both profiles. */
  private record VoteFixture(
      byte[] initialState,
      byte[] votePolicy,
      byte[] vote,
      byte[] expectedReceipt,
      String sha256) {
    private static final String TYPE_NAME = "DELTA_RECORD_VOTE_V1_FIXTURE";
    private static final Set<String> FIELDS =
        Set.of(
            "expected_receipt_hex",
            "formal_semantics_id",
            "initial_state_hex",
            "schema_version",
            "type_name",
            "vote_hex",
            "vote_policy_hex");

    private VoteFixture {
      initialState = Arrays.copyOf(initialState, initialState.length);
      votePolicy = Arrays.copyOf(votePolicy, votePolicy.length);
      vote = Arrays.copyOf(vote, vote.length);
      expectedReceipt = Arrays.copyOf(expectedReceipt, expectedReceipt.length);
      require(initialState.length > 0, "vote fixture initial state is empty");
      require(
          initialState.length <= SidecarIpcV1.MAX_CANONICAL_COMMAND_BYTES,
          "vote fixture initial state exceeds the frozen bound");
      require(
          votePolicy.length > 0
              && votePolicy.length <= SidecarIpcV1.MAX_CANONICAL_VOTE_POLICY_BYTES,
          "vote fixture policy exceeds the frozen bound");
      require(
          vote.length > 0 && vote.length <= SidecarIpcV1.MAX_CANONICAL_VOTE_BYTES,
          "vote fixture frame exceeds the frozen bound");
      require(
          expectedReceipt.length > 0
              && expectedReceipt.length <= SidecarIpcV1.MAX_CANONICAL_VOTE_RECEIPT_BYTES,
          "vote fixture accepted receipt exceeds the frozen bound");
      requireContentId(sha256, "vote fixture digest");
    }

    private static VoteFixture load(Path path) throws IOException {
      return load(FileSnapshot.read(path, "native vote fixture"));
    }

    private static VoteFixture load(FileSnapshot snapshot) {
      var raw = snapshot.bytes();
      var document = object(Json.parse(raw), "native vote fixture");
      exactFields(document, FIELDS, "native vote fixture");
      var canonical = Json.bytes(document);
      require(
          Arrays.equals(raw, canonical) || Arrays.equals(raw, appendNewline(canonical)),
          "native vote fixture is not canonical JSON");
      require(document.get("type_name").equals(TYPE_NAME), "native vote fixture type mismatch");
      require(
          document.get("schema_version").equals(SCHEMA_VERSION),
          "native vote fixture schema mismatch");
      require(
          document.get("formal_semantics_id").equals(FORMAL_SEMANTICS_ID),
          "native vote fixture formal semantics mismatch");
      return new VoteFixture(
          hexBytes(document.get("initial_state_hex"), "vote fixture initial state"),
          hexBytes(document.get("vote_policy_hex"), "vote fixture policy"),
          hexBytes(document.get("vote_hex"), "vote fixture frame"),
          hexBytes(document.get("expected_receipt_hex"), "vote fixture accepted receipt"),
          snapshot.sha256());
    }

    private static byte[] hexBytes(Object value, String label) {
      var encoded = textValue(value, label);
      require(
          !encoded.isEmpty()
              && encoded.length() % 2 == 0
              && encoded.matches("[0-9a-f]+"),
          label + " is not lowercase even-length hexadecimal");
      try {
        return HexFormat.of().parseHex(encoded);
      } catch (IllegalArgumentException error) {
        throw new CaptureException(label + " is not hexadecimal", error);
      }
    }

    @Override
    public byte[] initialState() {
      return Arrays.copyOf(initialState, initialState.length);
    }

    @Override
    public byte[] votePolicy() {
      return Arrays.copyOf(votePolicy, votePolicy.length);
    }

    @Override
    public byte[] vote() {
      return Arrays.copyOf(vote, vote.length);
    }

    @Override
    public byte[] expectedReceipt() {
      return Arrays.copyOf(expectedReceipt, expectedReceipt.length);
    }

  }

  private record FrozenDesign(
      Map<String, Object> aggregation,
      Map<String, Object> bounds,
      List<String> copyCounters,
      List<String> measurementIds,
      List<String> transcriptIds,
      List<String> pairedCrashPoints,
      List<String> sidecarCrashPoints) {
    private static FrozenDesign load(Path path) throws IOException {
      var raw = readRegularFile(path, "frozen design");
      require(sha256Id(raw).equals(DESIGN_RAW_SHA256), "frozen design raw digest mismatch");
      var document = object(Json.parse(raw), "frozen design");
      var canonical = Json.bytes(document);
      require(
          Arrays.equals(raw, canonical) || Arrays.equals(raw, appendNewline(canonical)),
          "frozen design is not canonical JSON");
      require(
          sha256Id(canonical).equals(DESIGN_CANONICAL_ID),
          "frozen design canonical digest mismatch");
      var comparison = object(document.get("comparison_plan"), "comparison plan");
      var aggregation = object(comparison.get("aggregation"), "aggregation rules");
      require(
          integer(aggregation.get("warmup_operations"), "warm-up operations")
              == WARMUP_OPERATIONS,
          "frozen warm-up count changed");
      require(
          integer(aggregation.get("measured_blocks"), "fixed block count") == FIXED_BLOCKS,
          "frozen fixed block count changed");
      require(
          integer(
                  aggregation.get("fixed_load_offered_operations_per_block"),
                  "fixed operations")
              == FIXED_OPERATIONS_PER_BLOCK,
          "frozen fixed operation count changed");
      require(
          integer(aggregation.get("fixed_offered_load_ops_per_second"), "fixed rate")
              == FIXED_RATE_PER_SECOND,
          "frozen fixed rate changed");
      require(
          integer(aggregation.get("saturation_blocks"), "saturation block count")
              == SATURATION_BLOCKS,
          "frozen saturation block count changed");
      require(
          integer(aggregation.get("throughput_window_seconds"), "throughput window")
              == WINDOW_SECONDS,
          "frozen window changed");
      var bounds =
          object(
              object(document.get("ipc_contract"), "IPC contract").get("bounds"),
              "IPC bounds");
      require(
          integer(bounds.get("max_logical_payload_bytes"), "maximum logical payload")
              == SidecarIpcV1.MAX_LOGICAL_PAYLOAD_BYTES,
          "Java/native maximum response bound differs from frozen design");
      require(
          integer(bounds.get("max_canonical_command_bytes"), "maximum command")
              == SidecarIpcV1.MAX_CANONICAL_COMMAND_BYTES,
          "Java/native command bound differs from frozen design");
      require(
          integer(bounds.get("max_canonical_effect_bytes"), "maximum effect")
              == SidecarIpcV1.MAX_CANONICAL_EFFECT_BYTES,
          "Java/native effect bound differs from frozen design");
      require(
          integer(bounds.get("max_canonical_vote_bytes"), "maximum vote")
              == SidecarIpcV1.MAX_CANONICAL_VOTE_BYTES
              && integer(bounds.get("max_canonical_vote_policy_bytes"), "maximum vote policy")
                  == SidecarIpcV1.MAX_CANONICAL_VOTE_POLICY_BYTES
              && integer(bounds.get("max_canonical_vote_receipt_bytes"), "maximum vote receipt")
                  == SidecarIpcV1.MAX_CANONICAL_VOTE_RECEIPT_BYTES,
          "Java/native vote bounds differ from frozen design");
      var copyCounters = strings(comparison.get("copy_accounting"), "copy counters");
      var measurementIds = strings(comparison.get("required_measurements"), "measurements");
      var transcriptIds =
          strings(comparison.get("exact_cross_profile_equalities"), "transcript equalities");
      require(copyCounters.equals(COPY_COUNTERS), "frozen copy-counter order changed");
      require(measurementIds.equals(MEASUREMENT_IDS), "frozen measurement order changed");
      require(transcriptIds.equals(TRANSCRIPT_IDS), "frozen transcript order changed");
      return new FrozenDesign(
          Map.copyOf(aggregation),
          Map.copyOf(bounds),
          copyCounters,
          measurementIds,
          transcriptIds,
          strings(comparison.get("paired_crash_points"), "paired crash points"),
          strings(
              comparison.get("sidecar_supplemental_crash_points"),
              "sidecar crash points"));
    }

    private List<String> crashPoints(Profile profile) {
      var result = new ArrayList<>(pairedCrashPoints);
      if (profile == Profile.ISOLATED_SIDECAR) {
        result.addAll(sidecarCrashPoints);
      }
      return List.copyOf(result);
    }
  }

  private record CrashObservations(
      List<Object> restartToReady,
      Map<String, Object> javaProcessSurvival,
      String artifactSha256) {
    private static final Set<String> ROOT_FIELDS =
        Set.of(
            "java_process_survival",
            "profile_id",
            "restart_to_ready",
            "schema_version",
            "type_name");

    private static CrashObservations load(
        Path path, Profile profile, List<String> crashPoints) throws IOException {
      var raw = readRegularFile(path, "crash observations");
      var document = object(Json.parse(raw), "crash observations");
      require(document.keySet().equals(ROOT_FIELDS), "crash observation fields are not exact");
      require(
          Arrays.equals(raw, Json.bytes(document))
              || Arrays.equals(raw, appendNewline(Json.bytes(document))),
          "crash observations are not canonical JSON");
      require(
          document.get("type_name").equals("FEATURE010_SIDECAR_CRASH_OBSERVATIONS"),
          "crash observation type mismatch");
      require(document.get("schema_version").equals(SCHEMA_VERSION), "crash schema mismatch");
      require(document.get("profile_id").equals(profile.name()), "crash profile mismatch");
      var restarts = array(document.get("restart_to_ready"), "restart observations");
      require(restarts.size() == crashPoints.size(), "restart observation count mismatch");
      var validatedRestarts = new ArrayList<Object>();
      for (var index = 0; index < crashPoints.size(); ++index) {
        var record = object(restarts.get(index), "restart observation");
        exactFields(
            record,
            Set.of("crash_point", "duration_ns", "evidence", "evidence_sha256"),
            "restart observation");
        var crashPoint = crashPoints.get(index);
        require(record.get("crash_point").equals(crashPoint), "restart order mismatch");
        var duration = integer(record.get("duration_ns"), "restart duration");
        require(duration > 0, "restart duration is not positive");
        var evidence =
            validateEvidence(record.get("evidence"), record.get("evidence_sha256"), "restart");
        var observations = object(evidence.get("observations"), "restart observations");
        require(observations.get("profile_id").equals(profile.name()), "restart profile mismatch");
        require(observations.get("crash_point").equals(crashPoint), "restart crash point mismatch");
        require(
            integer(observations.get("duration_ns"), "restart observation duration") == duration,
            "restart duration evidence mismatch");
        require(allChecksPass(evidence), "restart evidence contains a failed check");
        validatedRestarts.add(Map.copyOf(record));
      }
      var survival = object(document.get("java_process_survival"), "Java survival");
      exactFields(
          survival,
          Set.of("evidence", "evidence_sha256", "survived_all_native_deaths"),
          "Java survival");
      require(
          survival.get("survived_all_native_deaths") instanceof Boolean,
          "Java survival is not Boolean");
      var survived = (Boolean) survival.get("survived_all_native_deaths");
      require(
          survived == (profile == Profile.ISOLATED_SIDECAR),
          "Java survival observation contradicts the selected profile boundary");
      var evidence =
          validateEvidence(survival.get("evidence"), survival.get("evidence_sha256"), "survival");
      var observations = object(evidence.get("observations"), "survival observations");
      require(observations.get("profile_id").equals(profile.name()), "survival profile mismatch");
      require(
          observations.get("survived_all_native_deaths").equals(survived),
          "survival evidence mismatch");
      require(
          integer(observations.get("qualification_case_count"), "qualification case count")
              == crashPoints.size(),
          "qualification case count mismatch");
      var expectedNativeDeaths = crashPoints.size();
      require(
          integer(observations.get("native_death_injection_count"), "death injection count")
              == expectedNativeDeaths,
          "death injection count mismatch");
      require(allChecksPass(evidence), "survival evidence contains a failed check");
      return new CrashObservations(
          List.copyOf(validatedRestarts),
          Map.copyOf(survival),
          sha256Id(Json.bytes(document)));
    }
  }

  private record InputProvenance(
      Map<String, Object> document,
      String documentSha256,
      List<Object> graphNodes,
      Path gitExecutable) {
    private static final String TYPE_NAME = "FEATURE010_CAPTURE_INPUT_PROVENANCE";
    private static final Set<String> ROOT_FIELDS =
        Set.of(
            "capture_plan",
            "hardware_identity",
            "input_artifacts",
            "preparation_ended_at_utc",
            "preparation_started_at_utc",
            "runner_logs",
            "schema_version",
            "source",
            "tools",
            "type_name");
    private static final Set<String> SOURCE_FIELDS = Set.of("commit", "tracked_clean", "tree");
    private static final Set<String> CAPTURE_PLAN_FIELDS =
        Set.of("argv", "output_path", "profile_id");
    private static final Set<String> HARDWARE_FIELDS =
        Set.of(
            "allocation_artifact_sha256",
            "available_processors",
            "os_arch",
            "os_name",
            "os_version");
    private static final Set<String> FILE_FIELDS =
        Set.of("artifact_id", "path", "sha256", "size_bytes");
    private static final Set<String> TOOL_FIELDS =
        Set.of("path", "sha256", "size_bytes", "tool_id", "version");
    private static final Set<String> RUNNER_FIELDS =
        Set.of(
            "argv",
            "ended_at_utc",
            "path",
            "runner_id",
            "sha256",
            "size_bytes",
            "started_at_utc",
            "tool_id");

    private static InputProvenance load(Options options, FileSnapshot voteFixture)
        throws IOException {
      var raw = readRegularFile(options.inputProvenance(), "input provenance manifest");
      var document = object(Json.parse(raw), "input provenance manifest");
      exactFields(document, ROOT_FIELDS, "input provenance manifest");
      var canonical = Json.bytes(document);
      require(
          Arrays.equals(raw, canonical) || Arrays.equals(raw, appendNewline(canonical)),
          "input provenance manifest is not canonical JSON");
      require(document.get("type_name").equals(TYPE_NAME), "input provenance type mismatch");
      require(
          document.get("schema_version").equals(SCHEMA_VERSION),
          "input provenance schema mismatch");

      var source = object(document.get("source"), "input provenance source");
      exactFields(source, SOURCE_FIELDS, "input provenance source");
      require(source.get("commit").equals(options.sourceCommit()), "provenance commit mismatch");
      require(source.get("tree").equals(options.sourceTree()), "provenance tree mismatch");
      require(Boolean.TRUE.equals(source.get("tracked_clean")), "provenance source is not clean");

      var plan = object(document.get("capture_plan"), "capture plan");
      exactFields(plan, CAPTURE_PLAN_FIELDS, "capture plan");
      require(
          textArray(plan.get("argv"), "capture argv").equals(options.rawArguments()),
          "capture argv differs from input provenance");
      require(
          normalizedPath(plan.get("output_path"), "planned capture output")
              .equals(options.output().toAbsolutePath().normalize()),
          "planned capture output path mismatch");
      require(plan.get("profile_id").equals(options.profile().name()), "capture profile mismatch");

      var preparationStarted =
          utcInstant(document.get("preparation_started_at_utc"), "preparation start");
      var preparationEnded =
          utcInstant(document.get("preparation_ended_at_utc"), "preparation end");
      require(!preparationEnded.isBefore(preparationStarted), "preparation interval is reversed");

      var expectedArtifacts = new LinkedHashMap<String, Path>();
      expectedArtifacts.put("CORPUS", options.corpus());
      expectedArtifacts.put("CRASH_OBSERVATIONS", options.crashObservations());
      expectedArtifacts.put("FROZEN_DESIGN", options.design());
      expectedArtifacts.put("HARDWARE_ALLOCATION", options.hardwareAllocation());
      expectedArtifacts.put("NATIVE_CORE", options.nativeCore());
      expectedArtifacts.put("PAIRED_CORE_FAULT_TRACE", options.faultTrace());
      expectedArtifacts.put("PROJECTED_FORMAL_TRACE", options.projectedFormalTrace());
      expectedArtifacts.put("TOOLCHAINS", options.toolchains());
      expectedArtifacts.put("VOTE_FIXTURE", options.voteFixture());
      expectedArtifacts.put(
          options.profile() == Profile.EMBEDDED_FFM ? "NATIVE_LIBRARY" : "SIDECAR_EXECUTABLE",
          options.profile() == Profile.EMBEDDED_FFM
              ? Objects.requireNonNull(options.nativeLibrary())
              : Objects.requireNonNull(options.sidecarExecutable()));
      var artifactArray = array(document.get("input_artifacts"), "input artifacts");
      require(
          artifactArray.size() == expectedArtifacts.size(),
          "input provenance artifact count mismatch");
      var verifiedArtifacts = new LinkedHashMap<String, Map<String, Object>>();
      var artifactIndex = 0;
      for (var expected : expectedArtifacts.entrySet()) {
        var record = object(artifactArray.get(artifactIndex++), "input artifact");
        exactFields(record, FILE_FIELDS, "input artifact");
        require(record.get("artifact_id").equals(expected.getKey()), "input artifact order mismatch");
        verifyFileRecord(
            record,
            expected.getValue(),
            "input artifact " + expected.getKey(),
            expected.getKey().equals("VOTE_FIXTURE") ? voteFixture : null);
        verifiedArtifacts.put(expected.getKey(), Map.copyOf(record));
      }

      var hardware = object(document.get("hardware_identity"), "hardware identity");
      exactFields(hardware, HARDWARE_FIELDS, "hardware identity");
      require(
          hardware
              .get("allocation_artifact_sha256")
              .equals(verifiedArtifacts.get("HARDWARE_ALLOCATION").get("sha256")),
          "hardware allocation provenance mismatch");
      require(
          integer(hardware.get("available_processors"), "available processors")
              == Runtime.getRuntime().availableProcessors(),
          "available processor identity mismatch");
      require(
          hardware.get("os_arch").equals(System.getProperty("os.arch")),
          "OS architecture identity mismatch");
      require(
          hardware.get("os_name").equals(System.getProperty("os.name")),
          "OS name identity mismatch");
      require(
          hardware.get("os_version").equals(System.getProperty("os.version")),
          "OS version identity mismatch");

      var expectedTools = List.of("GIT", "JAVA_RUNTIME", "NATIVE_RUNTIME");
      var toolArray = array(document.get("tools"), "tools");
      require(toolArray.size() == expectedTools.size(), "tool identity count mismatch");
      var verifiedTools = new LinkedHashMap<String, Map<String, Object>>();
      Path gitExecutable = null;
      for (var index = 0; index < expectedTools.size(); ++index) {
        var toolId = expectedTools.get(index);
        var record = object(toolArray.get(index), "tool identity");
        exactFields(record, TOOL_FIELDS, "tool identity");
        require(record.get("tool_id").equals(toolId), "tool identity order mismatch");
        Path expectedPath = null;
        String expectedVersion = null;
        if (toolId.equals("JAVA_RUNTIME")) {
          expectedPath = javaExecutable();
          expectedVersion = Runtime.version().toString();
        } else if (toolId.equals("NATIVE_RUNTIME")) {
          expectedPath = expectedArtifacts.get(
              options.profile() == Profile.EMBEDDED_FFM
                  ? "NATIVE_LIBRARY"
                  : "SIDECAR_EXECUTABLE");
          expectedVersion = BUILD_ID;
        }
        var declaredPath = verifyFileRecord(record, expectedPath, "tool " + toolId);
        if (expectedVersion != null) {
          require(record.get("version").equals(expectedVersion), "tool version mismatch: " + toolId);
        }
        if (toolId.equals("GIT")) {
          gitExecutable = declaredPath;
          var version = runProcess(declaredPath, options.design().getParent(), "--version");
          require(version.exitCode() == 0, "declared Git executable failed --version");
          require(record.get("version").equals(version.output()), "Git version identity mismatch");
        }
        verifiedTools.put(toolId, Map.copyOf(record));
      }
      require(gitExecutable != null, "input provenance omitted Git executable");
      verifyCheckedOutSource(
          options.design(), options.sourceCommit(), options.sourceTree(), gitExecutable);

      var runnerArray = array(document.get("runner_logs"), "runner logs");
      require(!runnerArray.isEmpty(), "input provenance has no completed runner logs");
      var verifiedRunners = new ArrayList<Map<String, Object>>();
      var runnerIds = new java.util.HashSet<String>();
      for (var value : runnerArray) {
        var record = object(value, "runner log");
        exactFields(record, RUNNER_FIELDS, "runner log");
        var runnerId = text(record, "runner_id");
        require(runnerIds.add(runnerId), "duplicate runner log ID");
        var toolId = text(record, "tool_id");
        require(verifiedTools.containsKey(toolId), "runner log references an unknown tool");
        require(!textArray(record.get("argv"), "runner argv").isEmpty(), "runner argv is empty");
        var started = utcInstant(record.get("started_at_utc"), "runner start");
        var ended = utcInstant(record.get("ended_at_utc"), "runner end");
        require(!ended.isBefore(started), "runner interval is reversed");
        require(
            !started.isBefore(preparationStarted) && !ended.isAfter(preparationEnded),
            "runner interval lies outside preparation interval");
        verifyFileRecord(record, null, "runner log " + runnerId);
        verifiedRunners.add(Map.copyOf(record));
      }

      var documentSha256 = sha256Id(canonical);
      var graphNodes = new ArrayList<Object>();
      for (var entry : verifiedArtifacts.entrySet()) {
        graphNodes.add(graphNode("INPUT:" + entry.getKey(), entry.getValue(), documentSha256));
      }
      for (var entry : verifiedTools.entrySet()) {
        graphNodes.add(graphNode("TOOL:" + entry.getKey(), entry.getValue(), documentSha256));
      }
      for (var record : verifiedRunners) {
        graphNodes.add(
            graphNode("RUNNER_LOG:" + text(record, "runner_id"), record, documentSha256));
      }
      return new InputProvenance(
          Map.copyOf(document), documentSha256, List.copyOf(graphNodes), gitExecutable);
    }

    private static Map<String, Object> graphNode(
        String nodeId, Map<String, Object> fileRecord, String provenanceSha256) {
      return Map.of(
          "artifact_sha256", fileRecord.get("sha256"),
          "node_id", nodeId,
          "provenance_sha256", provenanceSha256,
          "size_bytes", fileRecord.get("size_bytes"));
    }

    private static Path verifyFileRecord(
        Map<String, Object> record, Path expectedPath, String label) throws IOException {
      return verifyFileRecord(record, expectedPath, label, null);
    }

    private static Path verifyFileRecord(
        Map<String, Object> record,
        Path expectedPath,
        String label,
        FileSnapshot snapshot)
        throws IOException {
      var path = normalizedPath(record.get("path"), label + " path");
      if (expectedPath != null) {
        require(
            path.equals(expectedPath.toAbsolutePath().normalize()),
            label + " path differs from the capture input");
      }
      var declaredSha256 = text(record, "sha256");
      requireContentId(declaredSha256, label + " digest");
      if (snapshot != null) {
        require(path.equals(snapshot.path()), label + " snapshot path mismatch");
        require(
            integer(record.get("size_bytes"), label + " size") == snapshot.sizeBytes(),
            label + " snapshot size differs from preparation");
        require(
            snapshot.sha256().equals(declaredSha256),
            label + " snapshot digest differs from preparation");
      } else {
        requireRegular(path, label);
        require(
            integer(record.get("size_bytes"), label + " size") == Files.size(path),
            label + " size changed after preparation");
        require(
            sha256Id(path).equals(declaredSha256), label + " digest changed after preparation");
      }
      return path;
    }

    private static Path normalizedPath(Object value, String label) {
      var rawPath = textValue(value, label);
      var path = Path.of(rawPath);
      require(path.isAbsolute(), label + " is not absolute");
      var normalized = path.normalize();
      require(normalized.toString().equals(rawPath), label + " is not normalized");
      return normalized;
    }

    private static Instant utcInstant(Object value, String label) {
      var timestamp = textValue(value, label);
      require(timestamp.endsWith("Z"), label + " is not UTC");
      try {
        return Instant.parse(timestamp);
      } catch (java.time.format.DateTimeParseException error) {
        throw new CaptureException(label + " is not an ISO-8601 instant", error);
      }
    }

    private static Path javaExecutable() {
      var executable = System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java";
      return Path.of(System.getProperty("java.home"), "bin", executable)
          .toAbsolutePath()
          .normalize();
    }
  }

  private static final class Capture {
    private final Options options;

    private Capture(Options options) {
      this.options = options;
    }

    private void run() throws Throwable {
      var voteFixtureSnapshot = FileSnapshot.read(options.voteFixture(), "native vote fixture");
      var provenance = InputProvenance.load(options, voteFixtureSnapshot);
      var design = FrozenDesign.load(options.design());
      var voteFixture = VoteFixture.load(voteFixtureSnapshot);
      var crash =
          CrashObservations.load(
              options.crashObservations(),
              options.profile(),
              design.crashPoints(options.profile()));
      requireRegular(options.hardwareAllocation(), "hardware allocation artifact");
      requireRegular(options.toolchains(), "toolchain artifact");
      requireRegular(options.nativeCore(), "native-core artifact");
      requireRegular(options.faultTrace(), "fault-trace artifact");
      requireRegular(options.projectedFormalTrace(), "projected formal trace");
      requireRegular(options.corpus(), "DLTSTRC1 corpus");
      Files.createDirectories(options.durableDirectory());
      var outputParent = options.output().getParent();
      require(outputParent != null, "output has no parent directory");
      Files.createDirectories(outputParent);

      var initialWalSha = hashFileOrEmpty(options.durableDirectory().resolve("runtime.wal"));
      var initialSnapshotSha =
          hashFileOrEmpty(options.durableDirectory().resolve("runtime.snapshot"));
      var descriptor = RuntimeDescriptor.frozen();
      var voteEvidence = captureVoteEvidence(descriptor, voteFixture);
      try (var corpus = new Corpus(options.corpus());
          var copies = new CopySpool(outputParent, design.copyCounters());
          var requestOrder = new RequestOrderSpool(options.corpus(), outputParent)) {
        require(
            corpus.operationCount()
                == (long) WARMUP_OPERATIONS
                    + ((long) FIXED_BLOCKS * FIXED_OPERATIONS_PER_BLOCK),
            "corpus must contain exactly the deterministic warm-up/fixed prefix");
        require(
            requestOrder.size() == corpus.operationCount(),
            "request-order catalog does not cover the complete corpus");
        var initialStateRoot = contentId(ROUND_STATE_DOMAIN, corpus.initialState());
        var formalTrace =
            ProjectedFormalTrace.load(
                options.projectedFormalTrace(),
                options.sourceCommit(),
                options.sourceTree(),
                corpus.fileSha256(),
                initialStateRoot,
                corpus.initialDurableSequence(),
                corpus.initialProjection(),
                corpus.operationCount(),
                requestOrder);
        var initialArtifacts = new TreeMap<String, Object>();
        initialArtifacts.put("initial_state_sha256", sha256Id(corpus.initialState()));
        initialArtifacts.put("snapshot_sha256", initialSnapshotSha);
        initialArtifacts.put("wal_sha256", initialWalSha);
        var adapter = openAdapter(options, descriptor, corpus.initialState());
        WorkloadResult result;
        try (adapter) {
          result =
              executeWorkload(
                  adapter,
                  corpus,
                  copies,
                  initialStateRoot,
                  corpus.initialDurableSequence(),
                  formalTrace,
                  voteEvidence);
        }
        require(
            result.deterministicTerminalStateRoot().equals(formalTrace.terminalStateRoot()),
            "projected formal trace terminal root differs from the executed deterministic prefix");
        copies.finish();
        if (options.profile() == Profile.ISOLATED_SIDECAR) {
          require(
              result.stats().maxSubmitStagingFallbackBytes() != null
                  && result.stats().maxSubmitStagingFallbackBytes()
                      >= copies.maximumStagingFallbackBytes(),
              "supervisor copy telemetry is smaller than a measured SUBMIT sample");
        }
        require(
            sha256Id(options.corpus()).equals(corpus.fileSha256()),
            "corpus changed while the qualification process was running");
        var root =
            rawRun(
                design,
                crash,
                provenance,
                descriptor,
                initialArtifacts,
                copies,
                requestOrder,
                result,
                corpus.fileSha256());
        writeAtomically(options.output(), root);
      }
    }

    private Adapter openAdapter(
        Options selected, RuntimeDescriptor descriptor, byte[] initialState) throws Throwable {
      return openAdapter(
          selected, descriptor, selected.durableDirectory(), initialState, null);
    }

    private Adapter openAdapter(
        Options selected,
        RuntimeDescriptor descriptor,
        Path durableDirectory,
        byte[] initialState,
        byte[] votePolicy)
        throws Throwable {
      return switch (selected.profile()) {
        case EMBEDDED_FFM ->
            new EmbeddedAdapter(
                Objects.requireNonNull(selected.nativeLibrary()),
                durableDirectory,
                initialState,
                votePolicy,
                descriptor);
        case ISOLATED_SIDECAR ->
            new IsolatedAdapter(
                Objects.requireNonNull(selected.sidecarExecutable()),
                durableDirectory,
                initialState,
                votePolicy,
                descriptor);
      };
    }

    private VoteEvidence captureVoteEvidence(
        RuntimeDescriptor descriptor, VoteFixture fixture) throws Throwable {
      var captureRoot = options.durableDirectory().toAbsolutePath().normalize();
      var voteDirectory = captureRoot.resolve("record-vote-v1").normalize();
      require(
          voteDirectory.getParent().equals(captureRoot),
          "vote durable directory escaped the capture root");
      require(!Files.exists(voteDirectory), "vote durable directory already exists");
      Files.createDirectory(voteDirectory);
      var wal = voteDirectory.resolve("runtime.wal");
      require(!Files.exists(wal), "vote WAL existed before the accepted vote");

      byte[] accepted;
      try (var adapter =
          openAdapter(
              options,
              descriptor,
              voteDirectory,
              fixture.initialState(),
              fixture.votePolicy())) {
        accepted = adapter.recordVote(fixture.vote());
        require(
            Arrays.equals(accepted, fixture.expectedReceipt()),
            "native accepted-vote receipt differs from the frozen fixture");
        requireRegular(wal, "accepted-vote WAL");
        require(Files.size(wal) > 0, "accepted vote returned before a non-empty WAL existed");
      }
      var acceptedWal = new WalArtifact(sha256Id(wal), Files.size(wal));

      byte[] replay;
      try (var adapter =
          openAdapter(
              options,
              descriptor,
              voteDirectory,
              fixture.initialState(),
              fixture.votePolicy())) {
        require(
            new WalArtifact(sha256Id(wal), Files.size(wal)).equals(acceptedWal),
            "vote WAL changed while reopening recovered durable state");
        replay = adapter.recordVote(fixture.vote());
        require(
            Arrays.equals(replay, fixture.expectedReceipt()),
            "native replay changed the canonical durable vote receipt");
        require(
            new WalArtifact(sha256Id(wal), Files.size(wal)).equals(acceptedWal),
            "exact vote replay appended or rewrote durable state");
      }
      require(
          new WalArtifact(sha256Id(wal), Files.size(wal)).equals(acceptedWal),
          "vote WAL changed while closing the recovered runtime");
      return new VoteEvidence(List.of(accepted, replay), acceptedWal);
    }

    private WorkloadResult executeWorkload(
        Adapter adapter,
        Corpus corpus,
        CopySpool copies,
        String initialStateRoot,
        long initialDurableSequence,
        ProjectedFormalTrace formalTrace,
        VoteEvidence voteEvidence)
        throws Throwable {
      var fixed = new ArrayList<Object>();
      var saturation = new ArrayList<Object>();
      var replays = new ArrayList<ReplayTarget>();
      var transcripts = new TranscriptDigests();
      for (var receipt : voteEvidence.receipts()) {
        transcripts.addVoteReceipt(receipt);
      }
      var cursor = new StateCursor(initialStateRoot, initialDurableSequence);
      var projection = formalTrace.executionVerifier();

      for (var index = 0; index < WARMUP_OPERATIONS; ++index) {
        var command = corpus.next();
        var result = validateNewOperation(command, adapter.execute(command), cursor);
        projection.accept(command, result);
        transcripts.addDeterministic(result);
      }

      for (var blockIndex = 0; blockIndex < FIXED_BLOCKS; ++blockIndex) {
        var latencies = new ArrayList<Object>(FIXED_OPERATIONS_PER_BLOCK);
        var phases = new ArrayList<Object>(FIXED_OPERATIONS_PER_BLOCK);
        var offerOffsets = new ArrayList<Object>(FIXED_OPERATIONS_PER_BLOCK);
        var pending = new ArrayList<PendingOperation>(FIXED_OPERATIONS_PER_BLOCK);
        var blockStart = System.nanoTime();
        var deadline = Math.addExact(blockStart, WINDOW_NANOS);
        for (var operationIndex = 0;
            operationIndex < FIXED_OPERATIONS_PER_BLOCK;
            ++operationIndex) {
          var targetOffer =
              Math.addExact(
                  blockStart, Math.multiplyExact(operationIndex, FIXED_INTERVAL_NANOS));
          await(targetOffer);
          var offeredAt = System.nanoTime();
          require(offeredAt >= targetOffer, "fixed-load monotonic offer preceded its slot");
          require(
              offeredAt - targetOffer < FIXED_INTERVAL_NANOS,
              "fixed-load offer missed its absolute 100/s slot");
          var command = corpus.next();
          var submission = adapter.tryExecute(command, offeredAt);
          require(submission.accepted(), "fixed-load bounded ingress rejected an offer");
          offerOffsets.add(checkedElapsed(offeredAt, blockStart, "fixed-load offer offset"));
          pending.add(new PendingOperation(command, submission));
        }

        CorpusRecord replayCommand = null;
        ValidatedOperation replayResult = null;
        for (var offered : pending) {
          var timed = awaitSubmission(offered.submission());
          require(
              timed.completedAtNanos() - deadline <= 0,
              "fixed-load operation missed its exact completion window");
          var command = offered.command();
          var result = validateNewOperation(command, timed.operation(), cursor);
          require(result.totalLatencyNanos() > 0, "fixed-load end-to-end latency is zero");
          require(result.phaseLatencyNanos() > 0, "fixed-load phase latency is zero");
          latencies.add(result.totalLatencyNanos());
          phases.add(result.phaseLatencyNanos());
          copies.add(command.requestId(), result.copyValues());
          projection.accept(command, result);
          transcripts.addDeterministic(result);
          replayCommand = command;
          replayResult = result;
        }
        await(deadline);
        require(replayCommand != null && replayResult != null, "fixed block had no replay target");
        replays.add(new ReplayTarget(replayCommand, replayResult));
        var block = new TreeMap<String, Object>();
        block.put("block_index", (long) blockIndex);
        block.put("completed_operations", (long) FIXED_OPERATIONS_PER_BLOCK);
        block.put("latency_ns", latencies);
        block.put("offer_offset_ns", offerOffsets);
        block.put("offered_operations", (long) FIXED_OPERATIONS_PER_BLOCK);
        block.put("offered_ops_per_second", (long) FIXED_RATE_PER_SECOND);
        block.put("phase_latency_ns", phases);
        block.put("window_seconds", (long) WINDOW_SECONDS);
        fixed.add(block);
      }

      var deterministicState = adapter.state();
      verifyState(deterministicState, cursor);
      projection.finish();
      var deterministicTerminalStateRoot = cursor.stateRoot();
      var walPath = options.durableDirectory().resolve("runtime.wal");
      requireRegular(walPath, "fixed-prefix WAL");
      var runtimeWal = new WalArtifact(sha256Id(walPath), Files.size(walPath));

      for (var target : replays) {
        var replay = adapter.execute(target.command());
        validateReplay(target, replay, cursor);
        transcripts.addReplay(target.result());
      }
      verifyState(adapter.state(), cursor);

      long saturationRetryCount = 0;
      for (var blockIndex = 0; blockIndex < SATURATION_BLOCKS; ++blockIndex) {
        var completed = 0L;
        var admitted = 0L;
        var blockStart = System.nanoTime();
        var deadline = Math.addExact(blockStart, WINDOW_NANOS);
        var outstanding = new ArrayDeque<PendingReplay>(SidecarIpcV1.IN_FLIGHT_CORRELATIONS);
        while (outstanding.size() < SidecarIpcV1.IN_FLIGHT_CORRELATIONS
            && admitted < SATURATION_OFFERS_PER_BLOCK
            && System.nanoTime() - deadline < 0) {
          var target = replays.get(Math.toIntExact(admitted % replays.size()));
          var submission = adapter.tryExecute(target.command(), System.nanoTime());
          require(submission.accepted(), "saturation bounded ingress rejected below capacity");
          outstanding.addLast(new PendingReplay(target, submission, admitted));
          admitted = Math.addExact(admitted, 1L);
        }
        while (!outstanding.isEmpty()) {
          var pendingReplay = outstanding.removeFirst();
          var timed = awaitSubmission(pendingReplay.submission());
          validateReplay(pendingReplay.target(), timed.operation(), cursor);
          saturationRetryCount = Math.addExact(saturationRetryCount, 1L);
          if (timed.completedAtNanos() - deadline <= 0) {
            copies.add(
                pendingReplay.target().command().requestId()
                    + "#saturation-"
                    + blockIndex
                    + "-"
                    + pendingReplay.logicalOfferOrdinal(),
                timed.operation().copyValues());
            completed = Math.addExact(completed, 1L);
          }
          while (outstanding.size() < SidecarIpcV1.IN_FLIGHT_CORRELATIONS
              && admitted < SATURATION_OFFERS_PER_BLOCK
              && System.nanoTime() - deadline < 0) {
            var target = replays.get(Math.toIntExact(admitted % replays.size()));
            var submission = adapter.tryExecute(target.command(), System.nanoTime());
            require(submission.accepted(), "saturation bounded ingress rejected below capacity");
            outstanding.addLast(new PendingReplay(target, submission, admitted));
            admitted = Math.addExact(admitted, 1L);
          }
        }
        require(
            admitted < SATURATION_OFFERS_PER_BLOCK,
            "finite saturation offer set was exhausted before the exact window ended");
        require(completed > 0, "saturation block completed no operation in its exact window");
        var block = new TreeMap<String, Object>();
        block.put("admitted_operations", admitted);
        block.put("block_index", (long) blockIndex);
        block.put("completed_operations", completed);
        block.put("cutoff_outcome", "HARNESS_CUTOFF_PRE_ADMISSION");
        block.put("offered_operations", SATURATION_OFFERS_PER_BLOCK);
        block.put(
            "unadmitted_at_cutoff",
            Math.subtractExact(SATURATION_OFFERS_PER_BLOCK, admitted));
        block.put("window_seconds", (long) WINDOW_SECONDS);
        saturation.add(block);
      }
      verifyState(adapter.state(), cursor);
      var stats = adapter.stats();
      require(
          new WalArtifact(sha256Id(walPath), Files.size(walPath)).equals(runtimeWal),
          "exact replays appended or rewrote the runtime WAL");
      var walArtifacts = new WalArtifacts(voteEvidence.walArtifact(), runtimeWal);
      return new WorkloadResult(
          List.copyOf(fixed),
          List.copyOf(saturation),
          transcripts.finish(walArtifacts, formalTrace.projectedTraceSha256()),
          walArtifacts,
          stats,
          Math.addExact((long) replays.size(), saturationRetryCount),
          corpus.consumedOperations(),
          deterministicTerminalStateRoot);
    }

    private Map<String, Object> rawRun(
        FrozenDesign design,
        CrashObservations crash,
        InputProvenance provenance,
        RuntimeDescriptor descriptor,
        Map<String, Object> initialArtifacts,
        CopySpool copies,
        RequestOrderSpool requestOrder,
        WorkloadResult result,
        String corpusSha256)
        throws IOException {
      var root = new TreeMap<String, Object>();
      root.put("aggregation_rules", design.aggregation());
      root.put("bounds", design.bounds());
      root.put("canonical_input_trace_sha256", corpusSha256);
      root.put("copy_accounting", copyAccounting(copies));
      root.put("design_canonical_id", DESIGN_CANONICAL_ID);
      root.put("design_sha256", DESIGN_RAW_SHA256);
      root.put("execution_class", EXECUTION_CLASS);
      root.put("fault_trace_sha256", sha256Id(options.faultTrace()));
      root.put("fixed_load_blocks", result.fixedLoadBlocks());
      root.put("formal_semantics_id", FORMAL_SEMANTICS_ID);
      root.put("hardware_allocation_sha256", sha256Id(options.hardwareAllocation()));
      root.put("initial_artifacts", initialArtifacts);
      root.put("input_graph_nodes", provenance.graphNodes());
      root.put("input_provenance", provenance.document());
      root.put("input_provenance_sha256", provenance.documentSha256());
      root.put("java_process_survival", crash.javaProcessSurvival());
      var runtimeStats = runtimeStats(result);
      root.put("measurements", measurements(crash, result, runtimeStats));
      root.put("native_core_sha256", sha256Id(options.nativeCore()));
      root.put("operation_copy_samples", copies.rawArray());
      root.put("output_transcripts", transcriptEvidence(result.transcriptSha256()));
      root.put("profile_id", options.profile().name());
      root.put("request_order", requestOrder.rawArray());
      root.put("restart_to_ready", crash.restartToReady());
      root.put("runtime_ids", descriptor.runtimeIds());
      root.put("runtime_stats", runtimeStats);
      root.put("saturation_blocks", result.saturationBlocks());
      root.put("saturation_request_schedule", saturationRequestSchedule(requestOrder));
      root.put("schema_version", SCHEMA_VERSION);
      root.put(
          "source",
          Map.of("commit", options.sourceCommit(), "tree", options.sourceTree()));
      root.put("timer_order", List.of());
      root.put("toolchains_sha256", sha256Id(options.toolchains()));
      root.put("type_name", RUN_TYPE);
      root.put("wal_artifacts", result.walArtifacts().document());
      root.put("warmup_completed_operations", (long) WARMUP_OPERATIONS);
      return root;
    }

    private Map<String, Object> saturationRequestSchedule(RequestOrderSpool requestOrder) {
      var targets = requestOrder.saturationReplayTargets();
      var core = new TreeMap<String, Object>();
      core.put("block_count", (long) SATURATION_BLOCKS);
      core.put("cycle_length", (long) targets.size());
      core.put("max_in_flight", (long) SidecarIpcV1.IN_FLIGHT_CORRELATIONS);
      core.put("offers_per_block", SATURATION_OFFERS_PER_BLOCK);
      core.put(
          "replay_rule",
          "FINITE_RLE_CYCLE_FIXED_BLOCK_TERMINAL_REQUESTS_THEN_HARNESS_CUTOFF_PRE_ADMISSION");
      core.put("schema_version", SCHEMA_VERSION);
      core.put("target_request_ids", targets);
      core.put(
          "total_logical_offers",
          Math.multiplyExact((long) SATURATION_BLOCKS, SATURATION_OFFERS_PER_BLOCK));
      core.put("type_name", "FEATURE010_SATURATION_REPLAY_SCHEDULE");
      var artifact = sha256Id(Json.bytes(core));
      var observations = new TreeMap<String, Object>();
      observations.put("cycle_length", (long) targets.size());
      observations.put("max_in_flight", (long) SidecarIpcV1.IN_FLIGHT_CORRELATIONS);
      observations.put("offers_per_block", SATURATION_OFFERS_PER_BLOCK);
      observations.put("replay_rule", core.get("replay_rule"));
      observations.put("target_request_ids_sha256", sha256Id(Json.bytes(targets)));
      var scheduleEvidence =
          evidence(artifact, "PREDECLARED_IDENTICAL_REPLAY_STREAM", observations);
      var schedule = new TreeMap<>(core);
      schedule.put("evidence", scheduleEvidence);
      schedule.put("evidence_sha256", sha256Id(Json.bytes(scheduleEvidence)));
      return schedule;
    }

    private List<Object> copyAccounting(CopySpool copies) {
      var result = new ArrayList<Object>();
      var totalsArtifact = sha256Id(Json.bytes(copies.totalsObject()));
      for (var index = 0; index < COPY_COUNTERS.size(); ++index) {
        var counter = COPY_COUNTERS.get(index);
        var value = copies.total(index);
        var observations = new TreeMap<String, Object>();
        observations.put("counter_id", counter);
        observations.put("profile_id", options.profile().name());
        observations.put("value", value);
        var evidence = evidence(totalsArtifact, "COUNTER_SUM_MATCHES_OPERATION_SAMPLES", observations);
        var record = new TreeMap<String, Object>();
        record.put("counter_id", counter);
        record.put("evidence", evidence);
        record.put("evidence_sha256", sha256Id(Json.bytes(evidence)));
        record.put("value", value);
        result.add(record);
      }
      return result;
    }

    private Map<String, Object> runtimeStats(WorkloadResult result) {
      var stats = new TreeMap<String, Object>();
      stats.put("duplicate_response_count", result.stats().duplicateResponses());
      stats.put("rejected_frame_count", result.stats().rejectedFrames());
      stats.put("retry_count", result.retryCount());
      stats.put("stale_response_count", result.stats().staleResponses());
      return stats;
    }

    private List<Object> measurements(
        CrashObservations crash,
        WorkloadResult result,
        Map<String, Object> runtimeStats) {
      var output = new ArrayList<Object>();
      var fixedArtifact = sha256Id(Json.bytes(result.fixedLoadBlocks()));
      var saturationArtifact = sha256Id(Json.bytes(result.saturationBlocks()));
      var transcriptArtifact = sha256Id(Json.bytes(result.transcriptSha256()));
      var runtimeStatsArtifact = sha256Id(Json.bytes(runtimeStats));
      for (var measurementId : MEASUREMENT_IDS) {
        var observations = new TreeMap<String, Object>();
        observations.put("measurement_id", measurementId);
        observations.put("profile_id", options.profile().name());
        String artifact;
        String check;
        switch (measurementId) {
          case "END_TO_END_LATENCY_NS", "PHASE_LATENCY_NS", "FIXED_LOAD_THROUGHPUT_OPS_PER_WINDOW" -> {
            artifact = fixedArtifact;
            check = "ALL_FIXED_LOAD_SAMPLES_PRESENT";
          }
          case "SATURATION_THROUGHPUT_OPS_PER_WINDOW" -> {
            observations.put("executed_corpus_prefix_operations", result.consumedCorpusOperations());
            observations.put("request_order_scope", "FULL_DLTSTRC1_ORDERED_INPUT_CORPUS");
            artifact = saturationArtifact;
            check = "ALL_SATURATION_WINDOWS_PRESENT";
          }
          case "RESTART_TO_READY_NS" -> {
            artifact = crash.artifactSha256();
            check = "INDEPENDENT_CRASH_RECEIPTS_IMPORTED";
          }
          case "JAVA_PROCESS_SURVIVAL" -> {
            artifact = crash.artifactSha256();
            check = "PROFILE_BOUNDARY_SURVIVAL_REPORTED";
          }
          case "STATE_EFFECT_WAL_REPLAY_IDENTITY" -> {
            artifact = transcriptArtifact;
            check = "CONCRETE_TRANSCRIPTS_CAPTURED";
          }
          case "RETRY_COUNT" -> {
            observations.put("value", result.retryCount());
            artifact = runtimeStatsArtifact;
            check = "EXACT_REPLAYS_COMPLETED";
          }
          case "DUPLICATE_RESPONSE_COUNT" -> {
            observations.put("value", result.stats().duplicateResponses());
            artifact = runtimeStatsArtifact;
            check = "CLIENT_COUNTER_CAPTURED";
          }
          case "STALE_RESPONSE_COUNT" -> {
            observations.put("value", result.stats().staleResponses());
            artifact = runtimeStatsArtifact;
            check = "CLIENT_COUNTER_CAPTURED";
          }
          case "REJECTED_FRAME_COUNT" -> {
            observations.put("value", result.stats().rejectedFrames());
            artifact = runtimeStatsArtifact;
            check = "CLIENT_COUNTER_CAPTURED";
          }
          default -> throw new CaptureException("unknown frozen measurement " + measurementId);
        }
        var evidence = evidence(artifact, check, observations);
        var record = new TreeMap<String, Object>();
        record.put("evidence", evidence);
        record.put("evidence_sha256", sha256Id(Json.bytes(evidence)));
        record.put("measurement_id", measurementId);
        output.add(record);
      }
      return output;
    }

    private List<Object> transcriptEvidence(Map<String, String> hashes) {
      var result = new ArrayList<Object>();
      for (var id : TRANSCRIPT_IDS) {
        var hash = hashes.get(id);
        require(hash != null, "missing transcript " + id);
        var observations = new TreeMap<String, Object>();
        observations.put("equality_id", id);
        observations.put("profile_id", options.profile().name());
        observations.put("transcript_sha256", hash);
        var evidence = evidence(hash, "CONCRETE_TRANSCRIPT_HASHED", observations);
        var record = new TreeMap<String, Object>();
        record.put("equality_id", id);
        record.put("evidence", evidence);
        record.put("evidence_sha256", sha256Id(Json.bytes(evidence)));
        record.put("transcript_sha256", hash);
        result.add(record);
      }
      return result;
    }
  }

  private static ValidatedOperation validateNewOperation(
      CorpusRecord command, OperationResult result, StateCursor cursor) {
    require(result.nativeStatus() == 0, "native submit returned status " + result.nativeStatus());
    var effect = CanonicalEnvelope.decode(result.effectBytes(), 7);
    require(
        text(effect, "request_id").equals(command.requestId()),
        "effect request ID differs from submitted command");
    var prior = text(effect, "prior_state_root");
    var next = text(effect, "next_state_root");
    require(prior.equals(cursor.stateRoot()), "effect prior state root is not contiguous");
    require(next.equals(result.nextStateRoot()), "native next-state receipt differs from effect");
    require(prior.equals(result.priorStateRoot()), "native prior-state receipt differs from effect");
    var effectId = contentId(EFFECT_BATCH_DOMAIN, result.effectBytes());
    require(effectId.equals(result.effectId()), "native effect identity differs from effect bytes");
    var sequence = Math.addExact(cursor.durableSequence(), 1L);
    require(result.durableSequence() == sequence, "native durable sequence is not contiguous");
    cursor.advance(next, sequence);
    return new ValidatedOperation(
        result.nativeStatus(),
        result.effectBytes(),
        effectId,
        prior,
        next,
        sequence,
        result.totalLatencyNanos(),
        result.phaseLatencyNanos(),
        result.copyValues());
  }

  private static void validateReplay(
      ReplayTarget target, OperationResult replay, StateCursor cursor) {
    require(replay.nativeStatus() == target.result().nativeStatus(), "replay status changed");
    require(Arrays.equals(replay.effectBytes(), target.result().effectBytes()), "replay effect changed");
    require(replay.effectId().equals(target.result().effectId()), "replay effect identity changed");
    require(
        replay.priorStateRoot().equals(target.result().priorStateRoot())
            && replay.nextStateRoot().equals(target.result().nextStateRoot()),
        "replay state roots changed");
    require(
        replay.durableSequence() == target.result().durableSequence(),
        "replay durable sequence changed");
    require(
        cursor.durableSequence() >= target.result().durableSequence(),
        "replay target is ahead of current durable state");
  }

  private static void verifyState(byte[] state, StateCursor cursor) {
    var decoded = CanonicalEnvelope.decode(state, 5);
    require(
        decimal(text(decoded, "durable_sequence"), "state durable sequence")
            == cursor.durableSequence(),
        "read-back durable sequence differs from receipts");
    require(
        contentId(ROUND_STATE_DOMAIN, state).equals(cursor.stateRoot()),
        "read-back canonical state root differs from receipts");
  }

  private static final class StateCursor {
    private String stateRoot;
    private long durableSequence;

    private StateCursor(String stateRoot, long durableSequence) {
      requireContentId(stateRoot, "initial state root");
      require(durableSequence >= 0, "initial durable sequence is negative");
      this.stateRoot = stateRoot;
      this.durableSequence = durableSequence;
    }

    private String stateRoot() {
      return stateRoot;
    }

    private long durableSequence() {
      return durableSequence;
    }

    private void advance(String nextStateRoot, long nextDurableSequence) {
      requireContentId(nextStateRoot, "next state root");
      require(nextDurableSequence > durableSequence, "durable sequence did not advance");
      stateRoot = nextStateRoot;
      durableSequence = nextDurableSequence;
    }
  }

  private record CopyValues(long[] values) {
    private CopyValues {
      Objects.requireNonNull(values, "values");
      require(values.length == COPY_COUNTERS.size(), "copy sample has the wrong counter count");
      values = Arrays.copyOf(values, values.length);
      for (var value : values) {
        require(value >= 0, "copy sample contains a negative counter");
      }
      require(values[6] <= 1 && values[7] <= 1, "zero-copy counters are not Boolean");
      require(values[7] <= values[6], "zero-copy hit exceeds eligibility");
    }

    @Override
    public long[] values() {
      return Arrays.copyOf(values, values.length);
    }
  }

  private record OperationResult(
      long nativeStatus,
      byte[] effectBytes,
      String effectId,
      String priorStateRoot,
      String nextStateRoot,
      long durableSequence,
      long totalLatencyNanos,
      long phaseLatencyNanos,
      CopyValues copyValues) {
    private OperationResult {
      Objects.requireNonNull(effectBytes, "effectBytes");
      effectBytes = Arrays.copyOf(effectBytes, effectBytes.length);
      requireContentId(effectId, "effect ID");
      requireContentId(priorStateRoot, "prior state root");
      requireContentId(nextStateRoot, "next state root");
      require(durableSequence >= 0, "invalid native durable sequence");
      require(totalLatencyNanos >= 0, "negative end-to-end latency");
      require(phaseLatencyNanos >= 0, "negative phase latency");
      Objects.requireNonNull(copyValues, "copyValues");
    }

    @Override
    public byte[] effectBytes() {
      return Arrays.copyOf(effectBytes, effectBytes.length);
    }
  }

  private record TimedOperation(
      OperationResult operation, long offeredAtNanos, long completedAtNanos) {
    private TimedOperation {
      Objects.requireNonNull(operation, "operation");
      require(offeredAtNanos >= 0, "operation offer timestamp is negative");
      require(completedAtNanos >= offeredAtNanos, "operation completed before it was offered");
    }
  }

  private record Submission(boolean accepted, CompletableFuture<TimedOperation> completion) {
    private Submission {
      Objects.requireNonNull(completion, "completion");
      require(accepted || completion.isCompletedExceptionally(), "rejected submission is not final");
    }

    private static Submission rejected(String reason) {
      var completion = new CompletableFuture<TimedOperation>();
      completion.completeExceptionally(new CaptureException(reason));
      return new Submission(false, completion);
    }
  }

  private record PendingOperation(CorpusRecord command, Submission submission) {
    private PendingOperation {
      Objects.requireNonNull(command, "command");
      require(submission.accepted(), "pending operation was not accepted");
    }
  }

  private record PendingReplay(
      ReplayTarget target, Submission submission, long logicalOfferOrdinal) {
    private PendingReplay {
      Objects.requireNonNull(target, "target");
      require(submission.accepted(), "pending replay was not accepted");
      require(logicalOfferOrdinal >= 0, "pending replay offer ordinal is negative");
    }
  }

  private record ValidatedOperation(
      long nativeStatus,
      byte[] effectBytes,
      String effectId,
      String priorStateRoot,
      String nextStateRoot,
      long durableSequence,
      long totalLatencyNanos,
      long phaseLatencyNanos,
      CopyValues copyValues) {
    private ValidatedOperation {
      effectBytes = Arrays.copyOf(effectBytes, effectBytes.length);
    }

    @Override
    public byte[] effectBytes() {
      return Arrays.copyOf(effectBytes, effectBytes.length);
    }
  }

  private record ReplayTarget(CorpusRecord command, ValidatedOperation result) {}

  private record RuntimeStats(
      long duplicateResponses,
      long staleResponses,
      long rejectedFrames,
      Long maxSubmitStagingFallbackBytes) {
    private RuntimeStats {
      require(duplicateResponses >= 0, "negative duplicate-response count");
      require(staleResponses >= 0, "negative stale-response count");
      require(rejectedFrames >= 0, "negative rejected-frame count");
      require(
          maxSubmitStagingFallbackBytes == null || maxSubmitStagingFallbackBytes >= 0,
          "negative maximum staging-fallback count");
    }
  }

  private record WorkloadResult(
      List<Object> fixedLoadBlocks,
      List<Object> saturationBlocks,
      Map<String, String> transcriptSha256,
      WalArtifacts walArtifacts,
      RuntimeStats stats,
      long retryCount,
      long consumedCorpusOperations,
      String deterministicTerminalStateRoot) {
    private WorkloadResult {
      require(retryCount >= 0, "retry count is negative");
    }
  }

  private record WalArtifact(String sha256, long sizeBytes) {
    private WalArtifact {
      requireContentId(sha256, "WAL artifact digest");
      require(sizeBytes > 0, "WAL artifact is empty");
    }

    private Map<String, Object> document() {
      var result = new TreeMap<String, Object>();
      result.put("sha256", sha256);
      result.put("size_bytes", sizeBytes);
      return result;
    }
  }

  private record WalArtifacts(WalArtifact recordVote, WalArtifact runtime) {
    private WalArtifacts {
      Objects.requireNonNull(recordVote, "recordVote");
      Objects.requireNonNull(runtime, "runtime");
    }

    private Map<String, Object> document() {
      var result = new TreeMap<String, Object>();
      result.put("record_vote", recordVote.document());
      result.put("runtime", runtime.document());
      return result;
    }
  }

  private record VoteEvidence(List<byte[]> receipts, WalArtifact walArtifact) {
    private VoteEvidence {
      require(receipts.size() == 2, "vote evidence must contain accepted and replay receipts");
      var copy = new ArrayList<byte[]>(receipts.size());
      for (var receipt : receipts) {
        require(receipt.length > 0, "vote evidence contains an empty receipt");
        copy.add(Arrays.copyOf(receipt, receipt.length));
      }
      receipts = List.copyOf(copy);
      Objects.requireNonNull(walArtifact, "walArtifact");
    }

    @Override
    public List<byte[]> receipts() {
      var copy = new ArrayList<byte[]>(receipts.size());
      for (var receipt : receipts) {
        copy.add(Arrays.copyOf(receipt, receipt.length));
      }
      return List.copyOf(copy);
    }
  }

  private static final class TranscriptDigests {
    private final MessageDigest statuses = newSha256();
    private final MessageDigest effects = newSha256();
    private final MessageDigest stateRoots = newSha256();
    private final MessageDigest replays = newSha256();
    private final MessageDigest voteReceipts = newSha256();
    private int voteReceiptCount;
    private boolean finished;

    private void addDeterministic(ValidatedOperation operation) {
      require(!finished, "transcript digest is already finished");
      updateU32(statuses, operation.nativeStatus());
      updateU32(effects, operation.effectBytes().length);
      effects.update(operation.effectBytes());
      stateRoots.update(contentIdDigest(operation.priorStateRoot()));
      stateRoots.update(contentIdDigest(operation.nextStateRoot()));
    }

    private void addReplay(ValidatedOperation operation) {
      require(!finished, "transcript digest is already finished");
      var identity = operation.effectId().getBytes(StandardCharsets.US_ASCII);
      updateU32(replays, identity.length);
      replays.update(identity);
      updateU64(replays, operation.durableSequence());
    }

    private void addVoteReceipt(byte[] receipt) {
      require(!finished, "transcript digest is already finished");
      require(
          receipt.length > 0
              && receipt.length <= SidecarIpcV1.MAX_CANONICAL_VOTE_RECEIPT_BYTES,
          "canonical vote receipt is outside the frozen bound");
      updateU32(voteReceipts, receipt.length);
      voteReceipts.update(receipt);
      voteReceiptCount = Math.addExact(voteReceiptCount, 1);
    }

    private Map<String, String> finish(
        WalArtifacts walArtifacts, String formalTraceSha256) {
      require(!finished, "transcript digest was finished twice");
      finished = true;
      Objects.requireNonNull(walArtifacts, "walArtifacts");
      requireContentId(formalTraceSha256, "formal trace hash");
      require(
          voteReceiptCount == 2,
          "vote transcript must contain exactly one accepted receipt and one replay receipt");
      var result = new LinkedHashMap<String, String>();
      result.put("CANONICAL_STATUS_BYTES", digestId(statuses));
      result.put("CANONICAL_EFFECT_BYTES", digestId(effects));
      result.put("STATE_ROOTS", digestId(stateRoots));
      result.put(
          "WAL_RECEIPTS_AND_DURABLE_SEQUENCES",
          sha256Id(Json.bytes(walArtifacts.document())));
      result.put("REPLAY_EFFECT_IDENTITIES", digestId(replays));
      result.put("PROJECTED_FORMAL_TRACE_BYTES_AFTER_STUTTER_ERASURE", formalTraceSha256);
      result.put("CANONICAL_VOTE_RECEIPT_BYTES", digestId(voteReceipts));
      return Map.copyOf(result);
    }
  }

  private record RawJsonArray(Path path, long size) {
    private RawJsonArray {
      Objects.requireNonNull(path, "path");
      require(size >= 0, "raw JSON array has a negative size");
    }
  }

  private static final class CopySpool implements AutoCloseable {
    private final List<String> counters;
    private final Path path;
    private final BufferedWriter writer;
    private final long[] totals;
    private long count;
    private long maximumStagingFallbackBytes;
    private boolean finished;

    private CopySpool(Path directory, List<String> counters) throws IOException {
      this.counters = List.copyOf(counters);
      require(this.counters.equals(COPY_COUNTERS), "copy spool counter order differs from design");
      path = Files.createTempFile(directory, ".sidecar-copy-samples-", ".jsonpart");
      writer =
          new BufferedWriter(
              new OutputStreamWriter(Files.newOutputStream(path), StandardCharsets.UTF_8),
              64 * 1024);
      totals = new long[counters.size()];
    }

    private void add(String operationId, CopyValues sample) throws IOException {
      require(!finished, "copy spool is closed");
      require(!operationId.isEmpty(), "copy operation ID is empty");
      var values = sample.values();
      var record = new TreeMap<String, Object>();
      record.put("operation_id", operationId);
      for (var index = 0; index < counters.size(); ++index) {
        totals[index] = Math.addExact(totals[index], values[index]);
        record.put(counters.get(index), values[index]);
      }
      maximumStagingFallbackBytes =
          Math.max(maximumStagingFallbackBytes, Math.addExact(values[4], values[5]));
      if (count != 0) {
        writer.write(',');
      }
      Json.write(record, writer);
      count = Math.addExact(count, 1L);
    }

    private void finish() throws IOException {
      if (finished) {
        return;
      }
      writer.flush();
      writer.close();
      finished = true;
      require(count > 0, "copy spool has no measured operation");
    }

    private long total(int index) {
      require(finished, "copy spool totals requested before finish");
      return totals[index];
    }

    private Map<String, Object> totalsObject() {
      require(finished, "copy spool totals requested before finish");
      var result = new TreeMap<String, Object>();
      for (var index = 0; index < counters.size(); ++index) {
        result.put(counters.get(index), totals[index]);
      }
      result.put("operation_count", count);
      return result;
    }

    private RawJsonArray rawArray() {
      require(finished, "copy spool requested before finish");
      return new RawJsonArray(path, count);
    }

    private long maximumStagingFallbackBytes() {
      require(finished, "copy spool maximum requested before finish");
      return maximumStagingFallbackBytes;
    }

    @Override
    public void close() throws IOException {
      try {
        if (!finished) {
          writer.close();
          finished = true;
        }
      } finally {
        Files.deleteIfExists(path);
      }
    }
  }

  /** Complete immutable input order; profile-specific execution is always a prefix of this list. */
  private static final class RequestOrderSpool implements AutoCloseable {
    private static final int DETERMINISTIC_PREFIX_OPERATIONS =
        WARMUP_OPERATIONS + (FIXED_BLOCKS * FIXED_OPERATIONS_PER_BLOCK);
    private static final String PREFIX_ENCODING =
        "DLTSTRC1_U64_ORDINAL_U32_LENGTH_COMMAND_SHA256";
    private static final byte[] TICKET_MAPPING_DOMAIN =
        "deltareduce:010:initial-abstraction-ticket-map:v1"
            .getBytes(StandardCharsets.US_ASCII);
    private static final String TICKET_MAPPING_ENCODING =
        "DLTSTW1_U64_COUNT_THEN_U64_ORDINAL_U32_TICKET_BYTES_U32_WORKER_BYTES_U64_EPOCH_BODY_SHA256";
    private final Path path;
    private final long size;
    private final String prefixTranscriptSha256;
    private final String ticketMappingSha256;
    private final List<DeterministicCommand> deterministicCommands;

    private RequestOrderSpool(Path corpusPath, Path directory) throws IOException {
      path = Files.createTempFile(directory, ".sidecar-request-order-", ".jsonpart");
      var digest = newSha256();
      var mapping = newSha256();
      var requestIds = new ArrayList<String>(DETERMINISTIC_PREFIX_OPERATIONS);
      var uniqueRequestIds = new java.util.HashSet<String>();
      var uniqueBodies = new java.util.HashSet<String>();
      var commands = new ArrayList<DeterministicCommand>(DETERMINISTIC_PREFIX_OPERATIONS);
      long count = 0;
      var complete = false;
      try (var corpus = new Corpus(corpusPath);
          var writer =
              new BufferedWriter(
                  new OutputStreamWriter(Files.newOutputStream(path), StandardCharsets.UTF_8),
                  64 * 1024)) {
        require(
            corpus.operationCount() == DETERMINISTIC_PREFIX_OPERATIONS,
            "comparison corpus must contain exactly the deterministic new-transition prefix");
        mapping.update(TICKET_MAPPING_DOMAIN);
        mapping.update((byte) 0);
        updateU64(mapping, corpus.operationCount());
        while (count < corpus.operationCount()) {
          var command = corpus.next();
          updateU64(digest, command.ordinal());
          updateU32(digest, command.command().length);
          digest.update(command.command());
          digest.update(contentIdDigest(command.commandSha256()));
          require(
              uniqueRequestIds.add(command.requestId()),
              "deterministic prefix reuses a canonical request ID");
          require(
              uniqueBodies.add(command.bodyHash()),
              "deterministic prefix reuses a commitment body hash");
          requestIds.add(command.requestId());
          require(
              command.commandKind().equals("ACCEPT_COMMITMENT"),
              "deterministic comparison prefix is not the frozen commitment workload");
          commands.add(
              new DeterministicCommand(
                  command.requestId(),
                  command.commandKind(),
                  command.actorId(),
                  command.bodyHash(),
                  command.roundId(),
                  command.height(),
                  command.view()));
          updateU64(mapping, command.ordinal());
          updateLengthPrefixedAscii(mapping, command.requestId(), "ticket ID");
          updateLengthPrefixedAscii(mapping, command.actorId(), "lease-holder worker ID");
          updateU64(mapping, 0);
          mapping.update(contentIdDigest(command.bodyHash()));
          var record = new TreeMap<String, Object>();
          record.put("canonical_request_sha256", command.commandSha256());
          record.put("ordinal", count);
          record.put("request_id", command.requestId());
          if (count != 0) {
            writer.write(',');
          }
          Json.write(record, writer);
          count = Math.addExact(count, 1L);
        }
        corpus.verifyComplete();
        writer.flush();
        complete = true;
      } finally {
        if (!complete) {
          Files.deleteIfExists(path);
        }
      }
      size = count;
      prefixTranscriptSha256 = digestId(digest);
      ticketMappingSha256 = digestId(mapping);
      require(
          requestIds.size() == DETERMINISTIC_PREFIX_OPERATIONS,
          "request-order catalog did not retain the complete deterministic prefix");
      require(
          commands.size() == DETERMINISTIC_PREFIX_OPERATIONS,
          "request-order catalog did not retain deterministic command projections");
      deterministicCommands = List.copyOf(commands);
    }

    private long size() {
      return size;
    }

    private String prefixTranscriptSha256() {
      return prefixTranscriptSha256;
    }

    private String ticketMappingSha256() {
      return ticketMappingSha256;
    }

    private List<DeterministicCommand> deterministicCommands() {
      return deterministicCommands;
    }

    private List<String> saturationReplayTargets() {
      var targets = new ArrayList<String>(FIXED_BLOCKS);
      for (var block = 0; block < FIXED_BLOCKS; ++block) {
        var ordinal = WARMUP_OPERATIONS + ((block + 1) * FIXED_OPERATIONS_PER_BLOCK) - 1;
        targets.add(deterministicCommands.get(ordinal).requestId());
      }
      return List.copyOf(targets);
    }

    private RawJsonArray rawArray() {
      return new RawJsonArray(path, size);
    }

    @Override
    public void close() throws IOException {
      Files.deleteIfExists(path);
    }
  }

  private record DeterministicCommand(
      String requestId,
      String commandKind,
      String actorId,
      String bodyHash,
      String roundId,
      long height,
      long view) {
    private DeterministicCommand {
      require(!requestId.isEmpty(), "deterministic command request ID is empty");
      require(commandKind.equals("ACCEPT_COMMITMENT"), "unsupported deterministic command kind");
      require(!actorId.isEmpty(), "deterministic command actor ID is empty");
      requireContentId(bodyHash, "deterministic command body hash");
      require(!roundId.isEmpty(), "deterministic command round ID is empty");
      require(height >= 0, "deterministic command height is negative");
      require(view >= 0, "deterministic command view is negative");
    }
  }

  private static final class ProjectedFormalTrace {
    private static final byte[] EXECUTION_BINDING_DOMAIN =
        "deltareduce:010:native-projection-binding:v1"
            .getBytes(StandardCharsets.US_ASCII);
    private static final String EXECUTION_BINDING_ENCODING =
        "DLTSPB1_U64_COUNT_THEN_U64_ORDINAL_U32_REQUEST_BYTES_COMMAND_STATUS_EFFECT_ROOTS_SEQUENCE_EVENT_SHA256";
    private final String projectedTraceSha256;
    private final String terminalStateRoot;
    private final String executionBindingSha256;
    private final List<ProjectedEvent> events;
    private static final Set<String> RECEIPT_FIELDS =
        Set.of(
            "canonical_input_trace_sha256",
            "deterministic_prefix",
            "formal_semantics_id",
            "initial_abstraction_witness",
            "initial_abstraction_witness_sha256",
            "projected_trace",
            "projected_trace_sha256",
            "schema_version",
            "source",
            "type_name");
    private static final Set<String> PREFIX_FIELDS =
        Set.of(
            "encoding",
            "execution_binding_encoding",
            "execution_binding_sha256",
            "first_ordinal",
            "last_ordinal",
            "operation_count",
            "request_transcript_sha256");
    private static final Set<String> INITIAL_WITNESS_FIELDS =
        Set.of(
            "abstraction_version",
            "abort_request_count",
            "active_lease_count",
            "canonical_input_operation_count",
            "certificate_progress_open",
            "command_transcript_encoding",
            "command_transcript_sha256",
            "completed_ticket_count",
            "content_universe_rule",
            "enable_ticket_actions",
            "first_ordinal",
            "initial_commitment_count",
            "initial_phase",
            "initial_state_root",
            "input_closed",
            "last_ordinal",
            "lease_epoch",
            "mapping_rule",
            "planned_ticket_count",
            "round_id",
            "schema_version",
            "ticket_count",
            "ticket_mapping_encoding",
            "ticket_mapping_sha256",
            "type_name",
            "worker_universe_rule");
    private static final Set<String> TRACE_FIELDS =
        Set.of(
            "abstraction_version",
            "events",
            "formal_semantics_id",
            "initial_state_root",
            "round_contract",
            "schema_version",
            "terminal_outcome",
            "terminal_state_root",
            "trace_id");
    private static final Set<String> EVENT_FIELDS =
        Set.of(
            "action_id",
            "actor_id",
            "actor_role",
            "artifact_refs",
            "body_hash",
            "durable_sequence",
            "error_code",
            "height",
            "logical_time",
            "next_state_root",
            "outcome",
            "parent_hashes",
            "prior_state_root",
            "request_id",
            "result_hash",
            "round_id",
            "schema_version",
            "validator_epoch",
            "view",
            "vote_context_id");
    private static final Set<String> ACTION_IDS =
        Set.of(
            "ACT-ABORT-FINALIZE",
            "ACT-ABORT-VOTE",
            "ACT-APC-FINALIZE",
            "ACT-APC-VOTE",
            "ACT-APPLY-COMPUTE",
            "ACT-APPLY-FINALIZE",
            "ACT-APPLY-VOTE",
            "ACT-ARTIFACT-CORRUPT",
            "ACT-ARTIFACT-LOSE",
            "ACT-ARTIFACT-REPAIR",
            "ACT-AVAIL-ATTEST",
            "ACT-AVAIL-FINALIZE",
            "ACT-COMMIT",
            "ACT-CONFIG-FINALIZE",
            "ACT-CONFIG-PROPOSE",
            "ACT-CONFIG-VOTE",
            "ACT-CRASH",
            "ACT-CURRENT-ADVANCE",
            "ACT-EC-FINALIZE",
            "ACT-EC-VOTE",
            "ACT-INPUT-CLOSE",
            "ACT-ISC-FINALIZE",
            "ACT-ISC-VOTE",
            "ACT-JOURNAL-RECOVER",
            "ACT-LEASE-EXPIRE",
            "ACT-LEASE-OPEN",
            "ACT-LEASE-REASSIGN",
            "ACT-LEASE-RENEW",
            "ACT-LOGICAL-TIME-ADVANCE",
            "ACT-MESSAGE-DELIVER",
            "ACT-MESSAGE-DROP",
            "ACT-MESSAGE-DUPLICATE",
            "ACT-MESSAGE-ENQUEUE",
            "ACT-MESSAGE-REPLAY",
            "ACT-PARAM-FINALIZE",
            "ACT-PARAM-PROPOSE",
            "ACT-PARAM-VOTE",
            "ACT-PARTITION-ENABLE",
            "ACT-PARTITION-HEAL",
            "ACT-PUBLISH",
            "ACT-RESTART",
            "ACT-ROOT-ASSEMBLE",
            "ACT-ROOT-FINALIZE",
            "ACT-ROOT-VOTE",
            "ACT-SEED-GENERATE",
            "ACT-TICKET-ISSUE",
            "ACT-TIMEOUT-SOFT",
            "ACT-VIEW-FINALIZE",
            "ACT-VIEW-VOTE");

    private ProjectedFormalTrace(
        String projectedTraceSha256,
        String terminalStateRoot,
        String executionBindingSha256,
        List<ProjectedEvent> events) {
      requireContentId(projectedTraceSha256, "projected trace digest");
      requireContentId(terminalStateRoot, "projected terminal state root");
      requireContentId(executionBindingSha256, "native projection execution binding");
      require(
          events.size() == RequestOrderSpool.DETERMINISTIC_PREFIX_OPERATIONS,
          "projected trace does not cover the complete deterministic prefix");
      this.projectedTraceSha256 = projectedTraceSha256;
      this.terminalStateRoot = terminalStateRoot;
      this.executionBindingSha256 = executionBindingSha256;
      this.events = List.copyOf(events);
    }

    private String projectedTraceSha256() {
      return projectedTraceSha256;
    }

    private String terminalStateRoot() {
      return terminalStateRoot;
    }

    private ExecutionVerifier executionVerifier() {
      return new ExecutionVerifier(events, executionBindingSha256);
    }

    private static ProjectedFormalTrace load(
        Path path,
        String sourceCommit,
        String sourceTree,
        String corpusSha256,
        String initialStateRoot,
        long initialDurableSequence,
        InitialStateProjection initialProjection,
        long corpusOperationCount,
        RequestOrderSpool requestOrder)
        throws IOException {
      var raw = readRegularFile(path, "projected formal trace receipt");
      var receipt = object(Json.parse(raw), "projected formal trace receipt");
      exactFields(receipt, RECEIPT_FIELDS, "projected formal trace receipt");
      var canonical = Json.bytes(receipt);
      require(
          Arrays.equals(raw, canonical) || Arrays.equals(raw, appendNewline(canonical)),
          "projected formal trace receipt is not canonical JSON");
      require(
          receipt.get("type_name").equals("FEATURE010_PROJECTED_FORMAL_TRACE_RECEIPT"),
          "projected formal trace receipt type mismatch");
      require(receipt.get("schema_version").equals(SCHEMA_VERSION), "trace receipt schema mismatch");
      require(
          receipt.get("formal_semantics_id").equals(FORMAL_SEMANTICS_ID),
          "trace receipt formal semantics mismatch");
      require(
          receipt.get("canonical_input_trace_sha256").equals(corpusSha256),
          "trace receipt is bound to a different DLTSTRC1 corpus");
      var source = object(receipt.get("source"), "trace receipt source");
      exactFields(source, Set.of("commit", "tree"), "trace receipt source");
      require(
          source.get("commit").equals(sourceCommit) && source.get("tree").equals(sourceTree),
          "trace receipt source differs from this qualification run");
      validateInitialWitness(
          receipt,
          initialStateRoot,
          initialProjection,
          corpusOperationCount,
          requestOrder);
      var prefix = object(receipt.get("deterministic_prefix"), "trace deterministic prefix");
      exactFields(prefix, PREFIX_FIELDS, "trace deterministic prefix");
      require(
          prefix.get("encoding").equals(RequestOrderSpool.PREFIX_ENCODING),
          "trace prefix encoding mismatch");
      require(
          prefix.get("execution_binding_encoding").equals(EXECUTION_BINDING_ENCODING),
          "trace execution-binding encoding mismatch");
      var executionBindingSha256 =
          textValue(prefix.get("execution_binding_sha256"), "trace execution binding");
      requireContentId(executionBindingSha256, "trace execution binding");
      require(integer(prefix.get("first_ordinal"), "trace first ordinal") == 0,
          "trace deterministic prefix does not start at zero");
      require(
          integer(prefix.get("operation_count"), "trace prefix operation count")
              == RequestOrderSpool.DETERMINISTIC_PREFIX_OPERATIONS,
          "trace deterministic prefix operation count mismatch");
      require(
          integer(prefix.get("last_ordinal"), "trace last ordinal")
              == RequestOrderSpool.DETERMINISTIC_PREFIX_OPERATIONS - 1L,
          "trace deterministic prefix end mismatch");
      require(
          prefix.get("request_transcript_sha256").equals(requestOrder.prefixTranscriptSha256()),
          "trace receipt request transcript differs from the DLTSTRC1 deterministic prefix");

      var trace = object(receipt.get("projected_trace"), "projected formal trace");
      var events =
          validateTrace(
              trace,
              initialStateRoot,
              initialDurableSequence,
              requestOrder.deterministicCommands());
      var traceSha256 = textValue(receipt.get("projected_trace_sha256"), "projected trace digest");
      requireContentId(traceSha256, "projected trace digest");
      require(
          sha256Id(Json.bytes(trace)).equals(traceSha256),
          "projected trace digest does not cover the canonical trace object");
      return new ProjectedFormalTrace(
          traceSha256,
          textValue(trace.get("terminal_state_root"), "trace terminal root"),
          executionBindingSha256,
          events);
    }

    private static void validateInitialWitness(
        Map<String, Object> receipt,
        String initialStateRoot,
        InitialStateProjection initial,
        long corpusOperationCount,
        RequestOrderSpool requestOrder) {
      var witness =
          object(receipt.get("initial_abstraction_witness"), "initial abstraction witness");
      exactFields(witness, INITIAL_WITNESS_FIELDS, "initial abstraction witness");
      var declaredDigest =
          textValue(
              receipt.get("initial_abstraction_witness_sha256"),
              "initial abstraction witness digest");
      requireContentId(declaredDigest, "initial abstraction witness digest");
      require(
          sha256Id(Json.bytes(witness)).equals(declaredDigest),
          "initial abstraction witness canonical digest mismatch");
      require(
          witness.get("type_name").equals("FEATURE010_INITIAL_ABSTRACTION_WITNESS"),
          "initial abstraction witness type mismatch");
      require(witness.get("schema_version").equals(SCHEMA_VERSION), "witness schema mismatch");
      require(
          witness.get("abstraction_version").equals("1.0.0"),
          "witness abstraction version mismatch");
      require(
          Boolean.TRUE.equals(witness.get("enable_ticket_actions")),
          "initial abstraction does not enable ticket actions");
      require(
          Boolean.TRUE.equals(witness.get("certificate_progress_open")),
          "initial abstraction certificate progress is not open");
      require(
          Boolean.FALSE.equals(witness.get("input_closed")),
          "initial abstraction input is already closed");
      require(
          integer(witness.get("abort_request_count"), "witness abort-request count") == 0,
          "initial abstraction contains an abort request");
      require(
          witness.get("worker_universe_rule").equals("EXACT_COMMAND_ACTOR_IDS"),
          "witness worker universe rule mismatch");
      require(
          witness.get("content_universe_rule").equals("EXACT_COMMAND_BODY_HASHES"),
          "witness content universe rule mismatch");
      require(
          witness.get("initial_state_root").equals(initialStateRoot),
          "witness initial state root mismatch");
      require(
          witness.get("initial_phase").equals("TICKETING_OPEN")
              && initial.phase().equals("TICKETING_OPEN"),
          "commitment workload does not start from TICKETING_OPEN");
      require(
          witness.get("round_id").equals(initial.roundId()),
          "witness round differs from the concrete initial state");
      require(
          integer(witness.get("canonical_input_operation_count"), "witness operation count")
              == corpusOperationCount,
          "witness operation count differs from the corpus");
      require(
          integer(witness.get("ticket_count"), "witness ticket count")
                  == corpusOperationCount
              && initial.ticketCount() == corpusOperationCount,
          "initial ticket plan does not cover the complete corpus exactly");
      require(
          integer(witness.get("planned_ticket_count"), "witness planned-ticket count")
                  == corpusOperationCount
              && integer(
                      witness.get("completed_ticket_count"),
                      "witness completed-ticket count")
                  == corpusOperationCount
              && integer(witness.get("active_lease_count"), "witness active-lease count")
                  == corpusOperationCount,
          "initial abstraction does not plan, complete, and lease every corpus ticket");
      require(
          integer(witness.get("initial_commitment_count"), "witness commitment count") == 0
              && initial.committedTicketCount() == 0,
          "commitment workload initial state already contains commitments");
      require(
          integer(witness.get("first_ordinal"), "witness first ordinal") == 0
              && integer(witness.get("last_ordinal"), "witness last ordinal")
                  == corpusOperationCount - 1,
          "witness ordinal range differs from the complete corpus");
      require(
          integer(witness.get("lease_epoch"), "witness lease epoch") == 0,
          "witness lease epoch is not zero");
      require(
          witness
              .get("mapping_rule")
              .equals(
                  "TICKET_ID_REQUEST_ID_WORKER_COMMAND_ACTOR_LEASE_EPOCH_0_CONTENT_BODY_HASH"),
          "witness ticket mapping rule mismatch");
      require(
          witness.get("ticket_mapping_encoding").equals(RequestOrderSpool.TICKET_MAPPING_ENCODING),
          "witness ticket mapping encoding mismatch");
      require(
          witness.get("ticket_mapping_sha256").equals(requestOrder.ticketMappingSha256()),
          "witness ticket mapping differs from the complete corpus");
      require(
          witness.get("command_transcript_encoding").equals(RequestOrderSpool.PREFIX_ENCODING),
          "witness command transcript encoding mismatch");
      require(
          witness.get("command_transcript_sha256").equals(requestOrder.prefixTranscriptSha256()),
          "witness command transcript differs from the complete corpus");
      for (var command : requestOrder.deterministicCommands()) {
        require(
            command.roundId().equals(initial.roundId())
                && command.height() == initial.height()
                && command.view() == initial.view(),
            "commitment command is outside the witnessed initial round/view");
      }
    }

    private static List<ProjectedEvent> validateTrace(
        Map<String, Object> trace,
        String initialStateRoot,
        long initialDurableSequence,
        List<DeterministicCommand> deterministicCommands) {
      exactFields(trace, TRACE_FIELDS, "projected formal trace");
      require(trace.get("schema_version").equals(SCHEMA_VERSION), "formal trace schema mismatch");
      require(
          trace.get("formal_semantics_id").equals(FORMAL_SEMANTICS_ID),
          "formal trace semantics mismatch");
      require(
          textValue(trace.get("trace_id"), "trace ID").matches("TRACE-[A-Z0-9][A-Z0-9._-]{0,127}"),
          "formal trace ID is invalid");
      require(
          textValue(trace.get("abstraction_version"), "abstraction version")
              .matches("[0-9]+\\.[0-9]+\\.[0-9]+"),
          "formal abstraction version is invalid");
      require(
          trace.get("initial_state_root").equals(initialStateRoot),
          "formal trace initial root differs from the corpus initial state");
      requireContentId(textValue(trace.get("terminal_state_root"), "terminal state root"),
          "terminal state root");
      require(
          Set.of("APPLIED", "ABORTED", "BLOCKED", "IN_PROGRESS")
              .contains(trace.get("terminal_outcome")),
          "formal trace terminal outcome is invalid");
      validateRoundContract(object(trace.get("round_contract"), "round contract"));
      var events = array(trace.get("events"), "formal events");
      require(
          events.size() == RequestOrderSpool.DETERMINISTIC_PREFIX_OPERATIONS,
          "stutter-erased projected trace must contain exactly one event per deterministic operation");
      var expectedPrior = initialStateRoot;
      var priorLogicalTime = -1L;
      var projectedEvents = new ArrayList<ProjectedEvent>(events.size());
      var uniqueRequests = new java.util.HashSet<String>();
      for (var index = 0; index < events.size(); ++index) {
        var item = events.get(index);
        var event = object(item, "formal event");
        var command = deterministicCommands.get(index);
        exactFields(event, EVENT_FIELDS, "formal event");
        require(event.get("schema_version").equals(SCHEMA_VERSION), "formal event schema mismatch");
        require(ACTION_IDS.contains(event.get("action_id")), "formal event action is unknown");
        require(
            event.get("action_id").equals("ACT-COMMIT"),
            "commitment comparison command did not project to ACT-COMMIT");
        require(
            textValue(event.get("round_id"), "formal event round ID").equals(command.roundId()),
            "formal event round differs from its concrete command");
        textValue(event.get("validator_epoch"), "formal event validator epoch");
        require(
            integer(event.get("height"), "formal event height") == command.height(),
            "formal event height differs from its concrete command");
        require(
            integer(event.get("view"), "formal event view") == command.view(),
            "formal event view differs from its concrete command");
        var logicalTime = integer(event.get("logical_time"), "formal event logical time");
        require(logicalTime >= priorLogicalTime, "formal event logical time moved backwards");
        priorLogicalTime = logicalTime;
        nullableText(event.get("actor_id"), "formal event actor ID");
        nullableText(event.get("vote_context_id"), "formal event vote context");
        var requestId = textValue(event.get("request_id"), "formal event request ID");
        require(
            requestId.equals(command.requestId()),
            "formal event request ID/order differs from the deterministic DLTSTRC1 prefix");
        require(uniqueRequests.add(requestId), "formal trace reuses a deterministic request ID");
        var role = event.get("actor_role");
        require(
            role == null
                || Set.of("WORKER", "VALIDATOR", "STORAGE", "P2P_PEER", "SYSTEM")
                    .contains(role),
            "formal event actor role is invalid");
        require(
            command.actorId().equals(event.get("actor_id")),
            "formal event actor differs from its concrete command");
        require("WORKER".equals(event.get("actor_role")), "ACT-COMMIT actor role is not WORKER");
        require(
            Set.of("ACCEPTED", "REJECTED", "FINALIZED", "NO_OP", "STUTTER", "FAULT", "BLOCKED")
                .contains(event.get("outcome")),
            "formal event outcome is invalid");
        require(event.get("outcome").equals("ACCEPTED"), "comparison commitment was not accepted");
        nullableError(event.get("error_code"));
        nullableContentId(event.get("body_hash"), "formal event body hash");
        require(
            command.bodyHash().equals(event.get("body_hash")),
            "formal event body differs from its concrete command");
        nullableContentId(event.get("result_hash"), "formal event result hash");
        var durableSequence =
            integer(event.get("durable_sequence"), "formal event durable sequence");
        var expectedSequence = Math.addExact(initialDurableSequence, index + 1L);
        require(
            durableSequence == expectedSequence,
            "formal event durable sequence is not the exact deterministic operation sequence");
        contentIdArray(event.get("parent_hashes"), "formal event parent hashes");
        contentIdArray(event.get("artifact_refs"), "formal event artifact refs");
        var prior = textValue(event.get("prior_state_root"), "formal prior state root");
        var next = textValue(event.get("next_state_root"), "formal next state root");
        requireContentId(prior, "formal prior state root");
        requireContentId(next, "formal next state root");
        require(prior.equals(expectedPrior), "formal trace state roots are not contiguous");
        require(!next.equals(prior), "stutter event remained in the projected formal trace");
        projectedEvents.add(
            new ProjectedEvent(
                index,
                requestId,
                prior,
                next,
                durableSequence,
                sha256(Json.bytes(event))));
        expectedPrior = next;
      }
      require(
          uniqueRequests.size() == deterministicCommands.size(),
          "formal trace is not a bijection over deterministic request IDs");
      require(
          expectedPrior.equals(trace.get("terminal_state_root")),
          "formal trace terminal root differs from its last event");
      return List.copyOf(projectedEvents);
    }

    private record ProjectedEvent(
        long ordinal,
        String requestId,
        String priorStateRoot,
        String nextStateRoot,
        long durableSequence,
        byte[] canonicalEventSha256) {
      private ProjectedEvent {
        require(ordinal >= 0, "projected event ordinal is negative");
        require(!requestId.isEmpty(), "projected event request ID is empty");
        requireContentId(priorStateRoot, "projected event prior state root");
        requireContentId(nextStateRoot, "projected event next state root");
        require(durableSequence >= 0, "projected event durable sequence is negative");
        require(canonicalEventSha256.length == 32, "projected event digest is not SHA-256");
        canonicalEventSha256 = Arrays.copyOf(canonicalEventSha256, canonicalEventSha256.length);
      }

      @Override
      public byte[] canonicalEventSha256() {
        return Arrays.copyOf(canonicalEventSha256, canonicalEventSha256.length);
      }
    }

    private static final class ExecutionVerifier {
      private final List<ProjectedEvent> events;
      private final String expectedBinding;
      private final MessageDigest binding = newSha256();
      private int nextIndex;
      private boolean finished;

      private ExecutionVerifier(List<ProjectedEvent> events, String expectedBinding) {
        this.events = List.copyOf(events);
        requireContentId(expectedBinding, "expected native projection execution binding");
        this.expectedBinding = expectedBinding;
        binding.update(EXECUTION_BINDING_DOMAIN);
        binding.update((byte) 0);
        updateU64(binding, events.size());
      }

      private void accept(CorpusRecord command, ValidatedOperation operation) {
        require(!finished, "native projection execution verifier is already finished");
        require(nextIndex < events.size(), "executed deterministic prefix exceeds formal events");
        var projected = events.get(nextIndex);
        require(
            command.ordinal() == projected.ordinal(),
            "executed operation ordinal differs from projected event ordinal");
        require(
            command.requestId().equals(projected.requestId()),
            "executed request ID differs from projected event request ID");
        require(
            operation.priorStateRoot().equals(projected.priorStateRoot()),
            "executed prior state root differs from projected event");
        require(
            operation.nextStateRoot().equals(projected.nextStateRoot()),
            "executed next state root differs from projected event");
        require(
            operation.durableSequence() == projected.durableSequence(),
            "executed durable sequence differs from projected event");

        updateU64(binding, command.ordinal());
        var requestId = command.requestId().getBytes(StandardCharsets.US_ASCII);
        require(
            new String(requestId, StandardCharsets.US_ASCII).equals(command.requestId()),
            "executed request ID is not ASCII");
        updateU32(binding, requestId.length);
        binding.update(requestId);
        binding.update(contentIdDigest(command.commandSha256()));
        updateU32(binding, operation.nativeStatus());
        binding.update(contentIdDigest(operation.effectId()));
        binding.update(contentIdDigest(operation.priorStateRoot()));
        binding.update(contentIdDigest(operation.nextStateRoot()));
        updateU64(binding, operation.durableSequence());
        binding.update(projected.canonicalEventSha256());
        ++nextIndex;
      }

      private void finish() {
        require(!finished, "native projection execution verifier was finished twice");
        finished = true;
        require(
            nextIndex == events.size(),
            "executed deterministic prefix does not cover every projected event");
        require(
            digestId(binding).equals(expectedBinding),
            "native projection execution binding differs from measured receipts");
      }
    }

    private static void validateRoundContract(Map<String, Object> contract) {
      exactFields(
          contract,
          Set.of("contract_id", "parameter_schema", "round_config", "round_id", "shard_plan"),
          "formal round contract");
      requireContentId(textValue(contract.get("contract_id"), "round contract ID"),
          "round contract ID");
      textValue(contract.get("round_id"), "round contract round ID");
      var config = object(contract.get("round_config"), "round config");
      exactFields(
          config,
          Set.of("body_hash", "domain_ids", "parameter_schema_hash", "shard_plan_hash"),
          "formal round config");
      requireContentId(textValue(config.get("body_hash"), "round body hash"), "round body hash");
      requireContentId(
          textValue(config.get("parameter_schema_hash"), "parameter schema hash"),
          "parameter schema hash");
      requireContentId(textValue(config.get("shard_plan_hash"), "shard plan hash"),
          "shard plan hash");
      uniqueTexts(config.get("domain_ids"), "round domains", true);
      var schema = object(contract.get("parameter_schema"), "parameter schema");
      exactFields(schema, Set.of("parameter_ids", "schema_hash"), "parameter schema");
      requireContentId(textValue(schema.get("schema_hash"), "schema hash"), "schema hash");
      uniqueTexts(schema.get("parameter_ids"), "parameter IDs", true);
      var plan = object(contract.get("shard_plan"), "shard plan");
      exactFields(plan, Set.of("assignments", "plan_hash"), "shard plan");
      requireContentId(textValue(plan.get("plan_hash"), "plan hash"), "plan hash");
      var assignments = array(plan.get("assignments"), "shard assignments");
      require(!assignments.isEmpty(), "shard assignments are empty");
      var canonicalAssignments = new java.util.HashSet<String>();
      for (var item : assignments) {
        var assignment = object(item, "shard assignment");
        exactFields(
            assignment,
            Set.of("domain_id", "parameter_id", "shard_id", "vote_context_id"),
            "shard assignment");
        for (var field : assignment.values()) {
          textValue(field, "shard assignment field");
        }
        require(
            canonicalAssignments.add(new String(Json.bytes(assignment), StandardCharsets.UTF_8)),
            "duplicate shard assignment");
      }
    }

    private static void nullableText(Object value, String label) {
      if (value != null) {
        textValue(value, label);
      }
    }

    private static void nullableError(Object value) {
      if (value != null) {
        require(
            textValue(value, "formal error code").matches("[A-Z][A-Z0-9_]{0,127}"),
            "formal error code is invalid");
      }
    }

    private static void nullableContentId(Object value, String label) {
      if (value != null) {
        requireContentId(textValue(value, label), label);
      }
    }

    private static void contentIdArray(Object value, String label) {
      var values = array(value, label);
      var unique = new java.util.HashSet<String>();
      for (var item : values) {
        var id = textValue(item, label + " item");
        requireContentId(id, label + " item");
        require(unique.add(id), label + " contains duplicates");
      }
    }

    private static void uniqueTexts(Object value, String label, boolean nonempty) {
      var values = strings(value, label);
      require(!nonempty || !values.isEmpty(), label + " is empty");
    }
  }

  private record CorpusRecord(
      long ordinal,
      byte[] command,
      String requestId,
      String commandSha256,
      String commandKind,
      String actorId,
      String bodyHash,
      String roundId,
      long height,
      long view) {
    private CorpusRecord {
      require(ordinal >= 0, "negative corpus ordinal");
      command = Arrays.copyOf(command, command.length);
      require(!requestId.isEmpty(), "empty corpus request ID");
      requireContentId(commandSha256, "corpus command hash");
      require(!commandKind.isEmpty(), "empty corpus command kind");
      require(!actorId.isEmpty(), "empty corpus actor ID");
      requireContentId(bodyHash, "corpus body hash");
      require(!roundId.isEmpty(), "empty corpus round ID");
      require(height >= 0, "negative corpus height");
      require(view >= 0, "negative corpus view");
    }

    @Override
    public byte[] command() {
      return Arrays.copyOf(command, command.length);
    }
  }

  private record InitialStateProjection(
      String phase,
      String roundId,
      long height,
      long view,
      long durableSequence,
      long ticketCount,
      long committedTicketCount) {
    private InitialStateProjection {
      require(!phase.isEmpty(), "initial phase is empty");
      require(!roundId.isEmpty(), "initial round ID is empty");
      require(height >= 0, "initial height is negative");
      require(view >= 0, "initial view is negative");
      require(durableSequence >= 0, "initial durable sequence is negative");
      require(ticketCount >= 0, "initial ticket count is negative");
      require(committedTicketCount >= 0, "initial committed-ticket count is negative");
      require(committedTicketCount <= ticketCount, "initial commitments exceed ticket count");
    }
  }

  private static final class Corpus implements AutoCloseable {
    private final Path path;
    private final long initialSize;
    private final long initialModified;
    private final String fileSha256;
    private final DataInputStream input;
    private final long operationCount;
    private final byte[] initialState;
    private final long initialDurableSequence;
    private final InitialStateProjection initialProjection;
    private long nextOrdinal;

    private Corpus(Path path) throws IOException {
      this.path = path;
      requireRegular(path, "DLTSTRC1 corpus");
      initialSize = Files.size(path);
      initialModified = Files.getLastModifiedTime(path).toMillis();
      fileSha256 = sha256Id(path);
      input = new DataInputStream(new BufferedInputStream(Files.newInputStream(path), 64 * 1024));
      var magic = input.readNBytes(CORPUS_MAGIC.length);
      require(Arrays.equals(magic, CORPUS_MAGIC), "corpus magic is not DLTSTRC1");
      require(input.readUnsignedShort() == CORPUS_MAJOR, "corpus major version mismatch");
      require(input.readUnsignedShort() == CORPUS_MINOR, "corpus minor version mismatch");
      operationCount = input.readLong();
      require(operationCount >= 0 && operationCount <= 10_000_000L, "corpus count is out of bounds");
      var initialLength = input.readInt();
      require(
          initialLength > 0 && initialLength <= SidecarIpcV1.MAX_CANONICAL_COMMAND_BYTES,
          "corpus initial-state length is out of bounds");
      initialState = input.readNBytes(initialLength);
      require(initialState.length == initialLength, "corpus initial state is truncated");
      var decoded = CanonicalEnvelope.decode(initialState, 5);
      initialDurableSequence =
          decimal(text(decoded, "durable_sequence"), "initial durable sequence");
      initialProjection =
          new InitialStateProjection(
              text(decoded, "phase"),
              text(decoded, "round_id"),
              decimal(text(decoded, "height"), "initial height"),
              decimal(text(decoded, "view"), "initial view"),
              initialDurableSequence,
              integer(decoded.get("ticket_count"), "initial ticket count"),
              integer(decoded.get("committed_ticket_count"), "initial committed-ticket count"));
    }

    private CorpusRecord next() throws IOException {
      require(nextOrdinal < operationCount, "DLTSTRC1 corpus exhausted during qualification");
      var ordinal = input.readLong();
      require(ordinal == nextOrdinal, "corpus operation ordinal is not contiguous");
      var length = input.readInt();
      require(
          length > 0 && length <= SidecarIpcV1.MAX_CANONICAL_COMMAND_BYTES,
          "corpus command length is out of bounds");
      var command = input.readNBytes(length);
      require(command.length == length, "corpus command is truncated");
      var declared = input.readNBytes(32);
      require(declared.length == 32, "corpus command digest is truncated");
      var actual = sha256(command);
      require(Arrays.equals(actual, declared), "corpus command digest mismatch");
      var decoded = CanonicalEnvelope.decode(command, 6);
      var requestId = text(decoded, "request_id");
      require(
          requestId.getBytes(StandardCharsets.US_ASCII).length
              <= SidecarIpcV1.MAX_REQUEST_ID_BYTES,
          "corpus request ID exceeds the IPC bound");
      nextOrdinal++;
      return new CorpusRecord(
          ordinal,
          command,
          requestId,
          "sha256:" + HexFormat.of().formatHex(actual),
          text(decoded, "command_kind"),
          text(decoded, "actor_id"),
          text(decoded, "body_hash"),
          text(decoded, "round_id"),
          decimal(text(decoded, "height"), "command height"),
          decimal(text(decoded, "view"), "command view"));
    }

    private long operationCount() {
      return operationCount;
    }

    private byte[] initialState() {
      return Arrays.copyOf(initialState, initialState.length);
    }

    private long initialDurableSequence() {
      return initialDurableSequence;
    }

    private InitialStateProjection initialProjection() {
      return initialProjection;
    }

    private String fileSha256() {
      return fileSha256;
    }

    private long consumedOperations() {
      return nextOrdinal;
    }

    private void verifyComplete() throws IOException {
      require(nextOrdinal == operationCount, "corpus validation stopped before its declared end");
      require(input.read() == -1, "corpus has trailing bytes after its declared operation count");
    }

    @Override
    public void close() throws IOException {
      input.close();
      require(Files.size(path) == initialSize, "corpus size changed during qualification");
      require(
          Files.getLastModifiedTime(path).toMillis() == initialModified,
          "corpus modification time changed during qualification");
    }
  }

  private record RuntimeDescriptor(
      int abiMajor,
      int abiMinor,
      long featureBits,
      String schemaVersion,
      String protocolVersion,
      String formalSemanticsId,
      String buildId,
      String schemaSetId,
      String runtimeProfile,
      byte[] canonicalBytes) {
    private RuntimeDescriptor {
      require(abiMajor == 1 && abiMinor == 0, "unexpected ABI version");
      require(
          featureBits == SidecarIpcV1.NESTED_ABI_FEATURE_BITS,
          "unexpected ABI feature bits");
      require(
          (featureBits & ABI_FEATURE_SUBMIT_RECEIPT_V1) != 0,
          "native submit-receipt-v1 feature is absent");
      require(schemaVersion.equals(SCHEMA_VERSION), "unexpected schema version");
      require(protocolVersion.equals(PROTOCOL_VERSION), "unexpected protocol version");
      require(formalSemanticsId.equals(FORMAL_SEMANTICS_ID), "unexpected formal semantics ID");
      require(buildId.equals(BUILD_ID), "unexpected build ID");
      require(schemaSetId.equals(SCHEMA_SET_ID), "unexpected schema-set ID");
      require(runtimeProfile.equals("embedded-ffm"), "unexpected nested runtime profile");
      canonicalBytes = Arrays.copyOf(canonicalBytes, canonicalBytes.length);
      var decoded = SidecarIpcV1.parseNestedDescriptor(canonicalBytes);
      require(decoded.structSize() == ABI_DESCRIPTOR_SIZE, "nested descriptor size mismatch");
    }

    private static RuntimeDescriptor frozen() {
      var nested =
          new SidecarIpcV1.NestedDescriptor(
              ABI_DESCRIPTOR_SIZE,
              1,
              0,
              SidecarIpcV1.NESTED_ABI_FEATURE_BITS,
              SCHEMA_VERSION,
              PROTOCOL_VERSION,
              FORMAL_SEMANTICS_ID,
              BUILD_ID,
              SCHEMA_SET_ID,
              "embedded-ffm");
      return new RuntimeDescriptor(
          nested.abiMajor(),
          nested.abiMinor(),
          nested.featureBits(),
          nested.schemaVersion(),
          nested.protocolVersion(),
          nested.formalSemanticsId(),
          nested.buildId(),
          nested.schemaSetId(),
          nested.runtimeProfile(),
          SidecarIpcV1.encodeNestedDescriptor(nested));
    }

    @Override
    public byte[] canonicalBytes() {
      return Arrays.copyOf(canonicalBytes, canonicalBytes.length);
    }

    private Map<String, Object> runtimeIds() {
      var result = new TreeMap<String, Object>();
      result.put("abi_sha256", sha256Id(canonicalBytes));
      result.put("build_id", buildId);
      result.put("formal_semantics_id", formalSemanticsId);
      result.put(
          "protocol_sha256", sha256Id(protocolVersion.getBytes(StandardCharsets.US_ASCII)));
      result.put("schema_set_id", schemaSetId);
      result.put("schema_sha256", sha256Id(schemaVersion.getBytes(StandardCharsets.US_ASCII)));
      return result;
    }
  }

  private interface Adapter extends AutoCloseable {
    Submission tryExecute(CorpusRecord command, long offeredAtNanos) throws Throwable;

    byte[] recordVote(byte[] canonicalVote) throws Throwable;

    default OperationResult execute(CorpusRecord command) throws Throwable {
      var submission = tryExecute(command, System.nanoTime());
      require(submission.accepted(), "adapter rejected a blocking qualification request");
      return awaitSubmission(submission).operation();
    }

    byte[] state() throws Throwable;

    RuntimeStats stats();

    @Override
    void close();
  }

  private static final class IsolatedAdapter implements Adapter {
    private final SidecarSupervisor supervisor;
    private long auxiliaryRequestCounter;

    private IsolatedAdapter(
        Path executable,
        Path durableDirectory,
        byte[] initialState,
        byte[] votePolicy,
        RuntimeDescriptor descriptor)
        throws Exception {
      requireRegular(executable, "sidecar executable");
      var executableSha = SidecarSupervisor.PipeProcessConnector.executableSha256(executable);
      var config =
          new SidecarSupervisor.Config(
              durableDirectory,
              initialState,
              executableSha,
              descriptor.buildId(),
              descriptor.canonicalBytes(),
              votePolicy);
      supervisor =
          new SidecarSupervisor(
              config, new SidecarSupervisor.PipeProcessConnector(executable, List.of()));
      supervisor
          .start()
          .toCompletableFuture()
          .get(
              SidecarSupervisor.RECOVERY_READY_TIMEOUT.plusSeconds(5).toMillis(),
              TimeUnit.MILLISECONDS);
      require(supervisor.state() == SidecarSupervisor.State.READY, "sidecar did not reach READY");
    }

    @Override
    public Submission tryExecute(CorpusRecord command, long offeredAtNanos) {
      var requestId = command.requestId().getBytes(StandardCharsets.US_ASCII);
      var prepared = LocalSidecarClient.submitRequest(requestId, command.command());
      var enqueued = supervisor.client().tryEnqueue(prepared);
      if (!enqueued.accepted()) {
        return Submission.rejected("sidecar client rejected a bounded qualification request");
      }
      var result = new CompletableFuture<TimedOperation>();
      enqueued
          .completion()
          .whenComplete(
              (response, error) -> {
                if (error != null) {
                  result.completeExceptionally(error);
                  return;
                }
                try {
                  var completedAtNanos = System.nanoTime();
                  result.complete(
                          new TimedOperation(
                          decodeSubmitResponse(command, response, offeredAtNanos, completedAtNanos),
                          offeredAtNanos,
                          completedAtNanos));
                } catch (Throwable failure) {
                  result.completeExceptionally(failure);
                }
              });
      return new Submission(true, result);
    }

    private OperationResult decodeSubmitResponse(
        CorpusRecord command,
        LocalSidecarClient.Response response,
        long offeredAtNanos,
        long completedAtNanos) {
      require(
          response.messageType() == SidecarIpcV1.MessageType.SUBMIT_RESPONSE,
          "sidecar submit did not return SUBMIT_RESPONSE");
      var payload = response.payload();
      var status = payload.u32(5);
      require(status == 0, "sidecar submit returned native status " + status);
      var effect = payload.bytes(17);
      var effectId = ascii(payload.bytes(16), "sidecar effect identity");
      var timing = response.operationalTiming();
      var measured = supervisor.operationCopy(response);
      var copies =
          new CopyValues(
              new long[] {
                measured.inlineIngressBytes(),
                measured.inlineEgressBytes(),
                measured.sharedMemoryIngressBytes(),
                measured.sharedMemoryEgressBytes(),
                measured.stagingFallbackIngressBytes(),
                measured.stagingFallbackEgressBytes(),
                measured.zeroCopyEligibleCount(),
                measured.zeroCopyHitCount()
              });
      return new OperationResult(
          status,
          effect,
          effectId,
          digestId(payload.bytes(20)),
          digestId(payload.bytes(21)),
          positiveSigned(payload.u64Bits(19), "sidecar durable sequence"),
          checkedElapsed(completedAtNanos, offeredAtNanos, "sidecar offered-to-completion"),
          timing.writeToValidatedReceiveNanos(),
          copies);
    }

    @Override
    public byte[] state() throws Exception {
      var request =
          LocalSidecarClient.stateRequest(auxiliaryRequestId("state"), supervisor.runtimeInstanceId());
      var response = submit(request);
      require(
          response.messageType() == SidecarIpcV1.MessageType.STATE_RESPONSE,
          "sidecar state did not return STATE_RESPONSE");
      require(response.nativeStatus() == 0, "sidecar state returned a native failure");
      return response.payload().bytes(19);
    }

    @Override
    public byte[] recordVote(byte[] canonicalVote) throws Exception {
      var response =
          submit(LocalSidecarClient.voteRequest(auxiliaryRequestId("vote"), canonicalVote));
      require(
          response.messageType() == SidecarIpcV1.MessageType.VOTE_RESPONSE,
          "sidecar vote did not return VOTE_RESPONSE");
      require(response.nativeStatus() == ABI_OK, "sidecar vote returned a native failure");
      return response.payload().bytes(16);
    }

    private LocalSidecarClient.Response submit(LocalSidecarClient.PreparedRequest request)
        throws Exception {
      var submission = supervisor.client().tryEnqueue(request);
      require(submission.accepted(), "sidecar client rejected a qualification request");
      return submission
          .completion()
          .toCompletableFuture()
          .get(
              LocalSidecarClient.REQUEST_WATCHDOG_TIMEOUT.plusSeconds(5).toMillis(),
              TimeUnit.MILLISECONDS);
    }

    private byte[] auxiliaryRequestId(String operation) {
      auxiliaryRequestCounter = Math.addExact(auxiliaryRequestCounter, 1L);
      return ("feature010-capture-" + operation + "-" + auxiliaryRequestCounter)
          .getBytes(StandardCharsets.US_ASCII);
    }

    @Override
    public RuntimeStats stats() {
      var telemetry = supervisor.telemetry();
      require(telemetry.state() == SidecarSupervisor.State.READY, "sidecar left READY during run");
      var client = telemetry.client();
      require(client != null, "sidecar client telemetry is absent");
      var maximum = telemetry.maxSubmitStagingFallback();
      require(maximum != null, "sidecar supervisor has no completed SUBMIT copy telemetry");
      return new RuntimeStats(
          client.duplicateResponses(),
          client.staleResponses(),
          client.rejectedFrames(),
          maximum.stagingFallbackTotalBytes());
    }

    @Override
    public void close() {
      supervisor.close();
    }
  }

  @SuppressWarnings("restricted")
  private static final class EmbeddedAdapter implements Adapter {
    private final Arena arena;
    private final ThreadPoolExecutor executor;
    private final MethodHandle submit;
    private final MethodHandle recordVote;
    private final MethodHandle state;
    private final MethodHandle release;
    private final MemorySegment handlePointer;
    private final MemorySegment handle;
    private final MemorySegment commandBuffer;
    private final MemorySegment commandView;
    private final MemorySegment responseBuffer;
    private final MemorySegment output;
    private final MemorySegment voteReceipt;
    private final MemorySegment submitReceipt;
    private boolean closed;

    private EmbeddedAdapter(
        Path library,
        Path durableDirectory,
        byte[] initialState,
        byte[] votePolicy,
        RuntimeDescriptor expected)
        throws Throwable {
      requireRegular(library, "embedded native library");
      executor =
          new ThreadPoolExecutor(
              1,
              1,
              0L,
              TimeUnit.MILLISECONDS,
              new ArrayBlockingQueue<>(SidecarIpcV1.INGRESS_QUEUE_REQUESTS - 1),
              runnable -> {
                var thread = new Thread(runnable, "feature010-embedded-reactor");
                thread.setDaemon(true);
                return thread;
              },
              new ThreadPoolExecutor.AbortPolicy());
      arena = Arena.ofShared();
      var linker = Linker.nativeLinker();
      var lookup = SymbolLookup.libraryLookup(library, arena);
      var descriptorFunction =
          downcall(
              linker,
              lookup,
              "delta_runtime_descriptor",
              FunctionDescriptor.of(JAVA_INT, JAVA_INT, ADDRESS));
      MethodHandle open;
      if (votePolicy == null) {
        open =
            downcall(
                linker,
                lookup,
                "delta_runtime_open",
                FunctionDescriptor.of(JAVA_INT, ADDRESS, ADDRESS));
      } else {
        open =
            downcall(
                linker,
                lookup,
                "delta_runtime_open_with_vote_policy_v1",
                FunctionDescriptor.of(JAVA_INT, ADDRESS, ABI_VIEW, ADDRESS));
      }
      submit =
          downcall(
              linker,
              lookup,
              "delta_runtime_submit_receipt_borrowed_v1",
              FunctionDescriptor.of(JAVA_INT, ADDRESS, ABI_VIEW, ADDRESS));
      recordVote =
          downcall(
              linker,
              lookup,
              "delta_runtime_record_vote_borrowed_v1",
              FunctionDescriptor.of(JAVA_INT, ADDRESS, ABI_VIEW, ADDRESS));
      state =
          downcall(
              linker,
              lookup,
              "delta_runtime_state",
              FunctionDescriptor.of(JAVA_INT, ADDRESS, ADDRESS));
      release =
          downcall(
              linker,
              lookup,
              "delta_runtime_release",
              FunctionDescriptor.of(JAVA_INT, ADDRESS));
      verifyDescriptor(arena, descriptorFunction, expected);
      var options = openOptions(arena, durableDirectory, initialState, expected);
      handlePointer = arena.allocate(ADDRESS);
      handlePointer.set(ADDRESS, 0, MemorySegment.NULL);
      int status;
      if (votePolicy == null) {
        status = (int) open.invoke(options, handlePointer);
      } else {
        var policyView = arena.allocate(ABI_VIEW);
        setView(policyView, 0, bytes(arena, votePolicy));
        status = (int) open.invoke(options, policyView, handlePointer);
      }
      require(status == ABI_OK, "embedded runtime open failed with status " + status);
      handle = handlePointer.get(ADDRESS, 0);
      require(!handle.equals(MemorySegment.NULL), "embedded runtime returned a null handle");
      commandBuffer = arena.allocate(SidecarIpcV1.MAX_CANONICAL_COMMAND_BYTES, 8);
      commandView = arena.allocate(ABI_VIEW);
      responseBuffer = arena.allocate(SidecarIpcV1.MAX_LOGICAL_PAYLOAD_BYTES, 8);
      output = arena.allocate(ABI_OUTPUT);
      voteReceipt = arena.allocate(ABI_VOTE_RECEIPT_V1);
      submitReceipt = arena.allocate(ABI_SUBMIT_RECEIPT_V1);
    }

    @Override
    public Submission tryExecute(CorpusRecord command, long offeredAtNanos) {
      var result = new CompletableFuture<TimedOperation>();
      try {
        executor.execute(
            () -> {
              try {
                var operation = executeNative(command, offeredAtNanos);
                var completedAtNanos = System.nanoTime();
                result.complete(
                    new TimedOperation(operation, offeredAtNanos, completedAtNanos));
              } catch (Throwable failure) {
                result.completeExceptionally(failure);
              }
            });
      } catch (RejectedExecutionException rejected) {
        return Submission.rejected("embedded bounded qualification queue is full");
      }
      return new Submission(true, result);
    }

    private OperationResult executeNative(CorpusRecord command, long offeredAtNanos)
        throws Throwable {
      var bytes = command.command();
      require(bytes.length <= commandBuffer.byteSize(), "command exceeds preallocated input bound");
      commandBuffer.asSlice(0, bytes.length).copyFrom(MemorySegment.ofArray(bytes));
      setView(commandView, 0, commandBuffer.asSlice(0, bytes.length));
      resetSubmitReceipt();
      var phaseStarted = System.nanoTime();
      var status = (int) submit.invoke(handle, commandView, submitReceipt);
      var phaseFinished = System.nanoTime();
      require(status == ABI_OK, "embedded submit failed with status " + status);
      var canonicalEffect = submitReceipt.asSlice(16, ABI_OUTPUT_SIZE);
      var written = written(canonicalEffect);
      var effect = responseBuffer.asSlice(0, written).toArray(JAVA_BYTE);
      var durableSequence = submitReceipt.get(JAVA_LONG, 8);
      // The Java long carries the native uint64_t bits; high-bit sequences are
      // valid and therefore must not be rejected as signed-negative values.
      require(durableSequence != 0, "embedded native submit receipt has no durable sequence");
      var finished = System.nanoTime();
      var decoded = CanonicalEnvelope.decode(effect, 7);
      var effectId = contentId(EFFECT_BATCH_DOMAIN, effect);
      return new OperationResult(
          Integer.toUnsignedLong(status),
          effect,
          effectId,
          text(decoded, "prior_state_root"),
          text(decoded, "next_state_root"),
          durableSequence,
          checkedElapsed(finished, offeredAtNanos, "embedded offered-to-completion"),
          checkedElapsed(phaseFinished, phaseStarted, "embedded native call"),
          new CopyValues(new long[] {0, 0, 0, 0, bytes.length, written, 0, 0}));
    }

    @Override
    public byte[] recordVote(byte[] canonicalVote) throws Throwable {
      var result = new CompletableFuture<byte[]>();
      try {
        executor.execute(
            () -> {
              try {
                result.complete(recordVoteNative(canonicalVote));
              } catch (Throwable failure) {
                result.completeExceptionally(failure);
              }
            });
      } catch (RejectedExecutionException rejected) {
        throw new CaptureException("embedded vote reactor rejected the bounded operation", rejected);
      }
      try {
        return result.get(
            SidecarSupervisor.RECOVERY_READY_TIMEOUT.plusSeconds(5).toMillis(),
            TimeUnit.MILLISECONDS);
      } catch (ExecutionException error) {
        throw error.getCause();
      } catch (TimeoutException error) {
        throw new CaptureException("embedded vote exceeded the hard wait bound", error);
      } catch (InterruptedException error) {
        Thread.currentThread().interrupt();
        throw new CaptureException("embedded vote wait was interrupted", error);
      }
    }

    private byte[] recordVoteNative(byte[] canonicalVote) throws Throwable {
      require(
          canonicalVote.length > 0 && canonicalVote.length <= commandBuffer.byteSize(),
          "canonical vote exceeds the preallocated native input bound");
      commandBuffer
          .asSlice(0, canonicalVote.length)
          .copyFrom(MemorySegment.ofArray(canonicalVote));
      setView(commandView, 0, commandBuffer.asSlice(0, canonicalVote.length));
      voteReceipt.set(JAVA_INT, 0, ABI_VOTE_RECEIPT_V1_SIZE);
      voteReceipt.set(JAVA_INT, 4, 0);
      resetOutput(voteReceipt.asSlice(8, ABI_OUTPUT_SIZE));
      var status = (int) recordVote.invoke(handle, commandView, voteReceipt);
      require(status == ABI_OK, "embedded vote failed with status " + status);
      var canonicalReceipt = voteReceipt.asSlice(8, ABI_OUTPUT_SIZE);
      return responseBuffer
          .asSlice(0, written(canonicalReceipt))
          .toArray(JAVA_BYTE);
    }

    @Override
    public byte[] state() throws Throwable {
      resetOutput();
      var status = (int) state.invoke(handle, output);
      require(status == ABI_OK, "embedded state failed with status " + status);
      return responseBuffer.asSlice(0, written()).toArray(JAVA_BYTE);
    }

    private void resetOutput() {
      resetOutput(output);
    }

    private long written() {
      return written(output);
    }

    private void resetSubmitReceipt() {
      submitReceipt.set(JAVA_INT, 0, ABI_SUBMIT_RECEIPT_V1_SIZE);
      submitReceipt.set(JAVA_INT, 4, 0);
      submitReceipt.set(JAVA_LONG, 8, 0);
      resetOutput(submitReceipt.asSlice(16, ABI_OUTPUT_SIZE));
    }

    private void resetOutput(MemorySegment target) {
      target.set(ADDRESS, 0, responseBuffer);
      target.set(JAVA_LONG, 8, responseBuffer.byteSize());
      target.set(JAVA_LONG, 16, 0);
      target.set(JAVA_LONG, 24, 0);
    }

    private long written(MemorySegment target) {
      var required = target.get(JAVA_LONG, 16);
      var written = target.get(JAVA_LONG, 24);
      require(
          required >= 0 && required <= responseBuffer.byteSize(),
          "embedded output required size exceeds frozen preallocation");
      require(
          written > 0 && written <= responseBuffer.byteSize(),
          "embedded output written size is out of bounds");
      return written;
    }

    @Override
    public RuntimeStats stats() {
      return new RuntimeStats(0, 0, 0, null);
    }

    @Override
    public void close() {
      if (closed) {
        return;
      }
      closed = true;
      try {
        executor.shutdown();
        require(
            executor.awaitTermination(5, TimeUnit.SECONDS),
            "embedded qualification reactor did not stop");
        var status = (int) release.invoke(handlePointer);
        require(status == ABI_OK, "embedded runtime release failed with status " + status);
        require(
            handlePointer.get(ADDRESS, 0).equals(MemorySegment.NULL),
            "embedded runtime release did not clear the handle");
      } catch (RuntimeException error) {
        throw error;
      } catch (InterruptedException error) {
        Thread.currentThread().interrupt();
        throw new CaptureException("embedded qualification reactor shutdown was interrupted", error);
      } catch (Throwable error) {
        throw new CaptureException("embedded runtime release failed", error);
      } finally {
        arena.close();
      }
    }

    private static void verifyDescriptor(
        Arena arena, MethodHandle function, RuntimeDescriptor expected) throws Throwable {
      var output = arena.allocate(ABI_DESCRIPTOR);
      var status = (int) function.invoke(ABI_DESCRIPTOR_SIZE, output);
      require(status == ABI_OK, "embedded descriptor call failed with status " + status);
      require(output.get(JAVA_INT, 0) == ABI_DESCRIPTOR_SIZE, "ABI descriptor size mismatch");
      require(Short.toUnsignedInt(output.get(JAVA_SHORT, 4)) == expected.abiMajor(),
          "ABI major mismatch");
      require(Short.toUnsignedInt(output.get(JAVA_SHORT, 6)) == expected.abiMinor(),
          "ABI minor mismatch");
      require(output.get(JAVA_LONG, 8) == expected.featureBits(), "ABI feature bits mismatch");
      require(cString(output.get(ADDRESS, 16)).equals(expected.schemaVersion()),
          "ABI schema version mismatch");
      require(cString(output.get(ADDRESS, 24)).equals(expected.protocolVersion()),
          "ABI protocol version mismatch");
      require(cString(output.get(ADDRESS, 32)).equals(expected.formalSemanticsId()),
          "ABI formal semantics mismatch");
      require(cString(output.get(ADDRESS, 40)).equals(expected.buildId()), "ABI build ID mismatch");
      require(cString(output.get(ADDRESS, 48)).equals(expected.schemaSetId()),
          "ABI schema-set mismatch");
      require(cString(output.get(ADDRESS, 56)).equals(expected.runtimeProfile()),
          "ABI runtime profile mismatch");
    }

    private static MemorySegment openOptions(
        Arena arena,
        Path durableDirectory,
        byte[] initialState,
        RuntimeDescriptor descriptor) {
      var output = arena.allocate(ABI_OPEN_OPTIONS);
      output.set(JAVA_INT, 0, ABI_OPEN_OPTIONS_SIZE);
      output.set(JAVA_INT, 4, SidecarIpcV1.INGRESS_QUEUE_REQUESTS);
      setView(
          output,
          8,
          bytes(arena, durableDirectory.toString().getBytes(StandardCharsets.UTF_8)));
      setView(output, 24, bytes(arena, initialState));
      output.set(JAVA_SHORT, 40, (short) descriptor.abiMajor());
      output.set(JAVA_SHORT, 42, (short) descriptor.abiMinor());
      output.set(JAVA_INT, 44, 0);
      setView(output, 48, bytes(arena, descriptor.schemaVersion().getBytes(StandardCharsets.US_ASCII)));
      setView(
          output, 64, bytes(arena, descriptor.protocolVersion().getBytes(StandardCharsets.US_ASCII)));
      setView(
          output,
          80,
          bytes(arena, descriptor.formalSemanticsId().getBytes(StandardCharsets.US_ASCII)));
      setView(output, 96, bytes(arena, descriptor.buildId().getBytes(StandardCharsets.US_ASCII)));
      setView(
          output, 112, bytes(arena, descriptor.schemaSetId().getBytes(StandardCharsets.US_ASCII)));
      return output;
    }

    private static MethodHandle downcall(
        Linker linker, SymbolLookup lookup, String name, FunctionDescriptor descriptor) {
      return linker.downcallHandle(
          lookup.find(name).orElseThrow(() -> new CaptureException("missing symbol " + name)),
          descriptor);
    }

    private static MemorySegment bytes(Arena arena, byte[] value) {
      var result = arena.allocate(value.length == 0 ? 1 : value.length);
      if (value.length != 0) {
        result.copyFrom(MemorySegment.ofArray(value));
      }
      return value.length == 0 ? result.asSlice(0, 0) : result;
    }

    private static void setView(MemorySegment target, long offset, MemorySegment value) {
      target.set(ADDRESS, offset, value);
      target.set(JAVA_LONG, offset + 8, value.byteSize());
    }

    private static String cString(MemorySegment address) {
      require(!address.equals(MemorySegment.NULL), "ABI descriptor contains a null string");
      return address.reinterpret(1024).getString(0);
    }
  }

  private static final class CanonicalEnvelope {
    private static final byte[] MAGIC = "DRC1".getBytes(StandardCharsets.US_ASCII);
    private static final int TAG_FALSE = 0x01;
    private static final int TAG_TRUE = 0x02;
    private static final int TAG_UNSIGNED = 0x10;
    private static final int TAG_SIGNED = 0x11;
    private static final int TAG_BYTES = 0x20;
    private static final int TAG_TEXT = 0x21;
    private static final int TAG_ARRAY = 0x30;
    private static final int TAG_MAP = 0x31;

    private CanonicalEnvelope() {}

    private static Map<String, Object> decode(byte[] bytes, int expectedType) {
      require(bytes.length >= 12, "canonical envelope is truncated");
      var reader = new ByteReader(bytes);
      require(Arrays.equals(reader.bytes(4), MAGIC), "canonical envelope magic mismatch");
      require(reader.u8() == 1 && reader.u8() == 0, "canonical envelope version mismatch");
      require(reader.u16() == expectedType, "canonical envelope type mismatch");
      var payloadLength = reader.u32();
      require(payloadLength == reader.remaining(), "canonical envelope payload length mismatch");
      var root = value(reader, 0);
      require(reader.remaining() == 0, "canonical envelope has trailing bytes");
      return object(root, "canonical envelope root");
    }

    private static Object value(ByteReader reader, int depth) {
      require(depth <= 16, "canonical envelope nesting exceeds harness bound");
      return switch (reader.u8()) {
        case TAG_FALSE -> false;
        case TAG_TRUE -> true;
        case TAG_UNSIGNED -> reader.nonnegativeU64();
        case TAG_SIGNED -> reader.i64();
        case TAG_BYTES -> reader.bytes(reader.length("byte string"));
        case TAG_TEXT -> reader.text(reader.length("text"));
        case TAG_ARRAY -> {
          var count = reader.length("array");
          var output = new ArrayList<Object>(count);
          for (var index = 0; index < count; ++index) {
            output.add(value(reader, depth + 1));
          }
          yield output;
        }
        case TAG_MAP -> {
          var count = reader.length("map");
          var output = new LinkedHashMap<String, Object>();
          String prior = null;
          for (var index = 0; index < count; ++index) {
            require(reader.u8() == TAG_TEXT, "canonical map key is not text");
            var key = reader.text(reader.length("map key"));
            require(!key.isEmpty(), "canonical map key is empty");
            require(prior == null || prior.compareTo(key) < 0, "canonical map keys are unordered");
            require(output.put(key, value(reader, depth + 1)) == null, "duplicate canonical map key");
            prior = key;
          }
          yield output;
        }
        default -> throw new CaptureException("unknown canonical value tag");
      };
    }

    private static byte[] encodeTextMap(int type, Map<String, String> fields) {
      return encodeMap(type, fields);
    }

    private static byte[] encodeMap(int type, Map<String, ?> fields) {
      try {
        var payloadBytes = new ByteArrayOutputStream();
        try (var payload = new DataOutputStream(payloadBytes)) {
          payload.writeByte(TAG_MAP);
          payload.writeInt(fields.size());
          for (var entry : new TreeMap<>(fields).entrySet()) {
            writeText(payload, entry.getKey());
            if (entry.getValue() instanceof String text) {
              writeText(payload, text);
            } else if (entry.getValue() instanceof Long number) {
              require(number >= 0, "self-test canonical integer is negative");
              payload.writeByte(TAG_UNSIGNED);
              payload.writeLong(number);
            } else {
              throw new AssertionError("unsupported self-test canonical value");
            }
          }
        }
        var envelopeBytes = new ByteArrayOutputStream();
        try (var envelope = new DataOutputStream(envelopeBytes)) {
          envelope.write(MAGIC);
          envelope.writeByte(1);
          envelope.writeByte(0);
          envelope.writeShort(type);
          envelope.writeInt(payloadBytes.size());
          payloadBytes.writeTo(envelope);
        }
        return envelopeBytes.toByteArray();
      } catch (IOException error) {
        throw new AssertionError("in-memory canonical encoding failed", error);
      }
    }

    private static void writeText(DataOutputStream output, String value) throws IOException {
      var bytes = value.getBytes(StandardCharsets.US_ASCII);
      require(new String(bytes, StandardCharsets.US_ASCII).equals(value), "self-test text is not ASCII");
      output.writeByte(TAG_TEXT);
      output.writeInt(bytes.length);
      output.write(bytes);
    }

    private static final class ByteReader {
      private final byte[] bytes;
      private int cursor;

      private ByteReader(byte[] bytes) {
        this.bytes = Arrays.copyOf(bytes, bytes.length);
      }

      private int remaining() {
        return bytes.length - cursor;
      }

      private int u8() {
        require(remaining() >= 1, "canonical value is truncated");
        return Byte.toUnsignedInt(bytes[cursor++]);
      }

      private int u16() {
        return (u8() << 8) | u8();
      }

      private long u32() {
        return ((long) u8() << 24) | ((long) u8() << 16) | ((long) u8() << 8) | u8();
      }

      private long i64() {
        require(remaining() >= 8, "canonical u64 is truncated");
        long output = 0;
        for (var index = 0; index < 8; ++index) {
          output = (output << 8) | u8();
        }
        return output;
      }

      private long nonnegativeU64() {
        var output = i64();
        require(output >= 0, "canonical u64 exceeds the harness/JSON signed range");
        return output;
      }

      private int length(String label) {
        var value = u32();
        require(value <= Integer.MAX_VALUE, "canonical " + label + " length exceeds Java bound");
        require(value <= remaining(), "canonical " + label + " is truncated");
        return (int) value;
      }

      private byte[] bytes(int count) {
        require(count >= 0 && count <= remaining(), "canonical byte slice is truncated");
        var output = Arrays.copyOfRange(bytes, cursor, cursor + count);
        cursor += count;
        return output;
      }

      private String text(int count) {
        var encoded = bytes(count);
        for (var value : encoded) {
          var unsigned = Byte.toUnsignedInt(value);
          require(unsigned >= 0x20 && unsigned <= 0x7e, "canonical text is not printable ASCII");
        }
        return new String(encoded, StandardCharsets.US_ASCII);
      }
    }
  }

  private static final class Json {
    private Json() {}

    private static Object parse(byte[] raw) {
      var parser = new Parser(decodeUtf8(raw));
      var value = parser.value();
      parser.whitespace();
      require(parser.finished(), "JSON has trailing data");
      return value;
    }

    private static byte[] bytes(Object value) {
      try {
        var output = new ByteArrayOutputStream();
        try (var writer = new OutputStreamWriter(output, StandardCharsets.UTF_8)) {
          write(value, writer);
        }
        return output.toByteArray();
      } catch (IOException error) {
        throw new AssertionError("in-memory JSON encoding failed", error);
      }
    }

    private static void write(Object value, java.io.Writer output) throws IOException {
      if (value == null) {
        output.write("null");
      } else if (value instanceof Boolean bool) {
        output.write(bool ? "true" : "false");
      } else if (value instanceof Byte
          || value instanceof Short
          || value instanceof Integer
          || value instanceof Long) {
        var number = ((Number) value).longValue();
        require(number >= 0, "canonical JSON forbids negative integers");
        output.write(Long.toString(number));
      } else if (value instanceof String text) {
        string(text, output);
      } else if (value instanceof RawJsonArray raw) {
        output.write('[');
        try (Reader reader = Files.newBufferedReader(raw.path(), StandardCharsets.UTF_8)) {
          reader.transferTo(output);
        }
        output.write(']');
      } else if (value instanceof List<?> list) {
        output.write('[');
        var first = true;
        for (var item : list) {
          if (!first) {
            output.write(',');
          }
          write(item, output);
          first = false;
        }
        output.write(']');
      } else if (value instanceof Map<?, ?> map) {
        var ordered = new TreeMap<String, Object>();
        for (var entry : map.entrySet()) {
          require(entry.getKey() instanceof String, "JSON object key is not text");
          var key = (String) entry.getKey();
          require(ordered.put(key, entry.getValue()) == null, "duplicate JSON object key");
        }
        output.write('{');
        var first = true;
        for (var entry : ordered.entrySet()) {
          if (!first) {
            output.write(',');
          }
          string(entry.getKey(), output);
          output.write(':');
          write(entry.getValue(), output);
          first = false;
        }
        output.write('}');
      } else {
        throw new CaptureException("unsupported JSON value " + value.getClass().getName());
      }
    }

    private static void string(String value, java.io.Writer output) throws IOException {
      output.write('"');
      for (var index = 0; index < value.length(); ) {
        var character = value.charAt(index);
        if (Character.isHighSurrogate(character)) {
          require(
              index + 1 < value.length() && Character.isLowSurrogate(value.charAt(index + 1)),
              "JSON string contains an unpaired high surrogate");
          output.write(character);
          output.write(value.charAt(index + 1));
          index += 2;
          continue;
        }
        require(!Character.isLowSurrogate(character), "JSON string contains an unpaired low surrogate");
        switch (character) {
          case '"' -> output.write("\\\"");
          case '\\' -> output.write("\\\\");
          case '\b' -> output.write("\\b");
          case '\f' -> output.write("\\f");
          case '\n' -> output.write("\\n");
          case '\r' -> output.write("\\r");
          case '\t' -> output.write("\\t");
          default -> {
            if (character < 0x20) {
              output.write(String.format("\\u%04x", (int) character));
            } else {
              output.write(character);
            }
          }
        }
        ++index;
      }
      output.write('"');
    }

    private static final class Parser {
      private final String input;
      private int cursor;

      private Parser(String input) {
        this.input = input;
      }

      private boolean finished() {
        return cursor == input.length();
      }

      private void whitespace() {
        while (!finished()) {
          var value = input.charAt(cursor);
          if (value != ' ' && value != '\n' && value != '\r' && value != '\t') {
            break;
          }
          ++cursor;
        }
      }

      private Object value() {
        whitespace();
        require(!finished(), "JSON value is missing");
        return switch (input.charAt(cursor)) {
          case 'n' -> literal("null", null);
          case 't' -> literal("true", true);
          case 'f' -> literal("false", false);
          case '"' -> string();
          case '[' -> array();
          case '{' -> object();
          default -> number();
        };
      }

      private Object literal(String literal, Object value) {
        require(input.startsWith(literal, cursor), "invalid JSON literal");
        cursor += literal.length();
        return value;
      }

      private Long number() {
        var start = cursor;
        require(input.charAt(cursor) >= '0' && input.charAt(cursor) <= '9', "JSON number is invalid");
        if (input.charAt(cursor) == '0') {
          ++cursor;
          require(
              finished() || input.charAt(cursor) < '0' || input.charAt(cursor) > '9',
              "JSON integer has a leading zero");
        } else {
          while (!finished() && input.charAt(cursor) >= '0' && input.charAt(cursor) <= '9') {
            ++cursor;
          }
        }
        require(
            finished()
                || (input.charAt(cursor) != '.'
                    && input.charAt(cursor) != 'e'
                    && input.charAt(cursor) != 'E'),
            "JSON floating-point values are forbidden");
        try {
          return Long.valueOf(input.substring(start, cursor));
        } catch (NumberFormatException error) {
          throw new CaptureException("JSON integer exceeds signed u64 evidence range", error);
        }
      }

      private String string() {
        require(input.charAt(cursor) == '"', "JSON string is missing its quote");
        ++cursor;
        var output = new StringBuilder();
        while (!finished()) {
          var value = input.charAt(cursor++);
          if (value == '"') {
            return output.toString();
          }
          require(value >= 0x20, "JSON string contains an unescaped control character");
          if (value != '\\') {
            output.append(value);
            continue;
          }
          require(!finished(), "JSON escape is truncated");
          var escape = input.charAt(cursor++);
          switch (escape) {
            case '"', '\\', '/' -> output.append(escape);
            case 'b' -> output.append('\b');
            case 'f' -> output.append('\f');
            case 'n' -> output.append('\n');
            case 'r' -> output.append('\r');
            case 't' -> output.append('\t');
            case 'u' -> output.append(unicodeEscape());
            default -> throw new CaptureException("unknown JSON escape");
          }
        }
        throw new CaptureException("JSON string is unterminated");
      }

      private char unicodeEscape() {
        require(cursor + 4 <= input.length(), "JSON Unicode escape is truncated");
        var value = 0;
        for (var index = 0; index < 4; ++index) {
          var digit = Character.digit(input.charAt(cursor++), 16);
          require(digit >= 0, "JSON Unicode escape is invalid");
          value = (value << 4) | digit;
        }
        return (char) value;
      }

      private List<Object> array() {
        ++cursor;
        var output = new ArrayList<Object>();
        whitespace();
        if (!finished() && input.charAt(cursor) == ']') {
          ++cursor;
          return output;
        }
        while (true) {
          output.add(value());
          whitespace();
          require(!finished(), "JSON array is unterminated");
          var delimiter = input.charAt(cursor++);
          if (delimiter == ']') {
            return output;
          }
          require(delimiter == ',', "JSON array delimiter is invalid");
        }
      }

      private Map<String, Object> object() {
        ++cursor;
        var output = new LinkedHashMap<String, Object>();
        whitespace();
        if (!finished() && input.charAt(cursor) == '}') {
          ++cursor;
          return output;
        }
        while (true) {
          whitespace();
          require(!finished() && input.charAt(cursor) == '"', "JSON object key is not text");
          var key = string();
          whitespace();
          require(!finished() && input.charAt(cursor++) == ':', "JSON object colon is missing");
          require(output.put(key, value()) == null, "JSON object contains a duplicate key");
          whitespace();
          require(!finished(), "JSON object is unterminated");
          var delimiter = input.charAt(cursor++);
          if (delimiter == '}') {
            return output;
          }
          require(delimiter == ',', "JSON object delimiter is invalid");
        }
      }
    }
  }

  private static Map<String, Object> evidence(
      String artifactSha256, String checkId, Map<String, Object> observations) {
    requireContentId(artifactSha256, "evidence artifact");
    require(!checkId.isEmpty(), "evidence check ID is empty");
    require(!observations.isEmpty(), "evidence observations are empty");
    var result = new TreeMap<String, Object>();
    result.put("artifact_sha256", artifactSha256);
    result.put("checks", Map.of(checkId, true));
    result.put("observations", observations);
    return result;
  }

  private static Map<String, Object> validateEvidence(
      Object value, Object declaredSha256, String label) {
    var evidence = object(value, label + " evidence");
    exactFields(
        evidence, Set.of("artifact_sha256", "checks", "observations"), label + " evidence");
    requireContentId(textValue(evidence.get("artifact_sha256"), label + " artifact"),
        label + " artifact");
    var checks = object(evidence.get("checks"), label + " checks");
    require(!checks.isEmpty(), label + " checks are empty");
    for (var entry : checks.entrySet()) {
      require(!entry.getKey().isEmpty(), label + " check ID is empty");
      require(entry.getValue() instanceof Boolean, label + " check is not Boolean");
    }
    var observations = object(evidence.get("observations"), label + " observations");
    require(!observations.isEmpty(), label + " observations are empty");
    var declared = textValue(declaredSha256, label + " evidence digest");
    requireContentId(declared, label + " evidence digest");
    require(
        sha256Id(Json.bytes(evidence)).equals(declared),
        label + " evidence canonical digest mismatch");
    return evidence;
  }

  private static boolean allChecksPass(Map<String, Object> evidence) {
    for (var value : object(evidence.get("checks"), "evidence checks").values()) {
      if (!Boolean.TRUE.equals(value)) {
        return false;
      }
    }
    return true;
  }

  private static Map<String, Object> object(Object value, String label) {
    require(value instanceof Map<?, ?>, label + " is not an object");
    var result = new LinkedHashMap<String, Object>();
    for (var entry : ((Map<?, ?>) value).entrySet()) {
      require(entry.getKey() instanceof String, label + " has a non-text key");
      var key = (String) entry.getKey();
      require(result.put(key, entry.getValue()) == null, label + " has a duplicate key");
    }
    return result;
  }

  private static List<Object> array(Object value, String label) {
    require(value instanceof List<?>, label + " is not an array");
    return new ArrayList<>((List<?>) value);
  }

  private static List<String> strings(Object value, String label) {
    var result = new ArrayList<>(textArray(value, label));
    require(result.size() == Set.copyOf(result).size(), label + " contains duplicates");
    return List.copyOf(result);
  }

  private static List<String> textArray(Object value, String label) {
    var values = array(value, label);
    var result = new ArrayList<String>();
    for (var item : values) {
      result.add(textValue(item, label + " item"));
    }
    return List.copyOf(result);
  }

  private static void exactFields(Map<String, Object> value, Set<String> fields, String label) {
    require(value.keySet().equals(fields), label + " fields are not exact");
  }

  private static long integer(Object value, String label) {
    require(value instanceof Long, label + " is not an integer");
    var result = (Long) value;
    require(result >= 0, label + " is negative");
    return result;
  }

  private static String textValue(Object value, String label) {
    require(value instanceof String && !((String) value).isEmpty(), label + " is not nonempty text");
    return (String) value;
  }

  private static String text(Map<String, Object> value, String field) {
    return textValue(value.get(field), "canonical field " + field);
  }

  private static long decimal(String value, String label) {
    require(!value.isEmpty(), label + " is empty");
    require(value.equals("0") || value.charAt(0) != '0', label + " has a leading zero");
    long result = 0;
    for (var index = 0; index < value.length(); ++index) {
      var character = value.charAt(index);
      require(character >= '0' && character <= '9', label + " is not unsigned decimal");
      result = Math.addExact(Math.multiplyExact(result, 10L), character - '0');
    }
    return result;
  }

  private static byte[] readRegularFile(Path path, String label) throws IOException {
    requireRegular(path, label);
    var size = Files.size(path);
    require(size <= 512L * 1024 * 1024, label + " exceeds the 512 MiB evidence bound");
    return Files.readAllBytes(path);
  }

  private static void verifyCheckedOutSource(
      Path repositoryArtifact,
      String expectedCommit,
      String expectedTree,
      Path gitExecutable)
      throws IOException {
    var anchor = repositoryArtifact.toAbsolutePath().getParent();
    require(anchor != null, "source identity anchor has no parent");
    var topLevel = runGit(gitExecutable, anchor, "rev-parse", "--show-toplevel");
    require(topLevel.exitCode() == 0, "cannot resolve the qualification Git worktree");
    var root = Path.of(topLevel.output()).toRealPath();
    require(
        repositoryArtifact.toRealPath().startsWith(root),
        "frozen design is outside the resolved qualification worktree");
    var head = runGit(gitExecutable, root, "rev-parse", "--verify", "HEAD");
    var tree = runGit(gitExecutable, root, "rev-parse", "--verify", "HEAD^{tree}");
    require(head.exitCode() == 0 && head.output().equals(expectedCommit),
        "declared source commit is not the checked-out HEAD");
    require(tree.exitCode() == 0 && tree.output().equals(expectedTree),
        "declared source tree is not the checked-out HEAD tree");
    var status =
        runGit(
            gitExecutable,
            root,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--ignore-submodules=none");
    require(status.exitCode() == 0, "cannot inspect qualification worktree cleanliness");
    require(
        status.output().isEmpty(),
        "qualification worktree has tracked, staged, submodule, or untracked source changes");
  }

  private record GitCommandResult(int exitCode, String output) {
    private GitCommandResult {
      require(exitCode >= 0, "Git process has an invalid exit code");
      Objects.requireNonNull(output, "output");
    }
  }

  private static GitCommandResult runGit(
      Path gitExecutable, Path directory, String... arguments) throws IOException {
    var command = new ArrayList<String>(arguments.length + 3);
    command.addAll(List.of("-C", directory.toString()));
    command.addAll(List.of(arguments));
    return runProcess(gitExecutable, null, command.toArray(String[]::new));
  }

  private static GitCommandResult runProcess(
      Path executable, Path directory, String... arguments) throws IOException {
    var command = new ArrayList<String>(arguments.length + 1);
    command.add(executable.toString());
    command.addAll(List.of(arguments));
    var builder = new ProcessBuilder(command).redirectErrorStream(true);
    if (directory != null) {
      builder.directory(directory.toFile());
    }
    var process = builder.start();
    byte[] output;
    try (var stream = process.getInputStream()) {
      output = stream.readNBytes(8193);
    }
    require(output.length <= 8192, "tool identity command output exceeds the evidence bound");
    try {
      require(process.waitFor(15, TimeUnit.SECONDS), "tool identity command timed out");
    } catch (InterruptedException error) {
      Thread.currentThread().interrupt();
      throw new CaptureException("tool identity command was interrupted", error);
    } finally {
      if (process.isAlive()) {
        process.destroyForcibly();
      }
    }
    return new GitCommandResult(process.exitValue(), decodeUtf8(output).trim());
  }

  private static void requireRegular(Path path, String label) {
    require(Files.isRegularFile(path), label + " is not a regular file: " + path);
  }

  private static byte[] appendNewline(byte[] value) {
    var result = Arrays.copyOf(value, value.length + 1);
    result[value.length] = '\n';
    return result;
  }

  private static String hashFileOrEmpty(Path path) throws IOException {
    return Files.exists(path) ? sha256Id(path) : sha256Id(new byte[0]);
  }

  private static MessageDigest newSha256() {
    try {
      return MessageDigest.getInstance("SHA-256");
    } catch (NoSuchAlgorithmException error) {
      throw new AssertionError("SHA-256 is unavailable", error);
    }
  }

  private static byte[] sha256(byte[] value) {
    return newSha256().digest(value);
  }

  private static String sha256Id(byte[] value) {
    return digestId(sha256(value));
  }

  private static String sha256Id(Path path) throws IOException {
    var digest = newSha256();
    try (InputStream input = Files.newInputStream(path)) {
      var buffer = new byte[64 * 1024];
      int count;
      while ((count = input.read(buffer)) >= 0) {
        if (count != 0) {
          digest.update(buffer, 0, count);
        }
      }
    }
    return digestId(digest);
  }

  private static String digestId(MessageDigest digest) {
    return digestId(digest.digest());
  }

  private static String digestId(byte[] digest) {
    require(digest.length == 32, "SHA-256 digest has the wrong length");
    return "sha256:" + HexFormat.of().formatHex(digest);
  }

  private static byte[] contentIdDigest(String value) {
    requireContentId(value, "content ID");
    return HexFormat.of().parseHex(value.substring("sha256:".length()));
  }

  private static String contentId(String domain, byte[] canonicalBytes) {
    var digest = newSha256();
    digest.update(domain.getBytes(StandardCharsets.US_ASCII));
    digest.update((byte) 0);
    digest.update(canonicalBytes);
    return digestId(digest);
  }

  private static void requireContentId(String value, String label) {
    require(CONTENT_ID.matcher(value).matches(), label + " is not a canonical SHA-256 ID");
  }

  private static void updateU32(MessageDigest digest, long value) {
    require(value >= 0 && value <= 0xffff_ffffL, "transcript u32 is out of range");
    digest.update((byte) (value >>> 24));
    digest.update((byte) (value >>> 16));
    digest.update((byte) (value >>> 8));
    digest.update((byte) value);
  }

  private static void updateU64(MessageDigest digest, long value) {
    require(value >= 0, "transcript u64 exceeds the signed evidence range");
    for (var shift = 56; shift >= 0; shift -= 8) {
      digest.update((byte) (value >>> shift));
    }
  }

  private static void updateLengthPrefixedAscii(
      MessageDigest digest, String value, String label) {
    var bytes = value.getBytes(StandardCharsets.US_ASCII);
    require(new String(bytes, StandardCharsets.US_ASCII).equals(value), label + " is not ASCII");
    updateU32(digest, bytes.length);
    digest.update(bytes);
  }

  private static void await(long deadline) {
    while (true) {
      var remaining = deadline - System.nanoTime();
      if (remaining <= 0) {
        return;
      }
      LockSupport.parkNanos(remaining);
      if (Thread.interrupted()) {
        Thread.currentThread().interrupt();
        throw new CaptureException("qualification thread was interrupted");
      }
    }
  }

  private static TimedOperation awaitSubmission(Submission submission) throws Throwable {
    require(submission.accepted(), "cannot await a rejected qualification submission");
    try {
      return submission
          .completion()
          .get(
              SidecarSupervisor.RECOVERY_READY_TIMEOUT.plusSeconds(5).toMillis(),
              TimeUnit.MILLISECONDS);
    } catch (ExecutionException error) {
      var cause = error.getCause();
      if (cause instanceof Error fatal) {
        throw fatal;
      }
      if (cause instanceof Exception exception) {
        throw exception;
      }
      throw new CaptureException("qualification submission failed", cause);
    } catch (TimeoutException error) {
      throw new CaptureException("qualification submission exceeded the hard wait bound", error);
    } catch (InterruptedException error) {
      Thread.currentThread().interrupt();
      throw new CaptureException("qualification submission wait was interrupted", error);
    }
  }

  private static long checkedElapsed(long end, long start, String label) {
    var elapsed = end - start;
    require(elapsed >= 0, label + " monotonic clock moved backwards");
    return elapsed;
  }

  private static long positiveSigned(long value, String label) {
    require(value > 0, label + " is zero or exceeds the signed evidence range");
    return value;
  }

  private static String ascii(byte[] value, String label) {
    require(value.length > 0, label + " is empty");
    for (var character : value) {
      var unsigned = Byte.toUnsignedInt(character);
      require(unsigned >= 0x20 && unsigned <= 0x7e, label + " is not printable ASCII");
    }
    return new String(value, StandardCharsets.US_ASCII);
  }

  private static String decodeUtf8(byte[] value) {
    try {
      return StandardCharsets.UTF_8
          .newDecoder()
          .onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
          .onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT)
          .decode(java.nio.ByteBuffer.wrap(value))
          .toString();
    } catch (java.nio.charset.CharacterCodingException error) {
      throw new CaptureException("JSON is not strict UTF-8", error);
    }
  }

  private static void writeAtomically(Path output, Map<String, Object> value) throws IOException {
    var parent = output.getParent();
    require(parent != null, "output has no parent directory");
    var temporary = Files.createTempFile(parent, ".sidecar-profile-run-", ".json.tmp");
    var moved = false;
    try {
      try (var stream = new BufferedOutputStream(Files.newOutputStream(temporary), 64 * 1024);
          var writer = new OutputStreamWriter(stream, StandardCharsets.UTF_8)) {
        Json.write(value, writer);
        writer.write('\n');
      }
      try {
        Files.move(
            temporary,
            output,
            StandardCopyOption.ATOMIC_MOVE,
            StandardCopyOption.REPLACE_EXISTING);
      } catch (AtomicMoveNotSupportedException ignored) {
        Files.move(temporary, output, StandardCopyOption.REPLACE_EXISTING);
      }
      moved = true;
    } finally {
      if (!moved) {
        Files.deleteIfExists(temporary);
      }
    }
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw new CaptureException(message);
    }
  }

  private static final class CaptureException extends IllegalStateException {
    private static final long serialVersionUID = 1L;

    private CaptureException(String message) {
      super(message);
    }

    private CaptureException(String message, Throwable cause) {
      super(message, cause);
    }
  }
}
