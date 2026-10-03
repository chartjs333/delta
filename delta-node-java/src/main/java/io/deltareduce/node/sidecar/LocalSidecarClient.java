package io.deltareduce.node.sidecar;

import java.io.EOFException;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.SocketChannel;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.Semaphore;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Bounded asynchronous client for one ready isolated-sidecar generation.
 *
 * <p>This class transports opaque canonical commands and native-authored results. It never owns a
 * WAL, reconstructs a state transition, interprets a timer token, or manufactures a consensus
 * outcome.
 */
public final class LocalSidecarClient implements AutoCloseable {
  public static final Duration REQUEST_WATCHDOG_TIMEOUT = Duration.ofSeconds(30);
  private static final byte[] SUBMIT_RECOVERY_PROOF_DOMAIN =
      "DELTAIPCSUBMITRECOVERY1".getBytes(StandardCharsets.US_ASCII);
  private static final byte[] VOTE_RECOVERY_PROOF_DOMAIN =
      "DELTAIPCVOTERECOVERY1".getBytes(StandardCharsets.US_ASCII);
  private static final Duration WATCHDOG_SCAN_INTERVAL = Duration.ofSeconds(1);
  private static final ValidatedResponseListener NOOP_RESPONSE_LISTENER =
      (request, response) -> null;

  private final Transport transport;
  private final SidecarIpcV1.Id128 sessionId;
  private final long generation;
  private final NanoClock clock;
  private final IdSource idSource;
  private final RequestIdentityLedger requestIdentityLedger;
  private final FailureListener failureListener;
  private final ValidatedResponseListener validatedResponseListener;
  private final long requestTimeoutNanos;
  private final ArrayBlockingQueue<Attempt> ingress =
      new ArrayBlockingQueue<>(SidecarIpcV1.INGRESS_QUEUE_REQUESTS);
  private final Semaphore correlationSlots =
      new Semaphore(SidecarIpcV1.IN_FLIGHT_CORRELATIONS);
  private final ConcurrentHashMap<SidecarIpcV1.Id128, Attempt> pending =
      new ConcurrentHashMap<>();
  private final Map<RequestKey, PreparedRequest> activeRequests = new LinkedHashMap<>();
  private final Set<SidecarIpcV1.Id128> activeCorrelations = new HashSet<>();
  private final CopyOnWriteArrayList<PreparedRequest> unknownRequests =
      new CopyOnWriteArrayList<>();
  private final Object stateLock = new Object();
  private final AtomicBoolean accepting = new AtomicBoolean(true);
  private final AtomicBoolean fenced = new AtomicBoolean(false);
  private final AtomicBoolean closed = new AtomicBoolean(false);
  private final AtomicLong staleResponses = new AtomicLong();
  private final AtomicLong duplicateResponses = new AtomicLong();
  private final AtomicLong rejectedFrames = new AtomicLong();
  private final AtomicLong backpressureRejects = new AtomicLong();
  private final AtomicLong requestConflicts = new AtomicLong();
  private final AtomicLong submitted = new AtomicLong();
  private final AtomicLong completed = new AtomicLong();
  private final AtomicLong retries = new AtomicLong();
  private final AtomicLong preAdmissionTimeouts = new AtomicLong();
  private final AtomicLong outcomeUnknown = new AtomicLong();
  private final ExecutorService writer;
  private final ExecutorService reader;
  private final ScheduledExecutorService watchdog;
  private final SidecarIpcV1.SequenceCursor sendSequences;
  private final SidecarIpcV1.SequenceCursor receiveSequences;

  public LocalSidecarClient(
      Transport transport,
      SidecarIpcV1.Id128 sessionId,
      long generation,
      long firstSendSequence,
      long firstReceiveSequence,
      FailureListener failureListener) {
    this(
        transport,
        sessionId,
        generation,
        firstSendSequence,
        firstReceiveSequence,
        System::nanoTime,
        new MonotonicIdSource(sessionId),
        new RequestIdentityLedger(),
        failureListener,
        NOOP_RESPONSE_LISTENER,
        REQUEST_WATCHDOG_TIMEOUT,
        WATCHDOG_SCAN_INTERVAL);
  }

  LocalSidecarClient(
      Transport transport,
      SidecarIpcV1.Id128 sessionId,
      long generation,
      long firstSendSequence,
      long firstReceiveSequence,
      RequestIdentityLedger requestIdentityLedger,
      FailureListener failureListener) {
    this(
        transport,
        sessionId,
        generation,
        firstSendSequence,
        firstReceiveSequence,
        requestIdentityLedger,
        failureListener,
        NOOP_RESPONSE_LISTENER);
  }

  LocalSidecarClient(
      Transport transport,
      SidecarIpcV1.Id128 sessionId,
      long generation,
      long firstSendSequence,
      long firstReceiveSequence,
      RequestIdentityLedger requestIdentityLedger,
      FailureListener failureListener,
      ValidatedResponseListener validatedResponseListener) {
    this(
        transport,
        sessionId,
        generation,
        firstSendSequence,
        firstReceiveSequence,
        System::nanoTime,
        new MonotonicIdSource(sessionId),
        requestIdentityLedger,
        failureListener,
        validatedResponseListener,
        REQUEST_WATCHDOG_TIMEOUT,
        WATCHDOG_SCAN_INTERVAL);
  }

  LocalSidecarClient(
      Transport transport,
      SidecarIpcV1.Id128 sessionId,
      long generation,
      long firstSendSequence,
      long firstReceiveSequence,
      NanoClock clock,
      IdSource idSource,
      FailureListener failureListener,
      Duration requestTimeout,
      Duration watchdogInterval) {
    this(
        transport,
        sessionId,
        generation,
        firstSendSequence,
        firstReceiveSequence,
        clock,
        idSource,
        new RequestIdentityLedger(),
        failureListener,
        NOOP_RESPONSE_LISTENER,
        requestTimeout,
        watchdogInterval);
  }

