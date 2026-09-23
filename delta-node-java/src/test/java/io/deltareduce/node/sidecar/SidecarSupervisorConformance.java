package io.deltareduce.node.sidecar;

import java.io.EOFException;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.CompletionStage;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.BooleanSupplier;

/** Self-contained concurrency, fencing, recovery, and lifecycle conformance with a fake peer. */
public final class SidecarSupervisorConformance {
  private static final Duration TEST_TIMEOUT = Duration.ofSeconds(5);
  private static final String FORMAL_SEMANTICS_ID =
      "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
  private static final String BUILD_ID =
      "sha256:1616161616161616161616161616161616161616161616161616161616161616";
  private static final String SCHEMA_SET_ID =
      "sha256:1717171717171717171717171717171717171717171717171717171717171717";

  private SidecarSupervisorConformance() {}

  public static void main(String[] arguments) throws Exception {
    require(arguments.length == 0, "SidecarSupervisorConformance takes no arguments");
    testBoundedIngressAndConflict();
    testTimeoutReenqueueCannotRebindActiveIdentity();
    testDefaultCorrelationAllocationIsMonotonicAndConcurrent();
    testCorrelationPermitFenceCompletesAll();
    testStaleAndDuplicateResponseSuppression();
    testVoteStaleGenerationResponseSuppression();
    testAdmittedRetryCannotBecomeNotAdmitted();
    testWrongErrorResponseOperationIsStale();
    testSafePreparseSentinel();
    testSharedMemoryCarrierFences();
    testSharedMemoryProbeFallback();
    testMappedProbeFailureTelemetry();
    testLateReadAfterCountingTransportCloseDoesNotRepublish();
    testUnsignedMaxSequenceAcceptedOnce();
    testPostHandoffTimeoutIsOutcomeUnknown();
    testConcurrentUnknownRecordingIsExactlyOnce();
    testDurableDirectoryRebindFailsBeforeConnect();
    testWalReplacementBetweenGenerationsFailsBeforeConnect();
    testRetryableCleanupConfirmation();
    testTerminalCloseLinearizesBeforeCompletion();
    testTerminalCloseRacesAlwaysComplete();
    testSupervisorRecoveryRetryAndExpectedClose();
    testSupervisorVoteLostResponseRecoveryRetry();
    testImmediatePostOpenFailureIsNotLost();
    testReplacementOpenErrorClearsGenerationCopyObservations();
    testStalePendingReplacementFailureDoesNotKillReadyGeneration();
    testImpossibleFutureFailureFailsClosed();
    testRecoveryReadyDeadlineAndRestartLimit();
    testCleanupFailureStaysQuarantinedUntilConfirmed();
    testUnconfirmedReplacementCleanupIsTerminal();
    testExpectedCloseRequiresConfirmedExit();
    testCloseDuringHandshakeCannotResurrectReady();
    testQueuedRecoveryCannotOverwriteClosed();
    testConnectCloseRaceIsContainedInCompletionStage();
    System.out.println(
        "sidecar client/supervisor compatible on JDK "
            + Runtime.version().feature()
            + ": bounded queue/correlation, stale suppression, protocol fencing, "
            + "outcome-unknown recovery/retry, copy fallback, graceful close");
  }

  private static void testBoundedIngressAndConflict() throws Exception {
    var transport = new BlockingWriteTransport();
    var client = client(transport, ignored -> {}, System::nanoTime, new CountingIds());
    var first = LocalSidecarClient.submitRequest(ascii("same-id"), new byte[] {1});
    var firstSubmission = client.tryEnqueue(first);
    require(firstSubmission.accepted(), "first request was rejected");
    require(transport.writeEntered.await(TEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS),
        "writer did not take the first request");

    var conflict = client.tryEnqueue(
        LocalSidecarClient.submitRequest(ascii("same-id"), new byte[] {2}));
    require(!conflict.accepted(), "conflicting request ID was accepted");
    expectFailure(conflict.completion(), LocalSidecarClient.RequestConflictException.class);

    var queued = new ArrayList<LocalSidecarClient.Submission>();
    for (var index = 0; index < SidecarIpcV1.INGRESS_QUEUE_REQUESTS; ++index) {
      var submission = client.tryEnqueue(
          LocalSidecarClient.submitRequest(
              ascii("queued-" + index), new byte[] {(byte) index}));
      require(submission.accepted(), "request within the frozen ingress bound was rejected");
      queued.add(submission);
    }
    var overflow = client.tryEnqueue(
        LocalSidecarClient.voteRequest(ascii("vote-overflow"), new byte[] {3}));
    require(!overflow.accepted(), "VOTE ingress capacity +1 was accepted");
    expectFailure(overflow.completion(), LocalSidecarClient.BackpressureException.class);
    var telemetry = client.telemetry();
    require(telemetry.queued() == SidecarIpcV1.INGRESS_QUEUE_REQUESTS,
        "ingress queue did not stop at the frozen bound");
    require(telemetry.inFlight() == 1 && telemetry.backpressureRejects() == 1,
        "bounded queue/in-flight accounting changed");
    require(telemetry.requestConflicts() == 1,
        "request conflict was not counted locally");
    transport.releaseWrite.countDown();
    waitUntil(
        () -> client.telemetry().queued() < SidecarIpcV1.INGRESS_QUEUE_REQUESTS,
        "queue space after backpressure rejection");
    var reuseRejectedId = client.tryEnqueue(
        LocalSidecarClient.voteRequest(ascii("vote-overflow"), new byte[] {4}));
    require(reuseRejectedId.accepted(),
        "pre-admission VOTE queue rejection leaked request identity into the durable ledger");
    client.close();
    expectFailure(
        reuseRejectedId.completion(), LocalSidecarClient.GenerationFencedException.class);
  }

  private static void testRetryableCleanupConfirmation() throws Exception {
    var progress = new SidecarSharedMemory.CleanupProgress();
    var firstCalls = new AtomicInteger();
    var secondCalls = new AtomicInteger();
    var allowSecond = new AtomicBoolean();
    IOException remembered = null;
    for (var attempt = 0; attempt < 2; ++attempt) {
      try {
        progress.close(
            () -> firstCalls.incrementAndGet(),
            () -> {
              secondCalls.incrementAndGet();
              if (!allowSecond.get()) {
                throw new IOException("injected unmap failure");
              }
            });
        throw new IllegalStateException("failed cleanup was reported as confirmed");
      } catch (IOException expected) {
        if (remembered == null) {
          remembered = expected;
        } else {
          require(expected == remembered, "cleanup did not retain its first failure");
        }
      }
      require(!progress.confirmed(), "failed cleanup became false idempotent success");
    }
    require(firstCalls.get() == 1 && secondCalls.get() == 2,
        "cleanup did not retry only the failed step");
    allowSecond.set(true);
    progress.close(
        () -> firstCalls.incrementAndGet(),
        () -> secondCalls.incrementAndGet());
    require(progress.confirmed() && firstCalls.get() == 1 && secondCalls.get() == 3,
        "cleanup was not confirmed after the failed step eventually succeeded");
  }

  private static void testSharedMemoryProbeFallback() throws Exception {
    var missing = Files.createTempDirectory("delta-sidecar-probe-fallback-")
        .resolve("missing-sidecar");
    if (SidecarSharedMemory.atomicAbiSupported()) {
      try (var resources = SidecarSharedMemory.GenerationResources.create(31)) {
        require(!SidecarSupervisor.PipeProcessConnector.mappedSharedMemoryAtomicAbiSupported(
                missing, resources, Duration.ofMillis(100)),
            "unavailable native executable passed the exact mapped atomic probe");
        require(resources.javaToNative().rawState(0) == SidecarSharedMemory.FREE
                && Arrays.equals(
                    resources.javaToNative().rawStateBytes(0),
                    new byte[] {0, 0, 0, 0})
                && !resources.mappedAtomicAbiProbed(),
            "failed mapped atomic probe did not restore its reserved slot to fresh FREE");
      }
    }
  }

  private static void testMappedProbeFailureTelemetry() throws Exception {
    if (!SidecarSharedMemory.atomicAbiSupported()) {
      return;
    }
    var failingExecutable = Path.of("/bin/false");
    if (!Files.isRegularFile(failingExecutable) || !Files.isExecutable(failingExecutable)) {
      return;
    }
    var config = new SidecarSupervisor.Config(
        Files.createTempDirectory("delta-sidecar-mapped-probe-fallback-"),
        new byte[] {1},
        SidecarSupervisor.PipeProcessConnector.executableSha256(failingExecutable),
        BUILD_ID,
        nestedDescriptor());
    var timing = new SidecarSupervisor.Timing(
        Duration.ofSeconds(30),
        Duration.ofMillis(100),
        Duration.ofSeconds(2),
        Duration.ofMillis(1));
    var supervisor = new SidecarSupervisor(
        config,
        new SidecarSupervisor.PipeProcessConnector(failingExecutable, List.of()),
        timing,
        Thread::sleep);
    try {
      expectAnyFailure(supervisor.start());
      require(supervisor.telemetry().sharedMemoryStatus().equals(
              "DISABLED_MAPPED_ATOMIC_ABI_PROBE_FAILED"),
          "failed exact mapped atomic probe was not exposed in fallback telemetry");
    } finally {
      supervisor.close();
    }
  }

  private static void testTimeoutReenqueueCannotRebindActiveIdentity() throws Exception {
    for (var iteration = 0; iteration < 32; ++iteration) {
      var ledger = new LocalSidecarClient.RequestIdentityLedger();
      var clock = new AtomicLong(100);
      var transport = new BlockingWriteTransport();
      var client = new LocalSidecarClient(
          transport,
          id(20 + iteration),
          20 + iteration,
          1,
          1,
          clock::get,
          new CountingIds(),
          ledger,
          ignored -> {},
          (request, response) -> null,
          Duration.ofNanos(10),
          Duration.ofMillis(1));
      var blocker = client.tryEnqueue(
          LocalSidecarClient.submitRequest(
              ascii("timeout-blocker-" + iteration), new byte[] {1}));
      require(blocker.accepted(), "timeout race blocker was rejected");
      require(transport.writeEntered.await(TEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS),
          "timeout race blocker did not enter transport write");

      clock.set(0);
      var requestId = ascii("timeout-race-" + iteration);
      var exact = LocalSidecarClient.submitRequest(requestId, new byte[] {2});
      var timedOut = client.tryEnqueue(exact);
      require(timedOut.accepted(), "timeout race request was rejected");
      var replacement = new AtomicReference<LocalSidecarClient.Submission>();
      var retry = new Thread(
          () -> {
            while (replacement.get() == null && client.isAccepting()) {
              var candidate = client.tryEnqueue(exact);
              if (candidate.accepted()) {
                replacement.compareAndSet(null, candidate);
                return;
              }
              Thread.onSpinWait();
            }
          },
          "timeout-exact-reenqueue-" + iteration);
      retry.start();
      clock.set(11);
      waitUntil(() -> replacement.get() != null, "exact timeout-race re-enqueue");
      join(retry, "exact timeout-race re-enqueue");
      expectFailure(timedOut.completion(), LocalSidecarClient.RequestTimeoutException.class);

      for (var conflictAttempt = 0; conflictAttempt < 8; ++conflictAttempt) {
        var conflict = client.tryEnqueue(
            LocalSidecarClient.submitRequest(requestId, new byte[] {3}));
        require(!conflict.accepted(),
            "different body was admitted while the exact timeout retry was active");
        expectFailure(conflict.completion(), LocalSidecarClient.RequestConflictException.class);
      }

      transport.releaseWrite.countDown();
      waitUntil(() -> client.telemetry().inFlight() == 2,
          "timeout retry native-reachable handoff");
      client.fence(
          LocalSidecarClient.FailureKind.TRANSPORT,
          new IOException("timeout race terminal fence"));
      expectAnyFailure(blocker.completion());
      expectAnyFailure(replacement.get().completion());

      var nextGeneration = new LocalSidecarClient(
          new SinkTransport(),
          id(200 + iteration),
          200 + iteration,
          1,
          1,
          ledger,
          ignored -> {});
      var changedBody = nextGeneration.tryEnqueue(
          LocalSidecarClient.submitRequest(requestId, new byte[] {3}));
      require(!changedBody.accepted(),
          "timeout/re-enqueue race rebound a native-reachable request ID");
      expectFailure(
          changedBody.completion(), LocalSidecarClient.RequestConflictException.class);
      nextGeneration.close();
      client.close();
    }
  }

  private static void testDefaultCorrelationAllocationIsMonotonicAndConcurrent()
      throws Exception {
    var pair = TransportPair.create();
    var failures = new LinkedBlockingQueue<LocalSidecarClient.Failure>();
    var client = new LocalSidecarClient(pair.javaEndpoint, id(1), 3, 1, 1, failures::add);
    var submissions = new LocalSidecarClient.Submission[SidecarIpcV1.IN_FLIGHT_CORRELATIONS];
    var callers = new ArrayList<Thread>();
    var start = new CountDownLatch(1);
    for (var index = 0; index < submissions.length; ++index) {
      var requestIndex = index;
      var caller = new Thread(
          () -> {
            awaitLatch(start);
            submissions[requestIndex] = client.tryEnqueue(
                LocalSidecarClient.submitRequest(
                    ascii("default-correlation-" + requestIndex),
                    new byte[] {(byte) requestIndex}));
          },
          "default-correlation-caller-" + index);
      caller.start();
      callers.add(caller);
    }
    start.countDown();
    for (var caller : callers) {
      join(caller, "default correlation caller");
    }
    for (var submission : submissions) {
      require(submission != null && submission.accepted(),
          "default correlation allocation blocked or rejected a bounded caller");
    }

    var correlations = new HashSet<SidecarIpcV1.Id128>();
    for (var index = 0; index < submissions.length; ++index) {
      var request = SidecarIpcV1.decodeFrame(pair.peerEndpoint.read());
      require(correlations.add(request.correlationId()),
          "default correlation source produced a duplicate ID");
      pair.peerEndpoint.write(
          submitResponse(
              request,
              request.sessionId(),
              request.generation(),
              index + 1L)
              .canonicalBytes());
    }
    for (var value = 1; value <= submissions.length; ++value) {
      require(correlations.contains(id(value)),
          "default correlation source was not the session-scoped monotonic allocator");
    }
    for (var submission : submissions) {
      await(submission.completion());
    }
    require(failures.isEmpty(),
        "default correlation allocation caused a generation failure");
    client.close();
  }

