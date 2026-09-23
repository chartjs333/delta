package io.deltareduce.node.sidecar;

import java.io.EOFException;
import java.io.IOException;
import java.lang.foreign.Arena;
import java.lang.foreign.MemorySegment;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.Objects;
import java.util.Optional;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;

/** Frozen POSIX shared-memory carrier for sidecar IPC v1.1. */
public final class SidecarSharedMemory {
  public static final int JAVA_TO_NATIVE = 1;
  public static final int NATIVE_TO_JAVA = 2;
  public static final int SLOT_COUNT = 64;
  public static final int CONTROL_RECORD_BYTES = 128;
  public static final int CONTROL_PREFIX_BYTES = 8_192;
  public static final long REGION_BYTES = 1L << 30;

  public static final int FREE = 0;
  public static final int WRITING = 1;
  public static final int PUBLISHED = 2;
  public static final int READING = 3;
  public static final int ACKED = 4;
  public static final int REJECTED = 5;

  private static final byte[] MAGIC = "DELTAIPC".getBytes(java.nio.charset.StandardCharsets.US_ASCII);
  private static final VarHandle STATE =
      MethodHandles.byteBufferViewVarHandle(int[].class, ByteOrder.BIG_ENDIAN);
  private static final boolean ATOMIC_ABI_SUPPORTED = probeAtomicAbi();

  private SidecarSharedMemory() {}

  @FunctionalInterface
  interface CleanupStep {
    void close() throws IOException;
  }

  /**
   * Two-step cleanup whose completion is confirmed only after both steps return successfully.
   * A failed step remains pending and is retried; the first failure is retained until cleanup is
   * positively confirmed.
   */
  static final class CleanupProgress {
    private boolean firstComplete;
    private boolean secondComplete;
    private IOException rememberedFailure;

    synchronized void close(CleanupStep first, CleanupStep second) throws IOException {
      Objects.requireNonNull(first, "first");
      Objects.requireNonNull(second, "second");
      IOException attemptFailure = null;
      if (!firstComplete) {
        try {
          first.close();
          firstComplete = true;
        } catch (IOException error) {
          attemptFailure = error;
        } catch (RuntimeException error) {
          attemptFailure = new IOException("cleanup step failed", error);
        }
      }
      if (!secondComplete) {
        try {
          second.close();
          secondComplete = true;
        } catch (IOException error) {
          attemptFailure = merge(attemptFailure, error);
        } catch (RuntimeException error) {
          attemptFailure = merge(
              attemptFailure, new IOException("cleanup step failed", error));
        }
      }
      if (firstComplete && secondComplete) {
        rememberedFailure = null;
        return;
      }
      if (rememberedFailure == null) {
        rememberedFailure = attemptFailure == null
            ? new IOException("cleanup is not confirmed")
            : attemptFailure;
      }
      throw rememberedFailure;
    }

    synchronized boolean confirmed() {
      return firstComplete && secondComplete;
    }

    private static IOException merge(IOException first, IOException second) {
      if (first == null) {
        return second;
      }
      first.addSuppressed(second);
      return first;
    }
  }

  public static boolean atomicAbiSupported() {
    return ATOMIC_ABI_SUPPORTED;
  }

  /** Per-generation sparse files and mappings. Close only after the child is confirmed dead. */
  public static final class GenerationResources implements AutoCloseable {
    private final Path directory;
    private final Path javaToNativePath;
    private final Path nativeToJavaPath;
    private final Region javaToNative;
    private final Region nativeToJava;
    private final FileIdentity javaToNativeIdentity;
    private final FileIdentity nativeToJavaIdentity;
    private final AtomicBoolean closed = new AtomicBoolean();
    private final CleanupProgress cleanup = new CleanupProgress();
    private boolean atomicProbePrepared;
    private boolean mappedAtomicAbiProbed;

    private GenerationResources(
        Path directory,
        Path javaToNativePath,
        Path nativeToJavaPath,
        Region javaToNative,
        Region nativeToJava,
        FileIdentity javaToNativeIdentity,
        FileIdentity nativeToJavaIdentity) {
      this.directory = directory;
      this.javaToNativePath = javaToNativePath;
      this.nativeToJavaPath = nativeToJavaPath;
      this.javaToNative = javaToNative;
      this.nativeToJava = nativeToJava;
      this.javaToNativeIdentity = javaToNativeIdentity;
      this.nativeToJavaIdentity = nativeToJavaIdentity;
    }

