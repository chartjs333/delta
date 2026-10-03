package io.deltareduce.node.sidecar;

import java.io.ByteArrayOutputStream;
import java.io.FilterInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.CompletionStage;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.regex.Pattern;

/** Executable crash/recovery qualification for embedded FFM and isolated sidecar profiles. */
public final class SidecarCrashQualification {
  private static final Duration PROCESS_TIMEOUT = Duration.ofSeconds(130);
  private static final Duration OPERATION_TIMEOUT = Duration.ofSeconds(125);
  private static final int MAX_PROCESS_OUTPUT = 1024 * 1024;
  private static final String BUILD_ID =
      "sha256:1616161616161616161616161616161616161616161616161616161616161616";
  private static final String SCHEMA_SET_ID =
      "sha256:1717171717171717171717171717171717171717171717171717171717171717";
  private static final String FORMAL_SEMANTICS_ID =
      "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
  private static final String FSYNC_TARGET = "DELTA_SIDECAR_QUALIFICATION_FSYNC_TARGET";
  private static final Pattern INSPECTION = Pattern.compile(
      "\\{\"recovered_durable_sequence\":([0-9]+),\"retry\":(null|\\{.*\\}),"
          + "\"schema_version\":\"1\\.0\\.0\",\"state_bytes_sha256\":"
          + "\"(sha256:[0-9a-f]{64})\",\"state_root\":\"([^\"]+)\","
          + "\"type_name\":\"DELTA_SIDECAR_DURABLE_INSPECTION\",\"wal_sha256\":"
          + "\"(sha256:[0-9a-f]{64})\",\"wal_size_bytes\":([0-9]+)\\}");
  private static final Pattern RETRY = Pattern.compile(
      "\\{\"durable_sequence\":([0-9]+),\"effect_identity\":\"([^\"]+)\","
          + "\"effect_sha256\":\"(sha256:[0-9a-f]{64})\",\"native_replay\":"
          + "(true|false),\"wal_receipt_identity\":\"([^\"]+)\","
          + "\"wal_receipt_sha256\":\"(sha256:[0-9a-f]{64})\"\\}");

  private SidecarCrashQualification() {}

  public static void main(String[] arguments) throws Exception {
    var options = Options.parse(arguments);
    var runner = new Runner(options);
    var output = runner.run();
    SidecarQualificationRaw.writeAtomically(options.output(), output);
    System.out.println(
        "wrote " + options.mode() + " " + options.profile() + " crash observations: "
            + options.output());
  }

  private enum Profile {
    EMBEDDED_FFM,
    ISOLATED_SIDECAR
  }

  private enum Mode {
    FAST,
    FULL
  }

  private enum Cut {
    BEFORE_WAL_APPEND("BEFORE_WAL_APPEND", "before-wal-append", 1, false),
    DURING_WAL_APPEND("DURING_WAL_APPEND", "during-wal-append", 2, false),
    AFTER_APPEND_BEFORE_DURABILITY(
        "AFTER_APPEND_BEFORE_DURABILITY", "after-append-before-durability", 3, true),
    AFTER_DURABILITY_BEFORE_COMMIT(
        "AFTER_DURABILITY_BEFORE_COMMIT", "after-durability-before-commit", 4, false),
    AFTER_COMMIT_BEFORE_EFFECT_RETURN(
        "AFTER_COMMIT_BEFORE_EFFECT_RETURN", "after-commit-before-effect-return", 5, false),
    AFTER_EFFECT_COPY_BEFORE_RETURN(
        "AFTER_EFFECT_COPY_BEFORE_RETURN", "after-effect-copy-before-return", 6, false),
    AFTER_NATIVE_RETURN_BEFORE_JAVA_SEND(
        "AFTER_NATIVE_RETURN_BEFORE_JAVA_SEND", "after-native-return-before-response", 7, false),
    DURING_IPC_RESPONSE_FRAME(
        "DURING_IPC_RESPONSE_FRAME", "during-ipc-response-frame", 0, false),
    DURING_SHARED_MEMORY_PUBLICATION(
        "DURING_SHARED_MEMORY_PUBLICATION", "during-shared-memory-publication", 0, false);

    private final String id;
    private final String sidecarFault;
    private final int probeCode;
    private final boolean interposerRequired;

    Cut(String id, String sidecarFault, int probeCode, boolean interposerRequired) {
      this.id = id;
      this.sidecarFault = sidecarFault;
      this.probeCode = probeCode;
      this.interposerRequired = interposerRequired;
    }
  }

  private record Options(
      Profile profile,
      Mode mode,
      Path output,
      Path workRoot,
      Path goldenFixture,
      Path inspector,
      Path javaExecutable,
      String classpath,
      Path probeLibrary,
      Path sidecarExecutable,
      Path fsyncInterposer) {
    private static Options parse(String[] arguments) {
      require(arguments.length % 2 == 0, usage());
      var values = new LinkedHashMap<String, String>();
      for (var index = 0; index < arguments.length; index += 2) {
        require(arguments[index].startsWith("--"), usage());
        require(values.put(arguments[index], arguments[index + 1]) == null,
            "duplicate option " + arguments[index]);
      }
      var profile = Profile.valueOf(required(values, "--profile"));
      var mode = Mode.valueOf(required(values, "--mode"));
      var result = new Options(
          profile,
          mode,
          path(values, "--output", true),
          path(values, "--work-root", true),
          path(values, "--golden-fixture", true),
          path(values, "--inspector", true),
          path(values, "--java-executable", profile == Profile.EMBEDDED_FFM),
          values.get("--classpath"),
          path(values, "--probe-library", profile == Profile.EMBEDDED_FFM),
          path(values, "--sidecar-executable", profile == Profile.ISOLATED_SIDECAR),
          path(values, "--fsync-interposer", false));
      if (profile == Profile.EMBEDDED_FFM) {
        require(result.classpath != null && !result.classpath.isEmpty(),
            "EMBEDDED_FFM requires --classpath");
      }
      if (mode == Mode.FULL) {
        require(isLinux(), "FULL mode requires Linux for exact point 3");
        require(result.fsyncInterposer != null && Files.isRegularFile(result.fsyncInterposer),
            "FULL mode requires --fsync-interposer");
      }
      return result;
    }

    private static String required(Map<String, String> values, String name) {
      var result = values.get(name);
      require(result != null && !result.isEmpty(), "missing " + name + "\n" + usage());
      return result;
    }

    private static Path path(Map<String, String> values, String name, boolean required) {
      var value = values.get(name);
      if (value == null) {
        require(!required, "missing " + name + "\n" + usage());
        return null;
      }
      return Path.of(value).toAbsolutePath().normalize();
    }

    private static String usage() {
      return "usage: SidecarCrashQualification --profile EMBEDDED_FFM|ISOLATED_SIDECAR "
          + "--mode FAST|FULL --output FILE --work-root DIR --golden-fixture FILE "
          + "--inspector FILE [--fsync-interposer FILE] "
          + "(--java-executable FILE --classpath CP --probe-library FILE | "
          + "--sidecar-executable FILE)";
    }
  }

