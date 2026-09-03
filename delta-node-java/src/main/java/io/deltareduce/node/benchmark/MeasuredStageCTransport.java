package io.deltareduce.node.benchmark;

import io.netty.bootstrap.Bootstrap;
import io.netty.bootstrap.ServerBootstrap;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import io.netty.channel.Channel;
import io.netty.channel.ChannelHandler;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;
import io.netty.channel.ChannelInitializer;
import io.netty.channel.ChannelOption;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.channel.socket.nio.NioSocketChannel;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Source-bound Stage C measurement process using an actual Netty loopback TCP path and the native
 * fault/WAL sidecar. It emits a bounded ASCII receipt protocol for strict parsing by Python.
 */
public final class MeasuredStageCTransport {
  private static final int MAXIMUM_PACKET_COUNT = 4096;
  private static final int MAXIMUM_PAYLOAD_BYTES = 4096;
  private static final int MAXIMUM_PROFILE_COUNT = 16;
  private static final int MAXIMUM_FAULT_COUNT = 64;
  private static final Duration COMPLETION_TIMEOUT = Duration.ofSeconds(30);

  private MeasuredStageCTransport() {}

  record Profile(
      String id,
      long seed,
      long rttMillis,
      long jitterMillis,
      long bandwidthKbps,
      long lossPpm,
      long duplicationPpm,
      long reorderingPpm,
      long disconnectMillis) {}

  record Fault(String id, String actor, String action, long step, boolean assumptionsHold) {}

  record Request(String planId, int packetCount, int payloadBytes, List<Profile> profiles,
      List<Fault> faults) {}

  record Measurement(
      String profileId,
      long attemptedPackets,
      long attemptedPayloadBytes,
      long uniqueDeliveredPackets,
      long uniqueDeliveredPayloadBytes,
      long droppedPackets,
      long droppedPayloadBytes,
      long duplicatePackets,
      long duplicatePayloadBytes,
      long reorderedPackets,
      long disconnectCount,
      long disconnectDurationMillis,
      long javaTxPayloadBytes,
      long javaRxPayloadBytes,
      long osTxBytesBefore,
      long osTxBytesAfter,
      long osTxBytes,
      long osRxBytesBefore,
      long osRxBytesAfter,
      long osRxBytes) {
    String receiptLine() {
      return String.join(
          " ",
          "PROFILE",
          profileId,
          Long.toString(attemptedPackets),
          Long.toString(attemptedPayloadBytes),
          Long.toString(uniqueDeliveredPackets),
          Long.toString(uniqueDeliveredPayloadBytes),
          Long.toString(droppedPackets),
          Long.toString(droppedPayloadBytes),
          Long.toString(duplicatePackets),
          Long.toString(duplicatePayloadBytes),
          Long.toString(reorderedPackets),
          Long.toString(disconnectCount),
          Long.toString(disconnectDurationMillis),
          Long.toString(javaTxPayloadBytes),
          Long.toString(javaRxPayloadBytes),
          Long.toString(osTxBytesBefore),
          Long.toString(osTxBytesAfter),
          Long.toString(osTxBytes),
          Long.toString(osRxBytesBefore),
          Long.toString(osRxBytesAfter),
          Long.toString(osRxBytes));
    }
  }

  record ServerSnapshot(long uniquePackets, long uniqueBytes, long duplicatePackets,
      long duplicateBytes, long reorderedPackets, long receivedBytes, Set<Long> packetIds) {}

  record Transmission(long packetId, long scheduledMillis, int copyOrdinal) {}

  record CausalMessage(String messageId, String actorId, String domainId, String ticketId,
      String kind, long scheduledTick, boolean transmit) {}

  record FaultSchedule(String eventId, String networkProfileId, long gstTick,
      long hardDeadlineTick, List<CausalMessage> messages, Set<Long> deliveredOrdinals) {
    String canonicalText() {
      var output = new StringBuilder();
      output.append("schema_version=1.0.0\n");
      output.append("event_id=").append(eventId).append('\n');
      output.append("network_profile_id=").append(networkProfileId).append('\n');
      output.append("gst_tick=").append(gstTick).append('\n');
      output.append("hard_deadline_tick=").append(hardDeadlineTick).append('\n');
      output.append("message_count=").append(messages.size()).append('\n');
      for (int index = 0; index < messages.size(); index++) {
        CausalMessage message = messages.get(index);
        boolean delivered = deliveredOrdinals.contains((long) index);
        output.append("message.").append(index).append('=').append(message.messageId()).append(',')
            .append(message.actorId()).append(',').append(message.domainId()).append(',')
            .append(message.ticketId()).append(',').append(message.kind()).append(',')
            .append(message.scheduledTick()).append(',')
            .append(delivered ? message.scheduledTick() : 0).append(',')
            .append(delivered ? 1 : 0).append('\n');
      }
      return output.toString();
    }
  }