  private static void testStaleAndDuplicateResponseSuppression() throws Exception {
    var pair = TransportPair.create();
    var failures = new LinkedBlockingQueue<LocalSidecarClient.Failure>();
    var client = client(pair.javaEndpoint, failures::add, System::nanoTime, new CountingIds());
    var request = LocalSidecarClient.submitRequest(ascii("stale"), new byte[] {4, 5});
    var submission = client.tryEnqueue(request);
    require(submission.accepted(), "normal request was rejected");
    var received = SidecarIpcV1.decodeFrame(pair.peerEndpoint.read());

    pair.peerEndpoint.write(submitResponse(received, id(99), received.generation(), 1)
        .canonicalBytes());
    pair.peerEndpoint.write(submitResponse(
        received, received.sessionId(), received.generation(), 1, 2, 0x21).canonicalBytes());
    var response = await(submission.completion());
    require(response.messageType() == SidecarIpcV1.MessageType.SUBMIT_RESPONSE,
        "validated response was not published");
    requireOperationalTiming(response.operationalTiming());
    waitUntil(() -> client.telemetry().staleResponses() == 1, "stale response count");

    var conflict = client.tryEnqueue(
        LocalSidecarClient.submitRequest(ascii("stale"), new byte[] {9}));
    require(!conflict.accepted(), "completed request ID accepted a conflicting body");
    expectFailure(conflict.completion(), LocalSidecarClient.RequestConflictException.class);
    var exactRetry = client.tryEnqueue(
        LocalSidecarClient.submitRequest(ascii("stale"), new byte[] {4, 5}));
    require(exactRetry.accepted(), "completed exact request could not be retried");
    var retried = SidecarIpcV1.decodeFrame(pair.peerEndpoint.read());
    pair.peerEndpoint.write(submitResponse(
        retried, retried.sessionId(), retried.generation(), 2, 91, 0x21).canonicalBytes());
    requireOperationalTiming(await(exactRetry.completion()).operationalTiming());
    pair.peerEndpoint.write(submitResponse(
        retried, retried.sessionId(), retried.generation(), 3).canonicalBytes());
    waitUntil(() -> client.telemetry().duplicateResponses() == 1, "duplicate response count");
    require(client.isAccepting() && failures.isEmpty(),
        "stale or duplicate response changed current-generation availability");

    var changedDurableRetry = client.tryEnqueue(
        LocalSidecarClient.submitRequest(ascii("stale"), new byte[] {4, 5}));
    require(changedDurableRetry.accepted(), "durable-proof negative retry was rejected locally");
    var changed = SidecarIpcV1.decodeFrame(pair.peerEndpoint.read());
    pair.peerEndpoint.write(submitResponse(
        changed, changed.sessionId(), changed.generation(), 4, 92, 0x22).canonicalBytes());
    expectFailure(changedDurableRetry.completion(), SidecarIpcV1.ProtocolException.class);
    var proofFailure = failures.poll(TEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS);
    require(proofFailure != null
            && proofFailure.kind() == LocalSidecarClient.FailureKind.PROTOCOL
            && client.telemetry().fenced(),
        "changed durable SUBMIT field did not permanently protocol-fence the generation");
    require(client.telemetry().requestConflicts() == 1,
        "completed request conflict was not retained in the generation ledger");
    require(client.telemetry().retries() == 2,
        "accepted exact same-generation retry was not counted");
    client.close();
  }

  private static void testVoteStaleGenerationResponseSuppression() throws Exception {
    var pair = TransportPair.create();
    var failures = new LinkedBlockingQueue<LocalSidecarClient.Failure>();
    var client = client(pair.javaEndpoint, failures::add, System::nanoTime, new CountingIds());
    var request = LocalSidecarClient.voteRequest(
        ascii("vote-stale-generation"), new byte[] {4, 5, 6});
    var submission = client.tryEnqueue(request);
    require(submission.accepted(), "VOTE stale-generation request was rejected");
    var received = SidecarIpcV1.decodeFrame(pair.peerEndpoint.read());

    var receipt = ascii("opaque-native-vote-receipt");
    pair.peerEndpoint.write(
        voteResponse(
                received,
                received.sessionId(),
                Math.addExact(received.generation(), 1),
                1,
                2,
                receipt)
            .canonicalBytes());
    pair.peerEndpoint.write(
        voteResponse(
                received,
                received.sessionId(),
                received.generation(),
                1,
                2,
                receipt)
            .canonicalBytes());
    var response = await(submission.completion());
    require(response.messageType() == SidecarIpcV1.MessageType.VOTE_RESPONSE,
        "current-generation VOTE response was not published");
    requireOperationalTiming(response.operationalTiming());
    waitUntil(
        () -> client.telemetry().staleResponses() == 1,
        "stale-generation VOTE response count");
    require(client.isAccepting() && failures.isEmpty(),
        "stale-generation VOTE response changed generation availability");
    client.close();
  }

  private static void testAdmittedRetryCannotBecomeNotAdmitted() throws Exception {
    var pair = TransportPair.create();
    var failures = new LinkedBlockingQueue<LocalSidecarClient.Failure>();
    var client = client(pair.javaEndpoint, failures::add, System::nanoTime, new CountingIds());
    var request = LocalSidecarClient.submitRequest(
        ascii("admitted-then-not-admitted"), new byte[] {4, 6});
    var admitted = client.tryEnqueue(request);
    require(admitted.accepted(), "first durable-result request was rejected");
    var firstFrame = SidecarIpcV1.decodeFrame(pair.peerEndpoint.read());
    pair.peerEndpoint.write(
        submitResponse(firstFrame, firstFrame.sessionId(), firstFrame.generation(), 1)
            .canonicalBytes());
    await(admitted.completion());

    var retry = client.tryEnqueue(request);
    require(retry.accepted(), "exact durable-result retry was rejected locally");
    var retryFrame = SidecarIpcV1.decodeFrame(pair.peerEndpoint.read());
    pair.peerEndpoint.write(notAdmittedResponse(retryFrame, 2).canonicalBytes());
    expectFailure(retry.completion(), SidecarIpcV1.ProtocolException.class);
    var failure = failures.poll(TEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS);
    require(failure != null
            && failure.kind() == LocalSidecarClient.FailureKind.PROTOCOL
            && client.telemetry().fenced(),
        "NOT_ADMITTED after a bound durable result did not fence the generation");
    client.close();
  }

  private static void testCorrelationPermitFenceCompletesAll() throws Exception {
    var transport = new SinkTransport();
    var client = client(transport, ignored -> {}, System::nanoTime, new CountingIds());
    var submissions = new ArrayList<LocalSidecarClient.Submission>();
    for (var index = 0; index < SidecarIpcV1.IN_FLIGHT_CORRELATIONS; ++index) {
      var submission = client.tryEnqueue(
          LocalSidecarClient.submitRequest(
              ascii("in-flight-" + index), new byte[] {(byte) index}));
      require(submission.accepted(), "request within correlation bound was rejected");
      submissions.add(submission);
    }
    waitUntil(
        () -> client.telemetry().inFlight() == SidecarIpcV1.IN_FLIGHT_CORRELATIONS,
        "all correlation permits in flight");
    for (var index = 0; index < SidecarIpcV1.INGRESS_QUEUE_REQUESTS; ++index) {
      var submission = client.tryEnqueue(
          LocalSidecarClient.submitRequest(
              ascii("permit-wait-" + index), new byte[] {(byte) index}));
      require(submission.accepted(), "request within queue bound was rejected at permit wait");
      submissions.add(submission);
    }
    waitUntil(
        () -> client.telemetry().queued() == SidecarIpcV1.INGRESS_QUEUE_REQUESTS,
        "full queue behind correlation permits");
    client.close();
    for (var submission : submissions) {
      expectFailure(submission.completion(), LocalSidecarClient.GenerationFencedException.class);
    }
    require(client.telemetry().queued() == 0 && client.telemetry().inFlight() == 0,
        "fence left a request outside both bounded containers");
  }

  private static void testWrongErrorResponseOperationIsStale() throws Exception {
    var pair = TransportPair.create();
    var failures = new LinkedBlockingQueue<LocalSidecarClient.Failure>();
    var client = client(pair.javaEndpoint, failures::add, System::nanoTime, new CountingIds());
    var submission = client.tryEnqueue(
        LocalSidecarClient.submitRequest(ascii("error-operation"), new byte[] {1, 2}));
    require(submission.accepted(), "ERROR_RESPONSE binding request was rejected");
    var request = SidecarIpcV1.decodeFrame(pair.peerEndpoint.read());

    pair.peerEndpoint.write(errorResponse(
        request, SidecarIpcV1.MessageType.STATE_REQUEST, 1).canonicalBytes());
    waitUntil(
        () -> client.telemetry().staleResponses() == 1,
        "wrong ERROR_RESPONSE offending message type rejection");
    require(!submission.completion().toCompletableFuture().isDone(),
        "wrong ERROR_RESPONSE offending message type completed the request");

    pair.peerEndpoint.write(errorResponse(
        request, SidecarIpcV1.MessageType.SUBMIT_REQUEST, 2).canonicalBytes());
    var response = await(submission.completion());
    require(response.messageType() == SidecarIpcV1.MessageType.ERROR_RESPONSE,
        "correctly bound ERROR_RESPONSE was not accepted");
    require(client.isAccepting() && failures.isEmpty(),
        "wrong ERROR_RESPONSE offending message type fenced the generation");
    client.close();
  }

  private static void testSafePreparseSentinel() throws Exception {
    var pair = TransportPair.create();
    var failures = new LinkedBlockingQueue<LocalSidecarClient.Failure>();
    var client = client(pair.javaEndpoint, failures::add, System::nanoTime, new CountingIds());
    var request = LocalSidecarClient.submitRequest(ascii("preparse"), new byte[] {6});
    var submission = client.tryEnqueue(request);
    var received = SidecarIpcV1.decodeFrame(pair.peerEndpoint.read());
    pair.peerEndpoint.write(preparseSentinel(
        received, SidecarIpcV1.MessageType.STATE_REQUEST, 1).canonicalBytes());
    waitUntil(
        () -> client.telemetry().staleResponses() == 1,
        "wrong preparse sentinel offending message type rejection");
    require(!submission.completion().toCompletableFuture().isDone(),
        "wrong preparse sentinel offending message type completed the request");
    pair.peerEndpoint.write(preparseSentinel(
        received, SidecarIpcV1.MessageType.SUBMIT_REQUEST, 2).canonicalBytes());

    expectFailure(submission.completion(), SidecarIpcV1.ProtocolException.class);
    var failure = failures.poll(TEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS);
    require(failure != null && failure.kind() == LocalSidecarClient.FailureKind.PROTOCOL,
        "trusted preparse sentinel did not immediately protocol-fence the generation");
    require(client.telemetry().fenced() && client.telemetry().rejectedFrames() == 1,
        "preparse sentinel fencing telemetry changed");
    require(client.outcomeUnknownRequests().isEmpty(),
        "proven pre-admission rejection was mislabeled outcome-unknown");
    client.close();
  }

  private static void testSharedMemoryCarrierFences() throws Exception {
    var pair = TransportPair.create();
    var failures = new LinkedBlockingQueue<LocalSidecarClient.Failure>();
    var client = client(pair.javaEndpoint, failures::add, System::nanoTime, new CountingIds());
    var request = LocalSidecarClient.submitRequest(ascii("shm-disabled"), new byte[] {7});
    var submission = client.tryEnqueue(request);
    var received = SidecarIpcV1.decodeFrame(pair.peerEndpoint.read());
    var shared = submitResponse(
        received, received.sessionId(), received.generation(), 1).canonicalBytes();
    ByteBuffer.wrap(shared).order(ByteOrder.BIG_ENDIAN)
        .putInt(16, SidecarIpcV1.FLAG_PAYLOAD_SHARED_MEMORY);
    pair.peerEndpoint.write(shared);

    expectFailure(submission.completion(), SidecarIpcV1.ProtocolException.class);
    var failure = failures.poll(TEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS);
    require(failure != null && failure.kind() == LocalSidecarClient.FailureKind.PROTOCOL,
        "disabled shared-memory carrier did not protocol-fence the generation");
    require(client.telemetry().rejectedFrames() == 1,
        "disabled shared-memory frame was not rejected before publication");
    require(client.outcomeUnknownRequests().equals(List.of(request)),
        "handed request was not retained for native recovery after malformed response");
    client.close();
  }