  private static final class Runner {
    private final Options options;
    private final Path runRoot;
    private final Path initialFile;
    private final Path commandFile;
    private final byte[] initialState;
    private final byte[] command;
    private final Reference reference;

    private Runner(Options options) throws Exception {
      this.options = options;
      require(Files.isRegularFile(options.goldenFixture()), "golden fixture is missing");
      require(Files.isRegularFile(options.inspector()), "durable inspector is missing");
      Files.createDirectories(options.workRoot());
      runRoot = Files.createTempDirectory(options.workRoot(), "sidecar-crash-");
      var fixture = Files.readString(options.goldenFixture(), StandardCharsets.US_ASCII);
      initialState = golden(fixture, 5);
      command = golden(fixture, 6);
      initialFile = runRoot.resolve("initial-state.bin");
      commandFile = runRoot.resolve("command.bin");
      Files.write(initialFile, initialState);
      Files.write(commandFile, command);
      reference = buildReference();
    }

    private Map<String, Object> run() throws Exception {
      var cuts = selectedCuts();
      var records = new ArrayList<Object>();
      var nativeDeaths = 0;
      var survived = true;
      for (var cut : cuts) {
        CaseResult result;
        if (options.profile() == Profile.EMBEDDED_FFM) {
          result = embedded(cut);
        } else {
          result = sidecar(cut);
        }
        if (result.nativeDeathInjected()) {
          ++nativeDeaths;
          survived &= result.javaProcessSurvived();
        }
        records.add(restartRecord(result));
      }
      var survivalObservations = new LinkedHashMap<String, Object>();
      survivalObservations.put("native_death_injection_count", nativeDeaths);
      survivalObservations.put("profile_id", options.profile().name());
      survivalObservations.put("qualification_case_count", cuts.size());
      survivalObservations.put("survived_all_native_deaths", survived);
      var expectedDeaths = cuts.size();
      var survivalEvidence = SidecarQualificationRaw.evidence(
          Map.of(
              "CASE_COUNT_OBSERVED", records.size() == cuts.size(),
              "NATIVE_DEATH_COUNT_OBSERVED", nativeDeaths == expectedDeaths,
              "PROFILE_SURVIVAL_BOUNDARY_OBSERVED",
                  survived == (options.profile() == Profile.ISOLATED_SIDECAR)),
          survivalObservations);
      var survival = new LinkedHashMap<String, Object>();
      survival.put("evidence", survivalEvidence.value());
      survival.put("evidence_sha256", survivalEvidence.sha256());
      survival.put("survived_all_native_deaths", survived);

      var root = new LinkedHashMap<String, Object>();
      root.put("java_process_survival", survival);
      root.put("profile_id", options.profile().name());
      root.put("restart_to_ready", records);
      root.put("schema_version", "1.0.0");
      root.put(
          "type_name",
          options.mode() == Mode.FULL
              ? "FEATURE010_SIDECAR_CRASH_OBSERVATIONS"
              : "FEATURE010_SIDECAR_CRASH_OBSERVATIONS_FAST_NONQUALIFYING");
      return root;
    }

    private List<Cut> selectedCuts() {
      if (options.mode() == Mode.FAST) {
        return options.profile() == Profile.EMBEDDED_FFM
            ? List.of(Cut.AFTER_DURABILITY_BEFORE_COMMIT)
            : List.of(
                Cut.AFTER_DURABILITY_BEFORE_COMMIT,
                Cut.DURING_IPC_RESPONSE_FRAME,
                Cut.DURING_SHARED_MEMORY_PUBLICATION);
      }
      var result = new ArrayList<Cut>();
      result.addAll(List.of(
          Cut.BEFORE_WAL_APPEND,
          Cut.DURING_WAL_APPEND,
          Cut.AFTER_APPEND_BEFORE_DURABILITY,
          Cut.AFTER_DURABILITY_BEFORE_COMMIT,
          Cut.AFTER_COMMIT_BEFORE_EFFECT_RETURN,
          Cut.AFTER_EFFECT_COPY_BEFORE_RETURN,
          Cut.AFTER_NATIVE_RETURN_BEFORE_JAVA_SEND));
      if (options.profile() == Profile.ISOLATED_SIDECAR) {
        result.add(Cut.DURING_IPC_RESPONSE_FRAME);
        result.add(Cut.DURING_SHARED_MEMORY_PUBLICATION);
      }
      return List.copyOf(result);
    }

    private Reference buildReference() throws Exception {
      var directory = Files.createDirectory(runRoot.resolve("reference"));
      var first = inspect(directory, true);
      require(first.recoveredSequence() == 0 && first.retry() != null,
          "reference did not execute from the initial state");
      var finalState = inspect(directory, false);
      require(finalState.recoveredSequence() == first.retry().durableSequence(),
          "reference durable sequence did not recover");
      return new Reference(first.retry(), finalState);
    }

    private CaseResult embedded(Cut cut) throws Exception {
      require(cut.probeCode != 0, "embedded cut has no probe code");
      var directory = Files.createDirectory(runRoot.resolve("embedded-" + cut.id.toLowerCase(Locale.ROOT)));
      var commandLine = List.of(
          options.javaExecutable().toString(),
          "--enable-native-access=ALL-UNNAMED",
          "-cp",
          options.classpath(),
          EmbeddedCrashProbeChild.class.getName(),
          options.probeLibrary().toString(),
          directory.toString(),
          initialFile.toString(),
          commandFile.toString(),
          Integer.toString(cut.probeCode));
      var environment = faultEnvironment(cut, directory);
      var crash = process(commandLine, environment);
      require(crash.exitCode() == 86, "embedded child did not reach " + cut.id + ": " + crash.text());
      require(crash.text().contains("FFM_DOWNCALL_ENTER"), "embedded child omitted downcall marker");
      var recoveryStart = System.nanoTime();
      var recovered = inspect(directory, false);
      var duration = positiveElapsed(System.nanoTime(), recoveryStart);
      var retry = inspect(directory, true);
      require(retry.retry() != null, "embedded retry receipt is absent");
      var finalState = inspect(directory, false);
      requireExact(reference, retry.retry(), finalState, cut.id);
      var observations = commonObservations(
          cut, duration, false, 0, crash.exitCode(), recovered, retry.retry(), finalState);
      observations.put("child_stdout_sha256", SidecarQualificationRaw.sha256Id(crash.output()));
      observations.put("child_stdout_size_bytes", crash.output().length);
      observations.put("first_attempt_completion", "OWNING_JVM_EXITED_WITHOUT_NATIVE_RETURN");
      observations.put("qualification_parent_jvm_survived", true);
      observations.put("validated_response_count_before_recovery", 0);
      if (cut.interposerRequired) {
        observations.put("fsync_interposer_sha256",
            SidecarQualificationRaw.sha256Id(options.fsyncInterposer()));
      }
      var checks = Map.of(
          "CHILD_EXIT_REACHED_REQUESTED_CUT", true,
          "NO_VALIDATED_RESPONSE_EXPOSED", true,
          "RECOVERY_COMPLETED_BEFORE_RETRY", true,
          "RETRY_DURABLE_RESULT_MATCHED_REFERENCE", true,
          "STATE_AND_WAL_MATCHED_REFERENCE_AFTER_RETRY", true);
      return new CaseResult(
          cut,
          duration,
          false,
          true,
          SidecarQualificationRaw.evidence(checks, observations));
    }