  @ChannelHandler.Sharable
  private static final class ReceiptHandler extends ChannelInboundHandlerAdapter {
    private final int expectedFrames;
    private final int expectedPayloadBytes;
    private final CountDownLatch complete;
    private final Set<Long> packetIds = new HashSet<>();
    private final ByteArrayOutputStream pending = new ByteArrayOutputStream();
    private final AtomicReference<RuntimeException> failure = new AtomicReference<>();
    private long maximumUniquePacket = -1;
    private long uniqueBytes;
    private long duplicatePackets;
    private long duplicateBytes;
    private long reorderedPackets;
    private long receivedBytes;
    private int frames;

    ReceiptHandler(int expectedFrames, int expectedPayloadBytes, CountDownLatch complete) {
      this.expectedFrames = expectedFrames;
      this.expectedPayloadBytes = expectedPayloadBytes;
      this.complete = complete;
    }

    @Override
    public synchronized void channelRead(ChannelHandlerContext context, Object message) {
      if (!(message instanceof ByteBuf buffer)) {
        context.fireChannelRead(message);
        return;
      }
      try {
        byte[] bytes = new byte[buffer.readableBytes()];
        buffer.readBytes(bytes);
        pending.write(bytes);
        parseFrames();
      } catch (RuntimeException | IOException error) {
        failure.compareAndSet(null, new IllegalStateException("invalid Netty measurement frame", error));
        while (complete.getCount() > 0) complete.countDown();
      } finally {
        buffer.release();
      }
    }

    private void parseFrames() throws IOException {
      byte[] bytes = pending.toByteArray();
      int offset = 0;
      while (bytes.length - offset >= Integer.BYTES) {
        int frameLength = ByteBuffer.wrap(bytes, offset, Integer.BYTES).order(ByteOrder.BIG_ENDIAN)
            .getInt();
        if (frameLength != Long.BYTES + Integer.BYTES + expectedPayloadBytes) {
          throw new IllegalStateException("frame length mismatch");
        }
        if (bytes.length - offset < Integer.BYTES + frameLength) break;
        var frame = ByteBuffer.wrap(bytes, offset + Integer.BYTES, frameLength)
            .order(ByteOrder.BIG_ENDIAN);
        long packetId = frame.getLong();
        int payloadLength = frame.getInt();
        if (payloadLength != expectedPayloadBytes || frame.remaining() != payloadLength) {
          throw new IllegalStateException("payload length mismatch");
        }
        byte expected = payloadByte(packetId);
        while (frame.hasRemaining()) {
          if (frame.get() != expected) throw new IllegalStateException("payload byte mismatch");
        }
        receivedBytes += payloadLength;
        if (packetIds.add(packetId)) {
          uniqueBytes += payloadLength;
          if (packetId < maximumUniquePacket) reorderedPackets++;
          maximumUniquePacket = Math.max(maximumUniquePacket, packetId);
        } else {
          duplicatePackets++;
          duplicateBytes += payloadLength;
        }
        frames++;
        complete.countDown();
        offset += Integer.BYTES + frameLength;
      }
      if (offset > 0) {
        pending.reset();
        pending.write(bytes, offset, bytes.length - offset);
      }
    }

    synchronized ServerSnapshot snapshot() {
      RuntimeException error = failure.get();
      if (error != null) throw error;
      BenchmarkContracts.require(frames == expectedFrames && pending.size() == 0,
          "incomplete Netty receipt");
      return new ServerSnapshot(
          packetIds.size(), uniqueBytes, duplicatePackets, duplicateBytes, reorderedPackets,
          receivedBytes, Set.copyOf(packetIds));
    }
  }

  private static final class NativeFaultProcess implements AutoCloseable {
    private final Process process;
    private final BufferedWriter writer;
    private final BufferedReader reader;