  LocalSidecarClient(
      Transport transport,
      SidecarIpcV1.Id128 sessionId,
      long generation,
      long firstSendSequence,
      long firstReceiveSequence,
      NanoClock clock,
      IdSource idSource,
      RequestIdentityLedger requestIdentityLedger,
      FailureListener failureListener,
      ValidatedResponseListener validatedResponseListener,
      Duration requestTimeout,
      Duration watchdogInterval) {
    this.transport = Objects.requireNonNull(transport, "transport");
    this.sessionId = Objects.requireNonNull(sessionId, "sessionId");
    require(generation != 0, "generation zero is reserved");
    require(firstSendSequence != 0 && firstReceiveSequence != 0,
        "transport sequence zero is reserved");
    this.generation = generation;
    sendSequences = new SidecarIpcV1.SequenceCursor(firstSendSequence);
    receiveSequences = new SidecarIpcV1.SequenceCursor(firstReceiveSequence);
    this.clock = Objects.requireNonNull(clock, "clock");
    this.idSource = Objects.requireNonNull(idSource, "idSource");
    this.requestIdentityLedger =
        Objects.requireNonNull(requestIdentityLedger, "requestIdentityLedger");
    this.failureListener = Objects.requireNonNull(failureListener, "failureListener");
    this.validatedResponseListener =
        Objects.requireNonNull(validatedResponseListener, "validatedResponseListener");
    require(!requestTimeout.isNegative() && !requestTimeout.isZero(),
        "request timeout must be positive");
    require(!watchdogInterval.isNegative() && !watchdogInterval.isZero(),
        "watchdog interval must be positive");
    requestTimeoutNanos = requestTimeout.toNanos();
    writer = Executors.newSingleThreadExecutor(threadFactory("delta-sidecar-writer"));
    reader = Executors.newSingleThreadExecutor(threadFactory("delta-sidecar-reader"));
    watchdog = Executors.newSingleThreadScheduledExecutor(threadFactory("delta-sidecar-watchdog"));
    writer.execute(this::writerLoop);
    reader.execute(this::readerLoop);
    watchdog.scheduleAtFixedRate(
        this::scanTimeouts,
        watchdogInterval.toNanos(),
        watchdogInterval.toNanos(),
        TimeUnit.NANOSECONDS);
  }

  public static PreparedRequest submitRequest(byte[] requestId, byte[] canonicalCommand) {
    return prepare(
        SidecarIpcV1.requestPayload(
            SidecarIpcV1.MessageType.SUBMIT_REQUEST,
            requestId,
            List.of(SidecarIpcV1.bytes(16, canonicalCommand))));
  }

  /** Opaque vote transport; native remains the sole parser and admission authority. */
  public static PreparedRequest voteRequest(byte[] requestId, byte[] canonicalVote) {
    Objects.requireNonNull(canonicalVote, "canonicalVote");
    require(
        canonicalVote.length > 0
            && canonicalVote.length <= SidecarIpcV1.MAX_CANONICAL_VOTE_BYTES,
        "canonical vote is outside the frozen sidecar bound");
    return prepare(
        SidecarIpcV1.requestPayload(
            SidecarIpcV1.MessageType.VOTE_REQUEST,
            requestId,
            List.of(SidecarIpcV1.bytes(16, canonicalVote))));
  }

  public static PreparedRequest stateRequest(
      byte[] requestId, SidecarIpcV1.Id128 runtimeInstanceId) {
    return runtimeRequest(SidecarIpcV1.MessageType.STATE_REQUEST, requestId, runtimeInstanceId);
  }

  public static PreparedRequest snapshotRequest(
      byte[] requestId, SidecarIpcV1.Id128 runtimeInstanceId) {
    return runtimeRequest(SidecarIpcV1.MessageType.SNAPSHOT_REQUEST, requestId, runtimeInstanceId);
  }

  public static PreparedRequest healthRequest(
      byte[] requestId, SidecarIpcV1.Id128 runtimeInstanceIdOrZero) {
    return runtimeRequest(
        SidecarIpcV1.MessageType.HEALTH_REQUEST, requestId, runtimeInstanceIdOrZero);
  }

  public static PreparedRequest closeRequest(
      byte[] requestId,
      SidecarIpcV1.Id128 runtimeInstanceId,
      SidecarIpcV1.CloseMode closeMode) {
    return prepare(
        SidecarIpcV1.requestPayload(
            SidecarIpcV1.MessageType.CLOSE_REQUEST,
            requestId,
            List.of(
                SidecarIpcV1.id128(16, runtimeInstanceId),
                SidecarIpcV1.u8(17, Objects.requireNonNull(closeMode, "closeMode").code()))));
  }

  public static PreparedRequest prepare(SidecarIpcV1.Payload request) {
    Objects.requireNonNull(request, "request");
    require(
        request.type().isRequest()
            && request.type() != SidecarIpcV1.MessageType.CLIENT_HELLO
            && request.type() != SidecarIpcV1.MessageType.OPEN_REQUEST,
        "client accepts only post-READY operation requests");
    SidecarIpcV1.requireRequestDigest(request);
    return new PreparedRequest(request);
  }

  /** Nonblocking bounded ingress. The returned stage cannot cancel a written native operation. */
  public Submission tryEnqueue(PreparedRequest request) {
    Objects.requireNonNull(request, "request");
    Attempt attempt;
    synchronized (stateLock) {
      if (!accepting.get() || fenced.get() || closed.get()) {
        return Submission.rejected(new GenerationFencedException("generation is not accepting"));
      }
      var registration = requestIdentityLedger.register(request);
      if (registration == null) {
        requestConflicts.incrementAndGet();
        return Submission.rejected(
            new RequestConflictException(
                "same request ID has a different operation, digest, or canonical body"));
      }
      var existing = activeRequests.get(request.key);
      if (existing != null) {
        requestIdentityLedger.rollback(request, registration);
        return Submission.rejected(
            new RequestConflictException("exact request is already queued or in flight"));
      }
      SidecarIpcV1.Id128 correlation;
      try {
        correlation = reserveCorrelationLocked();
      } catch (RuntimeException allocationFailure) {
        requestIdentityLedger.rollback(request, registration);
        fenceInternal(FailureKind.INTERNAL, allocationFailure, true);
        return Submission.rejected(allocationFailure);
      }
      attempt = new Attempt(request, registration, correlation, clock.nanoTime());
      activeRequests.put(request.key, request);
      if (!ingress.offer(attempt)) {
        activeRequests.remove(request.key);
        activeCorrelations.remove(correlation);
        requestIdentityLedger.rollback(request, registration);
        backpressureRejects.incrementAndGet();
        return Submission.rejected(new BackpressureException("sidecar ingress queue is full"));
      }
      submitted.incrementAndGet();
      if (registration.existing) {
        retries.incrementAndGet();
      }
    }
    return Submission.accepted(attempt.completion.minimalCompletionStage());
  }

  public boolean isAccepting() {
    return accepting.get() && !fenced.get() && !closed.get();
  }

  public long generation() {
    return generation;
  }

  public SidecarIpcV1.Id128 sessionId() {
    return sessionId;
  }

  /** Exact requests whose frame could have reached native admission before the generation fenced. */
  public List<PreparedRequest> outcomeUnknownRequests() {
    return List.copyOf(unknownRequests);
  }