  private static void testPostHandoffTimeoutIsOutcomeUnknown() throws Exception {
    var pair = TransportPair.create();
    var failures = new LinkedBlockingQueue<LocalSidecarClient.Failure>();
    var clock = new AtomicLong();
    var client = new LocalSidecarClient(
        pair.javaEndpoint,
        id(7),
        11,
        1,
        1,
        clock::get,
        new CountingIds(),
        failures::add,
        Duration.ofNanos(10),
        Duration.ofMillis(1));
    var request = LocalSidecarClient.submitRequest(ascii("watchdog"), new byte[] {8});
    var submission = client.tryEnqueue(request);
    SidecarIpcV1.decodeFrame(pair.peerEndpoint.read());
    clock.set(11);

    var failure = failures.poll(TEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS);
    require(failure != null && failure.kind() == LocalSidecarClient.FailureKind.OUTCOME_UNKNOWN,
        "post-handoff watchdog did not produce OUTCOME_UNKNOWN");
    expectFailure(submission.completion(), LocalSidecarClient.RequestTimeoutException.class);
    require(client.outcomeUnknownRequests().equals(List.of(request)),
        "watchdog did not retain the exact immutable request for recovery retry");
    require(client.telemetry().outcomeUnknown() == 1 && client.telemetry().fenced(),
        "post-handoff watchdog telemetry changed");
    client.close();
  }

  private static void testConcurrentUnknownRecordingIsExactlyOnce() throws Exception {
    var transport = new SinkTransport();
    var client = client(transport, ignored -> {}, System::nanoTime, new CountingIds());
    var request = LocalSidecarClient.submitRequest(ascii("concurrent-unknown"), new byte[] {8});
    var submission = client.tryEnqueue(request);
    require(submission.accepted(), "concurrent-unknown request was rejected");
    waitUntil(() -> client.telemetry().inFlight() == 1, "concurrent-unknown handoff");

    var start = new CountDownLatch(1);
    var terminators = new ArrayList<Thread>();
    for (var index = 0; index < 24; ++index) {
      var close = (index & 1) == 0;
      var terminator = new Thread(
          () -> {
            awaitLatch(start);
            if (close) {
              client.close();
            } else {
              client.fence(
                  LocalSidecarClient.FailureKind.OUTCOME_UNKNOWN,
                  new LocalSidecarClient.OutcomeUnknownException("concurrent fence"));
            }
          },
          "concurrent-unknown-terminator-" + index);
      terminator.start();
      terminators.add(terminator);
    }
    start.countDown();
    for (var terminator : terminators) {
      join(terminator, "concurrent unknown terminator");
    }
    expectAnyFailure(submission.completion());
    require(client.outcomeUnknownRequests().equals(List.of(request)),
        "concurrent terminal paths did not retain exactly one immutable unknown request");
    require(client.telemetry().outcomeUnknown() == 1,
        "concurrent terminal paths counted one unknown request more than once");
  }

  private static void testTerminalCloseLinearizesBeforeCompletion() throws Exception {
    var pair = TransportPair.create();
    var callbackComplete = new CountDownLatch(1);
    var callbackFailures = new LinkedBlockingQueue<Throwable>();
    var callbackRejected = new AtomicBoolean();
    var client = client(
        pair.javaEndpoint,
        failure -> {
          if (failure.kind() == LocalSidecarClient.FailureKind.EXPECTED_CLOSE) {
            throw new IllegalStateException("observer failure after terminal CLOSE");
          }
        },
        System::nanoTime,
        new CountingIds());
    var close = client.tryEnqueue(
        LocalSidecarClient.closeRequest(
            ascii("linearized-close"), id(400), SidecarIpcV1.CloseMode.TERMINATE_AND_FENCE));
    require(close.accepted(), "terminal CLOSE request was rejected");
    var request = SidecarIpcV1.decodeFrame(pair.peerEndpoint.read());
    close.completion().whenComplete(
        (response, error) -> {
          try {
            require(error == null && response != null,
                "terminal CLOSE did not publish its validated response");
            var afterClose = client.tryEnqueue(
                LocalSidecarClient.submitRequest(ascii("after-close"), new byte[] {1}));
            callbackRejected.set(!afterClose.accepted());
            require(afterClose.completion().toCompletableFuture().isCompletedExceptionally(),
                "post-CLOSE rejection was not contained in its CompletionStage");
            require(!client.isAccepting()
                    && client.telemetry().closed()
                    && client.telemetry().fenced(),
                "CLOSE completion callback observed a nonterminal client");
            require(pair.javaEndpoint.successfulWrites.get() == 1,
                "CLOSE completion callback caused a post-close transport write");
          } catch (Throwable failure) {
            callbackFailures.add(failure);
          } finally {
            callbackComplete.countDown();
          }
        });
    pair.peerEndpoint.write(terminalCloseResponse(request, 1).canonicalBytes());
    var response = await(close.completion());
    require(response.messageType() == SidecarIpcV1.MessageType.CLOSE_RESPONSE,
        "terminal CLOSE returned the wrong response");
    require(callbackComplete.await(TEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS),
        "terminal CLOSE completion callback did not run");
    require(callbackFailures.isEmpty(),
        "terminal CLOSE completion callback observed an invalid state: "
            + (callbackFailures.peek() == null ? "" : callbackFailures.peek().getMessage()));
    require(callbackRejected.get(), "terminal CLOSE callback admitted a later request");
  }

  private static void testTerminalCloseRacesAlwaysComplete() throws Exception {
    for (var fenceRace = 0; fenceRace < 2; ++fenceRace) {
      var pair = TransportPair.create();
      var client = client(pair.javaEndpoint, ignored -> {}, System::nanoTime, new CountingIds());
      var close = client.tryEnqueue(
          LocalSidecarClient.closeRequest(
              ascii("racing-close-" + fenceRace),
              id(401 + fenceRace),
              SidecarIpcV1.CloseMode.TERMINATE_AND_FENCE));
      require(close.accepted(), "racing CLOSE request was rejected");
      var request = SidecarIpcV1.decodeFrame(pair.peerEndpoint.read());
      var start = new CountDownLatch(1);
      var responder = new Thread(
          () -> {
            awaitLatch(start);
            try {
              pair.peerEndpoint.write(terminalCloseResponse(request, 1).canonicalBytes());
            } catch (IOException expectedIfLocalTerminalWon) {
              // A local terminal transition may close the endpoint before the response write.
            }
          },
          "racing-close-response");
      var useFence = fenceRace != 0;
      var terminator = new Thread(
          () -> {
            awaitLatch(start);
            if (useFence) {
              client.fence(
                  LocalSidecarClient.FailureKind.TRANSPORT,
                  new IOException("concurrent terminal fence"));
            } else {
              client.close();
            }
          },
          "racing-close-terminal");
      responder.start();
      terminator.start();
      start.countDown();
      join(responder, "racing CLOSE responder");
      join(terminator, "racing CLOSE terminator");
      awaitSuccessOrFailure(close.completion());
      require(close.completion().toCompletableFuture().isDone(),
          "CLOSE racing a local terminal transition orphaned its future");
      require(!client.isAccepting() && client.telemetry().fenced(),
          "CLOSE race left the generation accepting");
      client.close();
    }
  }

  private static void testUnsignedMaxSequenceAcceptedOnce() throws Exception {
    var pair = TransportPair.create();
    var failures = new LinkedBlockingQueue<LocalSidecarClient.Failure>();
    var client = new LocalSidecarClient(
        pair.javaEndpoint,
        id(12),
        13,
        -1L,
        -1L,
        System::nanoTime,
        new CountingIds(),
        failures::add,
        Duration.ofHours(1),
        Duration.ofHours(1));
    var atMaximum = client.tryEnqueue(
        LocalSidecarClient.submitRequest(ascii("unsigned-max"), new byte[] {1}));
    require(atMaximum.accepted(), "unsigned-max request was rejected before transport");
    var request = SidecarIpcV1.decodeFrame(pair.peerEndpoint.read());
    require(request.sequence() == -1L,
        "unsigned-max request sequence was narrowed before transmission");
    pair.peerEndpoint.write(
        submitResponse(request, request.sessionId(), request.generation(), -1L)
            .canonicalBytes());
    require(await(atMaximum.completion()).messageType()
            == SidecarIpcV1.MessageType.SUBMIT_RESPONSE,
        "unsigned-max response was not accepted exactly once");

    var afterMaximum = client.tryEnqueue(
        LocalSidecarClient.submitRequest(ascii("after-unsigned-max"), new byte[] {2}));
    require(afterMaximum.accepted(), "post-max request did not reach sequence fence");
    expectFailure(afterMaximum.completion(), SidecarIpcV1.ProtocolException.class);
    var failure = failures.poll(TEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS);
    require(failure != null && failure.kind() == LocalSidecarClient.FailureKind.PROTOCOL,
        "attempt after unsigned max did not permanently protocol-fence the generation");
    require(client.telemetry().fenced(), "sequence exhaustion left generation accepting");
    require(client.outcomeUnknownRequests().isEmpty(),
        "request rejected before the post-max write was mislabeled outcome-unknown");
    client.close();
  }

  private static void testLateReadAfterCountingTransportCloseDoesNotRepublish()
      throws Exception {
    var ledger = new SidecarSupervisor.CopyLedger();
    var newerGeneration = 42L;
    var newerResponse = copyTestErrorResponse(newerGeneration, 42);
    var newer =
        new SidecarSupervisor.CountingTransport(
            new OneShotReadTransport(newerResponse), ledger, newerGeneration);
    require(
        Arrays.equals(newer.read(), newerResponse),
        "newer-generation copy test did not read its response");
    require(
        ledger.transientObservationCount() == 1,
        "newer-generation copy observation was not retained for isolation test");

    var closedGeneration = 41L;
    var lateResponse = copyTestErrorResponse(closedGeneration, 41);
    var lateDelegate = new LateReadAfterCloseTransport(lateResponse);
    var closed =
        new SidecarSupervisor.CountingTransport(lateDelegate, ledger, closedGeneration);
    var lateBytes = new AtomicReference<byte[]>();
    var lateFailure = new AtomicReference<Throwable>();
    var reader = new Thread(
        () -> {
          try {
            lateBytes.set(closed.read());
          } catch (Throwable error) {
            lateFailure.set(error);
          }
        },
        "delta-sidecar-late-counting-read");
    reader.setDaemon(true);
    reader.start();
    require(
        lateDelegate.readEntered.await(TEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS),
        "late copy read did not enter the delegate");

    closed.close();
    require(
        ledger.transientObservationCount() == 1,
        "closing an old generation cleared a newer generation observation");
    lateDelegate.releaseRead.countDown();
    reader.join(TEST_TIMEOUT.toMillis());
    require(!reader.isAlive(), "late copy read did not finish after release");
    require(lateFailure.get() == null, "late copy read failed: " + lateFailure.get());
    require(Arrays.equals(lateBytes.get(), lateResponse), "late copy read bytes changed");
    require(
        ledger.transientObservationCount() == 1,
        "late read republished a closed-generation copy observation");

    newer.close();
    require(
        ledger.transientObservationCount() == 0,
        "newer-generation close did not clear its copy observation");
  }

  private static byte[] copyTestErrorResponse(long generation, int identityByte) {
    var prepared =
        LocalSidecarClient.submitRequest(
            ascii("copy-close-" + identityByte), new byte[] {(byte) identityByte});
    var request =
        SidecarIpcV1.frame(
            SidecarIpcV1.MessageType.SUBMIT_REQUEST,
            id(identityByte),
            generation,
            id(identityByte + 64),
            1,
            SidecarIpcV1.decodePayload(prepared.type(), prepared.canonicalPayload()));
    return notAdmittedResponse(request, 2).canonicalBytes();
  }