    NativeFaultProcess(Path executable, Path journal) {
      try {
        process = new ProcessBuilder(executable.toAbsolutePath().toString(),
            journal.toAbsolutePath().toString(), "8192")
            .redirectError(ProcessBuilder.Redirect.INHERIT)
            .start();
        writer = new BufferedWriter(
            new OutputStreamWriter(process.getOutputStream(), StandardCharsets.US_ASCII));
        reader = new BufferedReader(
            new InputStreamReader(process.getInputStream(), StandardCharsets.US_ASCII));
      } catch (IOException error) {
        throw new IllegalStateException("native fault sidecar launch failed", error);
      }
    }

    String execute(String planId, Fault fault, FaultSchedule schedule, int index) {
      String requestId = "stagec-" + planId.substring(7, 23) + "-" + index;
      try {
        writer.write(String.join(" ", "FAULT", requestId, fault.id(), fault.actor(),
            fault.action(), Long.toString(fault.step()), fault.assumptionsHold() ? "1" : "0",
            hex(schedule.canonicalText().getBytes(StandardCharsets.US_ASCII))));
        writer.newLine();
        writer.flush();
        String response = reader.readLine();
        if (response == null || !response.startsWith("FAULT_OK ")) {
          throw new IllegalStateException("native fault response invalid: " + response);
        }
        String[] fields = response.split(" ", -1);
        if (fields.length != 16 || !fields[2].equals("0")
            || !fields[4].equals("ACTUAL_RUNTIME_TRANSITION")) {
          throw new IllegalStateException("native fault response malformed or replayed");
        }
        for (int item = 5; item <= 8; item++) {
          BenchmarkContracts.requireContentId(fields[item], "native fault evidence ID");
        }
        BenchmarkContracts.require(fields[9].matches("[0-9]+")
                && fields[10].matches("[01]") && fields[11].matches("[01]")
                && fields[12].matches("[01]") && fields[13].matches("[01]")
                && fields[14].matches("(?:[0-9a-f]{2})*")
                && fields[15].matches("(?:[0-9a-f]{2})*"),
            "native fault execution proof invalid");
        return String.join(" ", "FAULT", fault.id(), Long.toString(fault.step()), fault.actor(),
            fault.action(), fields[3], fields[4], fields[5], fields[6], fields[7], fields[8],
            fields[9], fields[10], fields[11], fields[12], fields[13], fields[14], fields[15]);
      } catch (IOException error) {
        throw new IllegalStateException("native fault sidecar I/O failed", error);
      }
    }

    @Override
    public void close() {
      process.destroy();
      try {
        if (!process.waitFor(5, TimeUnit.SECONDS)) process.destroyForcibly();
      } catch (InterruptedException error) {
        Thread.currentThread().interrupt();
        process.destroyForcibly();
      }
    }
  }

  public static void main(String[] arguments) {
    if (arguments.length != 4) {
      throw new IllegalArgumentException(
          "usage: MeasuredStageCTransport REQUEST SIDECAR JOURNAL INTERFACE_COUNTER_ROOT");
    }
    Request request = readRequest(Path.of(arguments[0]));
    Path sidecar = Path.of(arguments[1]);
    Path journal = Path.of(arguments[2]);
    Path interfaceCounterRoot = Path.of(arguments[3]);
    BenchmarkContracts.require(Files.isRegularFile(sidecar) && Files.isExecutable(sidecar),
        "native sidecar is not executable");
    System.out.println("STAGEC_V1 " + request.planId());
    for (Profile profile : request.profiles()) {
      Measurement measurement = measure(request, profile, interfaceCounterRoot);
      String receipt = measurement.receiptLine();
      System.out.println(receipt + " " + BenchmarkContracts.sha256(
          ("deltareduce.010.stagec-java-transport-receipt.v1\0" + receipt)
              .getBytes(StandardCharsets.US_ASCII)));
    }
    try (var nativeProcess = new NativeFaultProcess(sidecar, journal)) {
      for (int index = 0; index < request.faults().size(); index++) {
        Fault fault = request.faults().get(index);
        FaultSchedule schedule = measureFaultSchedule(fault, profileForFault(request, fault));
        System.out.println(nativeProcess.execute(request.planId(), fault, schedule, index));
      }
    }
    System.out.println("END_STAGEC_V1");
  }

  private static Profile profileForFault(Request request, Fault fault) {
    String expected = switch (fault.actor() + ":" + fault.action()) {
      case "REGION:DELAY" -> "wan-regional";
      case "REGION:PARTITION" -> "wan-intercontinental";
      default -> "lan-control";
    };
    return request.profiles().stream().filter(profile -> profile.id().equals(expected)).findFirst()
        .orElseThrow(() -> new IllegalStateException("causal fault network profile missing"));
  }