  public Telemetry telemetry() {
    return new Telemetry(
        submitted.get(),
        completed.get(),
        retries.get(),
        backpressureRejects.get(),
        requestConflicts.get(),
        staleResponses.get(),
        duplicateResponses.get(),
        rejectedFrames.get(),
        preAdmissionTimeouts.get(),
        outcomeUnknown.get(),
        ingress.size(),
        pending.size(),
        fenced.get(),
        closed.get());
  }

  public void fence(FailureKind kind, Throwable cause) {
    fenceInternal(Objects.requireNonNull(kind, "kind"), cause, true);
  }

  @Override
  public void close() {
    GenerationFencedException failure;
    Outstanding outstanding;
    synchronized (stateLock) {
      if (!closed.compareAndSet(false, true)) {
        return;
      }
      accepting.set(false);
      fenced.set(true);
      failure = new GenerationFencedException("client closed");
      outstanding = detachOutstandingLocked();
    }
    for (var attempt : outstanding.queued) {
      requestIdentityLedger.rollback(attempt.request, attempt.registration);
      attempt.completion.completeExceptionally(failure);
    }
    for (var attempt : outstanding.inFlight) {
      recordUnknown(attempt);
      attempt.completion.completeExceptionally(failure);
    }
    validatedResponseListener.onTransportClosed(generation);
    try {
      transport.close();
    } catch (IOException ignored) {
      // The generation is already permanently closed.
    }
    watchdog.shutdownNow();
    writer.shutdownNow();
    reader.shutdownNow();
  }

  private static PreparedRequest runtimeRequest(
      SidecarIpcV1.MessageType type,
      byte[] requestId,
      SidecarIpcV1.Id128 runtimeInstanceId) {
    return prepare(
        SidecarIpcV1.requestPayload(
            type,
            requestId,
            List.of(SidecarIpcV1.id128(16, runtimeInstanceId))));
  }

  private SidecarIpcV1.Id128 reserveCorrelationLocked() {
    for (var attempt = 0; attempt < 16; ++attempt) {
      var candidate = idSource.next();
      if (activeCorrelations.add(candidate)) {
        return candidate;
      }
    }
    throw new IllegalStateException("unable to allocate a unique correlation ID");
  }

  private void writerLoop() {
    Attempt current = null;
    var permitHeld = false;
    var currentPending = false;
    try {
      while (!closed.get() && !fenced.get()) {
        correlationSlots.acquire();
        permitHeld = true;
        current = ingress.take();
        if (!isAccepting()) {
          correlationSlots.release();
          permitHeld = false;
          failQueued(current, new GenerationFencedException("generation fenced before write"));
          current = null;
          continue;
        }
        var sequence = sendSequences.claim();
        var frame = SidecarIpcV1.frame(
            current.request.type(),
            sessionId,
            generation,
            current.correlationId,
            sequence,
            current.request.payload);
        var handoff = false;
        synchronized (stateLock) {
          if (isAccepting()) {
            var prior = pending.putIfAbsent(current.correlationId, current);
            if (prior != null) {
              throw new IllegalStateException("duplicate active correlation ID");
            }
            current.handedToTransport = true;
            currentPending = true;
            permitHeld = false;
            current.writtenAtNanos = clock.nanoTime();
            handoff = true;
          }
        }
        if (!handoff) {
          correlationSlots.release();
          permitHeld = false;
          failQueued(current, new GenerationFencedException("generation fenced before write"));
          current = null;
          continue;
        }
        transport.write(frame.canonicalBytes());
        current = null;
        currentPending = false;
      }
    } catch (InterruptedException interrupted) {
      Thread.currentThread().interrupt();
      failUnpublished(current, currentPending, interrupted);
      if (!closed.get() && !fenced.get()) {
        fenceInternal(FailureKind.TRANSPORT, interrupted, true);
      }
    } catch (SidecarIpcV1.ProtocolException error) {
      failUnpublished(current, currentPending, error);
      if (!closed.get() && !fenced.get()) {
        fenceInternal(FailureKind.PROTOCOL, error, true);
      }
    } catch (IOException error) {
      failUnpublished(current, currentPending, error);
      if (!closed.get() && !fenced.get()) {
        fenceInternal(FailureKind.TRANSPORT, error, true);
      }
    } catch (RuntimeException error) {
      failUnpublished(current, currentPending, error);
      if (!closed.get() && !fenced.get()) {
        fenceInternal(FailureKind.INTERNAL, error, true);
      }
    } finally {
      if (permitHeld) {
        correlationSlots.release();
      }
    }
  }

  private void failUnpublished(Attempt attempt, boolean pendingAttempt, Throwable failure) {
    if (attempt != null && !pendingAttempt) {
      failQueued(attempt, failure);
    }
  }

  private void readerLoop() {
    try {
      while (!closed.get() && !fenced.get()) {
        var canonical = transport.read();
        byte[] consumedReference = null;
        if (SidecarSharedMemory.isSharedMemoryCarrier(canonical)) {
          var header = SidecarSharedMemory.inspectCarrierHeader(canonical);
          requireTrustedSharedMemoryHeader(header);
          consumedReference = SidecarSharedMemory.referenceBytes(canonical);
          canonical = transport.resolveSharedMemoryCarrier(canonical);
        }
        var response = SidecarIpcV1.decodeFrame(canonical);
        if (response.messageType() == SidecarIpcV1.MessageType.SHARED_MEMORY_ACK) {
          handleSharedMemoryAck(response);
          continue;
        }
        if (consumedReference != null) {
          writeSharedMemoryAck(response, consumedReference);
        }
        handleResponse(response);
      }
    } catch (SidecarIpcV1.ProtocolException error) {
      if (!closed.get() && !fenced.get()) {
        rejectedFrames.incrementAndGet();
        fenceInternal(FailureKind.PROTOCOL, error, true);
      }
    } catch (IOException error) {
      if (!closed.get() && !fenced.get()) {
        fenceInternal(FailureKind.TRANSPORT, error, true);
      }
    } catch (RuntimeException error) {
      if (!closed.get() && !fenced.get()) {
        fenceInternal(FailureKind.INTERNAL, error, true);
      }
    }
  }

  private void handleSharedMemoryAck(SidecarIpcV1.Frame notification) throws IOException {
    if (!notification.sessionId().equals(sessionId) || notification.generation() != generation) {
      staleResponses.incrementAndGet();
      return;
    }
    receiveSequences.accept(notification.sequence());
    if (!transport.acceptSharedMemoryAck(notification)) {
      throw new SidecarIpcV1.ProtocolException(
          "shared-memory ACK does not match a current publication");
    }
  }