  private static void testSupervisorRecoveryRetryAndExpectedClose() throws Exception {
    var connector = new FakeConnector();
    var durableDirectory = Files.createTempDirectory("delta-sidecar-fake-");
    var config = new SidecarSupervisor.Config(
        durableDirectory,
        new byte[] {1, 2, 3},
        digest(0x44),
        BUILD_ID,
        nestedDescriptor());
    var timing = new SidecarSupervisor.Timing(
        Duration.ofSeconds(30),
        Duration.ofMillis(100),
        Duration.ofSeconds(2),
        Duration.ofMillis(1));
    var supervisor = new SidecarSupervisor(config, connector, timing, Thread::sleep);
    try {
      var firstClient = await(supervisor.start());
      require(supervisor.state() == SidecarSupervisor.State.READY,
          "supervisor did not reach READY after descriptor/open recovery");
      var exact = LocalSidecarClient.submitRequest(ascii("supervised-retry"), new byte[] {9, 10});
      var firstAttempt = firstClient.tryEnqueue(exact);
      require(firstAttempt.accepted(), "first supervised request was rejected");
      expectAnyFailure(firstAttempt.completion());
      waitUntil(
          () -> connector.launches.get() == 2
              && supervisor.state() == SidecarSupervisor.State.READY,
          "replacement generation READY");
      require(
          supervisor.transientCopyObservationCount() == 0,
          "failed generation retained transient copy observations across recovery");
      require(firstClient.outcomeUnknownRequests().equals(List.of(exact)),
          "failed generation lost the exact outcome-unknown request");

      var conflict = supervisor.client().tryEnqueue(
          LocalSidecarClient.submitRequest(ascii("supervised-retry"), new byte[] {99}));
      require(!conflict.accepted(),
          "replacement generation accepted a conflicting prior request ID");
      expectFailure(conflict.completion(), LocalSidecarClient.RequestConflictException.class);
      var retry = supervisor.retryAfterRecovery(exact);
      require(retry.accepted(), "exact retry after READY was rejected");
      var retryResponse = await(retry.completion());
      requireOperationalTiming(retryResponse.operationalTiming());
      require(retryResponse.messageType() == SidecarIpcV1.MessageType.SUBMIT_RESPONSE
              && retryResponse.admittedSequenceBits() == 2,
          "recovery retry did not return the durable native result");
      var retryCopy = supervisor.operationCopy(retryResponse);
      require(
          retryCopy.generation() == 2
              && retryCopy.inlineIngressBytes()
                  == Math.addExact(
                      SidecarIpcV1.HEADER_BYTES, exact.canonicalPayloadLength())
              && retryCopy.inlineEgressBytes()
                  == Math.addExact(
                      SidecarIpcV1.HEADER_BYTES, retryResponse.payload().canonicalLength())
              && retryCopy.sharedMemoryIngressBytes() == 0
              && retryCopy.sharedMemoryEgressBytes() == 0
              && retryCopy.stagingFallbackIngressBytes() == exact.canonicalPayloadLength()
              && retryCopy.stagingFallbackEgressBytes()
                  == retryResponse.payload().canonicalLength()
              && retryCopy.zeroCopyEligibleCount() == 1
              && retryCopy.zeroCopyHitCount() == 0,
          "correlation-bound inline SUBMIT copy evidence is not exact");
      require(
          supervisor.transientCopyObservationCount() == 0,
          "completed SUBMIT retained transient copy observations");
      waitUntil(() -> connector.submitPayloads.size() == 2, "both submit attempts recorded");
      require(Arrays.equals(
              connector.submitPayloads.get(0), connector.submitPayloads.get(1)),
          "retry changed the canonical operation/request ID/body/digest");

      var close = supervisor.client().tryEnqueue(
          LocalSidecarClient.closeRequest(
              ascii("supervised-close"),
              supervisor.runtimeInstanceId(),
              SidecarIpcV1.CloseMode.TERMINATE_AND_FENCE));
      require(close.accepted(), "CLOSE request was rejected");
      var closeResponse = await(close.completion());
      require(closeResponse.messageType() == SidecarIpcV1.MessageType.CLOSE_RESPONSE
              && closeResponse.payload().u8(18) == 1,
          "CLOSE did not return closed=1");
      waitUntil(() -> supervisor.state() == SidecarSupervisor.State.CLOSED,
          "expected-close supervisor state");
      require(
          supervisor.transientCopyObservationCount() == 0,
          "closed generation retained transient copy observations");
      Thread.sleep(25);
      require(connector.launches.get() == 2,
          "validated CLOSE_RESPONSE incorrectly triggered a restart");

      var telemetry = supervisor.telemetry();
      require(telemetry.inlineIngressBytes() > 0 && telemetry.inlineEgressBytes() > 0,
          "inline copy traffic was not accounted");
      require(telemetry.stagingFallbackIngressBytes() > 0
              && telemetry.stagingFallbackEgressBytes() > 0,
          "bounded staging fallback traffic was not accounted");
      require(telemetry.sharedMemoryIngressBytes() == 0
              && telemetry.sharedMemoryEgressBytes() == 0
              && telemetry.zeroCopyEligibleCount() > 0
              && telemetry.zeroCopyHitCount() == 0,
          "inline-only fake transport SHM counters are inconsistent");
      require(telemetry.sharedMemoryStatus().equals(
              SidecarSharedMemory.atomicAbiSupported()
                  ? "AVAILABLE_NOT_CONFIGURED"
                  : "DISABLED_ATOMIC_ABI_UNAVAILABLE"),
          "shared-memory capability evidence label changed");
      require(telemetry.client() != null && telemetry.client().retries() == 1,
          "accepted exact cross-generation retry was not counted");
      var maximum = telemetry.maxSubmitStagingFallback();
      require(maximum != null
              && maximum.requestType() == SidecarIpcV1.MessageType.SUBMIT_REQUEST
              && maximum.generation() == 2
              && maximum.correlationId().length() == 32,
          "maximum measured SUBMIT copy pair lacks stable operation identity");
      require(maximum.stagingFallbackIngressBytes() == exact.canonicalPayload().length
              && maximum.stagingFallbackEgressBytes()
                  == retryResponse.payload().canonicalBytes().length
              && maximum.stagingFallbackTotalBytes()
                  == Math.addExact(
                      exact.canonicalPayload().length,
                      retryResponse.payload().canonicalBytes().length),
          "maximum measured SUBMIT copy pair is not exact ingress+egress bytes");
    } finally {
      supervisor.close();
    }
  }

  private static void testDurableDirectoryRebindFailsBeforeConnect() throws Exception {
    if (isWindows()) {
      return;
    }
    for (var symlinkReplacement : List.of(false, true)) {
      var root = Files.createTempDirectory("delta-sidecar-directory-rebind-");
      var durableDirectory = Files.createDirectory(root.resolve("durable"));
      var heldDirectory = root.resolve("held");
      var connector = new FakeConnector();
      var config = new SidecarSupervisor.Config(
          durableDirectory,
          new byte[] {1},
          digest(0x6a),
          BUILD_ID,
          nestedDescriptor());
      var supervisor = new SidecarSupervisor(config, connector);
      try {
        Files.move(durableDirectory, heldDirectory, StandardCopyOption.ATOMIC_MOVE);
        if (symlinkReplacement) {
          Files.createSymbolicLink(durableDirectory, heldDirectory);
        } else {
          Files.createDirectory(durableDirectory);
        }
        expectAnyFailure(supervisor.start());
        require(connector.launches.get() == 0,
            "durable directory replacement reached the generation connector");
        require(containsMessage(supervisor.lastFailure(), "durable directory"),
            "durable directory replacement did not retain a pathname-binding failure");
      } finally {
        supervisor.close();
      }
    }
  }

  private static void testWalReplacementBetweenGenerationsFailsBeforeConnect() throws Exception {
    if (isWindows()) {
      return;
    }
    var connector = new FakeConnector();
    var durableDirectory = Files.createTempDirectory("delta-sidecar-wal-rebind-");
    var config = new SidecarSupervisor.Config(
        durableDirectory,
        new byte[] {1},
        digest(0x6b),
        BUILD_ID,
        nestedDescriptor());
    var timing = new SidecarSupervisor.Timing(
        Duration.ofSeconds(30),
        Duration.ofMillis(100),
        Duration.ofSeconds(2),
        Duration.ofMillis(1));
    var backoffEntered = new CountDownLatch(1);
    var releaseBackoff = new CountDownLatch(1);
    var firstBackoff = new AtomicBoolean(true);
    var supervisor = new SidecarSupervisor(
        config,
        connector,
        timing,
        ignored -> {
          if (firstBackoff.compareAndSet(true, false)) {
            backoffEntered.countDown();
            releaseBackoff.await();
          }
        });
    try {
      var first = await(supervisor.start());
      var trigger = first.tryEnqueue(
          LocalSidecarClient.submitRequest(ascii("wal-rebind-trigger"), new byte[] {1}));
      require(trigger.accepted(), "WAL-rebind recovery trigger was rejected");
      expectAnyFailure(trigger.completion());
      require(backoffEntered.await(TEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS),
          "recovery did not confirm native death before replacement backoff");
      require(connector.firstConnection != null
              && !connector.firstConnection.isAlive()
              && connector.firstConnection.endpointClosed(),
          "WAL replacement test did not observe confirmed generation-1 death/cleanup");

      var wal = durableDirectory.resolve("runtime.wal");
      Files.move(wal, durableDirectory.resolve("runtime.wal.generation-1"));
      Files.write(
          wal,
          new byte[] {9, 9, 9},
          StandardOpenOption.CREATE_NEW,
          StandardOpenOption.WRITE);
      releaseBackoff.countDown();

      waitUntil(
          () -> supervisor.state() == SidecarSupervisor.State.UNREADY,
          "WAL replacement fail-closed recovery exhaustion");
      require(connector.launches.get() == 1,
          "replacement WAL reached the generation-2 connector");
      require(containsMessage(supervisor.lastFailure(), "runtime.wal pathname binding changed"),
          "replacement WAL did not retain the exact pathname-binding failure");
    } finally {
      releaseBackoff.countDown();
      supervisor.close();
    }
  }

  private static void testSupervisorVoteLostResponseRecoveryRetry() throws Exception {
    var connector = new FakeConnector();
    var durableDirectory = Files.createTempDirectory("delta-sidecar-vote-recovery-fake-");
    var config = new SidecarSupervisor.Config(
        durableDirectory,
        new byte[] {1, 2, 3},
        digest(0x45),
        BUILD_ID,
        nestedDescriptor());
    var timing = new SidecarSupervisor.Timing(
        Duration.ofSeconds(30),
        Duration.ofMillis(100),
        Duration.ofSeconds(2),
        Duration.ofMillis(1));
    var supervisor = new SidecarSupervisor(config, connector, timing, Thread::sleep);
    try {
      var firstClient = await(supervisor.start());
      var exact = LocalSidecarClient.voteRequest(
          ascii("supervised-vote-retry"), new byte[] {9, 10, 11});
      var lostResponse = firstClient.tryEnqueue(exact);
      require(lostResponse.accepted(), "first supervised VOTE was rejected");
      expectAnyFailure(lostResponse.completion());
      waitUntil(
          () -> connector.launches.get() == 2
              && supervisor.state() == SidecarSupervisor.State.READY,
          "replacement generation READY after lost VOTE response");
      require(firstClient.telemetry().fenced()
              && firstClient.outcomeUnknownRequests().equals(List.of(exact)),
          "dead VOTE generation was not fenced with the exact outcome-unknown request");

      var conflict = supervisor.client().tryEnqueue(
          LocalSidecarClient.voteRequest(
              ascii("supervised-vote-retry"), new byte[] {99}));
      require(!conflict.accepted(),
          "replacement generation accepted conflicting VOTE bytes for a prior request ID");
      expectFailure(conflict.completion(), LocalSidecarClient.RequestConflictException.class);

      var recovered = supervisor.retryAfterRecovery(exact);
      require(recovered.accepted(), "exact VOTE retry after READY was rejected");
      var recoveredResponse = await(recovered.completion());
      require(recoveredResponse.messageType() == SidecarIpcV1.MessageType.VOTE_RESPONSE
              && recoveredResponse.payload().u32(5) == 0,
          "recovered VOTE did not return its opaque durable result");
      var recoveredReceipt = recoveredResponse.payload().bytes(16);
      var recoveredReceiptDigest = recoveredResponse.payload().bytes(17);

      var sameGenerationRetry = supervisor.client().tryEnqueue(exact);
      require(sameGenerationRetry.accepted(),
          "same-generation exact VOTE retry was rejected");
      var repeatedResponse = await(sameGenerationRetry.completion());
      require(Arrays.equals(recoveredReceipt, repeatedResponse.payload().bytes(16))
              && Arrays.equals(
                  recoveredReceiptDigest, repeatedResponse.payload().bytes(17)),
          "exact VOTE replay changed the opaque durable recovery proof");

      waitUntil(() -> connector.votePayloads.size() == 3, "all VOTE attempts recorded");
      require(Arrays.equals(connector.votePayloads.get(0), connector.votePayloads.get(1))
              && Arrays.equals(connector.votePayloads.get(1), connector.votePayloads.get(2)),
          "VOTE recovery retry changed canonical operation/request ID/body/digest bytes");
      require(supervisor.state() == SidecarSupervisor.State.READY
              && supervisor.client().isAccepting(),
          "exact VOTE recovery retry did not preserve READY availability");
    } finally {
      supervisor.close();
    }
  }

  private static void testImmediatePostOpenFailureIsNotLost() throws Exception {
    var connector = new FakeConnector(false, false, false, true);
    var config = new SidecarSupervisor.Config(
        Files.createTempDirectory("delta-sidecar-post-open-failure-"),
        new byte[] {1},
        digest(0x4a),
        BUILD_ID,
        nestedDescriptor());
    var timing = new SidecarSupervisor.Timing(
        Duration.ofSeconds(30),
        Duration.ofMillis(25),
        Duration.ofSeconds(1),
        Duration.ofMillis(1));
    var supervisor = new SidecarSupervisor(config, connector, timing, Thread::sleep);
    try {
      var first = await(supervisor.start());
      var trigger = first.tryEnqueue(
          LocalSidecarClient.submitRequest(ascii("post-open-failure"), new byte[] {1}));
      require(trigger.accepted(), "post-OPEN recovery trigger was rejected");
      expectAnyFailure(trigger.completion());
      waitUntil(
          () -> connector.launches.get() == 3 && isReadyAndAccepting(supervisor),
          "follow-on recovery after immediate post-OPEN death");
      Thread.sleep(25);
      require(connector.launches.get() == 3,
          "immediate post-OPEN failure caused an unbounded or duplicate recovery");
    } finally {
      supervisor.close();
    }
  }

  private static void testReplacementOpenErrorClearsGenerationCopyObservations()
      throws Exception {
    var connector = new FakeConnector();
    connector.errorReplacementOpen.set(true);
    var config = new SidecarSupervisor.Config(
        Files.createTempDirectory("delta-sidecar-open-error-copy-cleanup-"),
        new byte[] {1},
        digest(0x4c),
        BUILD_ID,
        nestedDescriptor());
    var timing = new SidecarSupervisor.Timing(
        Duration.ofSeconds(30),
        Duration.ofMillis(25),
        Duration.ofSeconds(1),
        Duration.ofMillis(1));
    var supervisor = new SidecarSupervisor(config, connector, timing, Thread::sleep);
    try {
      var first = await(supervisor.start());
      var trigger = first.tryEnqueue(
          LocalSidecarClient.submitRequest(ascii("open-error-copy-cleanup"), new byte[] {1}));
      require(trigger.accepted(), "OPEN-error recovery trigger was rejected");
      expectAnyFailure(trigger.completion());
      waitUntil(
          () -> connector.launches.get() == 3 && isReadyAndAccepting(supervisor),
          "recovery after replacement OPEN ERROR_RESPONSE");
      require(
          supervisor.transientCopyObservationCount() == 0,
          "failed pre-READY generation retained ERROR_RESPONSE copy observations");
    } finally {
      supervisor.close();
    }
  }