    public static GenerationResources create(long generation) throws IOException {
      require(generation != 0, "shared-memory generation is zero");
      if (!ATOMIC_ABI_SUPPORTED) {
        throw new IOException("shared-memory atomic ABI is unavailable");
      }
      var directory = Files.createTempDirectory("delta-sidecar-shm-" +
          Long.toUnsignedString(generation) + "-");
      var javaToNative = directory.resolve("java-to-native.region");
      var nativeToJava = directory.resolve("native-to-java.region");
      try {
        createSparseFile(javaToNative);
        createSparseFile(nativeToJava);
        var javaToNativeIdentity = fileIdentity(javaToNative);
        var nativeToJavaIdentity = fileIdentity(nativeToJava);
        Region javaToNativeRegion = null;
        Region nativeToJavaRegion = null;
        try {
          javaToNativeRegion = Region.open(
              javaToNative, JAVA_TO_NATIVE, generation, javaToNativeIdentity);
          nativeToJavaRegion = Region.open(
              nativeToJava, NATIVE_TO_JAVA, generation, nativeToJavaIdentity);
          return new GenerationResources(
              directory,
              javaToNative,
              nativeToJava,
              javaToNativeRegion,
              nativeToJavaRegion,
              javaToNativeIdentity,
              nativeToJavaIdentity);
        } catch (Throwable error) {
          closeQuietly(nativeToJavaRegion);
          closeQuietly(javaToNativeRegion);
          throw error;
        }
      } catch (Throwable error) {
        tryDelete(nativeToJava);
        tryDelete(javaToNative);
        tryDelete(directory);
        throw error;
      }
    }

    public Path javaToNativePath() {
      return javaToNativePath;
    }

    public Path nativeToJavaPath() {
      return nativeToJavaPath;
    }

    public Region javaToNative() {
      return javaToNative;
    }

    public Region nativeToJava() {
      return nativeToJava;
    }

    public FileIdentity javaToNativeIdentity() {
      return javaToNativeIdentity;
    }

    public FileIdentity nativeToJavaIdentity() {
      return nativeToJavaIdentity;
    }

    synchronized void prepareMappedAtomicAbiProbe() {
      require(!closed.get(), "shared-memory generation resources are closed");
      require(!atomicProbePrepared && !mappedAtomicAbiProbed,
          "mapped atomic ABI probe was already started");
      javaToNative.prepareAtomicAbiProbe(0);
      atomicProbePrepared = true;
    }

    synchronized boolean completeMappedAtomicAbiProbe() {
      require(atomicProbePrepared, "mapped atomic ABI probe was not prepared");
      var completed = javaToNative.completeAtomicAbiProbe(0);
      if (completed) {
        atomicProbePrepared = false;
        mappedAtomicAbiProbed = true;
      }
      return completed;
    }

    synchronized void abortMappedAtomicAbiProbe() {
      if (atomicProbePrepared) {
        javaToNative.abortAtomicAbiProbe(0);
        atomicProbePrepared = false;
      }
    }

    public synchronized boolean mappedAtomicAbiProbed() {
      return mappedAtomicAbiProbed;
    }

    @Override
    public void close() throws IOException {
      // Make the generation unavailable immediately, but keep failed cleanup retryable.
      closed.set(true);
      cleanup.close(javaToNative::close, nativeToJava::close);
      // POSIX permits unlinking live mappings; Region.close first closes all handles.
      tryDelete(nativeToJavaPath);
      tryDelete(javaToNativePath);
      tryDelete(directory);
    }
  }

  public record FileIdentity(long device, long inode) {}

  /** A mapped directional region with frozen interprocess atomic state transitions. */
  public static final class Region implements AutoCloseable {
    private final int regionId;
    private final long generation;
    private final FileChannel channel;
    private final Arena arena;
    private final MemorySegment segment;
    private final ByteBuffer mapping;
    private final AtomicBoolean closed = new AtomicBoolean();
    private final CleanupProgress cleanup = new CleanupProgress();

    private Region(
        Path path,
        int regionId,
        long generation,
        FileIdentity expectedIdentity) throws IOException {
      this.regionId = regionId;
      this.generation = generation;
      this.channel = FileChannel.open(path, StandardOpenOption.READ, StandardOpenOption.WRITE);
      if (channel.size() != REGION_BYTES) {
        channel.close();
        throw new IOException("shared-memory region file has wrong size");
      }
      this.arena = Arena.ofShared();
      try {
        this.segment = channel.map(FileChannel.MapMode.READ_WRITE, 0, REGION_BYTES, arena);
      } catch (IOException | RuntimeException | Error error) {
        try {
          arena.close();
        } catch (RuntimeException closeError) {
          error.addSuppressed(closeError);
        }
        try {
          channel.close();
        } catch (IOException closeError) {
          error.addSuppressed(closeError);
        }
        throw error;
      }
      this.mapping = segment.asByteBuffer().order(ByteOrder.BIG_ENDIAN);
      try {
        verifyMappedBinding(path, expectedIdentity, mapping, segment);
        for (var slot = 0; slot < SLOT_COUNT; slot++) {
          var record = recordOffset(slot);
          if (((int) STATE.getVolatile(mapping, record)) != FREE
              || !allZero(record + 4, CONTROL_RECORD_BYTES - 4)) {
            throw new IOException("shared-memory control prefix is not fresh");
          }
        }
      } catch (IOException | RuntimeException | Error error) {
        try {
          arena.close();
        } catch (RuntimeException closeError) {
          error.addSuppressed(closeError);
        }
        try {
          channel.close();
        } catch (IOException closeError) {
          error.addSuppressed(closeError);
        }
        throw error;
      }
    }

    public static Region open(
        Path path, int regionId, long generation, FileIdentity expectedIdentity)
        throws IOException {
      return new Region(path, regionId, generation, expectedIdentity);
    }