  private static List<CausalMessage> causalMessages(
      Fault fault, Profile profile, long hardDeadlineTick) {
    var messages = new ArrayList<CausalMessage>();
    if (fault.actor().equals("WORKER") && fault.action().equals("CRASH")) {
      boolean concentrated = fault.id().equals("worker-loss-concentrated");
      BenchmarkContracts.require(concentrated || fault.id().equals("worker-loss-10pct"),
          "unknown worker-loss causal schedule");
      for (int index = 0; index < 10; index++) {
        String ordinal = paddedOrdinal(index);
        messages.add(new CausalMessage("worker-ticket-" + ordinal, "worker-" + ordinal,
            index < 5 ? "code" : "text", "ticket-" + ordinal, "WORK_TICKET",
            fault.step() + index, concentrated ? index >= 2 : index != 9));
      }
      if (concentrated) {
        for (int index = 0; index < 3; index++) {
          messages.add(new CausalMessage("abort-vote-" + index, "validator-" + index,
              "NONE", "NONE", "ABORT_VOTE", hardDeadlineTick, true));
        }
      } else {
        addQuorumMessages(messages, "aggregate", "AGGREGATE_VOTE", fault.step() + 20);
        addQuorumMessages(messages, "apply", "APPLY_VOTE", fault.step() + 30);
      }
    } else if (fault.actor().equals("REGION") && fault.action().equals("DELAY")) {
      long ticketTick = Math.addExact(fault.step(), Math.max(1, profile.jitterMillis()));
      long aggregateTick = Math.addExact(fault.step(), Math.max(1, profile.rttMillis() / 2));
      long applyTick = Math.addExact(
          aggregateTick, Math.max(1, Math.multiplyExact(profile.jitterMillis(), 2)));
      addFourTickets(messages, ticketTick);
      addQuorumMessages(messages, "aggregate", "AGGREGATE_VOTE", aggregateTick);
      addQuorumMessages(messages, "apply", "APPLY_VOTE", applyTick);
    } else if (fault.actor().equals("REGION") && fault.action().equals("PARTITION")) {
      addFourTickets(messages, fault.step());
      long partitionAttemptTick = Math.addExact(
          fault.step(), Math.max(1, profile.rttMillis() / 16));
      for (int index = 0; index < 4; index++) {
        messages.add(new CausalMessage("partition-aggregate-" + index, "validator-" + index,
            "NONE", "NONE", "AGGREGATE_VOTE", partitionAttemptTick + index, index < 2));
      }
      for (int index = 0; index < 3; index++) {
        messages.add(new CausalMessage("abort-vote-" + index, "validator-" + index,
            "NONE", "NONE", "ABORT_VOTE", hardDeadlineTick, true));
      }
    } else if (fault.actor().equals("VALIDATOR") && fault.action().equals("CRASH")) {
      addQuorumMessages(messages, "view-change", "VIEW_CHANGE_VOTE", fault.step() + 1);
    } else if (fault.actor().equals("VALIDATOR") && fault.action().equals("RESTART")) {
      messages.add(new CausalMessage("validator-recovery", "validator-0", "NONE", "NONE",
          "RECOVERY_SIGNAL", fault.step(), true));
    } else if (fault.actor().equals("STORAGE") && fault.action().equals("CRASH")) {
      messages.add(new CausalMessage("storage-availability", "storage-0", "NONE", "NONE",
          "STORAGE_SIGNAL", fault.step(), false));
    } else if (fault.actor().equals("STORAGE") && fault.action().equals("RESTART")) {
      messages.add(new CausalMessage("storage-repair", "storage-0", "NONE", "NONE",
          "STORAGE_SIGNAL", fault.step(), true));
    } else {
      throw new IllegalArgumentException("fault has no causal message schedule");
    }
    return List.copyOf(messages);
  }

  private static void addFourTickets(List<CausalMessage> messages, long firstTick) {
    for (int index = 0; index < 4; index++) {
      String ordinal = paddedOrdinal(index);
      messages.add(new CausalMessage("worker-ticket-" + ordinal, "worker-" + ordinal,
          index < 2 ? "code" : "text", "ticket-" + ordinal, "WORK_TICKET",
          firstTick + index, true));
    }
  }

  private static void addQuorumMessages(List<CausalMessage> messages, String prefix, String kind,
      long firstTick) {
    for (int index = 0; index < 3; index++) {
      messages.add(new CausalMessage(prefix + "-vote-" + index, "validator-" + index,
          "NONE", "NONE", kind, firstTick + index, true));
    }
  }

