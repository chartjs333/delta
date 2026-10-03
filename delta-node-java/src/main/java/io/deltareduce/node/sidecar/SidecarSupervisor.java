package io.deltareduce.node.sidecar;

import java.io.IOException;
import java.io.InputStream;
import java.nio.channels.SeekableByteChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.SecureDirectoryStream;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributeView;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Operational process supervisor for the isolated native runtime.
 *
 * <p>Lifecycle state, heartbeat time, session IDs and generations are local transport facts only.
 * This class does not emit formal actions or decide protocol legality.
 */
public final class SidecarSupervisor implements AutoCloseable {
  public static final Duration HEARTBEAT_INTERVAL = Duration.ofMillis(1_000);
  public static final int HEARTBEAT_MISS_LIMIT = 5;
  public static final Duration GRACEFUL_SHUTDOWN_TIMEOUT = Duration.ofMillis(10_000);
  public static final Duration RECOVERY_READY_TIMEOUT = Duration.ofMillis(120_000);
  public static final int RESTART_ATTEMPT_LIMIT = 3;
  public static final Duration RESTART_BACKOFF = Duration.ofMillis(1_000);

  private final Config config;
  private final GenerationConnector connector;
  private final Timing timing;
  private final Sleeper sleeper;
  private final DurableDirectoryPin durableDirectoryPin;
  private final DurableDirectoryIdentity durableDirectoryIdentity;
  private final SecureRandom random = new SecureRandom();
  private final AtomicLong generationCounter = new AtomicLong();
  private final AtomicReference<State> state = new AtomicReference<>(State.NEW);
  private final AtomicBoolean closed = new AtomicBoolean();
  private final AtomicInteger heartbeatMisses = new AtomicInteger();
  private final AtomicBoolean heartbeatOutstanding = new AtomicBoolean();
  private final Object lifecycleGate = new Object();
  private final Object recoveryGate = new Object();
  private final Object quarantineGate = new Object();
  private final List<Connection> quarantinedConnections = new ArrayList<>();
  private final ExecutorService lifecycle =
      Executors.newSingleThreadExecutor(operation -> daemon(operation, "delta-sidecar-supervisor"));
  private final ScheduledExecutorService heartbeat =
      Executors.newSingleThreadScheduledExecutor(
          operation -> daemon(operation, "delta-sidecar-heartbeat"));
  private final CopyLedger copyLedger = new CopyLedger();
  private final LocalSidecarClient.RequestIdentityLedger requestIdentityLedger =
      new LocalSidecarClient.RequestIdentityLedger();
  private volatile Connection connection;
  private volatile LocalSidecarClient client;
  private volatile SidecarIpcV1.Id128 runtimeInstanceId;
  private volatile ScheduledFuture<?> heartbeatTask;
  private volatile Throwable lastFailure;
  private boolean recoveryActive;
  private LocalSidecarClient.Failure pendingRecoveryFailure;

  public SidecarSupervisor(Config config, GenerationConnector connector) {
    this(config, connector, Timing.frozen(), Thread::sleep);
  }

  SidecarSupervisor(
      Config config, GenerationConnector connector, Timing timing, Sleeper sleeper) {
    this.config = Objects.requireNonNull(config, "config");
    this.connector = Objects.requireNonNull(connector, "connector");
    this.timing = Objects.requireNonNull(timing, "timing");
    this.sleeper = Objects.requireNonNull(sleeper, "sleeper");
    this.durableDirectoryPin = DurableDirectoryPin.open(config.durableDirectory);
    this.durableDirectoryIdentity =
        durableDirectoryPin == null ? null : durableDirectoryPin.identity();
  }

  /** Starts the first generation without blocking the caller or a Netty event loop. */
  public CompletionStage<LocalSidecarClient> start() {
    var result = new CompletableFuture<LocalSidecarClient>();
    synchronized (lifecycleGate) {
      if (closed.get() || !state.compareAndSet(State.NEW, State.DESCRIBE_ONLY)) {
        result.completeExceptionally(new IllegalStateException("supervisor was already started"));
        return result.minimalCompletionStage();
      }
      try {
        lifecycle.execute(() -> {
          try {
            var ready = startGeneration();
            result.complete(ready);
          } catch (Exception error) {
            lastFailure = error;
            setStateIfOpen(State.UNREADY);
            result.completeExceptionally(error);
          }
        });
      } catch (RejectedExecutionException rejected) {
        lastFailure = rejected;
        result.completeExceptionally(rejected);
      }
    }
    return result.minimalCompletionStage();
  }

  public State state() {
    return state.get();
  }

  public LocalSidecarClient client() {
    var current = client;
    if (state.get() != State.READY || current == null || !current.isAccepting()) {
      throw new IllegalStateException("sidecar is not READY");
    }
    return current;
  }

  public SidecarIpcV1.Id128 runtimeInstanceId() {
    var current = runtimeInstanceId;
    if (current == null) {
      throw new IllegalStateException("native runtime instance is unavailable");
    }
    return current;
  }

  /** Re-enqueues the exact immutable request only after replacement recovery reached READY. */
  public LocalSidecarClient.Submission retryAfterRecovery(
      LocalSidecarClient.PreparedRequest request) {
    return client().tryEnqueue(Objects.requireNonNull(request, "request"));
  }

  public Throwable lastFailure() {
    return lastFailure;
  }

  public Telemetry telemetry() {
    var current = client;
    return new Telemetry(
        state.get(),
        generationCounter.get(),
        heartbeatMisses.get(),
        copyLedger.inlineIngressBytes.get(),
        copyLedger.inlineEgressBytes.get(),
        copyLedger.sharedMemoryIngressBytes.get(),
        copyLedger.sharedMemoryEgressBytes.get(),
        copyLedger.stagingFallbackIngressBytes.get(),
        copyLedger.stagingFallbackEgressBytes.get(),
        copyLedger.zeroCopyEligibleCount.get(),
        copyLedger.zeroCopyHitCount.get(),
        copyLedger.sharedMemoryStatus(),
        copyLedger.maxSubmitStagingFallback(),
        current == null ? null : current.telemetry(),
        lastFailure == null ? "" : lastFailure.getClass().getSimpleName());
  }

  /** Returns the copy observation attached to this exact validated response. */
  public OperationCopy operationCopy(LocalSidecarClient.Response response) {
    Objects.requireNonNull(response, "response");
    require(
        response.responseEvidence() instanceof OperationCopy,
        "response has no completed SUBMIT copy observation");
    var measured = (OperationCopy) response.responseEvidence();
    require(
        measured.generation() == response.generation()
            && measured.correlationId().equals(response.correlationId().hex()),
        "response copy observation identity mismatch");
    return measured;
  }

  int transientCopyObservationCount() {
    return copyLedger.transientObservationCount();
  }

  @Override
  public void close() {
    State previousState;
    LocalSidecarClient currentClient;
    Connection currentConnection;
    synchronized (lifecycleGate) {
      if (!closed.compareAndSet(false, true)) {
        return;
      }
      previousState = state.getAndSet(State.CLOSED);
      currentClient = client;
      currentConnection = connection;
    }
    closeDurablePins();
    cancelHeartbeat();
    if (currentClient != null) {
      currentClient.close();
    }
    copyLedger.clearAllTransient();
    if (currentConnection != null) {
      if (previousState != State.READY && previousState != State.CLOSED) {
        forceExpiredGeneration(currentConnection);
      }
      lifecycle.execute(() -> stopConnection(currentConnection));
    }
    heartbeat.shutdownNow();
    lifecycle.shutdown();
  }