    public int regionId() {
      return regionId;
    }

    public long generation() {
      return generation;
    }

    private synchronized void prepareAtomicAbiProbe(int slot) {
      require(!closed.get(), "shared-memory region is closed");
      var record = recordOffset(slot);
      require(allZero(record, CONTROL_RECORD_BYTES),
          "mapped atomic ABI probe slot is not fresh");
      require((boolean) STATE.compareAndSet(mapping, record, FREE, WRITING),
          "mapped atomic ABI probe could not reserve its slot");
      try {
        zero(record + 4, CONTROL_RECORD_BYTES - 4);
        mapping.putInt(record + 4, regionId);
        mapping.putLong(record + 8, generation);
        mapping.putInt(record + 16, slot);
        // Publish the metadata to the native probe while retaining WRITING.
        // Its acquire load/CAS must observe this release-store before reading.
        STATE.setRelease(mapping, record, WRITING);
        require(rawState(slot) == WRITING
                && Arrays.equals(rawStateBytes(slot), new byte[] {0, 0, 0, 1}),
            "Java mapped atomic probe bytes are not big-endian WRITING");
      } catch (RuntimeException | Error error) {
        zero(record + 4, CONTROL_RECORD_BYTES - 4);
        STATE.setRelease(mapping, record, FREE);
        throw error;
      }
    }

    private synchronized boolean completeAtomicAbiProbe(int slot) {
      require(!closed.get(), "shared-memory region is closed");
      var record = recordOffset(slot);
      if ((int) STATE.getAcquire(mapping, record) != PUBLISHED
          || !Arrays.equals(rawStateBytes(slot), new byte[] {0, 0, 0, 2})
          || mapping.getInt(record + 4) != regionId
          || mapping.getLong(record + 8) != generation
          || mapping.getInt(record + 16) != slot
          || !allZero(record + 20, CONTROL_RECORD_BYTES - 20)
          || !(boolean) STATE.compareAndSet(mapping, record, PUBLISHED, READING)
          || !Arrays.equals(rawStateBytes(slot), new byte[] {0, 0, 0, 3})) {
        return false;
      }
      zero(record + 4, CONTROL_RECORD_BYTES - 4);
      STATE.setRelease(mapping, record, FREE);
      return (int) STATE.getAcquire(mapping, record) == FREE
          && allZero(record, CONTROL_RECORD_BYTES);
    }

    private synchronized void abortAtomicAbiProbe(int slot) {
      var record = recordOffset(slot);
      zero(record + 4, CONTROL_RECORD_BYTES - 4);
      STATE.setRelease(mapping, record, FREE);
    }

    public synchronized Optional<Reference> publish(byte[] logicalPayload, Runnable beforePublish) {
      require(!closed.get(), "shared-memory region is closed");
      var payload = Arrays.copyOf(Objects.requireNonNull(logicalPayload, "logicalPayload"),
          logicalPayload.length);
      require(payload.length > 0 && payload.length <= SidecarIpcV1.MAX_LOGICAL_PAYLOAD_BYTES,
          "shared-memory logical payload is outside bounds");
      reclaimTerminalSlots();

      Integer freeSlot = null;
      var occupied = new ArrayList<long[]>();
      for (var slot = 0; slot < SLOT_COUNT; slot++) {
        var state = getAcquire(slot);
        validState(state);
        if (state == FREE) {
          if (freeSlot == null) {
            freeSlot = slot;
          }
          continue;
        }
        // WRITING metadata is producer-owned and not publication-safe.  Do
        // not inspect a partially initialized record from another producer or
        // a corrupt leftover state; bounded copy remains available.
        if (state == WRITING) {
          return Optional.empty();
        }
        var offset = mapping.getLong(recordOffset(slot) + 24);
        var length = mapping.getLong(recordOffset(slot) + 32);
        require(validRange(offset, length), "live shared-memory slot range is invalid");
        occupied.add(new long[] {offset, Math.addExact(offset, length)});
      }
      if (freeSlot == null) {
        return Optional.empty();
      }
      occupied.sort(Comparator.comparingLong(interval -> interval[0]));
      var previousEnd = (long) CONTROL_PREFIX_BYTES;
      for (var interval : occupied) {
        require(interval[0] >= previousEnd, "live shared-memory slot ranges overlap");
        previousEnd = interval[1];
      }
      var offset = (long) CONTROL_PREFIX_BYTES;
      for (var interval : occupied) {
        if (interval[0] >= offset && payload.length <= interval[0] - offset) {
          break;
        }
        if (interval[1] > offset) {
          offset = align64(interval[1]);
        }
      }
      if (!validRange(offset, payload.length)) {
        return Optional.empty();
      }
      if (!(boolean) STATE.compareAndSet(mapping, recordOffset(freeSlot), FREE, WRITING)) {
        return Optional.empty();
      }
      var record = recordOffset(freeSlot);
      try {
        var digest = SidecarIpcV1.sha256(payload);
        zero(record + 4, CONTROL_RECORD_BYTES - 4);
        mapping.putInt(record + 4, regionId);
        mapping.putLong(record + 8, generation);
        mapping.putInt(record + 16, freeSlot);
        mapping.putLong(record + 24, offset);
        mapping.putLong(record + 32, payload.length);
        putBytes(record + 40, digest);
        putBytes(Math.toIntExact(offset), payload);
        if (beforePublish != null) {
          beforePublish.run();
        }
        STATE.setRelease(mapping, record, PUBLISHED);
        return Optional.of(
            new Reference(regionId, freeSlot, generation, offset, payload.length, digest));
      } catch (RuntimeException | Error error) {
        STATE.setRelease(mapping, record, REJECTED);
        throw error;
      }
    }