  private void writeSharedMemoryAck(
      SidecarIpcV1.Frame consumed,
      byte[] encodedReference) throws IOException {
    var payload = SidecarIpcV1.responsePayload(
        SidecarIpcV1.MessageType.SHARED_MEMORY_ACK,
        consumed.payload().bytes(1),
        consumed.payload().bytes(2),
        List.of(
            SidecarIpcV1.sharedMemoryReference(16, encodedReference),
            SidecarIpcV1.u8(
                17, SidecarIpcV1.SharedMemoryDisposition.ACKED.code())));
    transport.write(
        SidecarIpcV1.frame(
                SidecarIpcV1.MessageType.SHARED_MEMORY_ACK,
                sessionId,
                generation,
                consumed.correlationId(),
                sendSequences.claim(),
                payload)
            .canonicalBytes());
  }

  private void requireTrustedSharedMemoryHeader(
      SidecarSharedMemory.CarrierHeader header) {
    if (!header.sessionId().equals(sessionId) || header.generation() != generation) {
      throw new SidecarIpcV1.ProtocolException(
          "stale shared-memory response identity");
    }
    if (header.sequence() != receiveSequences.nextValue()) {
      throw new SidecarIpcV1.ProtocolException(
          "non-monotonic shared-memory response sequence");
    }
    var attempt = pending.get(header.correlationId());
    if (attempt == null) {
      throw new SidecarIpcV1.ProtocolException(
          "uncorrelated shared-memory response");
    }
    var expected = attempt.request.type().expectedResponse();
    if (header.messageType() != expected
        && header.messageType() != SidecarIpcV1.MessageType.ERROR_RESPONSE) {
      throw new SidecarIpcV1.ProtocolException(
          "shared-memory response operation mismatch");
    }
  }

  private void handleResponse(SidecarIpcV1.Frame response) {
    if (!response.sessionId().equals(sessionId) || response.generation() != generation) {
      staleResponses.incrementAndGet();
      validatedResponseListener.onResponseDiscarded(
          response.generation(), response.correlationId());
      return;
    }
    receiveSequences.accept(response.sequence());
    var attempt = pending.get(response.correlationId());
    if (attempt == null) {
      duplicateResponses.incrementAndGet();
      validatedResponseListener.onResponseDiscarded(
          response.generation(), response.correlationId());
      return;
    }
    if (isTrustedPreparseSentinel(attempt.request.type(), response)) {
      rejectedFrames.incrementAndGet();
      var rejection =
          new SidecarIpcV1.ProtocolException(
              "sidecar rejected the correlated frame before native admission");
      boolean removed;
      synchronized (stateLock) {
        removed = pending.remove(response.correlationId(), attempt);
        if (removed) {
          activeRequests.remove(attempt.request.key);
          activeCorrelations.remove(attempt.correlationId);
        }
      }
      if (removed) {
        correlationSlots.release();
        attempt.completion.completeExceptionally(rejection);
      }
      fenceInternal(
          FailureKind.PROTOCOL,
          rejection,
          true);
      return;
    }
    if (!matches(attempt, response)) {
      staleResponses.incrementAndGet();
      validatedResponseListener.onResponseDiscarded(
          response.generation(), response.correlationId());
      return;
    }
    var admission = SidecarIpcV1.AdmissionState.fromCode(response.payload().u8(3));
    if (admission != SidecarIpcV1.AdmissionState.ADMITTED_OUTCOME_AVAILABLE
        && attempt.identity.hasBoundResultProof()) {
      throw new SidecarIpcV1.ProtocolException(
          "response contradicts the request's previously validated admitted result");
    }
    if (admission == SidecarIpcV1.AdmissionState.OUTCOME_UNKNOWN) {
      recordUnknown(attempt);
      fenceInternal(
          FailureKind.OUTCOME_UNKNOWN,
          new OutcomeUnknownException("native admission outcome is unknown"),
          true);
      return;
    }
    var resultProof = admission == SidecarIpcV1.AdmissionState.ADMITTED_OUTCOME_AVAILABLE
        ? resultProofSha256(attempt.request, response)
        : null;
    OperationalTiming timing;
    Object responseEvidence;
    boolean accepted;
    GenerationFencedException expectedClose = null;
    Outstanding expectedCloseOutstanding = null;
    synchronized (stateLock) {
      if (!isAccepting()) {
        validatedResponseListener.onResponseDiscarded(
            response.generation(), response.correlationId());
        return;
      }
      if (resultProof != null) {
        attempt.identity.bindOrVerifyResultDigest(resultProof);
      }
      responseEvidence = validatedResponseListener.onValidated(attempt.request, response);
      accepted = pending.remove(response.correlationId(), attempt);
      if (!accepted) {
        return;
      }
      activeRequests.remove(attempt.request.key);
      activeCorrelations.remove(attempt.correlationId);
      timing = OperationalTiming.between(
          attempt.enqueuedAtNanos, attempt.writtenAtNanos, clock.nanoTime());
      if (response.messageType() == SidecarIpcV1.MessageType.CLOSE_RESPONSE
          && response.payload().u8(18) == 1) {
        accepting.set(false);
        // stateLock is the linearization boundary for terminal client state. The accepting check
        // above proves both flags were clear while holding this same lock; unconditional stores
        // avoid turning a harmless close/fence race into an exception that could orphan the
        // CLOSE completion.
        closed.set(true);
        fenced.set(true);
        expectedClose =
            new GenerationFencedException("native runtime closed after CLOSE_RESPONSE");
        expectedCloseOutstanding = detachOutstandingLocked();
      }
    }
    if (accepted) {
      correlationSlots.release();
      completed.incrementAndGet();
      if (expectedClose != null) {
        finishExpectedClose(expectedClose, expectedCloseOutstanding);
      }
      attempt.completion.complete(new Response(response, timing, responseEvidence));
    }
  }

  private void finishExpectedClose(
      GenerationFencedException terminal, Outstanding outstanding) {
    for (var attempt : outstanding.queued) {
      requestIdentityLedger.rollback(attempt.request, attempt.registration);
      attempt.completion.completeExceptionally(terminal);
    }
    for (var attempt : outstanding.inFlight) {
      recordUnknown(attempt);
      attempt.completion.completeExceptionally(terminal);
    }
    validatedResponseListener.onTransportClosed(generation);
    try {
      transport.close();
    } catch (IOException ignored) {
      // A validated CLOSE_RESPONSE already made endpoint shutdown expected.
    }
    watchdog.shutdownNow();
    writer.shutdownNow();
    reader.shutdown();
    try {
      failureListener.onFailure(new Failure(FailureKind.EXPECTED_CLOSE, generation, terminal));
    } catch (RuntimeException ignored) {
      // A lifecycle observer cannot roll back the already-linearized terminal transition or
      // prevent the validated CLOSE completion from being published to its caller.
    }
  }