  private LocalSidecarClient startGeneration() throws Exception {
    if (!setStateIfOpen(State.DESCRIBE_ONLY)) {
      throw new IllegalStateException("supervisor is closed");
    }
    var generation = nextGeneration();
    var session = randomId();
    var identity = new SidecarIpcV1.DescriptorIdentity(
        session,
        generation,
        config.executableSha256,
        config.sidecarBuildId,
        config.nestedDescriptor);
    var deadlineConnection = new AtomicReference<Connection>();
    var deadlineExpired = new AtomicBoolean();
    var ready = new AtomicBoolean();
    var readinessGate = new Object();
    var recoveryDeadline = heartbeat.schedule(
        () -> {
          Connection target;
          synchronized (readinessGate) {
            if (ready.get()) {
              return;
            }
            deadlineExpired.set(true);
            target = deadlineConnection.get();
          }
          if (target != null) {
            forceExpiredGeneration(target);
          }
        },
        timing.recoveryReadyTimeout.toNanos(),
        TimeUnit.NANOSECONDS);
    Connection launched = null;
    CountingTransport transport = null;
    try {
      verifyDurableBindingsForLaunch();
      launched = connector.connect(
          new LaunchContext(identity, config.durableDirectory, durableDirectoryIdentity),
          timing.recoveryReadyTimeout);
      boolean expiredAfterConnect;
      synchronized (readinessGate) {
        synchronized (lifecycleGate) {
          deadlineConnection.set(launched);
          connection = launched;
          expiredAfterConnect = deadlineExpired.get() || closed.get();
        }
      }
      if (expiredAfterConnect) {
        forceExpiredGeneration(launched);
        if (closed.get()) {
          throw new IllegalStateException("supervisor closed during sidecar startup");
        }
        throw new RecoveryReadyTimeoutException(
            "sidecar connection exceeded the recovery-ready deadline");
      }
      copyLedger.observeSharedMemoryStatus(launched.sharedMemoryStatus());
      transport = new CountingTransport(launched.transport(), copyLedger, generation);
      var sendSequences = new SidecarIpcV1.SequenceCursor(1);
      var receiveSequences = new SidecarIpcV1.SequenceCursor(1);
      var helloCorrelation = randomId();
      transport.write(
          SidecarIpcV1.frame(
                  SidecarIpcV1.MessageType.CLIENT_HELLO,
                  session,
                  generation,
                  helloCorrelation,
                  sendSequences.claim(),
                  SidecarIpcV1.descriptorPayload(
                      SidecarIpcV1.MessageType.CLIENT_HELLO, identity))
              .canonicalBytes());
      var descriptor = SidecarIpcV1.decodeFrame(transport.read());
      require(descriptor.messageType() == SidecarIpcV1.MessageType.SERVER_DESCRIPTOR,
          "handshake did not return SERVER_DESCRIPTOR");
      require(descriptor.sessionId().equals(session), "descriptor frame session mismatch");
      require(descriptor.generation() == generation, "descriptor frame generation mismatch");
      require(descriptor.correlationId().equals(helloCorrelation),
          "descriptor correlation mismatch");
      receiveSequences.accept(descriptor.sequence());
      SidecarIpcV1.requireDescriptor(descriptor.payload(), identity);

      if (!setStateIfOpen(State.RECOVERING)) {
        throw new IllegalStateException("supervisor closed during sidecar startup");
      }
      var openRequestId = randomId().bytes();
      var openFields = new ArrayList<SidecarIpcV1.Field>();
      openFields.add(SidecarIpcV1.u32(16, SidecarIpcV1.INGRESS_QUEUE_REQUESTS));
      openFields.add(SidecarIpcV1.text(17, config.durableDirectory.toString()));
      openFields.add(SidecarIpcV1.bytes(18, config.initialState));
      openFields.add(SidecarIpcV1.sha256Field(19, identity.nestedDescriptorSha256()));
      if (config.votePolicy != null) {
        openFields.add(SidecarIpcV1.bytes(20, config.votePolicy));
      }
      var openPayload = SidecarIpcV1.requestPayload(
          SidecarIpcV1.MessageType.OPEN_REQUEST,
          openRequestId,
          openFields);
      var openCorrelation = randomId();
      transport.write(
          SidecarIpcV1.frame(
                  SidecarIpcV1.MessageType.OPEN_REQUEST,
                  session,
                  generation,
                  openCorrelation,
                  sendSequences.claim(),
                  openPayload)
              .canonicalBytes());
      SidecarIpcV1.Frame open;
      while (true) {
        var candidate = SidecarIpcV1.decodeFrame(transport.read());
        require(candidate.sessionId().equals(session), "OPEN response session mismatch");
        require(candidate.generation() == generation, "OPEN response generation mismatch");
        receiveSequences.accept(candidate.sequence());
        if (candidate.messageType() != SidecarIpcV1.MessageType.SHARED_MEMORY_ACK) {
          open = candidate;
          break;
        }
        require(
            candidate.correlationId().equals(openCorrelation),
            "OPEN shared-memory ACK correlation mismatch");
        require(
            transport.acceptSharedMemoryAck(candidate),
            "OPEN shared-memory ACK did not match its publication");
      }
      SidecarIpcV1.requireResponseMatches(
          open,
          SidecarIpcV1.MessageType.OPEN_REQUEST,
          openPayload.bytes(1),
          openPayload.bytes(2),
          session,
          generation,
          openCorrelation);
      require(open.messageType() == SidecarIpcV1.MessageType.OPEN_RESPONSE,
          "OPEN failed before READY");
      require(
          SidecarIpcV1.AdmissionState.fromCode(open.payload().u8(3))
              == SidecarIpcV1.AdmissionState.ADMITTED_OUTCOME_AVAILABLE,
          "OPEN did not return an admitted native result");
      require(open.payload().u8(19) == 1, "OPEN completed without READY");
      pinOrVerifyWal();
      runtimeInstanceId = open.payload().id128(16);

      LocalSidecarClient readyClient;
      synchronized (readinessGate) {
        synchronized (lifecycleGate) {
          if (closed.get()) {
            throw new IllegalStateException("supervisor closed before sidecar reached READY");
          }
          if (deadlineExpired.get()) {
            throw new RecoveryReadyTimeoutException(
                "sidecar completed OPEN after the recovery-ready deadline");
          }
          readyClient = new LocalSidecarClient(
              transport,
              session,
              generation,
              sendSequences.nextValue(),
              receiveSequences.nextValue(),
              requestIdentityLedger,
              this::onClientFailure,
              copyLedger);
          client = readyClient;
          heartbeatMisses.set(0);
          heartbeatOutstanding.set(false);
          state.set(State.READY);
          ready.set(true);
          deadlineConnection.set(null);
        }
      }
      scheduleHeartbeat();
      return readyClient;
    } catch (Exception error) {
      if (transport != null) {
        try {
          transport.close();
        } catch (IOException ignored) {
          // The failed generation remains fail-closed.
        }
      }
      if (launched != null) {
        if (!stopConnection(launched)) {
          throw new ReplacementTerminationException(
              "failed generation cleanup did not confirm process exit and endpoint closure",
              error);
        }
      }
      if (deadlineExpired.get() && !(error instanceof RecoveryReadyTimeoutException)) {
        throw new RecoveryReadyTimeoutException(
            "sidecar did not reach READY before the recovery deadline", error);
      }
      throw error;
    } finally {
      deadlineConnection.set(null);
      recoveryDeadline.cancel(false);
    }
  }

  private void forceExpiredGeneration(Connection target) {
    try {
      synchronized (target) {
        target.forceTermination();
      }
    } finally {
      quarantineConnection(target);
    }
  }

  private void scheduleHeartbeat() {
    synchronized (lifecycleGate) {
      if (closed.get()) {
        return;
      }
      cancelHeartbeat();
      heartbeatTask = heartbeat.scheduleAtFixedRate(
          this::heartbeatTick,
          timing.heartbeatInterval.toNanos(),
          timing.heartbeatInterval.toNanos(),
          TimeUnit.NANOSECONDS);
    }
  }