    public synchronized byte[] consume(Reference reference) {
      require(!closed.get(), "shared-memory region is closed");
      Objects.requireNonNull(reference, "reference");
      require(reference.regionId == regionId, "shared-memory reference region mismatch");
      require(reference.generation == generation,
          "shared-memory reference generation mismatch");
      require(reference.slot >= 0 && reference.slot < SLOT_COUNT,
          "shared-memory slot is out of bounds");
      require(validRange(reference.offset, reference.length),
          "shared-memory reference range is invalid");
      var record = recordOffset(reference.slot);
      if (!(boolean) STATE.compareAndSet(mapping, record, PUBLISHED, READING)) {
        throw invalid("shared-memory slot is not published");
      }
      try {
        require(mapping.getInt(record + 4) == reference.regionId
                && mapping.getLong(record + 8) == reference.generation
                && mapping.getInt(record + 16) == reference.slot
                && mapping.getInt(record + 20) == 0
                && mapping.getLong(record + 24) == reference.offset
                && mapping.getLong(record + 32) == reference.length
                && Arrays.equals(readBytes(record + 40, 32), reference.digest)
                && allZero(record + 72, 56),
            "shared-memory reference differs from control record");
        // The single serialized producer checks every stable live range before
        // reserving a slot.  A consumer must not scan unrelated records while
        // another slot is WRITING or being reclaimed.
        var result = readBytes(Math.toIntExact(reference.offset), Math.toIntExact(reference.length));
        require(Arrays.equals(SidecarIpcV1.sha256(result), reference.digest),
            "shared-memory logical payload digest mismatch");
        STATE.setRelease(mapping, record, ACKED);
        return result;
      } catch (RuntimeException | Error error) {
        STATE.setRelease(mapping, record, REJECTED);
        throw error;
      }
    }

    enum NotificationMatch {
      MATCHED,
      RECLAIMED,
      MISMATCH
    }

    synchronized NotificationMatch classifyTerminalNotification(
        Reference reference, SidecarIpcV1.SharedMemoryDisposition disposition) {
      Objects.requireNonNull(reference, "reference");
      Objects.requireNonNull(disposition, "disposition");
      require(reference.regionId == regionId,
          "shared-memory notification region mismatch");
      require(reference.generation == generation,
          "shared-memory notification generation mismatch");
      require(reference.slot >= 0 && reference.slot < SLOT_COUNT,
          "shared-memory notification slot is out of bounds");
      require(validRange(reference.offset, reference.length),
          "shared-memory notification range is invalid");
      var record = Math.multiplyExact(reference.slot, CONTROL_RECORD_BYTES);
      var expectedState = disposition == SidecarIpcV1.SharedMemoryDisposition.ACKED
          ? ACKED : REJECTED;
      var state = (int) STATE.getAcquire(mapping, record);
      if (state == FREE || state == WRITING) {
        return NotificationMatch.RECLAIMED;
      }
      var exact = mapping.getInt(record + 4) == reference.regionId
          && mapping.getLong(record + 8) == reference.generation
          && mapping.getInt(record + 16) == reference.slot
          && mapping.getInt(record + 20) == 0
          && mapping.getLong(record + 24) == reference.offset
          && mapping.getLong(record + 32) == reference.length
          && bytesEqual(mapping, record + 40, reference.digest)
          && zeroRange(mapping, record + 72, CONTROL_RECORD_BYTES - 72);
      if (!exact) {
        return NotificationMatch.RECLAIMED;
      }
      return state == expectedState ? NotificationMatch.MATCHED : NotificationMatch.MISMATCH;
    }

    int rawState(int slot) {
      return (int) STATE.getAcquire(mapping, recordOffset(slot));
    }

    byte[] rawStateBytes(int slot) {
      return readBytes(recordOffset(slot), 4);
    }

    private void reclaimTerminalSlots() {
      for (var slot = 0; slot < SLOT_COUNT; slot++) {
        var state = getAcquire(slot);
        validState(state);
        if (state == ACKED || state == REJECTED) {
          var record = recordOffset(slot);
          zero(record + 4, CONTROL_RECORD_BYTES - 4);
          STATE.setRelease(mapping, record, FREE);
        }
      }
    }

    private int getAcquire(int slot) {
      return (int) STATE.getAcquire(mapping, recordOffset(slot));
    }

    private void putBytes(int offset, byte[] value) {
      var view = mapping.duplicate();
      view.position(offset);
      view.put(value);
    }