  private boolean matches(Attempt attempt, SidecarIpcV1.Frame response) {
    var expected = attempt.request.type().expectedResponse();
    if (response.messageType() != expected
        && response.messageType() != SidecarIpcV1.MessageType.ERROR_RESPONSE) {
      return false;
    }
    if (response.messageType() == SidecarIpcV1.MessageType.ERROR_RESPONSE
        && response.payload().u16(17) != attempt.request.type().code()) {
      return false;
    }
    if (!Arrays.equals(response.payload().bytes(1), attempt.request.requestId)
        || !Arrays.equals(response.payload().bytes(2), attempt.request.requestDigest)) {
      return false;
    }
    return response.correlationId().equals(attempt.correlationId);
  }

  private static byte[] resultProofSha256(
      PreparedRequest request, SidecarIpcV1.Frame response) {
    if (request.type() == SidecarIpcV1.MessageType.SUBMIT_REQUEST
        && response.messageType() == SidecarIpcV1.MessageType.SUBMIT_RESPONSE) {
      return submitRecoveryProofSha256(response);
    }
    if (request.type() == SidecarIpcV1.MessageType.VOTE_REQUEST
        && response.messageType() == SidecarIpcV1.MessageType.VOTE_RESPONSE) {
      return voteRecoveryProofSha256(response);
    }
    // Non-SUBMIT retries remain bound to the complete validated result. A later response that
    // differs even in an operational field therefore fences instead of being mistaken for an
    // idempotent completed retry.
    return response.payloadSha256();
  }

  /**
   * Durable SUBMIT recovery proof. Transport echoes, correlation and the per-generation native
   * admission sequence are deliberately excluded; every native-owned durable result field is
   * included with its canonical TLV identity and wire type.
   */
  static byte[] submitRecoveryProofSha256(SidecarIpcV1.Frame response) {
    Objects.requireNonNull(response, "response");
    require(
        response.messageType() == SidecarIpcV1.MessageType.SUBMIT_RESPONSE,
        "SUBMIT recovery proof requires SUBMIT_RESPONSE");
    var payload = response.payload();
    try {
      var digest = MessageDigest.getInstance("SHA-256");
      digest.update(SUBMIT_RECOVERY_PROOF_DOMAIN);
      digest.update(
          ByteBuffer.allocate(6)
              .order(ByteOrder.BIG_ENDIAN)
              .putShort((short) response.messageType().code())
              .putInt((int) payload.u32(5))
              .array());
      updateProofField(digest, 16, SidecarIpcV1.WireType.BYTES, payload.bytes(16));
      updateProofField(digest, 17, SidecarIpcV1.WireType.BYTES, payload.bytes(17));
      updateProofField(digest, 18, SidecarIpcV1.WireType.SHA256, payload.bytes(18));
      updateProofField(
          digest,
          19,
          SidecarIpcV1.WireType.U64_BE,
          ByteBuffer.allocate(Long.BYTES)
              .order(ByteOrder.BIG_ENDIAN)
              .putLong(payload.u64Bits(19))
              .array());
      updateProofField(digest, 20, SidecarIpcV1.WireType.SHA256, payload.bytes(20));
      updateProofField(digest, 21, SidecarIpcV1.WireType.SHA256, payload.bytes(21));
      return digest.digest();
    } catch (NoSuchAlgorithmException error) {
      throw new IllegalStateException("SHA-256 is unavailable", error);
    }
  }

  static byte[] voteRecoveryProofSha256(SidecarIpcV1.Frame response) {
    Objects.requireNonNull(response, "response");
    require(
        response.messageType() == SidecarIpcV1.MessageType.VOTE_RESPONSE,
        "VOTE recovery proof requires VOTE_RESPONSE");
    var payload = response.payload();
    try {
      var digest = MessageDigest.getInstance("SHA-256");
      digest.update(VOTE_RECOVERY_PROOF_DOMAIN);
      digest.update(
          ByteBuffer.allocate(6)
              .order(ByteOrder.BIG_ENDIAN)
              .putShort((short) response.messageType().code())
              .putInt((int) payload.u32(5))
              .array());
      updateProofField(digest, 16, SidecarIpcV1.WireType.BYTES, payload.bytes(16));
      updateProofField(digest, 17, SidecarIpcV1.WireType.SHA256, payload.bytes(17));
      return digest.digest();
    } catch (NoSuchAlgorithmException error) {
      throw new IllegalStateException("SHA-256 is unavailable", error);
    }
  }

  private static void updateProofField(
      MessageDigest digest, int fieldId, SidecarIpcV1.WireType wireType, byte[] value) {
    digest.update(
        ByteBuffer.allocate(8)
            .order(ByteOrder.BIG_ENDIAN)
            .putShort((short) fieldId)
            .put((byte) wireType.code())
            .put((byte) 0)
            .putInt(value.length)
            .array());
    digest.update(value);
  }

  private static boolean isTrustedPreparseSentinel(
      SidecarIpcV1.MessageType requestType, SidecarIpcV1.Frame response) {
    if (response.messageType() != SidecarIpcV1.MessageType.ERROR_RESPONSE) {
      return false;
    }
    var payload = response.payload();
    return payload.bytes(1).length == 0
        && Arrays.equals(payload.bytes(2), SidecarIpcV1.emptySha256())
        && payload.u8(3) == SidecarIpcV1.AdmissionState.NOT_ADMITTED_PROVEN.code()
        && payload.u64Bits(4) == 0
        && payload.u32(5) == SidecarIpcV1.NATIVE_STATUS_UNAVAILABLE
        && payload.u16(17) == requestType.code();
  }

  private void scanTimeouts() {
    if (closed.get() || fenced.get()) {
      return;
    }
    try {
      var now = clock.nanoTime();
      for (var attempt : ingress) {
        if (elapsed(now, attempt.enqueuedAtNanos) >= requestTimeoutNanos
            && ingress.remove(attempt)) {
          preAdmissionTimeouts.incrementAndGet();
          failQueued(attempt, new RequestTimeoutException(false));
        }
      }
      for (var attempt : pending.values()) {
        var start = attempt.writtenAtNanos == 0 ? attempt.enqueuedAtNanos : attempt.writtenAtNanos;
        if (elapsed(now, start) >= requestTimeoutNanos) {
          recordUnknown(attempt);
          fenceInternal(FailureKind.OUTCOME_UNKNOWN, new RequestTimeoutException(true), true);
          return;
        }
      }
    } catch (RuntimeException error) {
      fenceInternal(FailureKind.INTERNAL, error, true);
    }
  }