  private static void testStalePendingReplacementFailureDoesNotKillReadyGeneration()
      throws Exception {
    var connector = new FakeConnector(false, false, false, false, true);
    var config = new SidecarSupervisor.Config(
        Files.createTempDirectory("delta-sidecar-stale-pending-failure-"),
        new byte[] {1},
        digest(0x4b),
        BUILD_ID,
        nestedDescriptor());
    var timing = new SidecarSupervisor.Timing(
        Duration.ofSeconds(30),
        Duration.ofMillis(25),
        Duration.ofSeconds(1),
        Duration.ofMillis(1));
    var supervisor = new SidecarSupervisor(config, connector, timing, Thread::sleep);
    try {
      var first = await(supervisor.start());
      var trigger = first.tryEnqueue(
          LocalSidecarClient.submitRequest(ascii("stale-pending-trigger"), new byte[] {1}));
      require(trigger.accepted(), "stale-pending recovery trigger was rejected");
      expectAnyFailure(trigger.completion());
      require(
          connector.retryableHandshakeRead.await(
              TEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS),
          "generation 2 did not enter its failing startup handshake");

      injectClientFailure(
          supervisor,
          new LocalSidecarClient.Failure(
              LocalSidecarClient.FailureKind.TRANSPORT,
              2,
              new IOException("generation 2 immediate startup failure")));
      connector.releaseRetryableHandshake.countDown();
      waitUntil(
          () -> connector.launches.get() == 3 && isReadyAndAccepting(supervisor),
          "healthy generation 3 after generation 2 startup cleanup");
      Thread.sleep(50);
      require(connector.launches.get() == 3 && isReadyAndAccepting(supervisor),
          "stale pending generation 2 failure killed healthy generation 3");
    } finally {
      connector.releaseRetryableHandshake.countDown();
      supervisor.close();
    }
  }

  private static void testImpossibleFutureFailureFailsClosed() throws Exception {
    var connector = new FakeConnector();
    var config = new SidecarSupervisor.Config(
        Files.createTempDirectory("delta-sidecar-future-failure-"),
        new byte[] {1},
        digest(0x4c),
        BUILD_ID,
        nestedDescriptor());
    var timing = new SidecarSupervisor.Timing(
        Duration.ofSeconds(30),
        Duration.ofMillis(25),
        Duration.ofSeconds(1),
        Duration.ofMillis(1));
    var supervisor = new SidecarSupervisor(config, connector, timing, Thread::sleep);
    var client = await(supervisor.start());
    injectClientFailure(
        supervisor,
        new LocalSidecarClient.Failure(
            LocalSidecarClient.FailureKind.TRANSPORT,
            2,
            new IOException("impossible future generation")));
    waitUntil(
        () -> supervisor.state() == SidecarSupervisor.State.UNREADY
            && client.telemetry().closed(),
        "impossible-generation fail-close");
    Thread.sleep(25);
    require(connector.launches.get() == 1,
        "impossible future generation triggered replacement recovery");
    require(supervisor.lastFailure() instanceof SidecarSupervisor.RecoveryException,
        "impossible future generation did not retain a terminal recovery failure");
    try {
      supervisor.client();
      throw new IllegalStateException("future-generation failure left admission READY");
    } catch (IllegalStateException expected) {
      require(expected.getMessage().equals("sidecar is not READY"),
          "future-generation fail-close exposed an unexpected client failure");
    }
    supervisor.close();
  }

  private static void testRecoveryReadyDeadlineAndRestartLimit() throws Exception {
    var connector = new FakeConnector(true);
    var config = new SidecarSupervisor.Config(
        Files.createTempDirectory("delta-sidecar-deadline-"),
        new byte[] {1},
        digest(0x45),
        BUILD_ID,
        nestedDescriptor());
    var timing = new SidecarSupervisor.Timing(
        Duration.ofSeconds(30),
        Duration.ofMillis(25),
        Duration.ofMillis(100),
        Duration.ofMillis(1));
    var supervisor = new SidecarSupervisor(config, connector, timing, Thread::sleep);
    try {
      var client = await(supervisor.start());
      var submission = client.tryEnqueue(
          LocalSidecarClient.submitRequest(ascii("deadline-trigger"), new byte[] {1}));
      require(submission.accepted(), "deadline trigger request was rejected");
      expectAnyFailure(submission.completion());
      waitUntil(
          () -> supervisor.state() == SidecarSupervisor.State.UNREADY
              && connector.launches.get() == 1 + SidecarSupervisor.RESTART_ATTEMPT_LIMIT,
          "bounded recovery attempts after hung handshake");
      require(connector.forcedTerminations.get() == SidecarSupervisor.RESTART_ATTEMPT_LIMIT,
          "recovery deadline did not force-terminate every exact hung generation");
      require(supervisor.lastFailure()
              instanceof SidecarSupervisor.RecoveryReadyTimeoutException,
          "hung recovery did not retain a recovery-ready timeout failure");
      Thread.sleep(25);
      require(connector.launches.get() == 1 + SidecarSupervisor.RESTART_ATTEMPT_LIMIT,
          "supervisor exceeded the frozen restart-attempt bound");
    } finally {
      supervisor.close();
    }
  }

  private static void testCleanupFailureStaysQuarantinedUntilConfirmed() throws Exception {
    var cleanupRelease = new CountDownLatch(1);
    var connector = new FakeConnector(cleanupRelease);
    var config = new SidecarSupervisor.Config(
        Files.createTempDirectory("delta-sidecar-retryable-cleanup-"),
        new byte[] {1},
        digest(0x45),
        BUILD_ID,
        nestedDescriptor());
    var timing = new SidecarSupervisor.Timing(
        Duration.ofSeconds(30),
        Duration.ofMillis(10),
        Duration.ofSeconds(1),
        Duration.ofMillis(1));
    var supervisor = new SidecarSupervisor(config, connector, timing, Thread::sleep);
    try {
      var client = await(supervisor.start());
      var submission = client.tryEnqueue(
          LocalSidecarClient.submitRequest(ascii("retryable-cleanup"), new byte[] {1}));
      require(submission.accepted(), "retryable-cleanup trigger was rejected");
      expectAnyFailure(submission.completion());
      waitUntil(
          () -> supervisor.state() == SidecarSupervisor.State.UNREADY
              && supervisor.quarantinedConnectionCount() == 1
              && connector.cleanupAttempts.get() >= 2,
          "failed cleanup retained in quarantine");
      require(connector.firstConnection != null
              && !connector.firstConnection.endpointClosed()
              && connector.firstConnection.closeCalls.get() == 0,
          "failed cleanup falsely confirmed endpoint/mapping release");
      Thread.sleep(10);
      require(supervisor.quarantinedConnectionCount() == 1
              && !connector.firstConnection.endpointClosed(),
          "quarantine cleared after repeated cleanup failure");
      cleanupRelease.countDown();
      waitUntil(
          () -> connector.firstConnection.endpointClosed()
              && connector.firstConnection.closeCalls.get() == 1
              && supervisor.quarantinedConnectionCount() == 0,
          "retryable cleanup confirmation and quarantine release");
    } finally {
      cleanupRelease.countDown();
      supervisor.close();
    }
  }

  private static void testUnconfirmedReplacementCleanupIsTerminal() throws Exception {
    var connector = new FakeConnector(false, true);
    var config = new SidecarSupervisor.Config(
        Files.createTempDirectory("delta-sidecar-unconfirmed-cleanup-"),
        new byte[] {1},
        digest(0x46),
        BUILD_ID,
        nestedDescriptor());
    var timing = new SidecarSupervisor.Timing(
        Duration.ofSeconds(30),
        Duration.ofMillis(10),
        Duration.ofSeconds(1),
        Duration.ofMillis(1));
    var supervisor = new SidecarSupervisor(config, connector, timing, Thread::sleep);
    try {
      var client = await(supervisor.start());
      var submission = client.tryEnqueue(
          LocalSidecarClient.submitRequest(ascii("unconfirmed-cleanup"), new byte[] {1}));
      require(submission.accepted(), "unconfirmed-cleanup trigger was rejected");
      expectAnyFailure(submission.completion());
      waitUntil(
          () -> supervisor.state() == SidecarSupervisor.State.UNREADY,
          "terminal unconfirmed replacement cleanup");
      require(connector.launches.get() == 2,
          "supervisor launched another generation after unconfirmed replacement cleanup");
      require(supervisor.lastFailure()
              instanceof SidecarSupervisor.ReplacementTerminationException,
          "unconfirmed replacement cleanup did not retain the terminal failure type");
      require(connector.unstoppableReplacement != null
              && connector.unstoppableReplacement.closeCalls.get() == 0,
          "unconfirmed live replacement released its retained generation resources");
      require(supervisor.quarantinedConnectionCount() == 1,
          "unconfirmed live replacement was not retained in quarantine");
      Thread.sleep(25);
      require(connector.launches.get() == 2,
          "terminal cleanup failure was retried after reaching UNREADY");
    } finally {
      supervisor.close();
    }
  }

  private static void testExpectedCloseRequiresConfirmedExit() throws Exception {
    var connector = new FakeConnector(false, false, true);
    var config = new SidecarSupervisor.Config(
        Files.createTempDirectory("delta-sidecar-unconfirmed-close-"),
        new byte[] {1},
        digest(0x47),
        BUILD_ID,
        nestedDescriptor());
    var timing = new SidecarSupervisor.Timing(
        Duration.ofSeconds(30),
        Duration.ofMillis(10),
        Duration.ofSeconds(1),
        Duration.ofMillis(1));
    var supervisor = new SidecarSupervisor(config, connector, timing, Thread::sleep);
    try {
      var client = await(supervisor.start());
      var close = client.tryEnqueue(
          LocalSidecarClient.closeRequest(
              ascii("unconfirmed-close"),
              supervisor.runtimeInstanceId(),
              SidecarIpcV1.CloseMode.TERMINATE_AND_FENCE));
      require(close.accepted(), "unconfirmed CLOSE request was rejected");
      var response = await(close.completion());
      require(response.messageType() == SidecarIpcV1.MessageType.CLOSE_RESPONSE,
          "unconfirmed CLOSE did not return its validated response");
      waitUntil(
          () -> supervisor.state() == SidecarSupervisor.State.UNREADY,
          "unconfirmed expected-close termination");
      require(connector.forcedTerminations.get() == 1,
          "expected-close cleanup did not force the still-live process after its grace period");
      require(supervisor.lastFailure() instanceof SidecarSupervisor.RecoveryException,
          "unconfirmed expected-close cleanup did not retain a terminal recovery failure");
      require(connector.expectedCloseRelease.getCount() == 1,
          "test process exited despite refusing graceful and forced termination");
      require(connector.firstConnection != null
              && connector.firstConnection.closeCalls.get() == 0
              && !connector.firstConnection.endpointClosed(),
          "unconfirmed expected-close peer released generation resources before death");
      require(supervisor.quarantinedConnectionCount() == 1,
          "unconfirmed expected-close peer was not retained in quarantine");
      Thread.sleep(25);
      require(connector.launches.get() == 1,
          "unconfirmed expected CLOSE incorrectly entered recovery");
      connector.expectedCloseRelease.countDown();
      waitUntil(
          () -> connector.firstConnection.endpointClosed()
              && connector.firstConnection.closeCalls.get() == 1
              && supervisor.quarantinedConnectionCount() == 0,
          "confirmed-death generation resource cleanup");
    } finally {
      connector.expectedCloseRelease.countDown();
      supervisor.close();
    }
  }

  private static void testCloseDuringHandshakeCannotResurrectReady() throws Exception {
    var connector = new BlockingHandshakeConnector();
    var config = new SidecarSupervisor.Config(
        Files.createTempDirectory("delta-sidecar-close-handshake-"),
        new byte[] {1},
        digest(0x47),
        BUILD_ID,
        nestedDescriptor());
    var timing = new SidecarSupervisor.Timing(
        Duration.ofSeconds(30),
        Duration.ofMillis(25),
        Duration.ofSeconds(1),
        Duration.ofMillis(1));
    var supervisor = new SidecarSupervisor(config, connector, timing, Thread::sleep);
    var startup = supervisor.start();
    require(connector.handshakeRead.await(TEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS),
        "startup did not block in the descriptor handshake");
    supervisor.close();
    expectAnyFailure(startup);
    waitUntil(
        () -> connector.connection.exited.getCount() == 0,
        "close-time sidecar process termination");
    require(supervisor.state() == SidecarSupervisor.State.CLOSED,
        "close/start race resurrected a non-CLOSED supervisor state");
    require(connector.connection.forced.get(),
        "close during handshake did not terminate the in-progress generation");
    try {
      supervisor.client();
      throw new IllegalStateException("closed supervisor exposed a READY client");
    } catch (IllegalStateException expected) {
      require(expected.getMessage().equals("sidecar is not READY"),
          "closed supervisor exposed an unexpected client failure");
    }
  }