  private void heartbeatTick() {
    if (closed.get() || state.get() != State.READY) {
      return;
    }
    var current = client;
    var runtime = runtimeInstanceId;
    if (current == null || runtime == null) {
      return;
    }
    if (!heartbeatOutstanding.compareAndSet(false, true)) {
      recordHeartbeatMiss(current);
      return;
    }
    var request = LocalSidecarClient.healthRequest(healthRequestId(current.generation()), runtime);
    var submission = current.tryEnqueue(request);
    if (!submission.accepted()) {
      heartbeatOutstanding.set(false);
      recordHeartbeatMiss(current);
      return;
    }
    submission.completion().whenComplete((response, error) -> {
      heartbeatOutstanding.set(false);
      if (error != null) {
        recordHeartbeatMiss(current);
        return;
      }
      try {
        require(response.messageType() == SidecarIpcV1.MessageType.HEALTH_RESPONSE,
            "heartbeat returned the wrong response type");
        var payload = response.payload();
        require(payload.u64Bits(17) == current.generation(), "health generation mismatch");
        require(payload.u8(16) == SidecarIpcV1.HealthState.READY.code(),
            "sidecar health is not READY");
        require(payload.u8(20) == 1 && payload.u8(21) == 1,
            "sidecar is READY without durable lock evidence");
        heartbeatMisses.set(0);
      } catch (RuntimeException invalid) {
        current.fence(LocalSidecarClient.FailureKind.PROTOCOL, invalid);
      }
    });
  }

  private static byte[] healthRequestId(long generation) {
    return ("sidecar-health-" + Long.toUnsignedString(generation))
        .getBytes(StandardCharsets.US_ASCII);
  }

  private void recordHeartbeatMiss(LocalSidecarClient current) {
    if (heartbeatMisses.incrementAndGet() >= HEARTBEAT_MISS_LIMIT) {
      current.fence(
          LocalSidecarClient.FailureKind.TRANSPORT,
          new HeartbeatTimeoutException("five consecutive heartbeats were missed"));
    }
  }

  private void onClientFailure(LocalSidecarClient.Failure failure) {
    if (closed.get() || failure.kind() == LocalSidecarClient.FailureKind.LOCAL_CLOSE) {
      return;
    }
    boolean impossibleFutureGeneration;
    synchronized (recoveryGate) {
      if (closed.get()) {
        return;
      }
      var generationOrder = compareFailureToGenerationAuthority(failure);
      if (generationOrder < 0) {
        return;
      }
      impossibleFutureGeneration = generationOrder > 0;
      if (impossibleFutureGeneration) {
        pendingRecoveryFailure = null;
      } else if (failure.kind() != LocalSidecarClient.FailureKind.EXPECTED_CLOSE) {
        if (recoveryActive) {
          if (pendingRecoveryFailure == null
              || Long.compareUnsigned(
                      failure.generation(), pendingRecoveryFailure.generation())
                  > 0) {
            pendingRecoveryFailure = failure;
          }
          return;
        }
        recoveryActive = true;
      }
    }
    if (impossibleFutureGeneration) {
      failClosedImpossibleGeneration(failure);
      return;
    }
    if (failure.kind() == LocalSidecarClient.FailureKind.EXPECTED_CLOSE) {
      Connection terminalConnection;
      synchronized (lifecycleGate) {
        if (!closed.compareAndSet(false, true)) {
          return;
        }
        state.set(State.STOPPING);
        terminalConnection = connection;
      }
      closeDurablePins();
      cancelHeartbeat();
      if (terminalConnection == null) {
        lastFailure = new RecoveryException(
            "validated CLOSE_RESPONSE had no connection whose exit could be confirmed",
            failure.cause());
        state.set(State.UNREADY);
        heartbeat.shutdownNow();
        lifecycle.shutdown();
        return;
      }
      lifecycle.execute(() -> {
        if (stopConnection(terminalConnection)) {
          state.set(State.CLOSED);
          return;
        }
        lastFailure = new RecoveryException(
            "validated CLOSE_RESPONSE did not lead to confirmed process exit and endpoint closure",
            failure.cause());
        state.set(State.UNREADY);
      });
      heartbeat.shutdownNow();
      lifecycle.shutdown();
      return;
    }
    try {
      lifecycle.execute(() -> recover(failure));
    } catch (RuntimeException rejected) {
      synchronized (recoveryGate) {
        recoveryActive = false;
        pendingRecoveryFailure = null;
      }
      if (!closed.get()) {
        lastFailure = rejected;
        setStateIfOpen(State.UNREADY);
      }
    }
  }

  private void recover(LocalSidecarClient.Failure firstFailure) {
    var failure = firstFailure;
    while (true) {
      int generationOrder;
      synchronized (recoveryGate) {
        if (closed.get()) {
          pendingRecoveryFailure = null;
          recoveryActive = false;
          return;
        }
        generationOrder = compareFailureToGenerationAuthority(failure);
        if (generationOrder > 0) {
          pendingRecoveryFailure = null;
        }
      }
      if (generationOrder > 0) {
        failClosedImpossibleGeneration(failure);
      } else if (generationOrder == 0) {
        lastFailure = failure.cause();
        recoverIncident(failure);
      }
      synchronized (recoveryGate) {
        if (closed.get()) {
          pendingRecoveryFailure = null;
          recoveryActive = false;
          return;
        }
        failure = pendingRecoveryFailure;
        pendingRecoveryFailure = null;
        if (failure == null) {
          recoveryActive = false;
          return;
        }
      }
    }
  }

  /** Caller holds recoveryGate. Generation counter includes the currently launching process. */
  private int compareFailureToGenerationAuthority(LocalSidecarClient.Failure failure) {
    return Long.compareUnsigned(failure.generation(), generationCounter.get());
  }

  private void failClosedImpossibleGeneration(LocalSidecarClient.Failure failure) {
    var authority = generationCounter.get();
    var terminal = new RecoveryException(
        "client failure generation "
            + Long.toUnsignedString(failure.generation())
            + " is ahead of launching generation "
            + Long.toUnsignedString(authority),
        failure.cause());
    State previousState;
    LocalSidecarClient currentClient;
    Connection currentConnection;
    synchronized (lifecycleGate) {
      if (!closed.compareAndSet(false, true)) {
        return;
      }
      lastFailure = terminal;
      previousState = state.getAndSet(State.UNREADY);
      currentClient = client;
      currentConnection = connection;
    }
    closeDurablePins();
    synchronized (recoveryGate) {
      pendingRecoveryFailure = null;
    }
    cancelHeartbeat();
    if (currentClient != null) {
      currentClient.close();
    }
    if (currentConnection != null) {
      if (previousState != State.READY && previousState != State.CLOSED) {
        forceExpiredGeneration(currentConnection);
      }
      try {
        lifecycle.execute(() -> stopConnection(currentConnection));
      } catch (RuntimeException rejected) {
        lastFailure = new RecoveryException(
            "impossible-generation fail-close could not schedule process cleanup", rejected);
        forceExpiredGeneration(currentConnection);
      }
    }
    heartbeat.shutdownNow();
    lifecycle.shutdown();
  }

  private void recoverIncident(LocalSidecarClient.Failure failure) {
    cancelHeartbeat();
    if (!setStateIfOpen(State.FENCED)) {
      return;
    }
    var failedConnection = connection;
    var failedClient = client;
    if (failedClient != null && !failedClient.telemetry().closed()) {
      failedClient.close();
    }
    if (failedConnection == null || !stopConnection(failedConnection)) {
      lastFailure = new RecoveryException(
          "failed to confirm process exit and endpoint closure", failure.cause());
      setStateIfOpen(State.UNREADY);
      return;
    }
    for (var attempt = 1; attempt <= RESTART_ATTEMPT_LIMIT && !closed.get(); ++attempt) {
      try {
        sleeper.sleep(timing.restartBackoff.toMillis());
        if (closed.get()) {
          break;
        }
        startGeneration();
        return;
      } catch (InterruptedException interrupted) {
        Thread.currentThread().interrupt();
        lastFailure = interrupted;
        break;
      } catch (ReplacementTerminationException unconfirmedTermination) {
        lastFailure = unconfirmedTermination;
        break;
      } catch (Exception error) {
        lastFailure = error;
      }
    }
    setStateIfOpen(State.UNREADY);
  }

  private boolean setStateIfOpen(State next) {
    synchronized (lifecycleGate) {
      if (closed.get()) {
        return false;
      }
      state.set(next);
      return true;
    }
  }