    private CaseResult sidecar(Cut cut) throws Exception {
      var directory = Files.createDirectory(runRoot.resolve("sidecar-" + cut.id.toLowerCase(Locale.ROOT)));
      var connector = new FaultConnector(
          options.sidecarExecutable(), cut, options.fsyncInterposer(), directory);
      var config = new SidecarSupervisor.Config(
          directory,
          initialState,
          SidecarSupervisor.PipeProcessConnector.executableSha256(options.sidecarExecutable()),
          BUILD_ID,
          nestedDescriptor());
      var supervisor = new SidecarSupervisor(config, connector);
      InspectorObservation recovered;
      InspectorObservation finalState;
      InspectorRetry inspectorRetry;
      long recoveredSequence;
      long duration;
      int exitCode;
      long partialWireBytes;
      long validatedResponsesBeforeRecovery;
      long failedGenerationOpenAdmissionSequence;
      long failedGenerationSubmitAdmissionSequence;
      List<WireFrameObservation> failedGenerationFrames;
      String firstGenerationStderrSha256;
      long firstGenerationStderrSize;
      WalObservation failedGenerationWal;
      boolean retryWasNativeReplay;
      SidecarSupervisor.Telemetry transportTelemetry = null;
      int nativeToJavaStateAtExit = Integer.MIN_VALUE;
      try {
        var firstClient = await(supervisor.start());
        var firstConnection = connector.first();
        failedGenerationOpenAdmissionSequence = firstConnection.openAdmissionSequence();
        failedGenerationSubmitAdmissionSequence = Math.addExact(
            failedGenerationOpenAdmissionSequence, 1L);
        require(failedGenerationOpenAdmissionSequence == 1L
                && failedGenerationSubmitAdmissionSequence == 2L,
            "failed generation OPEN/SUBMIT admission order differs from the frozen sequence");
        var bytesBefore = firstConnection.stdoutBytes();
        var framesBefore = firstConnection.receivedFrameCount();
        var exact = LocalSidecarClient.submitRequest(ascii("request-001"), command);
        var firstAttempt = firstClient.tryEnqueue(exact);
        require(firstAttempt.accepted(), "sidecar first attempt was rejected locally");
        expectFailure(firstAttempt.completion());
        waitUntil(
            () -> supervisor.state() == SidecarSupervisor.State.READY
                && supervisor.telemetry().generation() == 2,
            OPERATION_TIMEOUT,
            "replacement sidecar READY");
        var readyNanos = System.nanoTime();
        require(firstConnection.confirmedExitNanos() != 0,
            "first sidecar death was not confirmed before replacement READY");
        duration = positiveElapsed(readyNanos, firstConnection.confirmedExitNanos());
        exitCode = firstConnection.exitCode();
        require(
            exitCode == expectedSidecarExitCode(cut),
            "first sidecar generation exited with an unexpected code at " + cut.id);
        partialWireBytes = Math.max(0, firstConnection.stdoutBytes() - bytesBefore);
        failedGenerationFrames = firstConnection.receivedFramesAfter(framesBefore);
        validatedResponsesBeforeRecovery = firstClient.telemetry().completed();

        var stateRequest = LocalSidecarClient.stateRequest(
            ascii("qualification-state-" + cut.id.toLowerCase(Locale.ROOT)),
            supervisor.runtimeInstanceId());
        var stateSubmission = supervisor.client().tryEnqueue(stateRequest);
        require(stateSubmission.accepted(), "recovered STATE was rejected");
        var state = await(stateSubmission.completion());
        recoveredSequence = state.payload().u64Bits(16);
        var recoveredStateBytes = state.payload().bytes(19);
        var recoveredStateBytesSha256 = digestIdentity(state.payload().bytes(18));
        require(
            recoveredStateBytesSha256.equals(
                SidecarQualificationRaw.sha256Id(recoveredStateBytes)),
            "recovered STATE bytes differ from their native digest");
        var recoveredWal = WalObservation.capture(directory);
        recovered = new InspectorObservation(
            recoveredSequence,
            null,
            recoveredStateBytesSha256,
            digestIdentity(state.payload().bytes(17)),
            recoveredWal.sha256(),
            recoveredWal.size());

        var retried = supervisor.retryAfterRecovery(exact);
        require(retried.accepted(), "sidecar exact retry was rejected");
        var response = await(retried.completion());
        require(response.messageType() == SidecarIpcV1.MessageType.SUBMIT_RESPONSE
                && response.nativeStatus() == 0,
            "sidecar retry did not return a successful SUBMIT_RESPONSE");
        var responseDurableSequence = response.payload().u64Bits(19);
        retryWasNativeReplay = recoveredSequence == responseDurableSequence;
        require(asciiText(response.payload().bytes(16)).equals(reference.retry().effectIdentity())
                && digestIdentity(response.payload().bytes(18)).equals(reference.retry().effectSha256())
                && responseDurableSequence == reference.retry().durableSequence(),
            "sidecar retry durable effect differs from reference");

        var close = supervisor.client().tryEnqueue(
            LocalSidecarClient.closeRequest(
                ascii("qualification-close-" + cut.id.toLowerCase(Locale.ROOT)),
                supervisor.runtimeInstanceId(),
                SidecarIpcV1.CloseMode.TERMINATE_AND_FENCE));
        require(close.accepted(), "sidecar CLOSE was rejected");
        await(close.completion());
        waitUntil(connector::allClosed, OPERATION_TIMEOUT, "sidecar lock/endpoint release");
        require(
            connector.launchCount() == 2 && connector.faultLaunchCount() == 1,
            "fault injection was not limited to the first sidecar generation");
        firstGenerationStderrSha256 = firstConnection.stderrSha256();
        firstGenerationStderrSize = firstConnection.stderrSize();
        failedGenerationWal = firstConnection.walAtConfirmedExit();
        nativeToJavaStateAtExit = firstConnection.nativeToJavaStateAtExit();
        transportTelemetry = supervisor.telemetry();
      } finally {
        supervisor.close();
      }
      var replay = inspect(directory, true);
      require(replay.retry() != null, "post-sidecar inspector replay is absent");
      var postRetryInspector = replay.retry();
      inspectorRetry = new InspectorRetry(
          postRetryInspector.durableSequence(),
          postRetryInspector.effectIdentity(),
          postRetryInspector.effectSha256(),
          retryWasNativeReplay,
          postRetryInspector.walReceiptIdentity(),
          postRetryInspector.walReceiptSha256());
      finalState = inspect(directory, false);
      requireExact(reference, inspectorRetry, finalState, cut.id);
      var observations = commonObservations(
          cut, duration, true, 0, exitCode, recovered, inspectorRetry, finalState);
      observations.put("failed_generation_stdout_bytes_after_submit", partialWireBytes);
      observations.put("failed_generation_wal_present", failedGenerationWal.present());
      observations.put("failed_generation_wal_sha256", failedGenerationWal.sha256());
      observations.put("failed_generation_wal_size_bytes", failedGenerationWal.size());
      observations.put("first_attempt_completion", "EXCEPTIONAL_TRANSPORT_COMPLETION");
      observations.put("first_generation_exit_code", exitCode);
      observations.put("first_generation_stderr_sha256", firstGenerationStderrSha256);
      observations.put("first_generation_stderr_size_bytes", firstGenerationStderrSize);
      observations.put("fault_injected_generation", 1);
      observations.put("fault_injected_launch_count", connector.faultLaunchCount());
      observations.put("generation_launch_count", connector.launchCount());
      observations.put(
          "retry_replay_classification_source",
          "RECOVERED_SEQUENCE_EQUALS_RESPONSE_DURABLE_SEQUENCE");
      observations.put("replacement_fault_injection_count", 0);
      observations.put("replacement_generation", 2);
      observations.put(
          "validated_response_count_before_recovery", validatedResponsesBeforeRecovery);
      if (cut == Cut.DURING_SHARED_MEMORY_PUBLICATION) {
        var ackFrames = failedGenerationFrames.stream()
            .filter(frame -> frame.messageType() == SidecarIpcV1.MessageType.SHARED_MEMORY_ACK)
            .toList();
        var operationResponseFrames = failedGenerationFrames.stream()
            .filter(frame -> frame.messageType() == SidecarIpcV1.MessageType.SUBMIT_RESPONSE
                || frame.messageType() == SidecarIpcV1.MessageType.ERROR_RESPONSE)
            .toList();
        var responseCarriers = failedGenerationFrames.stream()
            .filter(WireFrameObservation::sharedMemoryCarrier)
            .toList();
        var operationResponseWireBytes = operationResponseFrames.stream()
            .mapToLong(WireFrameObservation::wireBytes)
            .sum();
        require(nativeToJavaStateAtExit == SidecarSharedMemory.WRITING,
            "publication crash did not leave the native slot at WRITING");
        require(failedGenerationFrames.size() == 1
                && ackFrames.size() == 1
                && !ackFrames.get(0).sharedMemoryCarrier(),
            "publication crash exposed a frame other than the notification-only inline ACK");
        require(operationResponseFrames.isEmpty(),
            "publication crash exposed a SUBMIT_RESPONSE or ERROR_RESPONSE frame");
        require(responseCarriers.isEmpty(),
            "publication crash exposed a native-to-Java shared-memory response carrier");
        require(validatedResponsesBeforeRecovery == 0,
            "publication crash exposed a validated operation response");
        require(partialWireBytes == ackFrames.get(0).wireBytes(),
            "failed-generation stdout was not exactly the notification-only ACK frame");
        require(transportTelemetry != null
                && transportTelemetry.sharedMemoryIngressBytes() > 0
                && transportTelemetry.sharedMemoryEgressBytes() > 0
                && transportTelemetry.zeroCopyEligibleCount() > 0
                && transportTelemetry.zeroCopyHitCount() == 0,
            "shared-memory qualification did not account for copied mapped traffic truthfully");
        observations.put(
            "atomic_abi_probe_result",
            "LOCK_FREE_JAVA_NATIVE_MAP_SHARED_U32_BIG_ENDIAN");
        observations.put(
            "atomic_abi_probe_scope",
            "EXACT_PATH_DEVICE_INODE_GENERATION_SLOT");
        observations.put("atomic_abi_supported", true);
        observations.put("bounded_copy_equivalence", "EXACT");
        observations.put("fallback_transport", "NOT_USED");
        observations.put("shared_memory_admission_state", "ADMITTED_OUTCOME_AVAILABLE");
        observations.put(
            "shared_memory_admitted_sequence", failedGenerationSubmitAdmissionSequence);
        observations.put(
            "shared_memory_admitted_sequence_derivation",
            "OBSERVED_OPEN_ADMISSION_PLUS_FIRST_POST_OPEN_OPERATION");
        observations.put(
            "shared_memory_open_admitted_sequence", failedGenerationOpenAdmissionSequence);
        observations.put("shared_memory_control_frame_exposed", true);
        observations.put("shared_memory_enabled", true);
        observations.put("shared_memory_ingress_bytes",
            transportTelemetry.sharedMemoryIngressBytes());
        observations.put("shared_memory_egress_bytes",
            transportTelemetry.sharedMemoryEgressBytes());
        observations.put(
            "shared_memory_failed_generation_egress_control_bytes",
            partialWireBytes);
        observations.put(
            "shared_memory_failed_generation_operation_response_wire_bytes",
            operationResponseWireBytes);
        observations.put(
            "shared_memory_failed_generation_response_carrier_count",
            responseCarriers.size());
        observations.put(
            "shared_memory_failed_generation_response_frame_count",
            operationResponseFrames.size());
        observations.put("shared_memory_ingress_ack_frame_count", ackFrames.size());
        observations.put("shared_memory_notification_ack_inline_only", true);
        observations.put("shared_memory_operation_response_frame_exposed", false);
        observations.put("shared_memory_native_call_count", 1);
        observations.put("shared_memory_native_status", 0);
        observations.put("shared_memory_publication_completed", false);
        observations.put("shared_memory_publication_started", true);
        observations.put("shared_memory_region_id", "NATIVE_TO_JAVA");
        observations.put("shared_memory_slot_state_at_native_death", "WRITING");
        observations.put("shared_memory_status", transportTelemetry.sharedMemoryStatus());
        observations.put("shared_memory_telemetry_scope", "SUPERVISOR_ALL_GENERATIONS");
        observations.put("zero_copy_eligible_count",
            transportTelemetry.zeroCopyEligibleCount());
        observations.put("zero_copy_hit_count", transportTelemetry.zeroCopyHitCount());
      }
      if (cut.interposerRequired) {
        observations.put("fsync_interposer_sha256",
            SidecarQualificationRaw.sha256Id(options.fsyncInterposer()));
      }
      var checks = new LinkedHashMap<String, Boolean>();
      checks.put("FIRST_GENERATION_EXIT_CONFIRMED", true);
      checks.put("JAVA_PROCESS_SURVIVED_NATIVE_DEATH", true);
      checks.put("NO_VALIDATED_PARTIAL_RESPONSE_EXPOSED", true);
      checks.put("RECOVERY_READY_PRECEDED_RETRY", true);
      checks.put("RETRY_DURABLE_RESULT_MATCHED_REFERENCE", true);
      if (cut == Cut.DURING_SHARED_MEMORY_PUBLICATION) {
        checks.put("SHARED_MEMORY_ATOMIC_ABI_PROBED", true);
        checks.put("SHARED_MEMORY_ADMISSION_SEQUENCE_DERIVED", true);
        checks.put("SHARED_MEMORY_NOTIFICATION_ACK_ONLY", true);
        checks.put("SHARED_MEMORY_OPERATION_RESPONSE_NOT_EXPOSED", true);
        checks.put("SHARED_MEMORY_PUBLICATION_STARTED", true);
        checks.put("SHARED_MEMORY_PUBLICATION_NOT_EXPOSED", true);
      }
      return new CaseResult(
          cut,
          duration,
          true,
          true,
          SidecarQualificationRaw.evidence(checks, observations));
    }