  private static String paddedOrdinal(int value) {
    BenchmarkContracts.require(value >= 0 && value < 1000, "causal ordinal out of range");
    String digits = Integer.toString(value);
    return "0".repeat(3 - digits.length()) + digits;
  }

  private static FaultSchedule measureFaultSchedule(Fault fault, Profile profile) {
    long profileDeadlineSpan = Math.addExact(profile.rttMillis() / 4, profile.jitterMillis());
    long hardDeadlineTick = Math.addExact(fault.step(), Math.max(60, profileDeadlineSpan));
    List<CausalMessage> messages = causalMessages(fault, profile, hardDeadlineTick);
    int transmitted = (int) messages.stream().filter(CausalMessage::transmit).count();
    var complete = new CountDownLatch(transmitted);
    var handler = new ReceiptHandler(transmitted, 32, complete);
    EventLoopGroup boss = new NioEventLoopGroup(1);
    EventLoopGroup serverWorkers = new NioEventLoopGroup(1);
    EventLoopGroup clientWorkers = new NioEventLoopGroup(1);
    Channel server = null;
    Channel client = null;
    try {
      server = new ServerBootstrap()
          .group(boss, serverWorkers)
          .channel(NioServerSocketChannel.class)
          .childOption(ChannelOption.TCP_NODELAY, true)
          .childHandler(new ChannelInitializer<SocketChannel>() {
            @Override
            protected void initChannel(SocketChannel channel) {
              channel.pipeline().addLast(handler);
            }
          })
          .bind(new InetSocketAddress(InetAddress.getLoopbackAddress(), 0)).syncUninterruptibly()
          .channel();
      int port = ((InetSocketAddress) server.localAddress()).getPort();
      client = new Bootstrap()
          .group(clientWorkers)
          .channel(NioSocketChannel.class)
          .option(ChannelOption.TCP_NODELAY, true)
          .handler(new ChannelInitializer<SocketChannel>() {
            @Override
            protected void initChannel(SocketChannel channel) {
              // Causal benchmark frames remain opaque to the Java transport.
            }
          })
          .connect(InetAddress.getLoopbackAddress(), port).syncUninterruptibly().channel();
      long previousTick = fault.step();
      for (int index = 0; index < messages.size(); index++) {
        CausalMessage message = messages.get(index);
        if (!message.transmit()) continue;
        sleep(message.scheduledTick() - previousTick);
        client.writeAndFlush(frame(index, 32)).syncUninterruptibly();
        previousTick = message.scheduledTick();
      }
      try {
        if (!complete.await(COMPLETION_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS)) {
          throw new IllegalStateException("causal Netty schedule timed out");
        }
      } catch (InterruptedException error) {
        Thread.currentThread().interrupt();
        throw new IllegalStateException("causal Netty schedule interrupted", error);
      }
      client.eventLoop().submit(() -> {}).syncUninterruptibly();
      ServerSnapshot snapshot = handler.snapshot();
      BenchmarkContracts.require(snapshot.packetIds().size() == transmitted,
          "causal Netty delivery set mismatch");
      return new FaultSchedule(fault.id(), profile.id(), fault.step(), hardDeadlineTick,
          messages, snapshot.packetIds());
    } finally {
      if (client != null) client.close().syncUninterruptibly();
      if (server != null) server.close().syncUninterruptibly();
      clientWorkers.shutdownGracefully(0, 5, TimeUnit.SECONDS).syncUninterruptibly();
      serverWorkers.shutdownGracefully(0, 5, TimeUnit.SECONDS).syncUninterruptibly();
      boss.shutdownGracefully(0, 5, TimeUnit.SECONDS).syncUninterruptibly();
    }
  }

  private static String hex(byte[] value) {
    char[] digits = "0123456789abcdef".toCharArray();
    char[] encoded = new char[value.length * 2];
    for (int index = 0; index < value.length; index++) {
      int item = Byte.toUnsignedInt(value[index]);
      encoded[index * 2] = digits[item >>> 4];
      encoded[index * 2 + 1] = digits[item & 0x0f];
    }
    return new String(encoded);
  }