  private static long elapsed(long now, long start) {
    return now - start;
  }

  private void recordUnknown(Attempt attempt) {
    if (attempt.handedToTransport && unknownRequests.addIfAbsent(attempt.request)) {
      outcomeUnknown.incrementAndGet();
    }
  }

  private void failQueued(Attempt attempt, Throwable cause) {
    synchronized (stateLock) {
      activeRequests.remove(attempt.request.key);
      activeCorrelations.remove(attempt.correlationId);
      requestIdentityLedger.rollback(attempt.request, attempt.registration);
    }
    attempt.completion.completeExceptionally(cause);
  }

  private void fenceInternal(FailureKind kind, Throwable cause, boolean notify) {
    Throwable failure;
    Outstanding outstanding;
    synchronized (stateLock) {
      accepting.set(false);
      if (!fenced.compareAndSet(false, true)) {
        return;
      }
      failure = cause == null ? new GenerationFencedException("generation fenced") : cause;
      outstanding = detachOutstandingLocked();
    }
    for (var attempt : outstanding.queued) {
      requestIdentityLedger.rollback(attempt.request, attempt.registration);
      attempt.completion.completeExceptionally(failure);
    }
    for (var attempt : outstanding.inFlight) {
      recordUnknown(attempt);
      attempt.completion.completeExceptionally(failure);
    }
    validatedResponseListener.onTransportClosed(generation);
    try {
      transport.close();
    } catch (IOException ignored) {
      // The generation is already permanently fenced.
    }
    watchdog.shutdownNow();
    writer.shutdownNow();
    reader.shutdownNow();
    if (notify) {
      failureListener.onFailure(new Failure(kind, generation, failure));
    }
  }

  private Outstanding detachOutstandingLocked() {
    var queued = new ArrayList<Attempt>();
    var inFlight = new ArrayList<Attempt>();
    ingress.drainTo(queued);
    for (var entry : pending.entrySet()) {
      var attempt = entry.getValue();
      if (pending.remove(entry.getKey(), attempt)) {
        correlationSlots.release();
        inFlight.add(attempt);
      }
    }
    for (var attempt : queued) {
      activeRequests.remove(attempt.request.key);
      activeCorrelations.remove(attempt.correlationId);
    }
    for (var attempt : inFlight) {
      activeRequests.remove(attempt.request.key);
      activeCorrelations.remove(attempt.correlationId);
    }
    return new Outstanding(List.copyOf(queued), List.copyOf(inFlight));
  }