    private LinkedHashMap<String, Object> commonObservations(
        Cut cut,
        long duration,
        boolean javaSurvived,
        int validatedResponseCountBeforeRecovery,
        int exitCode,
        InspectorObservation recovered,
        InspectorRetry retry,
        InspectorObservation finalState) {
      var observations = new LinkedHashMap<String, Object>();
      observations.put("crash_point", cut.id);
      observations.put("crash_process_exit_code", exitCode);
      observations.put("duration_ns", duration);
      observations.put("java_process_survived", javaSurvived);
      observations.put("journal_recovered_before_admission", true);
      observations.put(
          "partial_response_exposed", validatedResponseCountBeforeRecovery != 0);
      observations.put(
          "persist_before_expose",
          validatedResponseCountBeforeRecovery == 0
              && retryMatchesReference(reference, retry)
              && finalStateMatchesReference(reference, finalState));
      observations.put("profile_id", options.profile().name());
      observations.put("reference_durable_sequence", reference.retry().durableSequence());
      observations.put("reference_effect_identity", reference.retry().effectIdentity());
      observations.put("reference_effect_sha256", reference.retry().effectSha256());
      observations.put(
          "reference_state_bytes_sha256", reference.finalState().stateBytesSha256());
      observations.put("reference_state_root", reference.finalState().stateRoot());
      observations.put("reference_wal_receipt_identity", reference.retry().walReceiptIdentity());
      observations.put("reference_wal_receipt_sha256", reference.retry().walReceiptSha256());
      observations.put("reference_wal_sha256", reference.finalState().walSha256());
      observations.put("reference_wal_size_bytes", reference.finalState().walSize());
      observations.put("recovered_durable_sequence", recovered.recoveredSequence());
      observations.put("recovered_state_bytes_sha256", recovered.stateBytesSha256());
      observations.put("recovered_state_root", recovered.stateRoot());
      observations.put("recovered_wal_sha256", recovered.walSha256());
      observations.put("recovered_wal_size_bytes", recovered.walSize());
      observations.put(
          "replay_identity_exact",
          retryMatchesReference(reference, retry)
              && finalStateMatchesReference(reference, finalState));
      observations.put("retry_durable_sequence", retry.durableSequence());
      observations.put("retry_effect_identity", retry.effectIdentity());
      observations.put("retry_effect_sha256", retry.effectSha256());
      observations.put("retry_native_replay", retry.nativeReplay());
      observations.put("retry_wal_receipt_identity", retry.walReceiptIdentity());
      observations.put("retry_wal_receipt_sha256", retry.walReceiptSha256());
      observations.put("stable_state_bytes_sha256", finalState.stateBytesSha256());
      observations.put("stable_state_root", finalState.stateRoot());
      observations.put("stable_wal_sha256", finalState.walSha256());
      observations.put("stable_wal_size_bytes", finalState.walSize());
      return observations;
    }