  private static Measurement measure(Request request, Profile profile, Path counterRoot) {
    var controller = new NetworkFaultController(profile.seed(), profile.rttMillis(),
        profile.jitterMillis(), profile.lossPpm(), profile.duplicationPpm(),
        profile.reorderingPpm());
    var decisions = new ArrayList<NetworkFaultController.Decision>();
    int transmittedFrames = 0;
    long droppedPackets = 0;
    long controllerDuplicatePackets = 0;
    for (int index = 0; index < request.packetCount(); index++) {
      var decision = controller.decision(index);
      decisions.add(decision);
      if (decision.dropped()) {
        droppedPackets++;
      } else {
        transmittedFrames++;
        if (decision.duplicated()) {
          transmittedFrames++;
          controllerDuplicatePackets++;
        }
      }
    }
    var complete = new CountDownLatch(transmittedFrames);
    var handler = new ReceiptHandler(transmittedFrames, request.payloadBytes(), complete);
    long osTxBefore = readCounter(counterRoot.resolve("tx_bytes"));
    long osRxBefore = readCounter(counterRoot.resolve("rx_bytes"));
    EventLoopGroup boss = new NioEventLoopGroup(1);
    EventLoopGroup serverWorkers = new NioEventLoopGroup(1);
    EventLoopGroup clientWorkers = new NioEventLoopGroup(1);
    Channel server = null;
    Channel client = null;
    long disconnectDuration = 0;
    long disconnectCount = 0;
    try {
      server = new ServerBootstrap()
          .group(boss, serverWorkers)
          .channel(NioServerSocketChannel.class)
          .childOption(ChannelOption.TCP_NODELAY, true)
          .childHandler(new ChannelInitializer<SocketChannel>() {
            @Override
            protected void initChannel(SocketChannel channel) {
              channel.pipeline().addLast(handler);
            }
          })
          .bind(new InetSocketAddress(InetAddress.getLoopbackAddress(), 0)).syncUninterruptibly()
          .channel();
      int port = ((InetSocketAddress) server.localAddress()).getPort();
      Bootstrap clientBootstrap = new Bootstrap()
          .group(clientWorkers)
          .channel(NioSocketChannel.class)
          .option(ChannelOption.TCP_NODELAY, true)
          .handler(new ChannelInitializer<SocketChannel>() {
            @Override
            protected void initChannel(SocketChannel channel) {
              // The sender transports opaque framed bytes only.
            }
          });
      client = clientBootstrap.connect(InetAddress.getLoopbackAddress(), port)
          .syncUninterruptibly().channel();
      if (profile.disconnectMillis() > 0) {
        long start = System.nanoTime();
        client.close().syncUninterruptibly();
        sleep(profile.disconnectMillis());
        client = clientBootstrap.connect(InetAddress.getLoopbackAddress(), port)
            .syncUninterruptibly().channel();
        disconnectDuration = elapsedMillis(start);
        disconnectCount = 1;
      }
      long maximumDelay = profile.rttMillis() / 2 + profile.jitterMillis();
      var transmissions = new ArrayList<Transmission>();
      for (int index = 0; index < decisions.size(); index++) {
        var decision = decisions.get(index);
        if (decision.dropped()) continue;
        long serializationDelay = divideRoundUp(
            (long) (index + 1) * request.payloadBytes() * 8L, profile.bandwidthKbps());
        long reorderDelay = decision.reordered() ? maximumDelay + 1 : 0;
        long delay = decision.delayMillis() + serializationDelay + reorderDelay;
        long packetId = index;
        transmissions.add(new Transmission(packetId, delay, 0));
        if (decision.duplicated()) {
          transmissions.add(new Transmission(packetId, delay + 1, 1));
        }
      }
      transmissions.sort(Comparator.comparingLong(Transmission::scheduledMillis)
          .thenComparingLong(Transmission::packetId)
          .thenComparingInt(Transmission::copyOrdinal));
      long previousDelay = 0;
      for (Transmission transmission : transmissions) {
        sleep(transmission.scheduledMillis() - previousDelay);
        client.writeAndFlush(frame(transmission.packetId(), request.payloadBytes()))
            .syncUninterruptibly();
        previousDelay = transmission.scheduledMillis();
      }
      try {
        if (!complete.await(COMPLETION_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS)) {
          throw new IllegalStateException("Netty measurement timed out");
        }
      } catch (InterruptedException error) {
        Thread.currentThread().interrupt();
        throw new IllegalStateException("Netty measurement interrupted", error);
      }
      client.eventLoop().submit(() -> {}).syncUninterruptibly();
    } finally {
      if (client != null) client.close().syncUninterruptibly();
      if (server != null) server.close().syncUninterruptibly();
      clientWorkers.shutdownGracefully(0, 5, TimeUnit.SECONDS).syncUninterruptibly();
      serverWorkers.shutdownGracefully(0, 5, TimeUnit.SECONDS).syncUninterruptibly();
      boss.shutdownGracefully(0, 5, TimeUnit.SECONDS).syncUninterruptibly();
    }
    long osTxAfter = readCounter(counterRoot.resolve("tx_bytes"));
    long osRxAfter = readCounter(counterRoot.resolve("rx_bytes"));
    long osTxBytes = subtractCounter(osTxAfter, osTxBefore);
    long osRxBytes = subtractCounter(osRxAfter, osRxBefore);
    ServerSnapshot serverReceipt = handler.snapshot();
    long uniquePackets = request.packetCount() - droppedPackets;
    long uniqueBytes = uniquePackets * request.payloadBytes();
    long droppedBytes = droppedPackets * request.payloadBytes();
    long duplicateBytes = controllerDuplicatePackets * request.payloadBytes();
    var metrics = new NettyMetricsCollector();
    metrics.add("attempted_packets", request.packetCount());
    metrics.add("attempted_payload_bytes", (long) request.packetCount() * request.payloadBytes());
    metrics.add("unique_delivered_packets", serverReceipt.uniquePackets());
    metrics.add("unique_delivered_payload_bytes", serverReceipt.uniqueBytes());
    metrics.add("dropped_packets", droppedPackets);
    metrics.add("dropped_payload_bytes", droppedBytes);
    metrics.add("duplicate_packets", serverReceipt.duplicatePackets());
    metrics.add("duplicate_payload_bytes", serverReceipt.duplicateBytes());
    metrics.add("java_rx_payload_bytes", serverReceipt.receivedBytes());
    metrics.requireClean(0, 0, 0, request.packetCount(), 0, 1, 0);
    Map<String, Long> measured = metrics.snapshot();
    BenchmarkContracts.require(
        measured.get("attempted_packets") == request.packetCount()
            && measured.get("attempted_payload_bytes")
                == (long) request.packetCount() * request.payloadBytes()
            && measured.get("unique_delivered_packets") == uniquePackets
            && measured.get("unique_delivered_payload_bytes") == uniqueBytes
            && measured.get("duplicate_packets") == controllerDuplicatePackets
            && measured.get("duplicate_payload_bytes") == duplicateBytes
            && measured.get("dropped_packets") == droppedPackets
            && measured.get("dropped_payload_bytes") == droppedBytes
            && measured.get("java_rx_payload_bytes") == uniqueBytes + duplicateBytes
            && osTxBytes >= serverReceipt.receivedBytes()
            && osRxBytes >= serverReceipt.receivedBytes()
            && (profile.disconnectMillis() == 0
                || (disconnectCount == 1 && disconnectDuration >= profile.disconnectMillis())),
        "cross-layer network measurement did not reconcile");
    return new Measurement(profile.id(), request.packetCount(),
        (long) request.packetCount() * request.payloadBytes(), uniquePackets, uniqueBytes,
        droppedPackets, droppedBytes, controllerDuplicatePackets, duplicateBytes,
        serverReceipt.reorderedPackets(), disconnectCount, disconnectDuration,
        uniqueBytes + duplicateBytes, serverReceipt.receivedBytes(), osTxBefore, osTxAfter,
        osTxBytes, osRxBefore, osRxAfter, osRxBytes);
  }