    private byte[] readBytes(int offset, int length) {
      var result = new byte[length];
      var view = mapping.duplicate();
      view.position(offset);
      view.get(result);
      return result;
    }

    private boolean allZero(int offset, int length) {
      for (var index = 0; index < length; index++) {
        if (mapping.get(offset + index) != 0) {
          return false;
        }
      }
      return true;
    }

    private void zero(int offset, int length) {
      for (var index = 0; index < length; index++) {
        mapping.put(offset + index, (byte) 0);
      }
    }

    @Override
    public void close() throws IOException {
      // Reject further carrier access as soon as cleanup begins. Cleanup completion itself is
      // tracked separately so an unmap/descriptor failure cannot become false idempotent success.
      closed.set(true);
      cleanup.close(this::closeMapping, this::closeChannel);
    }

    private void closeMapping() throws IOException {
      RuntimeException failure = null;
      try {
        if (arena.scope().isAlive()) {
          arena.close();
        }
      } catch (RuntimeException error) {
        failure = error;
      }
      if (arena.scope().isAlive()) {
        throw new IOException("cannot unmap shared-memory region", failure);
      }
    }

    private void closeChannel() throws IOException {
      IOException failure = null;
      try {
        if (channel.isOpen()) {
          channel.close();
        }
      } catch (IOException error) {
        failure = error;
      }
      if (channel.isOpen()) {
        if (failure != null) {
          throw failure;
        }
        throw new IOException("cannot close shared-memory region descriptor");
      }
    }
  }

  public static final class Transport implements LocalSidecarClient.Transport {
    private final LocalSidecarClient.Transport delegate;
    private final Region producer;
    private final Region consumer;
    private final PublishedNotification[] publications =
        new PublishedNotification[SLOT_COUNT];
    private volatile boolean lastWriteSharedMemory;

    public Transport(
        LocalSidecarClient.Transport delegate, Region producer, Region consumer) {
      this.delegate = Objects.requireNonNull(delegate, "delegate");
      this.producer = Objects.requireNonNull(producer, "producer");
      this.consumer = Objects.requireNonNull(consumer, "consumer");
    }

    @Override
    public synchronized void write(byte[] canonicalFrame) throws IOException {
      var carrier = makeCarrier(canonicalFrame, producer, null);
      lastWriteSharedMemory = carrier.isPresent();
      if (carrier.isPresent()) {
        var header = inspectCarrierHeader(carrier.get());
        var reference = Reference.decode(referenceBytes(carrier.get()));
        var frame = SidecarIpcV1.decodeFrame(canonicalFrame);
        publications[reference.slot] = new PublishedNotification(
            reference,
            header.correlationId(),
            frame.payload().bytes(1),
            frame.payload().bytes(2));
      }
      delegate.write(carrier.orElse(canonicalFrame));
    }

    @Override
    public boolean lastWriteSharedMemory() {
      return lastWriteSharedMemory;
    }

    @Override
    public boolean sharedMemoryConfigured() {
      return true;
    }

    @Override
    public byte[] read() throws IOException {
      var carrier = delegate.read();
      if (carrier.length < SidecarIpcV1.HEADER_BYTES) {
        throw new EOFException("shared-memory transport received a truncated frame");
      }
      return carrier;
    }

    @Override
    public byte[] resolveSharedMemoryCarrier(byte[] carrier) {
      return resolveCarrier(carrier, consumer);
    }