    private Map<String, String> faultEnvironment(Cut cut, Path directory) {
      if (!cut.interposerRequired) {
        return Map.of();
      }
      require(isLinux() && options.fsyncInterposer() != null,
          "point 3 requires Linux --fsync-interposer");
      return Map.of(
          "LD_PRELOAD", options.fsyncInterposer().toString(),
          FSYNC_TARGET, directory.resolve("runtime.wal").toAbsolutePath().normalize().toString());
    }

    private InspectorObservation inspect(Path directory, boolean retry) throws Exception {
      var commandLine = new ArrayList<String>();
      commandLine.add(options.inspector().toString());
      commandLine.add("--directory");
      commandLine.add(directory.toString());
      commandLine.add("--initial-state-file");
      commandLine.add(initialFile.toString());
      if (retry) {
        commandLine.add("--retry-command-file");
        commandLine.add(commandFile.toString());
      }
      var result = process(commandLine, Map.of());
      require(result.exitCode() == 0, "durable inspector failed: " + result.text());
      return InspectorObservation.parse(result.text());
    }

  }

  private record Reference(InspectorRetry retry, InspectorObservation finalState) {}

  private record WalObservation(boolean present, String sha256, long size) {
    private static WalObservation capture(Path directory) throws IOException {
      var wal = directory.resolve("runtime.wal");
      if (!Files.exists(wal)) {
        return new WalObservation(
            false, SidecarQualificationRaw.sha256Id(new byte[0]), 0);
      }
      require(Files.isRegularFile(wal), "runtime WAL is not a regular file");
      return new WalObservation(true, SidecarQualificationRaw.sha256Id(wal), Files.size(wal));
    }
  }

  private record CaseResult(
      Cut cut,
      long durationNanos,
      boolean javaProcessSurvived,
      boolean nativeDeathInjected,
      SidecarQualificationRaw.Evidence evidence) {}

  private static Map<String, Object> restartRecord(CaseResult result) {
    var record = new LinkedHashMap<String, Object>();
    record.put("crash_point", result.cut().id);
    record.put("duration_ns", result.durationNanos());
    record.put("evidence", result.evidence().value());
    record.put("evidence_sha256", result.evidence().sha256());
    return record;
  }