  private static Request readRequest(Path path) {
    Map<String, String> values = new HashMap<>();
    try {
      List<String> lines = Files.readAllLines(path, StandardCharsets.US_ASCII);
      for (String line : lines) {
        int separator = line.indexOf('=');
        if (separator <= 0 || separator == line.length() - 1
            || values.putIfAbsent(line.substring(0, separator), line.substring(separator + 1)) != null) {
          throw new IllegalArgumentException("request record invalid");
        }
      }
    } catch (IOException error) {
      throw new IllegalStateException("request read failed", error);
    }
    String planId = remove(values, "plan_id");
    BenchmarkContracts.requireContentId(planId, "plan ID");
    int packetCount = positiveInt(remove(values, "packet_count"), MAXIMUM_PACKET_COUNT);
    int payloadBytes = positiveInt(remove(values, "payload_bytes"), MAXIMUM_PAYLOAD_BYTES);
    int profileCount = positiveInt(remove(values, "profile_count"), MAXIMUM_PROFILE_COUNT);
    var profiles = new ArrayList<Profile>();
    for (int index = 0; index < profileCount; index++) {
      String prefix = "profile." + index + ".";
      profiles.add(new Profile(
          token(remove(values, prefix + "id")),
          nonnegative(remove(values, prefix + "seed")),
          nonnegative(remove(values, prefix + "rtt_ms")),
          nonnegative(remove(values, prefix + "jitter_ms")),
          positive(remove(values, prefix + "bandwidth_kbps")),
          ppm(remove(values, prefix + "loss_ppm")),
          ppm(remove(values, prefix + "duplication_ppm")),
          ppm(remove(values, prefix + "reordering_ppm")),
          nonnegative(remove(values, prefix + "disconnect_ms"))));
    }
    int faultCount = positiveInt(remove(values, "fault_count"), MAXIMUM_FAULT_COUNT);
    var faults = new ArrayList<Fault>();
    for (int index = 0; index < faultCount; index++) {
      String prefix = "fault." + index + ".";
      String assumptions = remove(values, prefix + "assumptions_hold");
      BenchmarkContracts.require(assumptions.equals("0") || assumptions.equals("1"),
          "fault assumptions invalid");
      faults.add(new Fault(token(remove(values, prefix + "id")),
          token(remove(values, prefix + "actor")), token(remove(values, prefix + "action")),
          nonnegative(remove(values, prefix + "step")), assumptions.equals("1")));
    }
    BenchmarkContracts.require(values.isEmpty(), "request contains unknown fields");
    return new Request(planId, packetCount, payloadBytes, List.copyOf(profiles),
        List.copyOf(faults));
  }