    @Override
    public synchronized boolean acceptSharedMemoryAck(SidecarIpcV1.Frame notification) {
      Objects.requireNonNull(notification, "notification");
      require(notification.messageType() == SidecarIpcV1.MessageType.SHARED_MEMORY_ACK,
          "transport expected SHARED_MEMORY_ACK");
      var payload = notification.payload();
      var reference = Reference.decode(payload.bytes(16));
      var disposition = SidecarIpcV1.SharedMemoryDisposition.fromCode(payload.u8(17));
      require(reference.regionId == producer.regionId()
              && reference.generation == producer.generation(),
          "shared-memory ACK has stale producer identity");
      PublishedNotification publication = null;
      for (var candidate : publications) {
        if (candidate != null && notification.correlationId().equals(candidate.correlationId)) {
          publication = candidate;
          break;
        }
      }
      // Correlations are unique for the whole session. Therefore a different correlation on an
      // identical reused reference belongs to an older superseded publication and must stutter;
      // only the current correlation has authority to validate the current publication owner.
      if (publication == null) {
        return true;
      }
      require(sameReference(publication.reference, reference)
              && Arrays.equals(payload.bytes(1), publication.requestId)
              && Arrays.equals(payload.bytes(2), publication.requestDigest),
          "shared-memory ACK does not match its publication");
      if (publication.notified) {
        return publication.disposition == disposition;
      }
      var notificationMatch = producer.classifyTerminalNotification(reference, disposition);
      if (notificationMatch == Region.NotificationMatch.MISMATCH) {
        return false;
      }
      if (notificationMatch == Region.NotificationMatch.RECLAIMED) {
        // The exact control record was reclaimed before this delayed frame
        // arrived. Correlation uniqueness makes it a transport stutter.
        return true;
      }
      publication.notified = true;
      publication.disposition = disposition;
      return true;
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

  private static final class PublishedNotification {
    private final Reference reference;
    private final SidecarIpcV1.Id128 correlationId;
    private final byte[] requestId;
    private final byte[] requestDigest;
    private boolean notified;
    private SidecarIpcV1.SharedMemoryDisposition disposition;

    private PublishedNotification(
        Reference reference,
        SidecarIpcV1.Id128 correlationId,
        byte[] requestId,
        byte[] requestDigest) {
      this.reference = reference;
      this.correlationId = correlationId;
      this.requestId = Arrays.copyOf(requestId, requestId.length);
      this.requestDigest = Arrays.copyOf(requestDigest, requestDigest.length);
    }
  }

  public static Optional<byte[]> makeCarrier(
      byte[] canonicalInlineFrame, Region producer, Runnable beforePublish) {
    var canonical = Arrays.copyOf(
        Objects.requireNonNull(canonicalInlineFrame, "canonicalInlineFrame"),
        canonicalInlineFrame.length);
    var decoded = SidecarIpcV1.decodeFrame(canonical);
    if (!decoded.messageType().sharedMemoryEligible()) {
      return Optional.empty();
    }
    var expectedRegion = decoded.messageType().isRequest()
        ? JAVA_TO_NATIVE : NATIVE_TO_JAVA;
    require(producer.regionId() == expectedRegion,
        "shared-memory producer region has wrong direction");
    require(producer.generation() == decoded.generation(),
        "shared-memory producer generation mismatch");
    var reference = producer.publish(decoded.payload().canonicalBytes(), beforePublish);
    if (reference.isEmpty()) {
      return Optional.empty();
    }
    var result = new byte[SidecarIpcV1.HEADER_BYTES + SidecarIpcV1.SHARED_MEMORY_REFERENCE_BYTES];
    System.arraycopy(canonical, 0, result, 0, SidecarIpcV1.HEADER_BYTES);
    ByteBuffer.wrap(result).order(ByteOrder.BIG_ENDIAN).putInt(
        16, SidecarIpcV1.sharedMemoryFlags(decoded.messageType()));
    System.arraycopy(reference.get().encode(), 0, result, SidecarIpcV1.HEADER_BYTES,
        SidecarIpcV1.SHARED_MEMORY_REFERENCE_BYTES);
    return Optional.of(result);
  }

  public static byte[] resolveCarrier(byte[] sharedCarrier, Region consumer) {
    var carrier = Arrays.copyOf(Objects.requireNonNull(sharedCarrier, "sharedCarrier"),
        sharedCarrier.length);
    var header = inspectCarrierHeader(carrier);
    var reference = Reference.decode(Arrays.copyOfRange(
        carrier, SidecarIpcV1.HEADER_BYTES, carrier.length));
    var expectedRegion = header.messageType().isRequest() ? JAVA_TO_NATIVE : NATIVE_TO_JAVA;
    require(consumer.regionId() == expectedRegion && reference.regionId == expectedRegion,
        "shared-memory consumer region has wrong direction");
    require(consumer.generation() == header.generation()
            && reference.generation == header.generation(),
        "shared-memory carrier generation mismatch");
    require(reference.length == header.logicalLength()
            && Arrays.equals(reference.digest, header.digest()),
        "shared-memory reference differs from frame header");
    var logical = consumer.consume(reference);
    var result = Arrays.copyOf(carrier, Math.addExact(SidecarIpcV1.HEADER_BYTES, logical.length));
    ByteBuffer.wrap(result).order(ByteOrder.BIG_ENDIAN).putInt(
        16, SidecarIpcV1.inlineFlags(header.messageType()));
    System.arraycopy(logical, 0, result, SidecarIpcV1.HEADER_BYTES, logical.length);
    SidecarIpcV1.decodeFrame(result);
    return result;
  }

  public static byte[] referenceBytes(byte[] carrier) {
    Objects.requireNonNull(carrier, "carrier");
    require(carrier.length == SidecarIpcV1.HEADER_BYTES + SidecarIpcV1.SHARED_MEMORY_REFERENCE_BYTES,
        "shared-memory carrier has wrong size");
    return Arrays.copyOfRange(carrier, SidecarIpcV1.HEADER_BYTES, carrier.length);
  }

  private static boolean sameReference(Reference left, Reference right) {
    return left.regionId == right.regionId
        && left.slot == right.slot
        && left.generation == right.generation
        && left.offset == right.offset
        && left.length == right.length
        && Arrays.equals(left.digest, right.digest);
  }

  private static boolean bytesEqual(ByteBuffer source, int offset, byte[] expected) {
    for (var index = 0; index < expected.length; ++index) {
      if (source.get(offset + index) != expected[index]) {
        return false;
      }
    }
    return true;
  }

  private static boolean zeroRange(ByteBuffer source, int offset, int length) {
    for (var index = 0; index < length; ++index) {
      if (source.get(offset + index) != 0) {
        return false;
      }
    }
    return true;
  }

  public record Reference(
      int regionId, int slot, long generation, long offset, long length, byte[] digest) {
    public Reference {
      require(regionId == JAVA_TO_NATIVE || regionId == NATIVE_TO_JAVA,
          "shared-memory region ID is invalid");
      require(slot >= 0 && slot < SLOT_COUNT, "shared-memory slot is out of bounds");
      require(generation != 0, "shared-memory generation is zero");
      require(validRange(offset, length), "shared-memory reference range is invalid");
      digest = Arrays.copyOf(Objects.requireNonNull(digest, "digest"), digest.length);
      require(digest.length == 32, "shared-memory digest has wrong size");
    }

    public byte[] digest() {
      return Arrays.copyOf(digest, digest.length);
    }

    byte[] encode() {
      var output = ByteBuffer.allocate(SidecarIpcV1.SHARED_MEMORY_REFERENCE_BYTES)
          .order(ByteOrder.BIG_ENDIAN);
      output.putInt(regionId);
      output.putInt(slot);
      output.putLong(generation);
      output.putLong(offset);
      output.putLong(length);
      output.put(digest);
      return output.array();
    }

    static Reference decode(byte[] encoded) {
      require(encoded.length == SidecarIpcV1.SHARED_MEMORY_REFERENCE_BYTES,
          "shared-memory reference has wrong size");
      var input = ByteBuffer.wrap(encoded).order(ByteOrder.BIG_ENDIAN);
      var region = input.getInt();
      var slot = input.getInt();
      var generation = input.getLong();
      var offset = input.getLong();
      var length = input.getLong();
      var digest = new byte[32];
      input.get(digest);
      return new Reference(region, slot, generation, offset, length, digest);
    }
  }

  public record CarrierHeader(
      SidecarIpcV1.MessageType messageType,
      SidecarIpcV1.Id128 sessionId,
      long generation,
      SidecarIpcV1.Id128 correlationId,
      long sequence,
      long logicalLength,
      byte[] digest) {
    public CarrierHeader {
      digest = Arrays.copyOf(digest, digest.length);
    }

    public byte[] digest() {
      return Arrays.copyOf(digest, digest.length);
    }
  }

  public static boolean isSharedMemoryCarrier(byte[] carrier) {
    return carrier != null && carrier.length >= SidecarIpcV1.HEADER_BYTES
        && (ByteBuffer.wrap(carrier).order(ByteOrder.BIG_ENDIAN).getInt(16)
            & SidecarIpcV1.FLAG_PAYLOAD_SHARED_MEMORY) != 0;
  }

  public static CarrierHeader inspectCarrierHeader(byte[] carrier) {
    require(carrier.length == SidecarIpcV1.HEADER_BYTES
            + SidecarIpcV1.SHARED_MEMORY_REFERENCE_BYTES,
        "shared-memory carrier has wrong size");
    var input = ByteBuffer.wrap(carrier).order(ByteOrder.BIG_ENDIAN);
    var magic = new byte[8];
    input.get(magic);
    require(Arrays.equals(magic, MAGIC), "frame magic mismatch");
    require(Short.toUnsignedInt(input.getShort()) == SidecarIpcV1.IPC_MAJOR,
        "IPC major mismatch");
    require(Short.toUnsignedInt(input.getShort()) == SidecarIpcV1.IPC_MINOR,
        "IPC minor mismatch");
    require(Short.toUnsignedInt(input.getShort()) == SidecarIpcV1.HEADER_BYTES,
        "header length mismatch");
    var type = SidecarIpcV1.MessageType.fromCode(Short.toUnsignedInt(input.getShort()));
    require(input.getInt() == SidecarIpcV1.sharedMemoryFlags(type),
        "frame flags differ from frozen table");
    var session = new byte[16];
    input.get(session);
    var generation = input.getLong();
    require(generation != 0, "generation zero is reserved");
    var correlation = new byte[16];
    input.get(correlation);
    var sequence = input.getLong();
    require(sequence != 0, "transport sequence zero is reserved");
    var length = input.getLong();
    require(length > 0 && length <= SidecarIpcV1.MAX_LOGICAL_PAYLOAD_BYTES,
        "payload length is outside bounds");
    var responseCapacity = input.getLong();
    require(responseCapacity == (type.responseExpected()
            ? SidecarIpcV1.MAX_LOGICAL_PAYLOAD_BYTES : 0L),
        "response capacity violates frozen rule");
    var digest = new byte[32];
    input.get(digest);
    for (var index = 0; index < 12; index++) {
      require(input.get() == 0, "frame reserved bytes are nonzero");
    }
    return new CarrierHeader(
        type,
        new SidecarIpcV1.Id128(session),
        generation,
        new SidecarIpcV1.Id128(correlation),
        sequence,
        length,
        digest);
  }

  private static void createSparseFile(Path path) throws IOException {
    try (var channel = FileChannel.open(
        path, StandardOpenOption.CREATE_NEW, StandardOpenOption.READ, StandardOpenOption.WRITE)) {
      channel.position(REGION_BYTES - 1);
      channel.write(ByteBuffer.wrap(new byte[] {0}));
      channel.force(true);
    }
  }

  public static FileIdentity fileIdentity(Path path) throws IOException {
    var basic = Files.readAttributes(
        path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
    if (!basic.isRegularFile() || basic.isSymbolicLink()) {
      throw new IOException("shared-memory path is not a non-symlink regular file");
    }
    Map<String, Object> unix = Files.readAttributes(
        path, "unix:dev,ino", LinkOption.NOFOLLOW_LINKS);
    return new FileIdentity(
        ((Number) unix.get("dev")).longValue(),
        ((Number) unix.get("ino")).longValue());
  }

  private static void verifyMappedBinding(
      Path path,
      FileIdentity expected,
      ByteBuffer mapping,
      MemorySegment segment) throws IOException {
    // Generation files live in a newly-created private temporary directory. We
    // additionally pin dev+ino before/after map and round-trip a marker through
    // the mapping and a NOFOLLOW pathname handle. Native receives that identity
    // and fstat-verifies its own opened handle. A privileged process that can
    // continuously swap the private pathname is outside the local peer model;
    // every deterministic substitution window fails closed.
    if (!fileIdentity(path).equals(expected)) {
      throw new IOException("shared-memory pathname binding changed before map");
    }
    var marker = SidecarIpcV1.sha256(
        (path.toAbsolutePath().normalize() + ":" + System.nanoTime())
            .getBytes(java.nio.charset.StandardCharsets.UTF_8));
    var offset = Math.toIntExact(REGION_BYTES - marker.length);
    var mappedView = mapping.duplicate();
    mappedView.position(offset);
    mappedView.put(marker);
    segment.force();
    try {
      if (!fileIdentity(path).equals(expected)) {
        throw new IOException("shared-memory pathname binding changed during map");
      }
      var observed = ByteBuffer.allocate(marker.length);
      try (var pathChannel = FileChannel.open(
          path, StandardOpenOption.READ, LinkOption.NOFOLLOW_LINKS)) {
        pathChannel.position(offset);
        while (observed.hasRemaining()) {
          if (pathChannel.read(observed) < 0) {
            throw new EOFException("shared-memory pathname marker is truncated");
          }
        }
      }
      if (!Arrays.equals(marker, observed.array()) || !fileIdentity(path).equals(expected)) {
        throw new IOException("shared-memory mapping and pathname identify different files");
      }
    } finally {
      mappedView.position(offset);
      mappedView.put(new byte[marker.length]);
      segment.force();
    }
    var cleared = ByteBuffer.allocate(marker.length);
    try (var pathChannel = FileChannel.open(
        path, StandardOpenOption.READ, LinkOption.NOFOLLOW_LINKS)) {
      pathChannel.position(offset);
      while (cleared.hasRemaining()) {
        if (pathChannel.read(cleared) < 0) {
          throw new EOFException("shared-memory cleared marker is truncated");
        }
      }
    }
    if (!Arrays.equals(new byte[marker.length], cleared.array())
        || !fileIdentity(path).equals(expected)) {
      throw new IOException("shared-memory pathname changed after mapping verification");
    }
  }

  private static void closeQuietly(Region region) {
    if (region == null) {
      return;
    }
    try {
      region.close();
    } catch (IOException ignored) {
      // The primary creation failure remains authoritative.
    }
  }

  private static boolean probeAtomicAbi() {
    var os = System.getProperty("os.name", "").toLowerCase(java.util.Locale.ROOT);
    var arch = System.getProperty("os.arch", "").toLowerCase(java.util.Locale.ROOT);
    if (os.contains("win")
        || !(arch.equals("amd64") || arch.equals("x86_64") || arch.equals("aarch64"))) {
      return false;
    }
    var probe = ByteBuffer.allocateDirect(128).order(ByteOrder.BIG_ENDIAN);
    return (boolean) STATE.compareAndSet(probe, 0, FREE, WRITING)
        && Arrays.equals(new byte[] {0, 0, 0, 1},
            new byte[] {probe.get(0), probe.get(1), probe.get(2), probe.get(3)})
        && (int) STATE.getAcquire(probe, 0) == WRITING;
  }

  private static int recordOffset(int slot) {
    require(slot >= 0 && slot < SLOT_COUNT, "shared-memory slot is out of bounds");
    return Math.multiplyExact(slot, CONTROL_RECORD_BYTES);
  }

  private static long align64(long value) {
    return Math.addExact(value, 63L) & ~63L;
  }

  private static boolean validRange(long offset, long length) {
    return offset >= CONTROL_PREFIX_BYTES && length > 0 && offset <= REGION_BYTES
        && length <= REGION_BYTES - offset;
  }

  private static void validState(int state) {
    require(state >= FREE && state <= REJECTED, "shared-memory control state is invalid");
  }

  private static void tryDelete(Path path) {
    try {
      Files.deleteIfExists(path);
    } catch (IOException ignored) {
      // Generation directories are best-effort cleanup after all handles close.
    }
  }

  private static SidecarIpcV1.ProtocolException invalid(String message) {
    return new SidecarIpcV1.ProtocolException(message);
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw invalid(message);
    }
  }
}