  private record InspectorRetry(
      long durableSequence,
      String effectIdentity,
      String effectSha256,
      boolean nativeReplay,
      String walReceiptIdentity,
      String walReceiptSha256) {
    private static InspectorRetry parse(String value) {
      var matcher = RETRY.matcher(value);
      require(matcher.matches(), "inspector retry JSON changed: " + value);
      return new InspectorRetry(
          decimal(matcher.group(1)),
          matcher.group(2),
          matcher.group(3),
          Boolean.parseBoolean(matcher.group(4)),
          matcher.group(5),
          matcher.group(6));
    }
  }

  private record InspectorObservation(
      long recoveredSequence,
      InspectorRetry retry,
      String stateBytesSha256,
      String stateRoot,
      String walSha256,
      long walSize) {
    private static InspectorObservation parse(String value) {
      var matcher = INSPECTION.matcher(value.strip());
      require(matcher.matches(), "inspector JSON changed: " + value);
      return new InspectorObservation(
          decimal(matcher.group(1)),
          matcher.group(2).equals("null") ? null : InspectorRetry.parse(matcher.group(2)),
          matcher.group(3),
          matcher.group(4),
          matcher.group(5),
          decimal(matcher.group(6)));
    }
  }

  private record ProcessResult(int exitCode, byte[] output) {
    private String text() {
      return new String(output, StandardCharsets.UTF_8);
    }
  }

  private static ProcessResult process(List<String> command, Map<String, String> environment)
      throws Exception {
    var builder = new ProcessBuilder(command).redirectErrorStream(true);
    builder.environment().putAll(environment);
    var process = builder.start();
    var output = new ByteArrayOutputStream();
    var readFailure = new IOException[1];
    var reader = new Thread(() -> {
      try (var input = process.getInputStream()) {
        var block = new byte[8192];
        int count;
        while ((count = input.read(block)) >= 0) {
          if (count > 0) {
            if (output.size() + count > MAX_PROCESS_OUTPUT) {
              throw new IOException("qualification process output exceeded 1 MiB");
            }
            output.write(block, 0, count);
          }
        }
      } catch (IOException error) {
        readFailure[0] = error;
      }
    }, "sidecar-qualification-output");
    reader.setDaemon(true);
    reader.start();
    if (!process.waitFor(PROCESS_TIMEOUT.toNanos(), TimeUnit.NANOSECONDS)) {
      process.destroyForcibly();
      process.waitFor(10, TimeUnit.SECONDS);
      throw new TimeoutException("qualification process timed out: " + command.get(0));
    }
    reader.join(10_000);
    require(!reader.isAlive(), "qualification output reader did not terminate");
    if (readFailure[0] != null) {
      throw readFailure[0];
    }
    return new ProcessResult(process.exitValue(), output.toByteArray());
  }

  private static final class FaultConnector implements SidecarSupervisor.GenerationConnector {
    private final Path executable;
    private final Cut cut;
    private final Path interposer;
    private final Path directory;
    private final AtomicInteger launches = new AtomicInteger();
    private final AtomicInteger faultLaunches = new AtomicInteger();
    private final List<TrackedConnection> connections = new ArrayList<>();

    private FaultConnector(Path executable, Cut cut, Path interposer, Path directory) {
      this.executable = Objects.requireNonNull(executable, "executable");
      this.cut = Objects.requireNonNull(cut, "cut");
      this.interposer = interposer;
      this.directory = Objects.requireNonNull(directory, "directory");
    }

    @Override
    public synchronized SidecarSupervisor.Connection connect(
        SidecarSupervisor.LaunchContext context, Duration readyTimeout) throws Exception {
      Objects.requireNonNull(readyTimeout, "readyTimeout");
      require(Arrays.equals(
              SidecarSupervisor.PipeProcessConnector.executableSha256(executable),
              context.identity().executableSha256()),
          "sidecar executable changed before launch");
      var launch = launches.incrementAndGet();
      require(SidecarSharedMemory.atomicAbiSupported(),
          "qualification requires lock-free big-endian shared-memory atomics");
      var sharedMemory = SidecarSharedMemory.GenerationResources.create(
          context.identity().generation());
      try {
        require(
            SidecarSupervisor.PipeProcessConnector.mappedSharedMemoryAtomicAbiSupported(
                executable, sharedMemory, readyTimeout)
                && sharedMemory.mappedAtomicAbiProbed(),
            "qualification requires the exact Java/native MAP_SHARED atomic ABI probe");
      } catch (Throwable error) {
        try {
          sharedMemory.close();
        } catch (IOException closeFailure) {
          error.addSuppressed(closeFailure);
        }
        throw error;
      }
      var command = new ArrayList<String>();
      command.add(executable.toString());
      command.add("--session");
      command.add(context.identity().sessionId().hex());
      command.add("--generation");
      command.add(Long.toUnsignedString(context.identity().generation()));
      if (context.durableDirectoryIdentity() != null) {
        command.add("--durable-device");
        command.add(Long.toUnsignedString(context.durableDirectoryIdentity().device()));
        command.add("--durable-inode");
        command.add(Long.toUnsignedString(context.durableDirectoryIdentity().inode()));
      }
      command.add("--java-to-native-shm");
      command.add(sharedMemory.javaToNativePath().toString());
      command.add("--native-to-java-shm");
      command.add(sharedMemory.nativeToJavaPath().toString());
      command.add("--java-to-native-shm-device");
      command.add(Long.toUnsignedString(sharedMemory.javaToNativeIdentity().device()));
      command.add("--java-to-native-shm-inode");
      command.add(Long.toUnsignedString(sharedMemory.javaToNativeIdentity().inode()));
      command.add("--native-to-java-shm-device");
      command.add(Long.toUnsignedString(sharedMemory.nativeToJavaIdentity().device()));
      command.add("--native-to-java-shm-inode");
      command.add(Long.toUnsignedString(sharedMemory.nativeToJavaIdentity().inode()));
      if (launch == 1) {
        faultLaunches.incrementAndGet();
        command.add("--fault");
        command.add(cut.sidecarFault);
      }
      var stderr = directory.resolve("generation-" + launch + ".stderr");
      var builder = new ProcessBuilder(command).redirectError(stderr.toFile());
      if (launch == 1 && cut.interposerRequired) {
        require(isLinux() && interposer != null,
            "point 3 sidecar requires Linux --fsync-interposer");
        builder.environment().put("LD_PRELOAD", interposer.toString());
        builder.environment().put(
            FSYNC_TARGET,
            directory.resolve("runtime.wal").toAbsolutePath().normalize().toString());
      }
      try {
        var process = builder.start();
        var counted = new CountingInputStream(process.getInputStream());
        LocalSidecarClient.Transport transport = new LocalSidecarClient.StreamTransport(
            counted, process.getOutputStream());
        transport = new SidecarSharedMemory.Transport(
            transport, sharedMemory.javaToNative(), sharedMemory.nativeToJava());
        var trackingTransport = new TrackingTransport(transport);
        var connection = new TrackedConnection(
            process, trackingTransport, counted, stderr, directory, sharedMemory);
        connections.add(connection);
        return connection;
      } catch (Throwable error) {
        sharedMemory.close();
        throw error;
      }
    }

