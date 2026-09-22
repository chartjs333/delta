package io.deltareduce.node.sidecar;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
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
  private final SecureRandom random = new SecureRandom();
  private final AtomicLong generationCounter = new AtomicLong();
  private final AtomicReference<State> state = new AtomicReference<>(State.NEW);
  private final AtomicBoolean closed = new AtomicBoolean();
  private final AtomicInteger heartbeatMisses = new AtomicInteger();
  private final AtomicBoolean heartbeatOutstanding = new AtomicBoolean();
  private final Object lifecycleGate = new Object();
  private final Object recoveryGate = new Object();
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
        0,
        0,
        copyLedger.stagingFallbackIngressBytes.get(),
        copyLedger.stagingFallbackEgressBytes.get(),
        0,
        0,
        "DISABLED_UNREACHABLE_COPY_FALLBACK",
        copyLedger.maxSubmitStagingFallback(),
        current == null ? null : current.telemetry(),
        lastFailure == null ? "" : lastFailure.getClass().getSimpleName());
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
    cancelHeartbeat();
    if (currentClient != null) {
      currentClient.close();
    }
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
      launched = connector.connect(
          new LaunchContext(identity, config.durableDirectory), timing.recoveryReadyTimeout);
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
      transport = new CountingTransport(launched.transport(), copyLedger);
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
      var openPayload = SidecarIpcV1.requestPayload(
          SidecarIpcV1.MessageType.OPEN_REQUEST,
          openRequestId,
          List.of(
              SidecarIpcV1.u32(16, SidecarIpcV1.INGRESS_QUEUE_REQUESTS),
              SidecarIpcV1.text(17, config.durableDirectory.toString()),
              SidecarIpcV1.bytes(18, config.initialState),
              SidecarIpcV1.sha256Field(19, identity.nestedDescriptorSha256())));
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
      var open = SidecarIpcV1.decodeFrame(transport.read());
      receiveSequences.accept(open.sequence());
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
              copyLedger::recordValidatedResponse);
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

  private static void forceExpiredGeneration(Connection target) {
    try {
      target.forceTermination();
    } finally {
      try {
        target.close();
      } catch (Exception ignored) {
        // The generation is already expired and remains fail-closed.
      }
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
      target.requestShutdown();
      var exited = target.awaitExit(timing.gracefulShutdownTimeout);
      if (!exited) {
        target.forceTermination();
        exited = target.awaitExit(timing.gracefulShutdownTimeout);
      }
      target.close();
      return exited && target.endpointClosed();
    } catch (InterruptedException interrupted) {
      Thread.currentThread().interrupt();
      lastFailure = interrupted;
      return false;
    } catch (Exception error) {
      lastFailure = error;
      return false;
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

    public Config(
        Path durableDirectory,
        byte[] initialState,
        byte[] executableSha256,
        String sidecarBuildId,
        byte[] nestedDescriptor) {
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
      SidecarIpcV1.DescriptorIdentity identity, Path durableDirectory) {
    public LaunchContext {
      Objects.requireNonNull(identity, "identity");
      Objects.requireNonNull(durableDirectory, "durableDirectory");
    }
  }

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
      var command = new ArrayList<String>();
      command.add(executable.toString());
      command.add("--session");
      command.add(context.identity().sessionId().hex());
      command.add("--generation");
      command.add(Long.toUnsignedString(context.identity().generation()));
      command.addAll(fixedArguments);
      var process = new ProcessBuilder(command)
          .redirectError(ProcessBuilder.Redirect.DISCARD)
          .start();
      var transport = new LocalSidecarClient.StreamTransport(
          process.getInputStream(), process.getOutputStream());
      return new PipeConnection(process, transport);
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

  /** Checked ingress+egress bounded-copy bytes for the largest completed SUBMIT operation. */
  public record OperationCopy(
      SidecarIpcV1.MessageType requestType,
      long generation,
      String correlationId,
      long stagingFallbackIngressBytes,
      long stagingFallbackEgressBytes,
      long stagingFallbackTotalBytes) {
    public OperationCopy {
      Objects.requireNonNull(requestType, "requestType");
      Objects.requireNonNull(correlationId, "correlationId");
      require(requestType == SidecarIpcV1.MessageType.SUBMIT_REQUEST,
          "measured operation is not SUBMIT_REQUEST");
      require(generation != 0, "measured operation generation is zero");
      require(correlationId.length() == 32, "measured correlation ID is not ID128 hex");
      require(stagingFallbackIngressBytes >= 0 && stagingFallbackEgressBytes >= 0,
          "measured copy bytes are negative");
      require(
          Math.addExact(stagingFallbackIngressBytes, stagingFallbackEgressBytes)
              == stagingFallbackTotalBytes,
          "measured copy-byte sum is inconsistent");
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

  private static final class CountingTransport implements LocalSidecarClient.Transport {
    private final LocalSidecarClient.Transport delegate;
    private final CopyLedger ledger;

    private CountingTransport(LocalSidecarClient.Transport delegate, CopyLedger ledger) {
      this.delegate = delegate;
      this.ledger = ledger;
    }

    @Override
    public void write(byte[] canonicalFrame) throws IOException {
      delegate.write(canonicalFrame);
      ledger.recordIngress(canonicalFrame);
    }

    @Override
    public byte[] read() throws IOException {
      var result = delegate.read();
      ledger.recordEgress(result);
      return result;
    }

    @Override
    public boolean isOpen() {
      return delegate.isOpen();
    }

    @Override
    public void close() throws IOException {
      delegate.close();
    }
  }

  private static final class CopyLedger {
    private final AtomicLong inlineIngressBytes = new AtomicLong();
    private final AtomicLong inlineEgressBytes = new AtomicLong();
    private final AtomicLong stagingFallbackIngressBytes = new AtomicLong();
    private final AtomicLong stagingFallbackEgressBytes = new AtomicLong();
    private OperationCopy maxSubmitStagingFallback;

    private void recordIngress(byte[] frame) {
      var logicalPayloadBytes = logicalPayloadLength(frame);
      addExact(inlineIngressBytes, frame.length);
      addExact(stagingFallbackIngressBytes, logicalPayloadBytes);
    }

    private void recordEgress(byte[] frame) {
      var logicalPayloadBytes = logicalPayloadLength(frame);
      addExact(inlineEgressBytes, frame.length);
      addExact(stagingFallbackEgressBytes, logicalPayloadBytes);
    }

    private synchronized void recordValidatedResponse(
        LocalSidecarClient.PreparedRequest request, SidecarIpcV1.Frame response) {
      if (request.type() != SidecarIpcV1.MessageType.SUBMIT_REQUEST) {
        return;
      }
      var ingress = request.canonicalPayloadLength();
      var egress = response.payloadLength();
      var total = Math.addExact(ingress, egress);
      var measured = new OperationCopy(
          SidecarIpcV1.MessageType.SUBMIT_REQUEST,
          response.generation(),
          response.correlationId().hex(),
          ingress,
          egress,
          total);
      if (maxSubmitStagingFallback == null
          || total > maxSubmitStagingFallback.stagingFallbackTotalBytes()) {
        maxSubmitStagingFallback = measured;
      }
    }

    private synchronized OperationCopy maxSubmitStagingFallback() {
      return maxSubmitStagingFallback;
    }

    private static long logicalPayloadLength(byte[] frame) {
      require(frame.length >= SidecarIpcV1.HEADER_BYTES, "telemetry saw a truncated frame");
      var header = java.nio.ByteBuffer.wrap(frame).order(java.nio.ByteOrder.BIG_ENDIAN);
      require(Short.toUnsignedInt(header.getShort(12)) == SidecarIpcV1.HEADER_BYTES,
          "telemetry saw a non-v1 header length");
      var flags = header.getInt(16);
      require((flags & SidecarIpcV1.FLAG_PAYLOAD_INLINE) != 0
              && (flags & SidecarIpcV1.FLAG_PAYLOAD_SHARED_MEMORY) == 0,
          "copy-only telemetry saw a shared-memory carrier");
      var length = header.getLong(68);
      require(length >= 0 && length <= SidecarIpcV1.MAX_LOGICAL_PAYLOAD_BYTES,
          "telemetry payload length is outside bounds");
      require(frame.length == SidecarIpcV1.HEADER_BYTES + length,
          "telemetry frame length differs from its logical payload length");
      return length;
    }

    private static void addExact(AtomicLong counter, long amount) {
      counter.updateAndGet(current -> Math.addExact(current, amount));
    }
  }

  private static final class PipeConnection implements Connection {
    private final Process process;
    private final LocalSidecarClient.Transport transport;
    private final AtomicBoolean endpointClosed = new AtomicBoolean();

    private PipeConnection(Process process, LocalSidecarClient.Transport transport) {
      this.process = process;
      this.transport = transport;
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
      return endpointClosed.get();
    }

    @Override
    public void close() throws IOException {
      transport.close();
      endpointClosed.set(true);
    }
  }
}