  private static void testQueuedRecoveryCannotOverwriteClosed() throws Exception {
    var connector = new FakeConnector();
    var config = new SidecarSupervisor.Config(
        Files.createTempDirectory("delta-sidecar-close-recovery-"),
        new byte[] {1},
        digest(0x48),
        BUILD_ID,
        nestedDescriptor());
    var timing = new SidecarSupervisor.Timing(
        Duration.ofSeconds(30),
        Duration.ofMillis(25),
        Duration.ofSeconds(1),
        Duration.ofMillis(1));
    var backoffEntered = new CountDownLatch(1);
    var releaseBackoff = new CountDownLatch(1);
    var supervisor = new SidecarSupervisor(
        config,
        connector,
        timing,
        ignored -> {
          backoffEntered.countDown();
          releaseBackoff.await();
        });
    try {
      var client = await(supervisor.start());
      var submission = client.tryEnqueue(
          LocalSidecarClient.submitRequest(ascii("close-during-recovery"), new byte[] {1}));
      require(submission.accepted(), "recovery-close trigger was rejected");
      expectAnyFailure(submission.completion());
      require(backoffEntered.await(TEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS),
          "recovery did not queue at the restart backoff");
      supervisor.close();
      releaseBackoff.countDown();
      Thread.sleep(25);
      require(supervisor.state() == SidecarSupervisor.State.CLOSED,
          "queued recovery overwrote CLOSED after close()");
      require(connector.launches.get() == 1,
          "queued recovery resurrected a replacement after close()");
      var restart = supervisor.start();
      expectFailure(restart, IllegalStateException.class);
    } finally {
      releaseBackoff.countDown();
      supervisor.close();
    }
  }

  private static void testConnectCloseRaceIsContainedInCompletionStage() throws Exception {
    var connector = new BlockingConnectConnector();
    var config = new SidecarSupervisor.Config(
        Files.createTempDirectory("delta-sidecar-close-connect-"),
        new byte[] {1},
        digest(0x49),
        BUILD_ID,
        nestedDescriptor());
    var timing = new SidecarSupervisor.Timing(
        Duration.ofSeconds(30),
        Duration.ofMillis(25),
        Duration.ofSeconds(1),
        Duration.ofMillis(1));
    var supervisor = new SidecarSupervisor(config, connector, timing, Thread::sleep);
    CompletionStage<LocalSidecarClient> startup;
    try {
      startup = supervisor.start();
    } catch (RuntimeException escaped) {
      throw new IllegalStateException("start failure escaped its CompletionStage", escaped);
    }
    require(connector.connectEntered.await(TEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS),
        "startup did not enter the blocked connector");
    supervisor.close();
    connector.releaseConnect.countDown();
    expectAnyFailure(startup);
    waitUntil(
        () -> connector.connection.exited.getCount() == 0,
        "post-close connected process termination");
    require(supervisor.state() == SidecarSupervisor.State.CLOSED,
        "connect/close race resurrected a non-CLOSED supervisor state");
    require(connector.connection.forced.get(),
        "connection returned after close was not force-terminated");

    CompletionStage<LocalSidecarClient> afterClose;
    try {
      afterClose = supervisor.start();
    } catch (RuntimeException escaped) {
      throw new IllegalStateException("post-close start escaped its CompletionStage", escaped);
    }
    expectFailure(afterClose, IllegalStateException.class);
  }

  private static void requireOperationalTiming(
      LocalSidecarClient.OperationalTiming timing) {
    require(timing.enqueueToWriteNanos() >= 0
            && timing.writeToValidatedReceiveNanos() >= 0
            && timing.totalEnqueueToValidatedReceiveNanos() >= 0,
        "operational timing contains a negative phase");
    require(Math.addExact(
            timing.enqueueToWriteNanos(), timing.writeToValidatedReceiveNanos())
            == timing.totalEnqueueToValidatedReceiveNanos(),
        "operational timing phases do not equal the measured total");
  }

  private static boolean isReadyAndAccepting(SidecarSupervisor supervisor) {
    if (supervisor.state() != SidecarSupervisor.State.READY) {
      return false;
    }
    try {
      return supervisor.client().isAccepting();
    } catch (IllegalStateException notReady) {
      return false;
    }
  }

  private static boolean containsMessage(Throwable failure, String expected) {
    for (var current = failure; current != null; current = current.getCause()) {
      if (current.getMessage() != null && current.getMessage().contains(expected)) {
        return true;
      }
    }
    return false;
  }

  private static boolean isWindows() {
    return System.getProperty("os.name", "")
        .toLowerCase(java.util.Locale.ROOT)
        .contains("win");
  }

  private static void injectClientFailure(
      SidecarSupervisor supervisor, LocalSidecarClient.Failure failure) throws Exception {
    var callback = SidecarSupervisor.class.getDeclaredMethod(
        "onClientFailure", LocalSidecarClient.Failure.class);
    callback.setAccessible(true);
    callback.invoke(supervisor, failure);
  }

  private static LocalSidecarClient client(
      LocalSidecarClient.Transport transport,
      LocalSidecarClient.FailureListener listener,
      LocalSidecarClient.NanoClock clock,
      LocalSidecarClient.IdSource ids) {
    return new LocalSidecarClient(
        transport,
        id(1),
        3,
        1,
        1,
        clock,
        ids,
        listener,
        Duration.ofHours(1),
        Duration.ofHours(1));
  }

  private static SidecarIpcV1.Frame submitResponse(
      SidecarIpcV1.Frame request,
      SidecarIpcV1.Id128 session,
      long generation,
      long sequence) {
    return submitResponse(request, session, generation, sequence, 2, 0x21);
  }

  private static SidecarIpcV1.Frame submitResponse(
      SidecarIpcV1.Frame request,
      SidecarIpcV1.Id128 session,
      long generation,
      long sequence,
      long admissionSequence,
      int nextStateDigestByte) {
    var effect = ascii("opaque-effect");
    var payload = SidecarIpcV1.responsePayload(
        SidecarIpcV1.MessageType.SUBMIT_RESPONSE,
        request.payload().bytes(1),
        request.payload().bytes(2),
        List.of(
            SidecarIpcV1.u8(3, SidecarIpcV1.AdmissionState.ADMITTED_OUTCOME_AVAILABLE.code()),
            SidecarIpcV1.u64(4, admissionSequence),
            SidecarIpcV1.u32(5, 0),
            SidecarIpcV1.bytes(16, ascii("effect-id")),
            SidecarIpcV1.bytes(17, effect),
            SidecarIpcV1.sha256Field(18, SidecarIpcV1.sha256(effect)),
            SidecarIpcV1.u64(19, 2),
            SidecarIpcV1.sha256Field(20, digest(0x20)),
            SidecarIpcV1.sha256Field(21, digest(nextStateDigestByte))));
    return SidecarIpcV1.frame(
        SidecarIpcV1.MessageType.SUBMIT_RESPONSE,
        session,
        generation,
        request.correlationId(),
        sequence,
        payload);
  }

  private static SidecarIpcV1.Frame voteResponse(
      SidecarIpcV1.Frame request,
      SidecarIpcV1.Id128 session,
      long generation,
      long sequence,
      long admissionSequence,
      byte[] opaqueReceipt) {
    var payload = SidecarIpcV1.responsePayload(
        SidecarIpcV1.MessageType.VOTE_RESPONSE,
        request.payload().bytes(1),
        request.payload().bytes(2),
        List.of(
            SidecarIpcV1.u8(3, SidecarIpcV1.AdmissionState.ADMITTED_OUTCOME_AVAILABLE.code()),
            SidecarIpcV1.u64(4, admissionSequence),
            SidecarIpcV1.u32(5, 0),
            SidecarIpcV1.bytes(16, opaqueReceipt),
            SidecarIpcV1.sha256Field(17, SidecarIpcV1.sha256(opaqueReceipt))));
    return SidecarIpcV1.frame(
        SidecarIpcV1.MessageType.VOTE_RESPONSE,
        session,
        generation,
        request.correlationId(),
        sequence,
        payload);
  }

  private static SidecarIpcV1.Frame notAdmittedResponse(
      SidecarIpcV1.Frame request, long sequence) {
    var payload = SidecarIpcV1.responsePayload(
        SidecarIpcV1.MessageType.ERROR_RESPONSE,
        request.payload().bytes(1),
        request.payload().bytes(2),
        List.of(
            SidecarIpcV1.u8(3, SidecarIpcV1.AdmissionState.NOT_ADMITTED_PROVEN.code()),
            SidecarIpcV1.u64(4, 0),
            SidecarIpcV1.u32(5, SidecarIpcV1.NATIVE_STATUS_UNAVAILABLE),
            SidecarIpcV1.u32(16, SidecarIpcV1.LocalError.BACKPRESSURE.code()),
            SidecarIpcV1.u16(17, request.messageType().code()),
            SidecarIpcV1.u64(18, 0),
            SidecarIpcV1.text(19, "not admitted")));
    return SidecarIpcV1.frame(
        SidecarIpcV1.MessageType.ERROR_RESPONSE,
        request.sessionId(),
        request.generation(),
        request.correlationId(),
        sequence,
        payload);
  }

  private static SidecarIpcV1.Frame terminalCloseResponse(
      SidecarIpcV1.Frame request, long sequence) {
    var payload = SidecarIpcV1.responsePayload(
        SidecarIpcV1.MessageType.CLOSE_RESPONSE,
        request.payload().bytes(1),
        request.payload().bytes(2),
        List.of(
            SidecarIpcV1.u8(3, SidecarIpcV1.AdmissionState.ADMITTED_OUTCOME_AVAILABLE.code()),
            SidecarIpcV1.u64(4, 1),
            SidecarIpcV1.u32(5, 0),
            SidecarIpcV1.u64(16, 1),
            SidecarIpcV1.sha256Field(17, digest(0x32)),
            SidecarIpcV1.u8(18, 1)));
    return SidecarIpcV1.frame(
        SidecarIpcV1.MessageType.CLOSE_RESPONSE,
        request.sessionId(),
        request.generation(),
        request.correlationId(),
        sequence,
        payload);
  }

  private static SidecarIpcV1.Frame preparseSentinel(
      SidecarIpcV1.Frame request,
      SidecarIpcV1.MessageType offendingType,
      long sequence) {
    var payload = SidecarIpcV1.responsePayload(
        SidecarIpcV1.MessageType.ERROR_RESPONSE,
        new byte[0],
        SidecarIpcV1.emptySha256(),
        List.of(
            SidecarIpcV1.u8(3, SidecarIpcV1.AdmissionState.NOT_ADMITTED_PROVEN.code()),
            SidecarIpcV1.u64(4, 0),
            SidecarIpcV1.u32(5, SidecarIpcV1.NATIVE_STATUS_UNAVAILABLE),
            SidecarIpcV1.u32(16, SidecarIpcV1.LocalError.FRAME_INVALID.code()),
            SidecarIpcV1.u16(17, offendingType.code()),
            SidecarIpcV1.u64(18, SidecarIpcV1.MAX_LOGICAL_PAYLOAD_BYTES),
            SidecarIpcV1.text(19, "safe preparse rejection")));
    return SidecarIpcV1.frame(
        SidecarIpcV1.MessageType.ERROR_RESPONSE,
        request.sessionId(),
        request.generation(),
        request.correlationId(),
        sequence,
        payload);
  }