    private synchronized TrackedConnection first() {
      require(!connections.isEmpty(), "first sidecar connection is absent");
      return connections.get(0);
    }

    private synchronized boolean allClosed() {
      return connections.size() >= 2 && connections.stream().allMatch(TrackedConnection::closed);
    }

    private int faultLaunchCount() {
      return faultLaunches.get();
    }

    private int launchCount() {
      return launches.get();
    }
  }

  private static final class TrackedConnection implements SidecarSupervisor.Connection {
    private final Process process;
    private final TrackingTransport transport;
    private final CountingInputStream input;
    private final Path stderr;
    private final Path directory;
    private final SidecarSharedMemory.GenerationResources sharedMemory;
    private final SidecarSharedMemory.CleanupProgress cleanup =
        new SidecarSharedMemory.CleanupProgress();
    private final AtomicLong confirmedExitNanos = new AtomicLong();
    private volatile int exitCode = Integer.MIN_VALUE;
    private volatile WalObservation walAtConfirmedExit;
    private volatile IOException walObservationFailure;
    private volatile int nativeToJavaStateAtExit = Integer.MIN_VALUE;

    private TrackedConnection(
        Process process,
        TrackingTransport transport,
        CountingInputStream input,
        Path stderr,
        Path directory,
        SidecarSharedMemory.GenerationResources sharedMemory) {
      this.process = process;
      this.transport = transport;
      this.input = input;
      this.stderr = stderr;
      this.directory = directory;
      this.sharedMemory = sharedMemory;
    }

    @Override
    public LocalSidecarClient.Transport transport() {
      return transport;
    }

    @Override
    public boolean isAlive() {
      return process.isAlive();
    }

    @Override
    public void requestShutdown() {
      if (process.isAlive()) {
        process.destroy();
      }
    }

    @Override
    public void forceTermination() {
      if (process.isAlive()) {
        process.destroyForcibly();
      }
    }

    @Override
    public boolean awaitExit(Duration timeout) throws InterruptedException {
      var exited = process.waitFor(timeout.toNanos(), TimeUnit.NANOSECONDS);
      if (exited) {
        exitCode = process.exitValue();
        if (walAtConfirmedExit == null && walObservationFailure == null) {
          try {
            walAtConfirmedExit = WalObservation.capture(directory);
          } catch (IOException error) {
            walObservationFailure = error;
          }
        }
        confirmedExitNanos.compareAndSet(0, System.nanoTime());
        nativeToJavaStateAtExit = sharedMemory.nativeToJava().rawState(0);
      }
      return exited;
    }

    @Override
    public boolean endpointClosed() {
      return cleanup.confirmed();
    }

    @Override
    public void close() throws IOException {
      cleanup.close(this::closeTransport, sharedMemory::close);
    }

    private void closeTransport() throws IOException {
      try {
        transport.close();
      } catch (IOException error) {
        if (transport.isOpen()) {
          throw error;
        }
      }
      if (transport.isOpen()) {
        throw new IOException("qualification transport close was not confirmed");
      }
    }

    private boolean closed() {
      return endpointClosed() && !process.isAlive();
    }

    private long confirmedExitNanos() {
      return confirmedExitNanos.get();
    }

    private int exitCode() {
      require(exitCode != Integer.MIN_VALUE, "sidecar exit code is unavailable");
      return exitCode;
    }

    private long stdoutBytes() {
      return input.count();
    }

    private int receivedFrameCount() {
      return transport.receivedFrameCount();
    }

    private List<WireFrameObservation> receivedFramesAfter(int firstIndex) {
      return transport.receivedFramesAfter(firstIndex);
    }

    private long openAdmissionSequence() {
      return transport.openAdmissionSequence();
    }

    private long stderrSize() throws IOException {
      var size = Files.size(stderr);
      require(size <= MAX_PROCESS_OUTPUT, "sidecar stderr exceeded 1 MiB");
      return size;
    }

    private String stderrSha256() throws IOException {
      stderrSize();
      return SidecarQualificationRaw.sha256Id(stderr);
    }

    private WalObservation walAtConfirmedExit() throws IOException {
      if (walObservationFailure != null) {
        throw walObservationFailure;
      }
      require(walAtConfirmedExit != null, "failed-generation WAL was not captured at exit");
      return walAtConfirmedExit;
    }

    private int nativeToJavaStateAtExit() {
      require(nativeToJavaStateAtExit != Integer.MIN_VALUE,
          "native-to-Java shared-memory state at exit is unavailable");
      return nativeToJavaStateAtExit;
    }
  }

  private record WireFrameObservation(
      SidecarIpcV1.MessageType messageType,
      boolean sharedMemoryCarrier,
      int wireBytes,
      long admissionSequence) {}

  /** Records only complete native-to-Java wire frames before any SHM carrier resolution. */
  private static final class TrackingTransport implements LocalSidecarClient.Transport {
    private final LocalSidecarClient.Transport delegate;
    private final List<WireFrameObservation> receivedFrames = new ArrayList<>();

    private TrackingTransport(LocalSidecarClient.Transport delegate) {
      this.delegate = Objects.requireNonNull(delegate, "delegate");
    }

    @Override
    public void write(byte[] canonicalFrame) throws IOException {
      delegate.write(canonicalFrame);
    }

    @Override
    public byte[] read() throws IOException {
      var result = delegate.read();
      SidecarIpcV1.MessageType messageType;
      long admissionSequence = 0L;
      var sharedMemoryCarrier = SidecarSharedMemory.isSharedMemoryCarrier(result);
      if (sharedMemoryCarrier) {
        messageType = SidecarSharedMemory.inspectCarrierHeader(result).messageType();
      } else {
        var frame = SidecarIpcV1.decodeFrame(result);
        messageType = frame.messageType();
        if (messageType == SidecarIpcV1.MessageType.OPEN_RESPONSE) {
          admissionSequence = frame.payload().u64Bits(4);
        }
      }
      synchronized (receivedFrames) {
        receivedFrames.add(
            new WireFrameObservation(
                messageType, sharedMemoryCarrier, result.length, admissionSequence));
      }
      return result;
    }

    @Override
    public byte[] resolveSharedMemoryCarrier(byte[] carrier) throws IOException {
      return delegate.resolveSharedMemoryCarrier(carrier);
    }

    @Override
    public boolean acceptSharedMemoryAck(SidecarIpcV1.Frame notification)
        throws IOException {
      return delegate.acceptSharedMemoryAck(notification);
    }