  private static String remove(Map<String, String> values, String name) {
    String value = values.remove(name);
    BenchmarkContracts.require(value != null, "request field missing: " + name);
    return value;
  }

  private static String token(String value) {
    BenchmarkContracts.require(value.matches("[A-Za-z0-9_.-]{1,128}"), "request token invalid");
    return value;
  }

  private static long nonnegative(String value) {
    try {
      long parsed = Long.parseLong(value);
      BenchmarkContracts.require(parsed >= 0, "negative request integer");
      return parsed;
    } catch (NumberFormatException error) {
      throw new IllegalArgumentException("request integer invalid", error);
    }
  }

  private static long positive(String value) {
    long parsed = nonnegative(value);
    BenchmarkContracts.require(parsed > 0, "request integer must be positive");
    return parsed;
  }

  private static int positiveInt(String value, int maximum) {
    long parsed = positive(value);
    BenchmarkContracts.require(parsed <= maximum, "request integer exceeds bound");
    return (int) parsed;
  }

  private static long ppm(String value) {
    long parsed = nonnegative(value);
    BenchmarkContracts.require(parsed <= 1_000_000, "request probability invalid");
    return parsed;
  }

  private static long readCounter(Path path) {
    try {
      BenchmarkContracts.require(Files.isRegularFile(path), "OS interface counter missing");
      return nonnegative(Files.readString(path, StandardCharsets.US_ASCII).trim());
    } catch (IOException error) {
      throw new IllegalStateException("OS interface counter read failed", error);
    }
  }

  private static long subtractCounter(long after, long before) {
    BenchmarkContracts.require(after >= before, "OS interface counter regressed");
    return after - before;
  }

  private static ByteBuf frame(long packetId, int payloadBytes) {
    ByteBuf frame = Unpooled.buffer(Integer.BYTES + Long.BYTES + Integer.BYTES + payloadBytes);
    frame.writeInt(Long.BYTES + Integer.BYTES + payloadBytes);
    frame.writeLong(packetId);
    frame.writeInt(payloadBytes);
    frame.writeZero(payloadBytes);
    byte expected = payloadByte(packetId);
    if (expected != 0) frame.setByte(frame.writerIndex() - payloadBytes, expected);
    for (int index = 1; index < payloadBytes; index++) {
      frame.setByte(frame.writerIndex() - payloadBytes + index, expected);
    }
    return frame;
  }

  private static byte payloadByte(long packetId) {
    return (byte) (packetId % 251);
  }

  private static long divideRoundUp(long numerator, long denominator) {
    return (numerator + denominator - 1) / denominator;
  }

  private static void sleep(long milliseconds) {
    try {
      Thread.sleep(milliseconds);
    } catch (InterruptedException error) {
      Thread.currentThread().interrupt();
      throw new IllegalStateException("disconnect interval interrupted", error);
    }
  }

  private static long elapsedMillis(long startNanos) {
    return Math.max(1, TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - startNanos));
  }
}