  private boolean stopConnection(Connection target) {
    state.compareAndSet(State.FENCED, State.STOPPING);
    try {
      synchronized (target) {
        target.requestShutdown();
        var exited = target.awaitExit(timing.gracefulShutdownTimeout);
        if (!exited) {
          target.forceTermination();
          exited = target.awaitExit(timing.gracefulShutdownTimeout);
        }
        if (!exited) {
          quarantineConnection(target);
          return false;
        }
        target.close();
        return target.endpointClosed();
      }
    } catch (InterruptedException interrupted) {
      Thread.currentThread().interrupt();
      lastFailure = interrupted;
      forceAndQuarantine(target, interrupted);
      return false;
    } catch (Exception error) {
      lastFailure = error;
      forceAndQuarantine(target, error);
      return false;
    }
  }

  private void forceAndQuarantine(Connection target, Throwable priorFailure) {
    try {
      synchronized (target) {
        target.forceTermination();
      }
    } catch (RuntimeException forceFailure) {
      priorFailure.addSuppressed(forceFailure);
    } finally {
      quarantineConnection(target);
    }
  }

  private void quarantineConnection(Connection target) {
    try {
      target.transport().close();
    } catch (IOException | RuntimeException ignored) {
      // Closing the byte-stream endpoint is best effort. Mapping ownership is
      // retained until awaitExit positively confirms peer death.
    }
    synchronized (quarantineGate) {
      for (var existing : quarantinedConnections) {
        if (existing == target) {
          return;
        }
      }
      quarantinedConnections.add(target);
    }
    daemon(
            () -> reapQuarantinedConnection(target),
            "delta-sidecar-generation-reaper")
        .start();
  }

  private void reapQuarantinedConnection(Connection target) {
    var cleaned = false;
    try {
      while (!cleaned) {
        try {
          synchronized (target) {
            if (target.awaitExit(timing.gracefulShutdownTimeout)) {
              target.close();
              cleaned = target.endpointClosed();
            }
          }
        } catch (InterruptedException interrupted) {
          throw interrupted;
        } catch (Exception cleanupFailure) {
          // Keep ownership quarantined and retry the exact failed cleanup step. A close failure
          // never confirms endpoint closure or mapping release.
          lastFailure = cleanupFailure;
        }
        if (!cleaned) {
          sleeper.sleep(timing.restartBackoff.toMillis());
        }
      }
    } catch (InterruptedException interrupted) {
      Thread.currentThread().interrupt();
      lastFailure = interrupted;
    } finally {
      if (cleaned) {
        synchronized (quarantineGate) {
          quarantinedConnections.removeIf(candidate -> candidate == target);
        }
      }
    }
  }

  int quarantinedConnectionCount() {
    synchronized (quarantineGate) {
      return quarantinedConnections.size();
    }
  }

  private void cancelHeartbeat() {
    var task = heartbeatTask;
    if (task != null) {
      task.cancel(false);
      heartbeatTask = null;
    }
    heartbeatOutstanding.set(false);
  }

  private long nextGeneration() {
    var next = generationCounter.incrementAndGet();
    if (next == 0) {
      throw new IllegalStateException("generation overflow");
    }
    return next;
  }

  private SidecarIpcV1.Id128 randomId() {
    var bytes = new byte[16];
    do {
      random.nextBytes(bytes);
    } while (allZero(bytes));
    return new SidecarIpcV1.Id128(bytes);
  }

  private static boolean allZero(byte[] value) {
    var aggregate = 0;
    for (var item : value) {
      aggregate |= item;
    }
    return aggregate == 0;
  }