  private static ThreadFactory threadFactory(String name) {
    return operation -> {
      var thread = new Thread(operation, name);
      thread.setDaemon(true);
      return thread;
    };
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalArgumentException(message);
    }
  }

  /** Exact immutable request. A supervisor-lifetime ledger preserves its identity across recovery. */
  public static final class PreparedRequest {
    private final SidecarIpcV1.Payload payload;
    private final byte[] requestId;
    private final byte[] requestDigest;
    private final RequestKey key;

    private PreparedRequest(SidecarIpcV1.Payload payload) {
      this.payload = payload;
      requestId = payload.bytes(1);
      requestDigest = payload.bytes(2);
      key = new RequestKey(requestId);
    }

    public SidecarIpcV1.MessageType type() {
      return payload.type();
    }

    public byte[] requestId() {
      return Arrays.copyOf(requestId, requestId.length);
    }

    public byte[] requestDigest() {
      return Arrays.copyOf(requestDigest, requestDigest.length);
    }

    public byte[] canonicalPayload() {
      return payload.canonicalBytes();
    }

    public int canonicalPayloadLength() {
      return payload.canonicalLength();
    }

  }

  /** Accepted enqueue or immediate local pre-admission rejection. */
  public static final class Submission {
    private final boolean accepted;
    private final CompletionStage<Response> completion;

    private Submission(boolean accepted, CompletionStage<Response> completion) {
      this.accepted = accepted;
      this.completion = completion;
    }

    public boolean accepted() {
      return accepted;
    }

    public CompletionStage<Response> completion() {
      return completion;
    }

    private static Submission accepted(CompletionStage<Response> completion) {
      return new Submission(true, completion);
    }

    private static Submission rejected(Throwable failure) {
      var result = new CompletableFuture<Response>();
      result.completeExceptionally(failure);
      return new Submission(false, result.minimalCompletionStage());
    }
  }

  /** Fully validated native/sidecar response; effect and state bytes remain opaque. */
  public static final class Response {
    private final SidecarIpcV1.Frame frame;
    private final OperationalTiming operationalTiming;
    private final Object responseEvidence;

    private Response(
        SidecarIpcV1.Frame frame, OperationalTiming operationalTiming, Object responseEvidence) {
      this.frame = frame;
      this.operationalTiming = operationalTiming;
      this.responseEvidence = responseEvidence;
    }

    public SidecarIpcV1.MessageType messageType() {
      return frame.messageType();
    }

    public SidecarIpcV1.Payload payload() {
      return frame.payload();
    }

    public long admittedSequenceBits() {
      return frame.payload().u64Bits(4);
    }

    public long nativeStatus() {
      return frame.payload().u32(5);
    }

    /** Local operational timing only; these integer values never enter consensus state. */
    public OperationalTiming operationalTiming() {
      return operationalTiming;
    }

    long generation() {
      return frame.generation();
    }

    SidecarIpcV1.Id128 correlationId() {
      return frame.correlationId();
    }

    Object responseEvidence() {
      return responseEvidence;
    }
  }

  /** Monotonic local timings for one validated response, suitable for raw benchmark samples. */
  public record OperationalTiming(
      long enqueueToWriteNanos,
      long writeToValidatedReceiveNanos,
      long totalEnqueueToValidatedReceiveNanos) {
    public OperationalTiming {
      require(enqueueToWriteNanos >= 0, "enqueue-to-write latency is negative");
      require(writeToValidatedReceiveNanos >= 0,
          "write-to-validated-receive latency is negative");
      require(totalEnqueueToValidatedReceiveNanos >= 0,
          "total operational latency is negative");
      require(
          Math.addExact(enqueueToWriteNanos, writeToValidatedReceiveNanos)
              == totalEnqueueToValidatedReceiveNanos,
          "operational latency phases do not sum to total");
    }

    private static OperationalTiming between(long enqueued, long written, long received) {
      var enqueueToWrite = checkedElapsed(written, enqueued, "enqueue-to-write");
      var writeToReceive = checkedElapsed(received, written, "write-to-receive");
      var total = checkedElapsed(received, enqueued, "enqueue-to-receive");
      return new OperationalTiming(enqueueToWrite, writeToReceive, total);
    }

    private static long checkedElapsed(long end, long start, String phase) {
      var elapsed = end - start;
      if (elapsed < 0) {
        throw new SidecarIpcV1.ProtocolException(
            "non-monotonic operational clock for " + phase);
      }
      return elapsed;
    }
  }

  public record Telemetry(
      long submitted,
      long completed,
      long retries,
      long backpressureRejects,
      long requestConflicts,
      long staleResponses,
      long duplicateResponses,
      long rejectedFrames,
      long preAdmissionTimeouts,
      long outcomeUnknown,
      int queued,
      int inFlight,
      boolean fenced,
      boolean closed) {}

  public enum FailureKind {
    TRANSPORT,
    OUTCOME_UNKNOWN,
    PROTOCOL,
    INTERNAL,
    EXPECTED_CLOSE,
    LOCAL_CLOSE
  }

  public record Failure(FailureKind kind, long generation, Throwable cause) {
    public Failure {
      Objects.requireNonNull(kind, "kind");
      Objects.requireNonNull(cause, "cause");
    }
  }

  @FunctionalInterface
  public interface FailureListener {
    void onFailure(Failure failure);
  }

  @FunctionalInterface
  interface ValidatedResponseListener {
    Object onValidated(PreparedRequest request, SidecarIpcV1.Frame response);

    default void onResponseDiscarded(
        long responseGeneration, SidecarIpcV1.Id128 correlationId) {}

    default void onTransportClosed(long closedGeneration) {}
  }

  @FunctionalInterface
  interface NanoClock {
    long nanoTime();
  }

  @FunctionalInterface
  interface IdSource {
    SidecarIpcV1.Id128 next();
  }

  /** A whole-frame, reliable local byte stream. */
  public interface Transport extends AutoCloseable {
    void write(byte[] canonicalFrame) throws IOException;

    byte[] read() throws IOException;

    default byte[] resolveSharedMemoryCarrier(byte[] carrier) throws IOException {
      throw new SidecarIpcV1.ProtocolException(
          "transport cannot resolve a shared-memory carrier");
    }

    default boolean acceptSharedMemoryAck(SidecarIpcV1.Frame notification)
        throws IOException {
      return false;
    }

    default boolean sharedMemoryConfigured() {
      return false;
    }

    default boolean lastWriteSharedMemory() {
      return false;
    }

    boolean isOpen();

    @Override
    void close() throws IOException;
  }

  /** Blocking socket adapter used only from the client's dedicated I/O threads. */
  public static final class SocketTransport implements Transport {
    private final SocketChannel channel;

    public SocketTransport(SocketChannel channel) throws IOException {
      this.channel = Objects.requireNonNull(channel, "channel");
      channel.configureBlocking(true);
    }

    @Override
    public synchronized void write(byte[] canonicalFrame) throws IOException {
      var output = ByteBuffer.wrap(Arrays.copyOf(canonicalFrame, canonicalFrame.length));
      while (output.hasRemaining()) {
        if (channel.write(output) < 0) {
          throw new EOFException("sidecar channel closed during write");
        }
      }
    }

    @Override
    public byte[] read() throws IOException {
      var header = ByteBuffer.allocate(SidecarIpcV1.HEADER_BYTES).order(ByteOrder.BIG_ENDIAN);
      readFully(header);
      var bytes = header.array();
      var view = ByteBuffer.wrap(bytes).order(ByteOrder.BIG_ENDIAN);
      var flags = view.getInt(16);
      var shared = (flags & SidecarIpcV1.FLAG_PAYLOAD_SHARED_MEMORY) != 0;
      var inline = (flags & SidecarIpcV1.FLAG_PAYLOAD_INLINE) != 0;
      if (shared == inline) {
        throw new SidecarIpcV1.ProtocolException("frame payload carrier is not exclusive");
      }
      var logicalLength = view.getLong(68);
      if (logicalLength < 0 || logicalLength > SidecarIpcV1.MAX_LOGICAL_PAYLOAD_BYTES) {
        throw new SidecarIpcV1.ProtocolException("frame payload length is outside bounds");
      }
      var physicalLength = shared
          ? SidecarIpcV1.SHARED_MEMORY_REFERENCE_BYTES
          : Math.toIntExact(logicalLength);
      var payload = ByteBuffer.allocate(physicalLength);
      readFully(payload);
      var result = new byte[Math.addExact(SidecarIpcV1.HEADER_BYTES, payload.capacity())];
      System.arraycopy(bytes, 0, result, 0, bytes.length);
      System.arraycopy(payload.array(), 0, result, bytes.length, payload.capacity());
      return result;
    }

    private void readFully(ByteBuffer target) throws IOException {
      while (target.hasRemaining()) {
        var count = channel.read(target);
        if (count < 0) {
          throw new EOFException("sidecar channel closed during frame read");
        }
      }
    }

    @Override
    public boolean isOpen() {
      return channel.isOpen();
    }

    @Override
    public void close() throws IOException {
      channel.close();
    }
  }

  /** Binary stdin/stdout adapter for a child process launched by Java. */
  public static final class StreamTransport implements Transport {
    private final InputStream input;
    private final OutputStream output;
    private final AtomicBoolean open = new AtomicBoolean(true);

    public StreamTransport(InputStream input, OutputStream output) {
      this.input = Objects.requireNonNull(input, "input");
      this.output = Objects.requireNonNull(output, "output");
    }

    @Override
    public synchronized void write(byte[] canonicalFrame) throws IOException {
      if (!open.get()) {
        throw new EOFException("sidecar process stream is closed");
      }
      output.write(Arrays.copyOf(canonicalFrame, canonicalFrame.length));
      output.flush();
    }

    @Override
    public byte[] read() throws IOException {
      var header = input.readNBytes(SidecarIpcV1.HEADER_BYTES);
      if (header.length != SidecarIpcV1.HEADER_BYTES) {
        throw new EOFException("sidecar process ended during frame header");
      }
      var view = ByteBuffer.wrap(header).order(ByteOrder.BIG_ENDIAN);
      var flags = view.getInt(16);
      var shared = (flags & SidecarIpcV1.FLAG_PAYLOAD_SHARED_MEMORY) != 0;
      var inline = (flags & SidecarIpcV1.FLAG_PAYLOAD_INLINE) != 0;
      if (shared == inline) {
        throw new SidecarIpcV1.ProtocolException("frame payload carrier is not exclusive");
      }
      var logicalLength = view.getLong(68);
      if (logicalLength < 0 || logicalLength > SidecarIpcV1.MAX_LOGICAL_PAYLOAD_BYTES) {
        throw new SidecarIpcV1.ProtocolException("frame payload length is outside bounds");
      }
      var physicalLength = shared
          ? SidecarIpcV1.SHARED_MEMORY_REFERENCE_BYTES
          : Math.toIntExact(logicalLength);
      var payload = input.readNBytes(physicalLength);
      if (payload.length != physicalLength) {
        throw new EOFException("sidecar process ended during frame payload");
      }
      var result = new byte[Math.addExact(header.length, payload.length)];
      System.arraycopy(header, 0, result, 0, header.length);
      System.arraycopy(payload, 0, result, header.length, payload.length);
      return result;
    }

    @Override
    public boolean isOpen() {
      return open.get();
    }

    @Override
    public void close() throws IOException {
      if (!open.compareAndSet(true, false)) {
        return;
      }
      IOException failure = null;
      try {
        output.close();
      } catch (IOException error) {
        failure = error;
      }
      try {
        input.close();
      } catch (IOException error) {
        if (failure == null) {
          failure = error;
        }
      }
      if (failure != null) {
        throw failure;
      }
    }
  }

  public static final class BackpressureException extends IllegalStateException {
    private static final long serialVersionUID = 1L;

    BackpressureException(String message) {
      super(message);
    }
  }

  public static final class RequestConflictException extends IllegalStateException {
    private static final long serialVersionUID = 1L;

    RequestConflictException(String message) {
      super(message);
    }
  }

  public static final class GenerationFencedException extends IllegalStateException {
    private static final long serialVersionUID = 1L;

    GenerationFencedException(String message) {
      super(message);
    }
  }

  public static final class OutcomeUnknownException extends IllegalStateException {
    private static final long serialVersionUID = 1L;

    OutcomeUnknownException(String message) {
      super(message);
    }
  }

  public static final class RequestTimeoutException extends IllegalStateException {
    private static final long serialVersionUID = 1L;
    private final boolean handedToTransport;

    RequestTimeoutException(boolean handedToTransport) {
      super(handedToTransport
          ? "request timed out after transport handoff; outcome unknown"
          : "queued request timed out before transport handoff");
      this.handedToTransport = handedToTransport;
    }

    public boolean handedToTransport() {
      return handedToTransport;
    }
  }

  /** Immutable request identities and validated result proofs retained for one supervisor life. */
  static final class RequestIdentityLedger {
    private final Map<RequestKey, RequestIdentity> identities = new LinkedHashMap<>();

    private synchronized RequestRegistration register(PreparedRequest request) {
      var existing = identities.get(request.key);
      if (existing == null) {
        var created = new RequestIdentity(request);
        identities.put(request.key, created);
        return new RequestRegistration(created, false);
      }
      return existing.matches(request) ? new RequestRegistration(existing, true) : null;
    }

    private synchronized void rollback(
        PreparedRequest request, RequestRegistration registration) {
      if (!registration.existing) {
        identities.remove(request.key, registration.identity);
      }
    }
  }

  private record RequestRegistration(RequestIdentity identity, boolean existing) {}

  private static final class RequestIdentity {
    private final SidecarIpcV1.MessageType type;
    private final byte[] requestDigest;
    private byte[] boundResultProofSha256;

    private RequestIdentity(PreparedRequest request) {
      type = request.type();
      requestDigest = request.requestDigest();
    }

    private boolean matches(PreparedRequest request) {
      return type == request.type() && Arrays.equals(requestDigest, request.requestDigest);
    }

    private synchronized void bindOrVerifyResultDigest(byte[] proofSha256) {
      if (boundResultProofSha256 == null) {
        boundResultProofSha256 = Arrays.copyOf(proofSha256, proofSha256.length);
        return;
      }
      if (!Arrays.equals(boundResultProofSha256, proofSha256)) {
        throw new SidecarIpcV1.ProtocolException(
            "recovery result differs from the first validated native result");
      }
    }

    private synchronized boolean hasBoundResultProof() {
      return boundResultProofSha256 != null;
    }
  }

  private record Outstanding(List<Attempt> queued, List<Attempt> inFlight) {}

  private static final class Attempt {
    private final PreparedRequest request;
    private final RequestRegistration registration;
    private final RequestIdentity identity;
    private final SidecarIpcV1.Id128 correlationId;
    private final long enqueuedAtNanos;
    private final CompletableFuture<Response> completion = new CompletableFuture<>();
    private volatile long writtenAtNanos;
    private volatile boolean handedToTransport;

    private Attempt(
        PreparedRequest request,
        RequestRegistration registration,
        SidecarIpcV1.Id128 correlationId,
        long enqueuedAtNanos) {
      this.request = request;
      this.registration = registration;
      identity = registration.identity;
      this.correlationId = correlationId;
      this.enqueuedAtNanos = enqueuedAtNanos;
    }
  }

  private static final class RequestKey {
    private final byte[] bytes;

    private RequestKey(byte[] value) {
      bytes = Arrays.copyOf(value, value.length);
    }

    @Override
    public boolean equals(Object other) {
      return other instanceof RequestKey value && Arrays.equals(bytes, value.bytes);
    }

    @Override
    public int hashCode() {
      return Arrays.hashCode(bytes);
    }
  }

  /** Session-scoped monotonic IDs; allocation performs no entropy or other blocking I/O. */
  private static final class MonotonicIdSource implements IdSource {
    private final long sessionPrefix;
    private long next = 1;
    private boolean exhausted;

    private MonotonicIdSource(SidecarIpcV1.Id128 sessionId) {
      sessionPrefix = ByteBuffer.wrap(sessionId.bytes()).order(ByteOrder.BIG_ENDIAN).getLong();
    }

    @Override
    public synchronized SidecarIpcV1.Id128 next() {
      if (exhausted) {
        throw new IllegalStateException("correlation ID space exhausted");
      }
      var value = next;
      if (value == -1L) {
        exhausted = true;
      } else {
        next = value + 1;
      }
      var bytes = ByteBuffer.allocate(16).order(ByteOrder.BIG_ENDIAN)
          .putLong(sessionPrefix)
          .putLong(value)
          .array();
      return new SidecarIpcV1.Id128(bytes);
    }
  }
}