    @Override
    public boolean sharedMemoryConfigured() {
      return delegate.sharedMemoryConfigured();
    }

    @Override
    public boolean lastWriteSharedMemory() {
      return delegate.lastWriteSharedMemory();
    }

    @Override
    public boolean isOpen() {
      return delegate.isOpen();
    }

    @Override
    public void close() throws IOException {
      delegate.close();
    }

    private int receivedFrameCount() {
      synchronized (receivedFrames) {
        return receivedFrames.size();
      }
    }

    private List<WireFrameObservation> receivedFramesAfter(int firstIndex) {
      synchronized (receivedFrames) {
        require(firstIndex >= 0 && firstIndex <= receivedFrames.size(),
            "wire-frame observation index is outside bounds");
        return List.copyOf(receivedFrames.subList(firstIndex, receivedFrames.size()));
      }
    }

    private long openAdmissionSequence() {
      synchronized (receivedFrames) {
        var opens = receivedFrames.stream()
            .filter(frame -> frame.messageType() == SidecarIpcV1.MessageType.OPEN_RESPONSE)
            .toList();
        require(opens.size() == 1 && opens.get(0).admissionSequence() != 0L,
            "wire observations do not contain one admitted OPEN response");
        return opens.get(0).admissionSequence();
      }
    }
  }

  private static final class CountingInputStream extends FilterInputStream {
    private final AtomicLong count = new AtomicLong();

    private CountingInputStream(InputStream input) {
      super(input);
    }

    @Override
    public int read() throws IOException {
      var result = in.read();
      if (result >= 0) {
        count.incrementAndGet();
      }
      return result;
    }

    @Override
    public int read(byte[] value, int offset, int length) throws IOException {
      var result = in.read(value, offset, length);
      if (result > 0) {
        count.addAndGet(result);
      }
      return result;
    }

    private long count() {
      return count.get();
    }
  }

  private static int expectedSidecarExitCode(Cut cut) {
    if (cut == Cut.DURING_IPC_RESPONSE_FRAME) {
      return 87;
    }
    return cut == Cut.DURING_SHARED_MEMORY_PUBLICATION ? 88 : 86;
  }

  private static byte[] nestedDescriptor() {
    return SidecarIpcV1.encodeNestedDescriptor(
        new SidecarIpcV1.NestedDescriptor(
            64,
            1,
            0,
            SidecarIpcV1.NESTED_ABI_FEATURE_BITS,
            "1.0.0",
            "003.1.0",
            FORMAL_SEMANTICS_ID,
            BUILD_ID,
            SCHEMA_SET_ID,
            "embedded-ffm"));
  }

  private static void requireExact(
      Reference reference,
      InspectorRetry retry,
      InspectorObservation finalState,
      String cut) {
    require(
        retryMatchesReference(reference, retry),
        cut + " retry identity/bytes/sequence differ from reference");
    require(
        finalStateMatchesReference(reference, finalState),
        cut + " recovered state/WAL differ from reference");
  }

  private static boolean retryMatchesReference(Reference reference, InspectorRetry retry) {
    var expected = reference.retry();
    return retry.durableSequence() == expected.durableSequence()
        && retry.effectIdentity().equals(expected.effectIdentity())
        && retry.effectSha256().equals(expected.effectSha256())
        && retry.walReceiptIdentity().equals(expected.walReceiptIdentity())
        && retry.walReceiptSha256().equals(expected.walReceiptSha256());
  }

  private static boolean finalStateMatchesReference(
      Reference reference, InspectorObservation finalState) {
    var expected = reference.finalState();
    return finalState.recoveredSequence() == expected.recoveredSequence()
        && finalState.stateBytesSha256().equals(expected.stateBytesSha256())
        && finalState.stateRoot().equals(expected.stateRoot())
        && finalState.walSha256().equals(expected.walSha256())
        && finalState.walSize() == expected.walSize();
  }

  private static <T> T await(CompletionStage<T> stage) throws Exception {
    try {
      return stage.toCompletableFuture().get(
          OPERATION_TIMEOUT.toNanos(), TimeUnit.NANOSECONDS);
    } catch (ExecutionException error) {
      if (error.getCause() instanceof Exception exception) {
        throw exception;
      }
      throw error;
    }
  }

  private static void expectFailure(CompletionStage<?> stage) throws Exception {
    try {
      await(stage);
    } catch (Exception expected) {
      return;
    }
    throw new IllegalStateException("crash-injected operation unexpectedly returned a response");
  }

  private static void waitUntil(
      java.util.function.BooleanSupplier condition, Duration timeout, String label)
      throws Exception {
    var deadline = System.nanoTime() + timeout.toNanos();
    while (!condition.getAsBoolean()) {
      if (System.nanoTime() - deadline >= 0) {
        throw new TimeoutException("timed out waiting for " + label);
      }
      Thread.sleep(10);
    }
  }

  private static long positiveElapsed(long end, long start) {
    var elapsed = end - start;
    require(elapsed > 0, "non-positive recovery-ready duration");
    return elapsed;
  }

  private static byte[] golden(String fixture, int typeCode) {
    var pattern = Pattern.compile(
        "\\\"envelope_hex\\\":\\\"([0-9a-f]+)\\\","
            + "\\\"envelope_sha256\\\":\\\"[0-9a-f]+\\\","
            + "\\\"type_code\\\":"
            + typeCode);
    var matcher = pattern.matcher(fixture);
    require(matcher.find(), "golden type " + typeCode + " is missing");
    var result = HexFormat.of().parseHex(matcher.group(1));
    require(!matcher.find(), "golden type " + typeCode + " is duplicated");
    return result;
  }

  private static SidecarIpcV1.Id128 id(int value) {
    var result = new byte[16];
    result[12] = (byte) (value >>> 24);
    result[13] = (byte) (value >>> 16);
    result[14] = (byte) (value >>> 8);
    result[15] = (byte) value;
    return new SidecarIpcV1.Id128(result);
  }

  private static byte[] ascii(String value) {
    return value.getBytes(StandardCharsets.US_ASCII);
  }

  private static String asciiText(byte[] value) {
    return new String(value, StandardCharsets.US_ASCII);
  }

  private static String digestIdentity(byte[] value) {
    require(value.length == 32, "digest has the wrong size");
    return "sha256:" + HexFormat.of().formatHex(value);
  }

  private static long decimal(String value) {
    try {
      var result = Long.parseLong(value);
      require(result >= 0, "negative decimal");
      return result;
    } catch (NumberFormatException error) {
      throw new IllegalArgumentException("qualification integer is outside signed u63", error);
    }
  }

  private static boolean isLinux() {
    return System.getProperty("os.name").toLowerCase(Locale.ROOT).contains("linux");
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalStateException(message);
    }
  }
}