  private static Thread daemon(Runnable operation, String name) {
    var thread = new Thread(operation, name);
    thread.setDaemon(true);
    return thread;
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw new SidecarIpcV1.ProtocolException(message);
    }
  }

  public enum State {
    NEW,
    DESCRIBE_ONLY,
    RECOVERING,
    READY,
    FENCED,
    STOPPING,
    UNREADY,
    CLOSED
  }

  /** Immutable exact identities and OPEN inputs. */
  public static final class Config {
    private final Path durableDirectory;
    private final byte[] initialState;
    private final byte[] executableSha256;
    private final String sidecarBuildId;
    private final byte[] nestedDescriptor;
    private final byte[] votePolicy;

    public Config(
        Path durableDirectory,
        byte[] initialState,
        byte[] executableSha256,
        String sidecarBuildId,
        byte[] nestedDescriptor) {
      this(
          durableDirectory,
          initialState,
          executableSha256,
          sidecarBuildId,
          nestedDescriptor,
          null);
    }

    public Config(
        Path durableDirectory,
        byte[] initialState,
        byte[] executableSha256,
        String sidecarBuildId,
        byte[] nestedDescriptor,
        byte[] votePolicy) {
      this.durableDirectory = Objects.requireNonNull(durableDirectory, "durableDirectory");
      this.initialState = Arrays.copyOf(Objects.requireNonNull(initialState, "initialState"),
          initialState.length);
      require(this.initialState.length <= SidecarIpcV1.MAX_CANONICAL_COMMAND_BYTES,
          "initial state exceeds frozen bound");
      this.executableSha256 = Arrays.copyOf(
          Objects.requireNonNull(executableSha256, "executableSha256"),
          executableSha256.length);
      require(this.executableSha256.length == 32, "executable SHA-256 has the wrong size");
      this.sidecarBuildId = Objects.requireNonNull(sidecarBuildId, "sidecarBuildId");
      this.nestedDescriptor = Arrays.copyOf(
          Objects.requireNonNull(nestedDescriptor, "nestedDescriptor"),
          nestedDescriptor.length);
      SidecarIpcV1.parseNestedDescriptor(this.nestedDescriptor);
      this.votePolicy = votePolicy == null ? null : Arrays.copyOf(votePolicy, votePolicy.length);
      require(
          this.votePolicy == null
              || (this.votePolicy.length > 0
                  && this.votePolicy.length <= SidecarIpcV1.MAX_CANONICAL_VOTE_POLICY_BYTES),
          "vote policy is outside the frozen bound");
      // Exercise the exact descriptor validator, including canonical build text.
      new SidecarIpcV1.DescriptorIdentity(
          new SidecarIpcV1.Id128(new byte[] {1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}),
          1,
          this.executableSha256,
          this.sidecarBuildId,
          this.nestedDescriptor);
    }
  }

  public record LaunchContext(
      SidecarIpcV1.DescriptorIdentity identity,
      Path durableDirectory,
      DurableDirectoryIdentity durableDirectoryIdentity) {
    public LaunchContext {
      Objects.requireNonNull(identity, "identity");
      Objects.requireNonNull(durableDirectory, "durableDirectory");
    }
  }

  /** POSIX directory identity pinned for the whole supervisor lifetime. */
  public record DurableDirectoryIdentity(long device, long inode) {}

  @FunctionalInterface
  public interface GenerationConnector {
    Connection connect(LaunchContext context, Duration readyTimeout) throws Exception;
  }

  public interface Connection {
    LocalSidecarClient.Transport transport();

    boolean isAlive();

    void requestShutdown();

    void forceTermination();

    boolean awaitExit(Duration timeout) throws InterruptedException;

    boolean endpointClosed();

    default String sharedMemoryStatus() {
      return SidecarSharedMemory.atomicAbiSupported()
          ? "AVAILABLE_NOT_CONFIGURED"
          : "DISABLED_ATOMIC_ABI_UNAVAILABLE";
    }

    void close() throws Exception;
  }

  /**
   * Anonymous-pipe connector for the current native executable. ProcessBuilder creates the local
   * binary endpoints; stderr is kept separate from protocol stdout.
   */
  public static final class PipeProcessConnector implements GenerationConnector {
    private final Path executable;
    private final List<String> fixedArguments;

    public PipeProcessConnector(Path executable, List<String> fixedArguments) {
      this.executable = Objects.requireNonNull(executable, "executable").toAbsolutePath();
      this.fixedArguments = List.copyOf(Objects.requireNonNull(fixedArguments, "fixedArguments"));
    }

    @Override
    public Connection connect(LaunchContext context, Duration readyTimeout) throws Exception {
      Objects.requireNonNull(readyTimeout, "readyTimeout");
      require(Files.isRegularFile(executable), "sidecar executable is not a regular file");
      require(Arrays.equals(fileSha256(executable), context.identity().executableSha256()),
          "sidecar executable changed before launch");
      SidecarSharedMemory.GenerationResources sharedMemory = null;
      var sharedMemoryStatus = SidecarSharedMemory.atomicAbiSupported()
          ? "AVAILABLE_NOT_CONFIGURED"
          : "DISABLED_ATOMIC_ABI_UNAVAILABLE";
      if (SidecarSharedMemory.atomicAbiSupported()) {
        SidecarSharedMemory.GenerationResources candidate = null;
        try {
          candidate = SidecarSharedMemory.GenerationResources.create(
              context.identity().generation());
          if (mappedSharedMemoryAtomicAbiSupported(executable, candidate, readyTimeout)) {
            sharedMemory = candidate;
            candidate = null;
            sharedMemoryStatus = "ENABLED_LOCK_FREE_U32_BIG_ENDIAN";
          } else {
            var rejected = candidate;
            candidate = null;
            try {
              rejected.close();
            } catch (IOException cleanupFailure) {
              throw new IllegalStateException(
                  "failed mapped atomic probe resources could not be released",
                  cleanupFailure);
            }
            sharedMemoryStatus = "DISABLED_MAPPED_ATOMIC_ABI_PROBE_FAILED";
          }
        } catch (InterruptedException interrupted) {
          if (candidate != null) {
            try {
              candidate.close();
            } catch (IOException closeFailure) {
              interrupted.addSuppressed(closeFailure);
            }
          }
          throw interrupted;
        } catch (IOException unavailable) {
          if (candidate != null) {
            try {
              candidate.close();
            } catch (IOException closeFailure) {
              unavailable.addSuppressed(closeFailure);
              throw unavailable;
            }
          }
          sharedMemoryStatus = "DISABLED_MAPPED_ATOMIC_ABI_PROBE_FAILED";
        }
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
      if (sharedMemory != null) {
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
      }
      command.addAll(fixedArguments);
      try {
        var process = new ProcessBuilder(command)
            .redirectError(ProcessBuilder.Redirect.DISCARD)
            .start();
        LocalSidecarClient.Transport transport = new LocalSidecarClient.StreamTransport(
            process.getInputStream(), process.getOutputStream());
        if (sharedMemory != null) {
          transport = new SidecarSharedMemory.Transport(
              transport, sharedMemory.javaToNative(), sharedMemory.nativeToJava());
        }
        return new PipeConnection(process, transport, sharedMemory, sharedMemoryStatus);
      } catch (Throwable error) {
        if (sharedMemory != null) {
          try {
            sharedMemory.close();
          } catch (IOException closeFailure) {
            error.addSuppressed(closeFailure);
          }
        }
        throw error;
      }
    }

    public static byte[] executableSha256(Path executable) throws IOException {
      return fileSha256(Objects.requireNonNull(executable, "executable").toAbsolutePath());
    }

    private static byte[] fileSha256(Path path) throws IOException {
      try {
        var digest = MessageDigest.getInstance("SHA-256");
        try (InputStream input = Files.newInputStream(path)) {
          var block = new byte[64 * 1024];
          int count;
          while ((count = input.read(block)) >= 0) {
            if (count > 0) {
              digest.update(block, 0, count);
            }
          }
        }
        return digest.digest();
      } catch (NoSuchAlgorithmException error) {
        throw new IllegalStateException("SHA-256 is unavailable", error);
      }
    }

    static boolean mappedSharedMemoryAtomicAbiSupported(
        Path executable,
        SidecarSharedMemory.GenerationResources resources,
        Duration timeout) throws InterruptedException {
      Objects.requireNonNull(executable, "executable");
      Objects.requireNonNull(resources, "resources");
      Objects.requireNonNull(timeout, "timeout");
      resources.prepareMappedAtomicAbiProbe();
      Process process = null;
      var interrupted = false;
      try {
        try {
          process = new ProcessBuilder(
                  executable.toString(),
                  "--probe-mapped-shm-atomic",
                  resources.javaToNativePath().toString(),
                  "--region",
                  Integer.toUnsignedString(resources.javaToNative().regionId()),
                  "--generation",
                  Long.toUnsignedString(resources.javaToNative().generation()),
                  "--device",
                  Long.toUnsignedString(resources.javaToNativeIdentity().device()),
                  "--inode",
                  Long.toUnsignedString(resources.javaToNativeIdentity().inode()),
                  "--slot",
                  "0")
              .redirectError(ProcessBuilder.Redirect.DISCARD)
              .start();
        } catch (IOException unavailable) {
          return false;
        }
        try {
          if (!process.waitFor(timeout.toNanos(), TimeUnit.NANOSECONDS)) {
            process.destroyForcibly();
            while (true) {
              try {
                process.waitFor();
                break;
              } catch (InterruptedException delayed) {
                interrupted = true;
              }
            }
            return false;
          }
        } catch (InterruptedException delayed) {
          interrupted = true;
          process.destroyForcibly();
          while (true) {
            try {
              process.waitFor();
              break;
            } catch (InterruptedException ignored) {
              interrupted = true;
            }
          }
        }
        if (interrupted) {
          throw new InterruptedException("mapped shared-memory atomic probe interrupted");
        }
        try {
          var output = new String(
              process.getInputStream().readAllBytes(), StandardCharsets.US_ASCII).trim();
          return process.exitValue() == 0
              && output.equals("LOCK_FREE_JAVA_NATIVE_MAP_SHARED_U32_BIG_ENDIAN")
              && resources.completeMappedAtomicAbiProbe();
        } catch (IOException unavailable) {
          return false;
        }
      } finally {
        resources.abortMappedAtomicAbiProbe();
        if (interrupted) {
          Thread.currentThread().interrupt();
        }
      }
    }
  }

  private void verifyDurableBindingsForLaunch() {
    if (durableDirectoryPin != null) {
      durableDirectoryPin.verifyForLaunch();
    }
  }

  private void pinOrVerifyWal() {
    if (durableDirectoryPin != null) {
      durableDirectoryPin.pinOrVerifyWal();
    }
  }

  private void closeDurablePins() {
    if (durableDirectoryPin == null) {
      return;
    }
    try {
      durableDirectoryPin.close();
    } catch (IOException closeFailure) {
      var failure = new IllegalStateException("cannot release durable pathname pins", closeFailure);
      var prior = lastFailure;
      if (prior != null) {
        prior.addSuppressed(failure);
      } else {
        lastFailure = failure;
      }
    }
  }

  private static final class DurableDirectoryPin implements AutoCloseable {
    private static final Path WAL_PATH = Path.of("runtime.wal");
    private static final Set<java.nio.file.OpenOption> WAL_OPEN_OPTIONS =
        Set.of(StandardOpenOption.READ, LinkOption.NOFOLLOW_LINKS);

    private final Path pathname;
    private final SecureDirectoryStream<Path> directoryStream;
    private final PosixFileIdentity pinnedIdentity;
    private DurableWalPin walPin;
    private boolean closed;

    private DurableDirectoryPin(
        Path pathname,
        SecureDirectoryStream<Path> directoryStream,
        PosixFileIdentity pinnedIdentity) {
      this.pathname = pathname;
      this.directoryStream = directoryStream;
      this.pinnedIdentity = pinnedIdentity;
    }

    private static DurableDirectoryPin open(Path directory) {
      var normalized = Objects.requireNonNull(directory, "directory").toAbsolutePath().normalize();
      if (isWindows()) {
        return null;
      }
      DirectoryStream<Path> opened = null;
      try {
        opened = Files.newDirectoryStream(normalized);
        require(opened instanceof SecureDirectoryStream<?>,
            "durable directory provider does not support retained secure handles");
        @SuppressWarnings("unchecked")
        var secure = (SecureDirectoryStream<Path>) opened;
        var pinned = readPinnedDirectoryAttributes(secure);
        var pathnameIdentity = readUnixIdentity(normalized, PosixFileType.DIRECTORY);
        require(pinned.fileKey() != null
                && pinned.fileKey().equals(pathnameIdentity.fileKey()),
            "durable directory handle/pathname binding changed while pinning");
        return new DurableDirectoryPin(normalized, secure, pathnameIdentity);
      } catch (IOException | RuntimeException error) {
        if (opened != null) {
          try {
            opened.close();
          } catch (IOException closeFailure) {
            error.addSuppressed(closeFailure);
          }
        }
        throw new SidecarIpcV1.ProtocolException(
            "cannot pin durable directory identity", error);
      }
    }

    private synchronized DurableDirectoryIdentity identity() {
      ensureOpen();
      return new DurableDirectoryIdentity(pinnedIdentity.device(), pinnedIdentity.inode());
    }

    private synchronized void verifyForLaunch() {
      ensureOpen();
      verifyDirectoryPathname();
      if (walPin != null) {
        verifyWalPathname();
      }
    }

    private synchronized void pinOrVerifyWal() {
      ensureOpen();
      verifyDirectoryPathname();
      if (walPin != null) {
        verifyWalPathname();
        return;
      }
      SeekableByteChannel opened = null;
      try {
        opened = directoryStream.newByteChannel(WAL_PATH, WAL_OPEN_OPTIONS);
        // Public Java NIO has no fstat/fileKey operation on an opened byte channel. The
        // documented trusted-supervisor prerequisite excludes same-principal mutation in this
        // first-pin window; retaining the channel then prevents inode-reuse ABA across restarts.
        var pathnameIdentity = readUnixIdentity(pathname.resolve(WAL_PATH), PosixFileType.REGULAR);
        walPin = new DurableWalPin(opened, pathnameIdentity);
      } catch (IOException | RuntimeException error) {
        if (opened != null) {
          try {
            opened.close();
          } catch (IOException closeFailure) {
            error.addSuppressed(closeFailure);
          }
        }
        throw new SidecarIpcV1.ProtocolException("cannot pin runtime.wal identity", error);
      }
    }

    private void verifyDirectoryPathname() {
      try {
        var pinned = readPinnedDirectoryAttributes(directoryStream);
        require(pinned.fileKey() != null && pinned.fileKey().equals(pinnedIdentity.fileKey()),
            "retained durable directory identity changed");
        var current = readUnixIdentity(pathname, PosixFileType.DIRECTORY);
        require(pinnedIdentity.equals(current),
            "durable directory pathname binding changed");
      } catch (IOException error) {
        throw new SidecarIpcV1.ProtocolException(
            "cannot verify durable directory pathname binding", error);
      }
    }

    private void verifyWalPathname() {
      require(walPin != null && walPin.channel().isOpen(),
          "retained runtime.wal handle is closed");
      try {
        var current = readUnixIdentity(pathname.resolve(WAL_PATH), PosixFileType.REGULAR);
        require(walPin.identity().equals(current), "runtime.wal pathname binding changed");
      } catch (IOException error) {
        throw new SidecarIpcV1.ProtocolException(
            "cannot verify runtime.wal pathname binding", error);
      }
    }

    private static BasicFileAttributes readPinnedDirectoryAttributes(
        SecureDirectoryStream<Path> directory) throws IOException {
      var view = directory.getFileAttributeView(BasicFileAttributeView.class);
      require(view != null, "durable directory handle has no basic attribute view");
      var attributes = view.readAttributes();
      require(attributes.isDirectory() && !attributes.isSymbolicLink(),
          "retained durable directory handle is not a directory");
      return attributes;
    }

    private static PosixFileIdentity readUnixIdentity(Path path, PosixFileType expected)
        throws IOException {
      Map<String, Object> attributes =
          Files.readAttributes(path, "unix:*", LinkOption.NOFOLLOW_LINKS);
      require(!Boolean.TRUE.equals(attributes.get("isSymbolicLink")),
          expected.description + " is a symbolic link");
      require(expected.matches(attributes), expected.description + " has the wrong file type");
      var fileKey = attributes.get("fileKey");
      var device = attributes.get("dev");
      var inode = attributes.get("ino");
      require(fileKey != null && device instanceof Number && inode instanceof Number,
          expected.description + " has no stable Unix identity");
      return new PosixFileIdentity(
          fileKey, ((Number) device).longValue(), ((Number) inode).longValue());
    }

    private void ensureOpen() {
      require(!closed, "durable pathname pins are closed");
    }

    @Override
    public synchronized void close() throws IOException {
      if (closed) {
        return;
      }
      closed = true;
      IOException failure = null;
      if (walPin != null) {
        try {
          walPin.channel().close();
        } catch (IOException error) {
          failure = error;
        }
      }
      try {
        directoryStream.close();
      } catch (IOException error) {
        if (failure == null) {
          failure = error;
        } else {
          failure.addSuppressed(error);
        }
      }
      if (failure != null) {
        throw failure;
      }
    }
  }

  private enum PosixFileType {
    DIRECTORY("durable directory") {
      @Override
      boolean matches(Map<String, Object> attributes) {
        return Boolean.TRUE.equals(attributes.get("isDirectory"));
      }
    },
    REGULAR("runtime.wal") {
      @Override
      boolean matches(Map<String, Object> attributes) {
        return Boolean.TRUE.equals(attributes.get("isRegularFile"));
      }
    };

    private final String description;

    PosixFileType(String description) {
      this.description = description;
    }

    abstract boolean matches(Map<String, Object> attributes);
  }

  private record PosixFileIdentity(Object fileKey, long device, long inode) {
    private PosixFileIdentity {
      Objects.requireNonNull(fileKey, "fileKey");
    }
  }

  private record DurableWalPin(SeekableByteChannel channel, PosixFileIdentity identity) {
    private DurableWalPin {
      Objects.requireNonNull(channel, "channel");
      Objects.requireNonNull(identity, "identity");
    }
  }

  private static boolean isWindows() {
    return System.getProperty("os.name", "").toLowerCase(java.util.Locale.ROOT)
        .contains("win");
  }

  public record Telemetry(
      State state,
      long generation,
      int heartbeatMisses,
      long inlineIngressBytes,
      long inlineEgressBytes,
      long sharedMemoryIngressBytes,
      long sharedMemoryEgressBytes,
      long stagingFallbackIngressBytes,
      long stagingFallbackEgressBytes,
      long zeroCopyEligibleCount,
      long zeroCopyHitCount,
      String sharedMemoryStatus,
      OperationCopy maxSubmitStagingFallback,
      LocalSidecarClient.Telemetry client,
      String lastFailureType) {}

  /** Exact carrier/copy evidence for one correlation-bound completed SUBMIT operation. */
  public record OperationCopy(
      SidecarIpcV1.MessageType requestType,
      long generation,
      String correlationId,
      long inlineIngressBytes,
      long inlineEgressBytes,
      long sharedMemoryIngressBytes,
      long sharedMemoryEgressBytes,
      long stagingFallbackIngressBytes,
      long stagingFallbackEgressBytes,
      long stagingFallbackTotalBytes,
      long zeroCopyEligibleCount,
      long zeroCopyHitCount) {
    public OperationCopy {
      Objects.requireNonNull(requestType, "requestType");
      Objects.requireNonNull(correlationId, "correlationId");
      require(requestType == SidecarIpcV1.MessageType.SUBMIT_REQUEST,
          "measured operation is not SUBMIT_REQUEST");
      require(generation != 0, "measured operation generation is zero");
      require(correlationId.length() == 32, "measured correlation ID is not ID128 hex");
      require(
          inlineIngressBytes >= 0
              && inlineEgressBytes >= 0
              && sharedMemoryIngressBytes >= 0
              && sharedMemoryEgressBytes >= 0
              && stagingFallbackIngressBytes >= 0
              && stagingFallbackEgressBytes >= 0,
          "measured copy bytes are negative");
      require(
          (inlineIngressBytes == 0) != (sharedMemoryIngressBytes == 0)
              && (inlineEgressBytes == 0) != (sharedMemoryEgressBytes == 0),
          "measured operation does not identify exactly one carrier per direction");
      require(
          Math.addExact(stagingFallbackIngressBytes, stagingFallbackEgressBytes)
              == stagingFallbackTotalBytes,
          "measured copy-byte sum is inconsistent");
      require(
          zeroCopyEligibleCount == 1 && zeroCopyHitCount == 0,
          "measured SUBMIT zero-copy evidence is inconsistent");
    }
  }

  record Timing(
      Duration heartbeatInterval,
      Duration gracefulShutdownTimeout,
      Duration recoveryReadyTimeout,
      Duration restartBackoff) {
    Timing {
      positive(heartbeatInterval, "heartbeat interval");
      positive(gracefulShutdownTimeout, "graceful shutdown timeout");
      positive(recoveryReadyTimeout, "recovery-ready timeout");
      positive(restartBackoff, "restart backoff");
    }

    static Timing frozen() {
      return new Timing(
          HEARTBEAT_INTERVAL,
          GRACEFUL_SHUTDOWN_TIMEOUT,
          RECOVERY_READY_TIMEOUT,
          RESTART_BACKOFF);
    }

    private static void positive(Duration value, String label) {
      Objects.requireNonNull(value, label);
      require(!value.isNegative() && !value.isZero(), label + " must be positive");
    }
  }

  @FunctionalInterface
  interface Sleeper {
    void sleep(long milliseconds) throws InterruptedException;
  }

  public static final class HeartbeatTimeoutException extends IllegalStateException {
    private static final long serialVersionUID = 1L;

    HeartbeatTimeoutException(String message) {
      super(message);
    }
  }

  public static final class RecoveryException extends IllegalStateException {
    private static final long serialVersionUID = 1L;

    RecoveryException(String message, Throwable cause) {
      super(message, cause);
    }
  }

  public static final class ReplacementTerminationException extends IllegalStateException {
    private static final long serialVersionUID = 1L;

    ReplacementTerminationException(String message, Throwable cause) {
      super(message, cause);
    }
  }

  public static final class RecoveryReadyTimeoutException extends IllegalStateException {
    private static final long serialVersionUID = 1L;

    RecoveryReadyTimeoutException(String message) {
      super(message);
    }

    RecoveryReadyTimeoutException(String message, Throwable cause) {
      super(message, cause);
    }
  }

  static final class CountingTransport implements LocalSidecarClient.Transport {
    private final LocalSidecarClient.Transport delegate;
    private final CopyLedger ledger;
    private final long generation;
    private final Object observationGate = new Object();
    private boolean transportClosed;

    CountingTransport(
        LocalSidecarClient.Transport delegate, CopyLedger ledger, long generation) {
      this.delegate = delegate;
      this.ledger = ledger;
      require(generation != 0, "counting transport generation is zero");
      this.generation = generation;
      if (delegate.sharedMemoryConfigured()) {
        ledger.sharedMemoryConfigured.set(true);
      }
    }

    @Override
    public void write(byte[] canonicalFrame) throws IOException {
      synchronized (observationGate) {
        if (transportClosed) {
          throw new IOException("counting transport is closed");
        }
        delegate.write(canonicalFrame);
        var shared = delegate.lastWriteSharedMemory();
        ledger.recordIngress(canonicalFrame, shared);
      }
    }

    @Override
    public byte[] read() throws IOException {
      var result = delegate.read();
      if (!SidecarSharedMemory.isSharedMemoryCarrier(result)) {
        synchronized (observationGate) {
          if (!transportClosed) {
            ledger.recordEgress(result, false);
          }
        }
      }
      return result;
    }

    @Override
    public byte[] resolveSharedMemoryCarrier(byte[] carrier) throws IOException {
      var resolved = delegate.resolveSharedMemoryCarrier(carrier);
      synchronized (observationGate) {
        if (!transportClosed) {
          ledger.recordEgress(resolved, true);
        }
      }
      return resolved;
    }

    @Override
    public boolean acceptSharedMemoryAck(SidecarIpcV1.Frame notification)
        throws IOException {
      return delegate.acceptSharedMemoryAck(notification);
    }

    @Override
    public boolean isOpen() {
      return delegate.isOpen();
    }

    @Override
    public void close() throws IOException {
      IOException failure = null;
      try {
        delegate.close();
      } catch (IOException error) {
        failure = error;
      } finally {
        synchronized (observationGate) {
          transportClosed = true;
          ledger.clearGeneration(generation);
        }
      }
      if (failure != null) {
        throw failure;
      }
    }
  }

  static final class CopyLedger
      implements LocalSidecarClient.ValidatedResponseListener {
    private final AtomicLong inlineIngressBytes = new AtomicLong();
    private final AtomicLong inlineEgressBytes = new AtomicLong();
    private final AtomicLong sharedMemoryIngressBytes = new AtomicLong();
    private final AtomicLong sharedMemoryEgressBytes = new AtomicLong();
    private final AtomicLong stagingFallbackIngressBytes = new AtomicLong();
    private final AtomicLong stagingFallbackEgressBytes = new AtomicLong();
    private final AtomicLong zeroCopyEligibleCount = new AtomicLong();
    private final AtomicLong zeroCopyHitCount = new AtomicLong();
    private final AtomicBoolean sharedMemoryConfigured = new AtomicBoolean();
    private final AtomicReference<String> sharedMemoryCapabilityStatus =
        new AtomicReference<>(
            SidecarSharedMemory.atomicAbiSupported()
                ? "AVAILABLE_NOT_CONFIGURED"
                : "DISABLED_ATOMIC_ABI_UNAVAILABLE");
    private final Map<CopyKey, CarrierObservation> ingressObservations =
        new java.util.LinkedHashMap<>();
    private final Map<CopyKey, CarrierObservation> egressObservations =
        new java.util.LinkedHashMap<>();
    private OperationCopy maxSubmitStagingFallback;

    private synchronized void recordIngress(byte[] frame, boolean sharedMemory) {
      var logicalPayloadBytes = logicalPayloadLength(frame);
      var type = messageType(frame);
      var eligible = type.sharedMemoryEligible();
      if (sharedMemory) {
        addExact(sharedMemoryIngressBytes, logicalPayloadBytes);
      } else {
        addExact(inlineIngressBytes, frame.length);
      }
      if (eligible) {
        zeroCopyEligibleCount.incrementAndGet();
        // The current SHM carrier copies logical bytes into and out of the
        // mapped region.  Count mapped traffic separately, but do not report a
        // zero-copy hit until a genuinely borrowed-buffer path exists.
        if (!sharedMemory) {
          addExact(stagingFallbackIngressBytes, logicalPayloadBytes);
        }
      }
      if (type == SidecarIpcV1.MessageType.SUBMIT_REQUEST) {
        putBounded(
            ingressObservations,
            copyKey(frame),
            new CarrierObservation(sharedMemory, frame.length, logicalPayloadBytes));
      }
    }

    private synchronized void recordEgress(byte[] frame, boolean sharedMemory) {
      var logicalPayloadBytes = logicalPayloadLength(frame);
      var type = messageType(frame);
      var eligible = type.sharedMemoryEligible();
      if (sharedMemory) {
        addExact(sharedMemoryEgressBytes, logicalPayloadBytes);
      } else {
        addExact(inlineEgressBytes, frame.length);
      }
      if (eligible) {
        zeroCopyEligibleCount.incrementAndGet();
        // Native-to-Java carrier resolution also copies the logical payload.
        if (!sharedMemory) {
          addExact(stagingFallbackEgressBytes, logicalPayloadBytes);
        }
      }
      if (type == SidecarIpcV1.MessageType.SUBMIT_RESPONSE
          || type == SidecarIpcV1.MessageType.ERROR_RESPONSE) {
        putBounded(
            egressObservations,
            copyKey(frame),
            new CarrierObservation(sharedMemory, frame.length, logicalPayloadBytes));
      }
    }

    @Override
    public synchronized Object onValidated(
        LocalSidecarClient.PreparedRequest request, SidecarIpcV1.Frame response) {
      var key = new CopyKey(response.generation(), response.correlationId().hex());
      var ingress = ingressObservations.remove(key);
      var egress = egressObservations.remove(key);
      if (request.type() != SidecarIpcV1.MessageType.SUBMIT_REQUEST) {
        return null;
      }
      require(ingress != null, "validated SUBMIT lacks its exact ingress carrier observation");
      require(egress != null, "validated SUBMIT lacks its exact egress carrier observation");
      require(
          ingress.logicalPayloadBytes() == request.canonicalPayloadLength()
              && egress.logicalPayloadBytes() == response.payloadLength(),
          "validated SUBMIT copy observation length mismatch");
      var ingressFallback = ingress.sharedMemory() ? 0L : ingress.logicalPayloadBytes();
      var egressEligible = response.messageType().sharedMemoryEligible();
      var egressFallback = egressEligible && !egress.sharedMemory()
          ? egress.logicalPayloadBytes()
          : 0L;
      var total = Math.addExact(ingressFallback, egressFallback);
      var measured = new OperationCopy(
          SidecarIpcV1.MessageType.SUBMIT_REQUEST,
          response.generation(),
          response.correlationId().hex(),
          ingress.sharedMemory() ? 0L : ingress.frameBytes(),
          egress.sharedMemory() ? 0L : egress.frameBytes(),
          ingress.sharedMemory() ? ingress.logicalPayloadBytes() : 0L,
          egress.sharedMemory() ? egress.logicalPayloadBytes() : 0L,
          ingressFallback,
          egressFallback,
          total,
          1,
          0);
      if (maxSubmitStagingFallback == null
          || total > maxSubmitStagingFallback.stagingFallbackTotalBytes()) {
        maxSubmitStagingFallback = measured;
      }
      return measured;
    }

    @Override
    public synchronized void onResponseDiscarded(
        long responseGeneration, SidecarIpcV1.Id128 correlationId) {
      egressObservations.remove(new CopyKey(responseGeneration, correlationId.hex()));
    }

    @Override
    public synchronized void onTransportClosed(long closedGeneration) {
      clearGeneration(closedGeneration);
    }

    private synchronized void clearGeneration(long closedGeneration) {
      ingressObservations.keySet().removeIf(key -> key.generation() == closedGeneration);
      egressObservations.keySet().removeIf(key -> key.generation() == closedGeneration);
    }

    private synchronized void clearAllTransient() {
      ingressObservations.clear();
      egressObservations.clear();
    }

    private synchronized OperationCopy maxSubmitStagingFallback() {
      return maxSubmitStagingFallback;
    }

    synchronized int transientObservationCount() {
      return Math.addExact(ingressObservations.size(), egressObservations.size());
    }

    private void observeSharedMemoryStatus(String status) {
      sharedMemoryCapabilityStatus.set(Objects.requireNonNull(status, "status"));
    }

    private static long logicalPayloadLength(byte[] frame) {
      require(frame.length >= SidecarIpcV1.HEADER_BYTES, "telemetry saw a truncated frame");
      var header = java.nio.ByteBuffer.wrap(frame).order(java.nio.ByteOrder.BIG_ENDIAN);
      require(Short.toUnsignedInt(header.getShort(12)) == SidecarIpcV1.HEADER_BYTES,
          "telemetry saw a non-v1 header length");
      var flags = header.getInt(16);
      require((flags & SidecarIpcV1.FLAG_PAYLOAD_INLINE) != 0
              && (flags & SidecarIpcV1.FLAG_PAYLOAD_SHARED_MEMORY) == 0,
          "telemetry requires a resolved canonical inline frame");
      var length = header.getLong(68);
      require(length >= 0 && length <= SidecarIpcV1.MAX_LOGICAL_PAYLOAD_BYTES,
          "telemetry payload length is outside bounds");
      require(frame.length == SidecarIpcV1.HEADER_BYTES + length,
          "telemetry frame length differs from its logical payload length");
      return length;
    }

    private static SidecarIpcV1.MessageType messageType(byte[] frame) {
      return SidecarIpcV1.MessageType.fromCode(
          Short.toUnsignedInt(
              java.nio.ByteBuffer.wrap(frame)
                  .order(java.nio.ByteOrder.BIG_ENDIAN)
                  .getShort(14)));
    }

    private static CopyKey copyKey(byte[] frame) {
      var header = java.nio.ByteBuffer.wrap(frame).order(java.nio.ByteOrder.BIG_ENDIAN);
      var generation = header.getLong(36);
      var correlation = java.util.HexFormat.of().formatHex(
          java.util.Arrays.copyOfRange(frame, 44, 60));
      return new CopyKey(generation, correlation);
    }

    private static <V> void putBounded(Map<CopyKey, V> target, CopyKey key, V value) {
      require(
          target.containsKey(key)
              || target.size() < SidecarIpcV1.IN_FLIGHT_CORRELATIONS,
          "copy observation ledger reached the frozen in-flight bound");
      target.put(key, value);
      require(
          target.size() <= SidecarIpcV1.IN_FLIGHT_CORRELATIONS,
          "copy observation ledger exceeded the frozen in-flight bound");
    }

    private String sharedMemoryStatus() {
      if (sharedMemoryConfigured.get()) {
        return "ENABLED_LOCK_FREE_U32_BIG_ENDIAN";
      }
      return sharedMemoryCapabilityStatus.get();
    }

    private static void addExact(AtomicLong counter, long amount) {
      counter.updateAndGet(current -> Math.addExact(current, amount));
    }

    private record CopyKey(long generation, String correlationId) {
      private CopyKey {
        require(generation != 0, "copy observation generation is zero");
        Objects.requireNonNull(correlationId, "correlationId");
        require(correlationId.length() == 32, "copy observation correlation is not ID128 hex");
      }
    }

    private record CarrierObservation(
        boolean sharedMemory, long frameBytes, long logicalPayloadBytes) {
      private CarrierObservation {
        require(
            frameBytes >= SidecarIpcV1.HEADER_BYTES && logicalPayloadBytes > 0,
            "copy carrier observation is empty or truncated");
        require(
            frameBytes == Math.addExact(SidecarIpcV1.HEADER_BYTES, logicalPayloadBytes),
            "copy carrier observation length mismatch");
      }
    }
  }

  private static final class PipeConnection implements Connection {
    private final Process process;
    private final LocalSidecarClient.Transport transport;
    private final SidecarSharedMemory.GenerationResources sharedMemory;
    private final String sharedMemoryStatus;
    private final SidecarSharedMemory.CleanupProgress cleanup =
        new SidecarSharedMemory.CleanupProgress();

    private PipeConnection(
        Process process,
        LocalSidecarClient.Transport transport,
        SidecarSharedMemory.GenerationResources sharedMemory,
        String sharedMemoryStatus) {
      this.process = process;
      this.transport = transport;
      this.sharedMemory = sharedMemory;
      this.sharedMemoryStatus = Objects.requireNonNull(sharedMemoryStatus, "sharedMemoryStatus");
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
      process.destroy();
    }

    @Override
    public void forceTermination() {
      process.destroyForcibly();
    }

    @Override
    public boolean awaitExit(Duration timeout) throws InterruptedException {
      return process.waitFor(timeout.toNanos(), TimeUnit.NANOSECONDS);
    }

    @Override
    public boolean endpointClosed() {
      return cleanup.confirmed();
    }

    @Override
    public String sharedMemoryStatus() {
      return sharedMemoryStatus;
    }

    @Override
    public void close() throws IOException {
      cleanup.close(this::closeTransport, this::closeSharedMemory);
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
        throw new IOException("sidecar byte-stream endpoint close was not confirmed");
      }
    }

    private void closeSharedMemory() throws IOException {
      if (sharedMemory != null) {
        sharedMemory.close();
      }
    }
  }
}