  private static SidecarIpcV1.Frame errorResponse(
      SidecarIpcV1.Frame request,
      SidecarIpcV1.MessageType offendingType,
      long sequence) {
    var payload = SidecarIpcV1.responsePayload(
        SidecarIpcV1.MessageType.ERROR_RESPONSE,
        request.payload().bytes(1),
        request.payload().bytes(2),
        List.of(
            SidecarIpcV1.u8(3, SidecarIpcV1.AdmissionState.ADMITTED_OUTCOME_AVAILABLE.code()),
            SidecarIpcV1.u64(4, 1),
            SidecarIpcV1.u32(5, 1),
            SidecarIpcV1.u32(16, SidecarIpcV1.LocalError.INTERNAL_TRANSPORT_ERROR.code()),
            SidecarIpcV1.u16(17, offendingType.code()),
            SidecarIpcV1.u64(18, 0),
            SidecarIpcV1.text(19, "bound error")));
    return SidecarIpcV1.frame(
        SidecarIpcV1.MessageType.ERROR_RESPONSE,
        request.sessionId(),
        request.generation(),
        request.correlationId(),
        sequence,
        payload);
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

  private static byte[] ascii(String value) {
    return value.getBytes(StandardCharsets.US_ASCII);
  }

  private static byte[] digest(int value) {
    var result = new byte[32];
    Arrays.fill(result, (byte) value);
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

  private static <T> T await(CompletionStage<T> stage)
      throws InterruptedException, ExecutionException, TimeoutException {
    return stage.toCompletableFuture().get(TEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS);
  }

  private static void expectFailure(CompletionStage<?> stage, Class<? extends Throwable> type)
      throws Exception {
    try {
      await(stage);
    } catch (ExecutionException expected) {
      require(type.isInstance(expected.getCause()),
          "wrong failure type: " + expected.getCause().getClass().getName());
      return;
    }
    throw new IllegalStateException("operation unexpectedly completed successfully");
  }

  private static void expectAnyFailure(CompletionStage<?> stage) throws Exception {
    try {
      await(stage);
    } catch (ExecutionException expected) {
      require(expected.getCause() != null, "exceptional completion lacked a cause");
      return;
    }
    throw new IllegalStateException("operation unexpectedly completed successfully");
  }

  private static void awaitSuccessOrFailure(CompletionStage<?> stage) throws Exception {
    try {
      await(stage);
    } catch (ExecutionException expected) {
      require(expected.getCause() != null, "exceptional completion lacked a cause");
    }
  }

  private static void awaitLatch(CountDownLatch latch) {
    try {
      require(latch.await(TEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS),
          "timed out waiting for concurrent test start");
    } catch (InterruptedException interrupted) {
      Thread.currentThread().interrupt();
      throw new IllegalStateException("concurrent test thread was interrupted", interrupted);
    }
  }

  private static void join(Thread thread, String label) throws InterruptedException {
    thread.join(TEST_TIMEOUT.toMillis());
    require(!thread.isAlive(), "timed out waiting for " + label);
  }

  private static void waitUntil(BooleanSupplier condition, String label) throws Exception {
    var deadline = System.nanoTime() + TEST_TIMEOUT.toNanos();
    while (!condition.getAsBoolean() && System.nanoTime() - deadline < 0) {
      Thread.sleep(2);
    }
    require(condition.getAsBoolean(), "timed out waiting for " + label);
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalStateException(message);
    }
  }

  private static final class CountingIds implements LocalSidecarClient.IdSource {
    private final AtomicInteger next = new AtomicInteger(100);

    @Override
    public SidecarIpcV1.Id128 next() {
      return id(next.getAndIncrement());
    }
  }

  private static final class OneShotReadTransport implements LocalSidecarClient.Transport {
    private final byte[] response;
    private final AtomicBoolean open = new AtomicBoolean(true);
    private final AtomicBoolean read = new AtomicBoolean();

    private OneShotReadTransport(byte[] response) {
      this.response = Arrays.copyOf(response, response.length);
    }

    @Override
    public void write(byte[] canonicalFrame) throws IOException {
      throw new IOException("one-shot read transport does not accept writes");
    }

    @Override
    public byte[] read() throws IOException {
      if (!open.get() || !read.compareAndSet(false, true)) {
        throw new EOFException("one-shot read transport is exhausted");
      }
      return Arrays.copyOf(response, response.length);
    }

    @Override
    public boolean isOpen() {
      return open.get();
    }

    @Override
    public void close() {
      open.set(false);
    }
  }

  private static final class LateReadAfterCloseTransport
      implements LocalSidecarClient.Transport {
    private final byte[] response;
    private final AtomicBoolean closed = new AtomicBoolean();
    private final CountDownLatch readEntered = new CountDownLatch(1);
    private final CountDownLatch releaseRead = new CountDownLatch(1);

    private LateReadAfterCloseTransport(byte[] response) {
      this.response = Arrays.copyOf(response, response.length);
    }

    @Override
    public void write(byte[] canonicalFrame) throws IOException {
      throw new IOException("late-read transport does not accept writes");
    }

    @Override
    public byte[] read() throws IOException {
      readEntered.countDown();
      try {
        if (!releaseRead.await(TEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS)) {
          throw new IOException("late read release timed out");
        }
      } catch (InterruptedException interrupted) {
        Thread.currentThread().interrupt();
        throw new IOException("late read was interrupted", interrupted);
      }
      require(closed.get(), "late read was released before delegate close");
      return Arrays.copyOf(response, response.length);
    }

    @Override
    public boolean isOpen() {
      return !closed.get();
    }

    @Override
    public void close() {
      closed.set(true);
    }
  }

  private static final class BlockingWriteTransport implements LocalSidecarClient.Transport {
    private final AtomicBoolean open = new AtomicBoolean(true);
    private final CountDownLatch writeEntered = new CountDownLatch(1);
    private final CountDownLatch releaseWrite = new CountDownLatch(1);
    private final CountDownLatch closed = new CountDownLatch(1);

    @Override
    public void write(byte[] canonicalFrame) throws IOException {
      writeEntered.countDown();
      try {
        releaseWrite.await();
      } catch (InterruptedException interrupted) {
        Thread.currentThread().interrupt();
        throw new IOException("write interrupted", interrupted);
      }
      if (!open.get()) {
        throw new EOFException("transport closed");
      }
    }

    @Override
    public byte[] read() throws IOException {
      try {
        closed.await();
      } catch (InterruptedException interrupted) {
        Thread.currentThread().interrupt();
        throw new IOException("read interrupted", interrupted);
      }
      throw new EOFException("transport closed");
    }

    @Override
    public boolean isOpen() {
      return open.get();
    }

    @Override
    public void close() {
      open.set(false);
      releaseWrite.countDown();
      closed.countDown();
    }
  }

  private static final class SinkTransport implements LocalSidecarClient.Transport {
    private final AtomicBoolean open = new AtomicBoolean(true);
    private final CountDownLatch closed = new CountDownLatch(1);

    @Override
    public void write(byte[] canonicalFrame) throws IOException {
      if (!open.get()) {
        throw new EOFException("transport closed");
      }
    }

    @Override
    public byte[] read() throws IOException {
      try {
        closed.await();
      } catch (InterruptedException interrupted) {
        Thread.currentThread().interrupt();
        throw new IOException("read interrupted", interrupted);
      }
      throw new EOFException("transport closed");
    }

    @Override
    public boolean isOpen() {
      return open.get();
    }

    @Override
    public void close() {
      open.set(false);
      closed.countDown();
    }
  }

  private static final class TransportPair {
    private static final byte[] CLOSED = new byte[0];
    private final QueueTransport javaEndpoint;
    private final QueueTransport peerEndpoint;

    private TransportPair(QueueTransport javaEndpoint, QueueTransport peerEndpoint) {
      this.javaEndpoint = javaEndpoint;
      this.peerEndpoint = peerEndpoint;
    }

    private static TransportPair create() {
      var javaToPeer = new LinkedBlockingQueue<byte[]>();
      var peerToJava = new LinkedBlockingQueue<byte[]>();
      var open = new AtomicBoolean(true);
      return new TransportPair(
          new QueueTransport(peerToJava, javaToPeer, open),
          new QueueTransport(javaToPeer, peerToJava, open));
    }

    private static final class QueueTransport implements LocalSidecarClient.Transport {
      private final BlockingQueue<byte[]> incoming;
      private final BlockingQueue<byte[]> outgoing;
      private final AtomicBoolean open;
      private final AtomicInteger successfulWrites = new AtomicInteger();

      private QueueTransport(
          BlockingQueue<byte[]> incoming,
          BlockingQueue<byte[]> outgoing,
          AtomicBoolean open) {
        this.incoming = incoming;
        this.outgoing = outgoing;
        this.open = open;
      }

      @Override
      public void write(byte[] canonicalFrame) throws IOException {
        if (!open.get()) {
          throw new EOFException("transport closed");
        }
        outgoing.add(Arrays.copyOf(canonicalFrame, canonicalFrame.length));
        successfulWrites.incrementAndGet();
      }

      @Override
      public byte[] read() throws IOException {
        try {
          var value = incoming.take();
          if (value == CLOSED || value.length == 0) {
            throw new EOFException("transport closed");
          }
          return value;
        } catch (InterruptedException interrupted) {
          Thread.currentThread().interrupt();
          throw new IOException("read interrupted", interrupted);
        }
      }

      @Override
      public boolean isOpen() {
        return open.get();
      }

      @Override
      public void close() {
        if (open.compareAndSet(true, false)) {
          incoming.offer(CLOSED);
          outgoing.offer(CLOSED);
        }
      }
    }
  }

  private static final class FakeConnector implements SidecarSupervisor.GenerationConnector {
    private final AtomicInteger launches = new AtomicInteger();
    private final AtomicBoolean crashFirstSubmit = new AtomicBoolean(true);
    private final AtomicBoolean crashFirstVote = new AtomicBoolean(true);
    private final List<byte[]> submitPayloads = new java.util.concurrent.CopyOnWriteArrayList<>();
    private final List<byte[]> votePayloads = new java.util.concurrent.CopyOnWriteArrayList<>();
    private final byte[] durableVoteReceipt = ascii("opaque-native-vote-receipt");
    private final boolean hangReplacements;
    private final boolean failReplacementCleanup;
    private final boolean refuseExpectedCloseTermination;
    private final AtomicBoolean crashReplacementAfterOpen;
    private final AtomicBoolean errorReplacementOpen = new AtomicBoolean();
    private final boolean failSecondHandshakeRetryably;
    private final AtomicInteger forcedTerminations = new AtomicInteger();
    private final CountDownLatch expectedCloseRelease = new CountDownLatch(1);
    private final CountDownLatch retryableHandshakeRead = new CountDownLatch(1);
    private final CountDownLatch releaseRetryableHandshake = new CountDownLatch(1);
    private final AtomicInteger cleanupAttempts = new AtomicInteger();
    private CountDownLatch cleanupRelease;
    private volatile FakeConnection firstConnection;
    private volatile UnstoppableHandshakeFailureConnection unstoppableReplacement;

    private FakeConnector() {
      this(false, false, false, false, false);
    }

    private FakeConnector(CountDownLatch cleanupRelease) {
      this();
      this.cleanupRelease = Objects.requireNonNull(cleanupRelease, "cleanupRelease");
    }

    private FakeConnector(boolean hangReplacements) {
      this(hangReplacements, false, false, false, false);
    }

    private FakeConnector(boolean hangReplacements, boolean failReplacementCleanup) {
      this(hangReplacements, failReplacementCleanup, false, false, false);
    }

    private FakeConnector(
        boolean hangReplacements,
        boolean failReplacementCleanup,
        boolean refuseExpectedCloseTermination) {
      this(
          hangReplacements,
          failReplacementCleanup,
          refuseExpectedCloseTermination,
          false,
          false);
    }

    private FakeConnector(
        boolean hangReplacements,
        boolean failReplacementCleanup,
        boolean refuseExpectedCloseTermination,
        boolean crashReplacementAfterOpen) {
      this(
          hangReplacements,
          failReplacementCleanup,
          refuseExpectedCloseTermination,
          crashReplacementAfterOpen,
          false);
    }

    private FakeConnector(
        boolean hangReplacements,
        boolean failReplacementCleanup,
        boolean refuseExpectedCloseTermination,
        boolean crashReplacementAfterOpen,
        boolean failSecondHandshakeRetryably) {
      this.hangReplacements = hangReplacements;
      this.failReplacementCleanup = failReplacementCleanup;
      this.refuseExpectedCloseTermination = refuseExpectedCloseTermination;
      this.crashReplacementAfterOpen = new AtomicBoolean(crashReplacementAfterOpen);
      this.failSecondHandshakeRetryably = failSecondHandshakeRetryably;
    }

    @Override
    public SidecarSupervisor.Connection connect(
        SidecarSupervisor.LaunchContext context, Duration readyTimeout) throws IOException {
      require(!readyTimeout.isNegative() && !readyTimeout.isZero(),
          "supervisor supplied a non-positive recovery timeout");
      var launch = launches.incrementAndGet();
      if (launch == 1) {
        Files.write(
            context.durableDirectory().resolve("runtime.wal"),
            new byte[] {1, 2, 3},
            StandardOpenOption.CREATE_NEW,
            StandardOpenOption.WRITE);
      }
      if (hangReplacements && launch > 1) {
        return new HungConnection(this);
      }
      if (failReplacementCleanup && launch > 1) {
        unstoppableReplacement = new UnstoppableHandshakeFailureConnection();
        return unstoppableReplacement;
      }
      if (failSecondHandshakeRetryably && launch == 2) {
        return new RetryableHandshakeFailureConnection(
            retryableHandshakeRead, releaseRetryableHandshake);
      }
      var connection = new FakeConnection(context, this);
      if (launch == 1) {
        firstConnection = connection;
      }
      connection.start();
      return connection;
    }
  }

  private static final class UnstoppableHandshakeFailureConnection
      implements SidecarSupervisor.Connection {
    private final AtomicBoolean open = new AtomicBoolean(true);
    private final AtomicInteger closeCalls = new AtomicInteger();
    private final LocalSidecarClient.Transport transport = new LocalSidecarClient.Transport() {
      @Override
      public void write(byte[] canonicalFrame) throws IOException {
        if (!open.get()) {
          throw new EOFException("transport closed");
        }
      }

      @Override
      public byte[] read() throws IOException {
        throw new EOFException("replacement handshake failed");
      }

      @Override
      public boolean isOpen() {
        return open.get();
      }

      @Override
      public void close() {
        open.set(false);
      }
    };

    @Override
    public LocalSidecarClient.Transport transport() {
      return transport;
    }

    @Override
    public boolean isAlive() {
      return true;
    }

    @Override
    public void requestShutdown() {}

    @Override
    public void forceTermination() {}

    @Override
    public boolean awaitExit(Duration timeout) {
      return false;
    }

    @Override
    public boolean endpointClosed() {
      return !open.get();
    }

    @Override
    public void close() {
      closeCalls.incrementAndGet();
      open.set(false);
    }
  }

  private static final class RetryableHandshakeFailureConnection
      implements SidecarSupervisor.Connection {
    private final AtomicBoolean open = new AtomicBoolean(true);
    private final AtomicBoolean alive = new AtomicBoolean(true);
    private final CountDownLatch exited = new CountDownLatch(1);
    private final CountDownLatch handshakeRead;
    private final CountDownLatch releaseHandshake;
    private final LocalSidecarClient.Transport transport = new LocalSidecarClient.Transport() {
      @Override
      public void write(byte[] canonicalFrame) throws IOException {
        if (!open.get()) {
          throw new EOFException("transport closed");
        }
      }

      @Override
      public byte[] read() throws IOException {
        handshakeRead.countDown();
        try {
          releaseHandshake.await();
        } catch (InterruptedException interrupted) {
          Thread.currentThread().interrupt();
          throw new IOException("replacement handshake interrupted", interrupted);
        }
        throw new EOFException("retryable replacement handshake failed");
      }

      @Override
      public boolean isOpen() {
        return open.get();
      }

      @Override
      public void close() {
        open.set(false);
      }
    };

    private RetryableHandshakeFailureConnection(
        CountDownLatch handshakeRead, CountDownLatch releaseHandshake) {
      this.handshakeRead = handshakeRead;
      this.releaseHandshake = releaseHandshake;
    }

    @Override
    public LocalSidecarClient.Transport transport() {
      return transport;
    }

    @Override
    public boolean isAlive() {
      return alive.get();
    }

    @Override
    public void requestShutdown() {
      terminate();
    }

    @Override
    public void forceTermination() {
      terminate();
    }

    @Override
    public boolean awaitExit(Duration timeout) throws InterruptedException {
      return exited.await(timeout.toNanos(), TimeUnit.NANOSECONDS);
    }

    @Override
    public boolean endpointClosed() {
      return !open.get();
    }

    @Override
    public void close() {
      open.set(false);
      terminate();
    }

    private void terminate() {
      releaseHandshake.countDown();
      if (alive.compareAndSet(true, false)) {
        open.set(false);
        exited.countDown();
      }
    }
  }

  private static final class BlockingConnectConnector
      implements SidecarSupervisor.GenerationConnector {
    private final CountDownLatch connectEntered = new CountDownLatch(1);
    private final CountDownLatch releaseConnect = new CountDownLatch(1);
    private final BlockingHandshakeConnection connection =
        new BlockingHandshakeConnection(new CountDownLatch(1));

    @Override
    public SidecarSupervisor.Connection connect(
        SidecarSupervisor.LaunchContext context, Duration readyTimeout)
        throws InterruptedException {
      connectEntered.countDown();
      releaseConnect.await();
      return connection;
    }
  }

  private static final class BlockingHandshakeConnector
      implements SidecarSupervisor.GenerationConnector {
    private final CountDownLatch handshakeRead = new CountDownLatch(1);
    private final BlockingHandshakeConnection connection =
        new BlockingHandshakeConnection(handshakeRead);

    @Override
    public SidecarSupervisor.Connection connect(
        SidecarSupervisor.LaunchContext context, Duration readyTimeout) {
      return connection;
    }
  }

  private static final class BlockingHandshakeConnection
      implements SidecarSupervisor.Connection {
    private final AtomicBoolean open = new AtomicBoolean(true);
    private final AtomicBoolean alive = new AtomicBoolean(true);
    private final AtomicBoolean forced = new AtomicBoolean();
    private final CountDownLatch exited = new CountDownLatch(1);
    private final CountDownLatch handshakeRead;
    private final LocalSidecarClient.Transport transport = new LocalSidecarClient.Transport() {
      @Override
      public void write(byte[] canonicalFrame) throws IOException {
        if (!open.get()) {
          throw new EOFException("transport closed");
        }
      }

      @Override
      public byte[] read() throws IOException {
        handshakeRead.countDown();
        try {
          exited.await();
        } catch (InterruptedException interrupted) {
          Thread.currentThread().interrupt();
          throw new IOException("handshake read interrupted", interrupted);
        }
        throw new EOFException("transport closed");
      }

      @Override
      public boolean isOpen() {
        return open.get();
      }

      @Override
      public void close() {
        open.set(false);
      }
    };

    private BlockingHandshakeConnection(CountDownLatch handshakeRead) {
      this.handshakeRead = handshakeRead;
    }

    @Override
    public LocalSidecarClient.Transport transport() {
      return transport;
    }

    @Override
    public boolean isAlive() {
      return alive.get();
    }

    @Override
    public void requestShutdown() {
      terminate(false);
    }

    @Override
    public void forceTermination() {
      terminate(true);
    }

    @Override
    public boolean awaitExit(Duration timeout) throws InterruptedException {
      return exited.await(timeout.toNanos(), TimeUnit.NANOSECONDS);
    }

    @Override
    public boolean endpointClosed() {
      return !open.get();
    }

    @Override
    public void close() {
      open.set(false);
      terminate(false);
    }

    private void terminate(boolean force) {
      if (force) {
        forced.set(true);
      }
      if (alive.compareAndSet(true, false)) {
        open.set(false);
        exited.countDown();
      }
    }
  }

  private static final class HungConnection implements SidecarSupervisor.Connection {
    private final FakeConnector owner;
    private final TransportPair pair = TransportPair.create();
    private final AtomicBoolean alive = new AtomicBoolean(true);
    private final AtomicBoolean endpointClosed = new AtomicBoolean();
    private final CountDownLatch exited = new CountDownLatch(1);

    private HungConnection(FakeConnector owner) {
      this.owner = owner;
    }

    @Override
    public LocalSidecarClient.Transport transport() {
      return pair.javaEndpoint;
    }

    @Override
    public boolean isAlive() {
      return alive.get();
    }

    @Override
    public void requestShutdown() {
      terminate(false);
    }

    @Override
    public void forceTermination() {
      terminate(true);
    }

    @Override
    public boolean awaitExit(Duration timeout) throws InterruptedException {
      return exited.await(timeout.toNanos(), TimeUnit.NANOSECONDS);
    }

    @Override
    public boolean endpointClosed() {
      return endpointClosed.get();
    }

    @Override
    public void close() {
      pair.javaEndpoint.close();
      endpointClosed.set(true);
      terminate(false);
    }

    private void terminate(boolean forced) {
      if (alive.compareAndSet(true, false)) {
        if (forced) {
          owner.forcedTerminations.incrementAndGet();
        }
        pair.peerEndpoint.close();
        exited.countDown();
      }
    }
  }

  private static final class FakeConnection implements SidecarSupervisor.Connection {
    private final SidecarSupervisor.LaunchContext context;
    private final FakeConnector owner;
    private final TransportPair pair = TransportPair.create();
    private final AtomicBoolean alive = new AtomicBoolean(true);
    private final AtomicBoolean endpointClosed = new AtomicBoolean();
    private final AtomicInteger closeCalls = new AtomicInteger();
    private final CountDownLatch exited = new CountDownLatch(1);

    private FakeConnection(
        SidecarSupervisor.LaunchContext context, FakeConnector owner) {
      this.context = context;
      this.owner = owner;
    }

    private void start() {
      var thread = new Thread(this::serve, "delta-sidecar-fake-peer");
      thread.setDaemon(true);
      thread.start();
    }

    private void serve() {
      try {
        var hello = SidecarIpcV1.decodeFrame(pair.peerEndpoint.read());
        require(hello.messageType() == SidecarIpcV1.MessageType.CLIENT_HELLO,
            "fake peer expected CLIENT_HELLO");
        SidecarIpcV1.requireDescriptor(hello.payload(), context.identity());
        pair.peerEndpoint.write(
            SidecarIpcV1.frame(
                    SidecarIpcV1.MessageType.SERVER_DESCRIPTOR,
                    context.identity().sessionId(),
                    context.identity().generation(),
                    hello.correlationId(),
                    1,
                    SidecarIpcV1.descriptorPayload(
                        SidecarIpcV1.MessageType.SERVER_DESCRIPTOR, context.identity()))
                .canonicalBytes());

        var open = SidecarIpcV1.decodeFrame(pair.peerEndpoint.read());
        require(open.messageType() == SidecarIpcV1.MessageType.OPEN_REQUEST,
            "fake peer expected OPEN_REQUEST");
        require(open.payload().text(17).equals(context.durableDirectory().toString()),
            "OPEN durable directory changed");
        if (context.identity().generation() > 1
            && owner.errorReplacementOpen.compareAndSet(true, false)) {
          pair.peerEndpoint.write(notAdmittedResponse(open, 2).canonicalBytes());
          return;
        }
        pair.peerEndpoint.write(openResponse(open, context.identity(), 2).canonicalBytes());
        if (context.identity().generation() > 1
            && owner.crashReplacementAfterOpen.compareAndSet(true, false)) {
          crashFromPeer();
          return;
        }

        var responseSequences = new SidecarIpcV1.SequenceCursor(3);
        while (alive.get()) {
          var request = SidecarIpcV1.decodeFrame(pair.peerEndpoint.read());
          var responseSequence = responseSequences.claim();
          if (request.messageType() == SidecarIpcV1.MessageType.SUBMIT_REQUEST) {
            owner.submitPayloads.add(request.payload().canonicalBytes());
            if (owner.crashFirstSubmit.compareAndSet(true, false)) {
              crashFromPeer();
              return;
            }
            pair.peerEndpoint.write(
                submitResponse(
                    request,
                    context.identity().sessionId(),
                    context.identity().generation(),
                    responseSequence).canonicalBytes());
          } else if (request.messageType() == SidecarIpcV1.MessageType.VOTE_REQUEST) {
            owner.votePayloads.add(request.payload().canonicalBytes());
            if (owner.crashFirstVote.compareAndSet(true, false)) {
              // Model a native-reachable durable VOTE whose response is lost with the process.
              crashFromPeer();
              return;
            }
            pair.peerEndpoint.write(
                voteResponse(
                    request,
                    context.identity().sessionId(),
                    context.identity().generation(),
                    responseSequence,
                    responseSequence - 1,
                    owner.durableVoteReceipt).canonicalBytes());
          } else if (request.messageType() == SidecarIpcV1.MessageType.HEALTH_REQUEST) {
            pair.peerEndpoint.write(healthResponse(request, responseSequence).canonicalBytes());
          } else if (request.messageType() == SidecarIpcV1.MessageType.CLOSE_REQUEST) {
            pair.peerEndpoint.write(closeResponse(request, responseSequence).canonicalBytes());
            if (owner.refuseExpectedCloseTermination) {
              try {
                owner.expectedCloseRelease.await();
              } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt();
              }
            }
            return;
          } else {
            throw new IllegalStateException(
                "fake peer received unsupported operation " + request.messageType());
          }
        }
      } catch (IOException expectedAfterClose) {
        if (alive.get() && pair.peerEndpoint.isOpen()) {
          throw new IllegalStateException("fake peer transport failed", expectedAfterClose);
        }
      } finally {
        alive.set(false);
        exited.countDown();
      }
    }

    private static SidecarIpcV1.Frame openResponse(
        SidecarIpcV1.Frame request,
        SidecarIpcV1.DescriptorIdentity identity,
        long sequence) {
      var payload = SidecarIpcV1.responsePayload(
          SidecarIpcV1.MessageType.OPEN_RESPONSE,
          request.payload().bytes(1),
          request.payload().bytes(2),
          List.of(
              SidecarIpcV1.u8(3, SidecarIpcV1.AdmissionState.ADMITTED_OUTCOME_AVAILABLE.code()),
              SidecarIpcV1.u64(4, 1),
              SidecarIpcV1.u32(5, 0),
              SidecarIpcV1.id128(16, id((int) identity.generation() + 1_000)),
              SidecarIpcV1.u64(17, 0),
              SidecarIpcV1.sha256Field(18, digest(0x31)),
              SidecarIpcV1.u8(19, 1)));
      return SidecarIpcV1.frame(
          SidecarIpcV1.MessageType.OPEN_RESPONSE,
          identity.sessionId(),
          identity.generation(),
          request.correlationId(),
          sequence,
          payload);
    }

    private SidecarIpcV1.Frame healthResponse(
        SidecarIpcV1.Frame request, long sequence) {
      var payload = SidecarIpcV1.responsePayload(
          SidecarIpcV1.MessageType.HEALTH_RESPONSE,
          request.payload().bytes(1),
          request.payload().bytes(2),
          List.of(
              SidecarIpcV1.u8(3, SidecarIpcV1.AdmissionState.NOT_APPLICABLE.code()),
              SidecarIpcV1.u64(4, 0),
              SidecarIpcV1.u32(5, 0),
              SidecarIpcV1.u8(16, SidecarIpcV1.HealthState.READY.code()),
              SidecarIpcV1.u64(17, context.identity().generation()),
              SidecarIpcV1.u64(18, 2),
              SidecarIpcV1.u32(19, 0),
              SidecarIpcV1.u8(20, 1),
              SidecarIpcV1.u8(21, 1)));
      return SidecarIpcV1.frame(
          SidecarIpcV1.MessageType.HEALTH_RESPONSE,
          context.identity().sessionId(),
          context.identity().generation(),
          request.correlationId(),
          sequence,
          payload);
    }

    private SidecarIpcV1.Frame closeResponse(
        SidecarIpcV1.Frame request, long sequence) {
      var payload = SidecarIpcV1.responsePayload(
          SidecarIpcV1.MessageType.CLOSE_RESPONSE,
          request.payload().bytes(1),
          request.payload().bytes(2),
          List.of(
              SidecarIpcV1.u8(3, SidecarIpcV1.AdmissionState.ADMITTED_OUTCOME_AVAILABLE.code()),
              SidecarIpcV1.u64(4, 3),
              SidecarIpcV1.u32(5, 0),
              SidecarIpcV1.u64(16, 2),
              SidecarIpcV1.sha256Field(17, digest(0x32)),
              SidecarIpcV1.u8(18, 1)));
      return SidecarIpcV1.frame(
          SidecarIpcV1.MessageType.CLOSE_RESPONSE,
          context.identity().sessionId(),
          context.identity().generation(),
          request.correlationId(),
          sequence,
          payload);
    }

    private void crashFromPeer() {
      alive.set(false);
      pair.peerEndpoint.close();
      exited.countDown();
    }

    @Override
    public LocalSidecarClient.Transport transport() {
      return pair.javaEndpoint;
    }

    @Override
    public boolean isAlive() {
      return alive.get();
    }

    @Override
    public void requestShutdown() {
      if (!owner.refuseExpectedCloseTermination) {
        crashFromPeer();
      }
    }

    @Override
    public void forceTermination() {
      owner.forcedTerminations.incrementAndGet();
      if (!owner.refuseExpectedCloseTermination) {
        crashFromPeer();
      }
    }

    @Override
    public boolean awaitExit(Duration timeout) throws InterruptedException {
      return exited.await(timeout.toNanos(), TimeUnit.NANOSECONDS);
    }

    @Override
    public boolean endpointClosed() {
      return endpointClosed.get();
    }

    @Override
    public void close() throws IOException {
      owner.cleanupAttempts.incrementAndGet();
      if (owner.cleanupRelease != null && owner.cleanupRelease.getCount() != 0) {
        throw new IOException("injected generation unmap failure");
      }
      if (endpointClosed.compareAndSet(false, true)) {
        closeCalls.incrementAndGet();
        pair.javaEndpoint.close();
      }
    }
  }
}
