package io.deltareduce.demo;

import io.deltareduce.node.benchmark.BenchmarkTransport;
import io.deltareduce.node.benchmark.NettyMetricsCollector;
import io.netty.bootstrap.Bootstrap;
import io.netty.bootstrap.ServerBootstrap;
import io.netty.buffer.ByteBuf;
import io.netty.channel.Channel;
import io.netty.channel.ChannelFuture;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;
import io.netty.channel.ChannelInitializer;
import io.netty.channel.ChannelOption;
import io.netty.channel.SimpleChannelInboundHandler;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.channel.socket.nio.NioSocketChannel;
import io.netty.util.concurrent.DefaultEventExecutorGroup;
import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.channels.FileChannel;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.security.GeneralSecurityException;
import java.security.KeyFactory;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.PublicKey;
import java.security.Signature;
import java.security.spec.X509EncodedKeySpec;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import java.util.regex.Pattern;

/**
 * Demo-only bounded relay for signed opaque MNIST contributions.
 *
 * <p>The bytes really cross a Netty loopback TCP connection and are atomically persisted without
 * interpretation. This adapter deliberately performs no aggregation, vote, certificate, consensus,
 * or training operation.
 */
public final class MnistDeltaNettyRelay {
  private static final int MAXIMUM_ENTRIES = 128;
  private static final int MAXIMUM_MANIFEST_BYTES = 1 << 20;
  private static final int MAXIMUM_LINE_CHARS = 16 << 10;
  private static final int MAXIMUM_MESSAGE_BYTES = 64 << 20;
  private static final long MAXIMUM_TOTAL_BYTES = 256L << 20;
  private static final int FRAME_HEADER_BYTES = Integer.BYTES * 2;
  private static final Duration DELIVERY_TIMEOUT = Duration.ofSeconds(60);
  private static final Pattern CONTENT_ID = Pattern.compile("sha256:[0-9a-f]{64}");
  private static final Pattern DESTINATION_SEGMENT =
      Pattern.compile("[A-Za-z0-9][A-Za-z0-9._-]{0,127}");
  private static final byte[] SIGNATURE_DOMAIN =
      "deltareduce.mnist-demo.transport.v1\0".getBytes(StandardCharsets.US_ASCII);
  private static final byte[] ED25519_SUBJECT_PUBLIC_KEY_INFO_PREFIX =
      HexFormat.of().parseHex("302a300506032b6570032100");
  private static final String COMPONENT = "delta-node-java/netty";
  private static final String TRANSPORT = "NETTY_LOOPBACK_TCP";
  private static final char[] HEX = "0123456789abcdef".toCharArray();

  private MnistDeltaNettyRelay() {}

  /** Runs the relay. The four arguments are MANIFEST, OUTPUT_ROOT, RECEIPT, and TRACE. */
  public static void main(String[] arguments) {
    try {
      require(
          arguments.length == 4,
          "usage: MnistDeltaNettyRelay MANIFEST OUTPUT_ROOT RECEIPT TRACE");
      String receipt = run(arguments);
      System.out.println(receipt);
    } catch (Exception error) {
      System.err.println("mnist-delta-netty-relay error: " + safeMessage(error));
      System.exit(2);
    }
  }

  private static String run(String[] arguments) throws Exception {
    Path manifest = requireManifestPath(Path.of(arguments[0]));
    Path outputRoot = requireOutputRoot(Path.of(arguments[1]));
    Path receiptPath = resolveOutputPath(outputRoot, arguments[2], "receipt");
    Path tracePath = resolveOutputPath(outputRoot, arguments[3], "trace");

    List<Entry> entries = readManifest(manifest, outputRoot);
    List<Path> allTargets = new ArrayList<>();
    for (Entry entry : entries) {
      allTargets.add(entry.destination());
    }
    allTargets.add(receiptPath);
    allTargets.add(tracePath);
    requireNonConflictingTargets(allTargets);
    for (Path target : allTargets) {
      prepareNewOutput(outputRoot, target);
    }

    NettyMetricsCollector metrics = new NettyMetricsCollector();
    List<Output> outputs = relay(entries, outputRoot, metrics);
    metrics.requireClean(0, 0, 0, MAXIMUM_ENTRIES, 0, 1, 0);

    long pid = ProcessHandle.current().pid();
    String trace = buildTrace(entries, outputs, pid);
    writeAtomicallyNew(
        outputRoot, tracePath, (trace + "\n").getBytes(StandardCharsets.UTF_8));
    String receipt = buildReceipt(entries, outputs, metrics.snapshot(), pid);
    writeAtomicallyNew(
        outputRoot, receiptPath, (receipt + "\n").getBytes(StandardCharsets.UTF_8));
    return receipt;
  }

  private static List<Entry> readManifest(Path manifest, Path outputRoot) throws Exception {
    long manifestSize = Files.size(manifest);
    require(
        manifestSize > 0 && manifestSize <= MAXIMUM_MANIFEST_BYTES,
        "manifest size is outside demo bounds");
    byte[] manifestBytes = Files.readAllBytes(manifest);
    require(manifestBytes.length == manifestSize, "manifest changed while it was read");
    String document = decodeUtf8Strict(manifestBytes);
    require(document.indexOf('\0') < 0, "manifest contains a NUL character");
    document = document.replace("\r\n", "\n");
    require(document.indexOf('\r') < 0, "manifest contains a bare carriage return");

    String[] rawLines = document.split("\n", -1);
    int lineCount = rawLines.length;
    if (lineCount > 0 && rawLines[lineCount - 1].isEmpty()) {
      --lineCount;
    }
    require(lineCount > 0 && lineCount <= MAXIMUM_ENTRIES, "invalid manifest entry count");

    List<Entry> entries = new ArrayList<>(lineCount);
    Set<Path> sources = new HashSet<>();
    Set<Path> destinations = new HashSet<>();
    Set<String> contentIds = new HashSet<>();
    long totalBytes = 0;
    for (int index = 0; index < lineCount; ++index) {
      String line = rawLines[index];
      require(!line.isEmpty(), "blank manifest line " + (index + 1));
      require(line.length() <= MAXIMUM_LINE_CHARS, "manifest line is too long");
      String[] fields = line.split("\t", -1);
      require(fields.length == 5, "manifest line must contain exactly five TSV fields");
      for (String field : fields) {
        require(!field.isEmpty(), "manifest fields must not be empty");
      }

      Path source = requireSourcePath(Path.of(fields[0]));
      require(sources.add(source), "duplicate source path in manifest");
      String destinationText = requireDestinationText(fields[1]);
      Path destination = outputRoot.resolve(destinationText).normalize();
      require(destination.startsWith(outputRoot), "destination escapes output root");
      require(destinations.add(destination), "duplicate destination in manifest");
      String contentId = fields[2];
      require(CONTENT_ID.matcher(contentId).matches(), "invalid manifest content ID");
      require(contentIds.add(contentId), "duplicate content ID in manifest");

      long declaredSize = Files.size(source);
      require(
          declaredSize > 0 && declaredSize <= MAXIMUM_MESSAGE_BYTES,
          "source size is outside demo bounds");
      byte[] bytes = Files.readAllBytes(source);
      require(bytes.length == declaredSize, "source changed while it was read");
      totalBytes = Math.addExact(totalBytes, bytes.length);
      require(totalBytes <= MAXIMUM_TOTAL_BYTES, "manifest payload total exceeds demo bound");
      require(sha256(bytes).equals(contentId), "source SHA-256 does not match manifest");
      verifySignature(fields[3], fields[4], bytes);
      entries.add(new Entry(index, source, destinationText, destination, contentId, bytes));
    }
    return List.copyOf(entries);
  }

  private static List<Output> relay(
      List<Entry> entries, Path outputRoot, NettyMetricsCollector metrics) throws Exception {
    BenchmarkTransport transport =
        new BenchmarkTransport(MAXIMUM_MESSAGE_BYTES, MAXIMUM_ENTRIES);
    RelayState state = new RelayState(entries, outputRoot, transport, metrics);
    AtomicBoolean connectionClaimed = new AtomicBoolean();
    NioEventLoopGroup acceptor = new NioEventLoopGroup(1);
    NioEventLoopGroup serverIo = new NioEventLoopGroup(1);
    NioEventLoopGroup clientIo = new NioEventLoopGroup(1);
    DefaultEventExecutorGroup persistence = new DefaultEventExecutorGroup(1);
    Channel server = null;
    Channel client = null;
    try {
      ServerBootstrap serverBootstrap = new ServerBootstrap();
      serverBootstrap
          .group(acceptor, serverIo)
          .channel(NioServerSocketChannel.class)
          .option(ChannelOption.SO_BACKLOG, 1)
          .childOption(ChannelOption.TCP_NODELAY, true)
          .childHandler(
              new ChannelInitializer<SocketChannel>() {
                @Override
                protected void initChannel(SocketChannel channel) {
                  channel
                      .pipeline()
                      .addLast(
                          persistence,
                          "opaque-persistence",
                          new RelayServerHandler(state, connectionClaimed));
                }
              });
      server =
          serverBootstrap
              .bind(new InetSocketAddress(InetAddress.getLoopbackAddress(), 0))
              .sync()
              .channel();
      InetSocketAddress address = (InetSocketAddress) server.localAddress();
      require(address.getAddress().isLoopbackAddress(), "server did not bind to loopback");

      Bootstrap clientBootstrap = new Bootstrap();
      clientBootstrap
          .group(clientIo)
          .channel(NioSocketChannel.class)
          .option(ChannelOption.TCP_NODELAY, true)
          .handler(new ChannelInboundHandlerAdapter());
      client =
          clientBootstrap
              .connect(new InetSocketAddress(InetAddress.getLoopbackAddress(), address.getPort()))
              .sync()
              .channel();

      for (Entry entry : entries) {
        ByteBuf frame =
            client.alloc().buffer(Integer.BYTES + FRAME_HEADER_BYTES + entry.bytes().length);
        boolean submitted = false;
        try {
          frame.writeInt(FRAME_HEADER_BYTES + entry.bytes().length);
          frame.writeInt(entry.index());
          frame.writeInt(entry.bytes().length);
          frame.writeBytes(entry.bytes());
          metrics.add("netty_tx_messages", 1);
          metrics.add("netty_tx_payload_bytes", entry.bytes().length);
          ChannelFuture write = client.writeAndFlush(frame);
          submitted = true;
          write.sync();
        } finally {
          if (!submitted) {
            frame.release();
          }
        }
        state.await(entry.index(), DELIVERY_TIMEOUT);
      }
      state.requireComplete();
      require(
          transport.snapshotSizes().size() == entries.size(),
          "benchmark transport delivery coverage is incomplete");
      return state.outputs();
    } finally {
      if (client != null) {
        client.close().syncUninterruptibly();
      }
      if (server != null) {
        server.close().syncUninterruptibly();
      }
      clientIo.shutdownGracefully(0, 5, TimeUnit.SECONDS).syncUninterruptibly();
      serverIo.shutdownGracefully(0, 5, TimeUnit.SECONDS).syncUninterruptibly();
      acceptor.shutdownGracefully(0, 5, TimeUnit.SECONDS).syncUninterruptibly();
      persistence.shutdownGracefully(0, 5, TimeUnit.SECONDS).syncUninterruptibly();
    }
  }

  private static final class RelayServerHandler extends SimpleChannelInboundHandler<ByteBuf> {
    private final RelayState state;
    private final AtomicBoolean connectionClaimed;
    private final ByteBuffer header =
        ByteBuffer.allocate(Integer.BYTES + FRAME_HEADER_BYTES);
    private boolean acceptedConnection;
    private int payloadIndex = -1;
    private byte[] payload;
    private int payloadOffset;

    RelayServerHandler(RelayState state, AtomicBoolean connectionClaimed) {
      this.state = state;
      this.connectionClaimed = connectionClaimed;
    }

    @Override
    public void channelActive(ChannelHandlerContext context) {
      acceptedConnection = connectionClaimed.compareAndSet(false, true);
      if (!acceptedConnection) {
        context.close();
      }
    }

    @Override
    protected void channelRead0(ChannelHandlerContext context, ByteBuf frame) throws Exception {
      require(acceptedConnection, "message arrived on an unaccepted connection");
      while (frame.isReadable()) {
        if (payload == null) {
          int headerBytes = Math.min(frame.readableBytes(), header.remaining());
          frame.readBytes(header.array(), header.position(), headerBytes);
          header.position(header.position() + headerBytes);
          if (header.hasRemaining()) {
            continue;
          }
          header.flip();
          int frameLength = header.getInt();
          payloadIndex = header.getInt();
          int payloadLength = header.getInt();
          header.clear();
          require(
              payloadLength > 0 && payloadLength <= MAXIMUM_MESSAGE_BYTES,
              "invalid relay payload length");
          require(
              frameLength == FRAME_HEADER_BYTES + payloadLength,
              "relay frame length mismatch");
          payload = new byte[payloadLength];
          payloadOffset = 0;
        }

        int payloadBytes = Math.min(frame.readableBytes(), payload.length - payloadOffset);
        frame.readBytes(payload, payloadOffset, payloadBytes);
        payloadOffset += payloadBytes;
        if (payloadOffset == payload.length) {
          state.accept(payloadIndex, payload);
          payload = null;
          payloadIndex = -1;
          payloadOffset = 0;
          if (state.isComplete()) {
            require(!frame.isReadable(), "unexpected bytes after complete relay delivery");
            context.close();
          }
        }
      }
    }

    @Override
    public void channelInactive(ChannelHandlerContext context) {
      if (acceptedConnection && !state.isComplete()) {
        state.fail(new IllegalStateException("relay connection closed before complete delivery"));
      }
    }

    @Override
    public void exceptionCaught(ChannelHandlerContext context, Throwable cause) {
      state.fail(cause);
      context.close();
    }
  }

  private static final class RelayState {
    private final List<Entry> entries;
    private final Path outputRoot;
    private final BenchmarkTransport transport;
    private final NettyMetricsCollector metrics;
    private final CountDownLatch[] delivered;
    private final Output[] outputs;
    private final AtomicReference<Throwable> failure = new AtomicReference<>();
    private int nextIndex;

    RelayState(
        List<Entry> entries,
        Path outputRoot,
        BenchmarkTransport transport,
        NettyMetricsCollector metrics) {
      this.entries = entries;
      this.outputRoot = outputRoot;
      this.transport = transport;
      this.metrics = metrics;
      delivered = new CountDownLatch[entries.size()];
      outputs = new Output[entries.size()];
      for (int index = 0; index < delivered.length; ++index) {
        delivered[index] = new CountDownLatch(1);
      }
    }

    synchronized void accept(int index, byte[] payload) throws IOException {
      require(failure.get() == null, "relay is already failed");
      require(index >= 0 && index < entries.size(), "relay entry index is outside bounds");
      require(index == nextIndex, "duplicate or out-of-order relay entry");
      Entry expected = entries.get(index);
      require(
          payload.length == expected.bytes().length,
          "received payload size differs from source");
      require(sha256(payload).equals(expected.contentId()), "received payload hash mismatch");
      metrics.add("netty_rx_messages", 1);
      metrics.add("netty_rx_payload_bytes", payload.length);
      byte[] opaque = transport.deliver(expected.contentId(), payload);
      require(sha256(opaque).equals(expected.contentId()), "transport changed opaque payload");
      writeAtomicallyNew(outputRoot, expected.destination(), opaque);
      byte[] persisted = Files.readAllBytes(expected.destination());
      require(persisted.length == opaque.length, "persisted payload size mismatch");
      String persistedId = sha256(persisted);
      require(persistedId.equals(expected.contentId()), "persisted payload hash mismatch");
      metrics.add("atomic_files_written", 1);
      outputs[index] =
          new Output(expected.destinationText(), persistedId, persisted.length);
      ++nextIndex;
      delivered[index].countDown();
    }

    void await(int index, Duration timeout) throws InterruptedException {
      boolean complete = delivered[index].await(timeout.toMillis(), TimeUnit.MILLISECONDS);
      require(complete, "timed out waiting for relay delivery");
      throwIfFailed();
    }

    void fail(Throwable cause) {
      if (failure.compareAndSet(null, cause)) {
        for (CountDownLatch latch : delivered) {
          latch.countDown();
        }
      }
    }

    synchronized boolean isComplete() {
      return nextIndex == entries.size() && failure.get() == null;
    }

    synchronized void requireComplete() {
      throwIfFailed();
      require(nextIndex == entries.size(), "relay delivery coverage is incomplete");
      for (Output output : outputs) {
        require(output != null, "relay output coverage is incomplete");
      }
    }

    synchronized List<Output> outputs() {
      requireComplete();
      return List.of(outputs.clone());
    }

    private void throwIfFailed() {
      Throwable cause = failure.get();
      if (cause != null) {
        throw new IllegalStateException("relay server failed: " + safeMessage(cause), cause);
      }
    }
  }

  private static String buildTrace(List<Entry> entries, List<Output> outputs, long pid) {
    StringBuilder result = new StringBuilder();
    long sequence = 0;
    for (Entry entry : entries) {
      appendTraceLine(result, ++sequence, "SOURCE_VERIFIED", entry, entry.contentId(), pid);
    }
    for (int index = 0; index < entries.size(); ++index) {
      Entry entry = entries.get(index);
      Output output = outputs.get(index);
      appendTraceLine(result, ++sequence, "NETTY_TRANSMITTED", entry, entry.contentId(), pid);
      appendTraceLine(result, ++sequence, "NETTY_RECEIVED", entry, entry.contentId(), pid);
      appendTraceLine(result, ++sequence, "ATOMIC_WRITE_VERIFIED", entry, output.contentId(), pid);
    }
    if (!result.isEmpty()) {
      result.setLength(result.length() - 1);
    }
    return result.toString();
  }

  private static void appendTraceLine(
      StringBuilder target,
      long sequence,
      String action,
      Entry entry,
      String outputContentId,
      long pid) {
    target
        .append("{\"action\":")
        .append(jsonString(action))
        .append(",\"component\":")
        .append(jsonString(COMPONENT))
        .append(",\"destination\":")
        .append(jsonString(entry.destinationText()))
        .append(",\"input_content_id\":")
        .append(jsonString(entry.contentId()))
        .append(",\"output_content_id\":")
        .append(jsonString(outputContentId))
        .append(",\"pid\":")
        .append(pid)
        .append(",\"sequence\":")
        .append(sequence)
        .append(",\"size_bytes\":")
        .append(entry.bytes().length)
        .append(",\"status\":\"PASS\"}\n");
  }

  private static String buildReceipt(
      List<Entry> entries, List<Output> outputs, Map<String, Long> metrics, long pid) {
    StringBuilder result = new StringBuilder();
    result
        .append("{\"component\":")
        .append(jsonString(COMPONENT))
        .append(",\"entry_count\":")
        .append(entries.size())
        .append(",\"input_content_ids\":[");
    appendEntryIds(result, entries);
    result.append("],\"metrics\":{");
    boolean first = true;
    for (Map.Entry<String, Long> metric : new java.util.TreeMap<>(metrics).entrySet()) {
      if (!first) {
        result.append(',');
      }
      first = false;
      result.append(jsonString(metric.getKey())).append(':').append(metric.getValue());
    }
    result.append("},\"output_content_ids\":[");
    appendOutputIds(result, outputs);
    result.append("],\"outputs\":[");
    for (int index = 0; index < outputs.size(); ++index) {
      if (index != 0) {
        result.append(',');
      }
      Output output = outputs.get(index);
      result
          .append("{\"destination\":")
          .append(jsonString(output.destinationText()))
          .append(",\"sha256\":")
          .append(jsonString(output.contentId()))
          .append(",\"size_bytes\":")
          .append(output.sizeBytes())
          .append('}');
    }
    return result
        .append("],\"pid\":")
        .append(pid)
        .append(",\"schema_version\":\"1.0.0\",\"status\":\"PASS\"")
        .append(",\"transport\":")
        .append(jsonString(TRANSPORT))
        .append(",\"type_name\":\"MNIST_DELTA_NETTY_RELAY_RECEIPT\"}")
        .toString();
  }

  private static void appendEntryIds(StringBuilder target, List<Entry> entries) {
    for (int index = 0; index < entries.size(); ++index) {
      if (index != 0) {
        target.append(',');
      }
      target.append(jsonString(entries.get(index).contentId()));
    }
  }

  private static void appendOutputIds(StringBuilder target, List<Output> outputs) {
    for (int index = 0; index < outputs.size(); ++index) {
      if (index != 0) {
        target.append(',');
      }
      target.append(jsonString(outputs.get(index).contentId()));
    }
  }

  private static Path requireManifestPath(Path path) throws IOException {
    require(path.isAbsolute(), "manifest path must be absolute");
    Path normalized = path.normalize();
    require(
        Files.isRegularFile(normalized, LinkOption.NOFOLLOW_LINKS),
        "manifest is not a regular non-symlink file");
    require(!Files.isSymbolicLink(normalized), "manifest must not be a symbolic link");
    return normalized;
  }

  private static Path requireSourcePath(Path path) throws IOException {
    require(path.isAbsolute(), "source path must be absolute");
    Path normalized = path.normalize();
    require(
        Files.isRegularFile(normalized, LinkOption.NOFOLLOW_LINKS),
        "source is not a regular non-symlink file");
    require(!Files.isSymbolicLink(normalized), "source must not be a symbolic link");
    return normalized;
  }

  private static Path requireOutputRoot(Path requested) throws IOException {
    Path normalized = requested.toAbsolutePath().normalize();
    if (Files.exists(normalized, LinkOption.NOFOLLOW_LINKS)) {
      require(!Files.isSymbolicLink(normalized), "output root must not be a symbolic link");
      require(Files.isDirectory(normalized), "output root is not a directory");
    } else {
      Files.createDirectories(normalized);
    }
    Path real = normalized.toRealPath();
    require(Files.isDirectory(real), "output root is not a real directory");
    return real;
  }

  private static String requireDestinationText(String value) {
    require(value.length() <= 512, "destination path is too long");
    require(value.indexOf('\\') < 0, "destination must use forward slashes");
    require(!value.startsWith("/"), "destination must be relative");
    String[] segments = value.split("/", -1);
    require(segments.length > 0, "destination is empty");
    for (String segment : segments) {
      require(
          DESTINATION_SEGMENT.matcher(segment).matches(),
          "destination contains an invalid path segment");
      require(!segment.equals(".") && !segment.equals(".."), "destination traverses directories");
    }
    Path relative = Path.of(value);
    require(!relative.isAbsolute() && relative.getRoot() == null, "destination must be relative");
    require(relative.normalize().equals(relative), "destination is not normalized");
    return value;
  }

  private static Path resolveOutputPath(Path outputRoot, String value, String name) {
    require(!value.isBlank(), name + " path is empty");
    Path requested = Path.of(value);
    Path resolved =
        requested.isAbsolute()
            ? requested.normalize()
            : outputRoot.resolve(requireDestinationText(value)).normalize();
    require(resolved.startsWith(outputRoot), name + " path escapes output root");
    require(!resolved.equals(outputRoot), name + " path names the output root");
    return resolved;
  }

  private static void requireNonConflictingTargets(List<Path> targets) {
    Set<Path> unique = new HashSet<>();
    for (Path target : targets) {
      require(unique.add(target), "duplicate output target");
    }
    for (int left = 0; left < targets.size(); ++left) {
      for (int right = left + 1; right < targets.size(); ++right) {
        Path first = targets.get(left);
        Path second = targets.get(right);
        require(
            !first.startsWith(second) && !second.startsWith(first),
            "one output target is a parent of another");
      }
    }
  }

  private static void prepareNewOutput(Path outputRoot, Path target) throws IOException {
    require(target.startsWith(outputRoot), "output target escapes output root");
    require(!Files.exists(target, LinkOption.NOFOLLOW_LINKS), "output target already exists");
    Path parent = target.getParent();
    require(parent != null && parent.startsWith(outputRoot), "invalid output parent");
    Path relativeParent = outputRoot.relativize(parent);
    Path current = outputRoot;
    for (Path segment : relativeParent) {
      current = current.resolve(segment);
      if (Files.exists(current, LinkOption.NOFOLLOW_LINKS)) {
        require(!Files.isSymbolicLink(current), "output parent contains a symbolic link");
        require(Files.isDirectory(current), "output parent contains a non-directory");
      } else {
        Files.createDirectory(current);
      }
      Path real = current.toRealPath();
      require(real.startsWith(outputRoot), "output parent escapes output root");
    }
  }

  private static void writeAtomicallyNew(Path outputRoot, Path target, byte[] bytes)
      throws IOException {
    require(target.startsWith(outputRoot), "output target escapes output root");
    require(!Files.exists(target, LinkOption.NOFOLLOW_LINKS), "output target already exists");
    Path parent = target.getParent();
    require(parent != null && Files.isDirectory(parent), "output parent is unavailable");
    require(!Files.isSymbolicLink(parent), "output parent became a symbolic link");
    require(parent.toRealPath().startsWith(outputRoot), "output parent escapes output root");
    Path temporary = Files.createTempFile(parent, ".mnist-delta-relay-", ".tmp");
    boolean moved = false;
    try {
      try (FileChannel channel =
          FileChannel.open(
              temporary, StandardOpenOption.WRITE, StandardOpenOption.TRUNCATE_EXISTING)) {
        ByteBuffer buffer = ByteBuffer.wrap(bytes);
        while (buffer.hasRemaining()) {
          channel.write(buffer);
        }
        channel.force(true);
      }
      require(
          !Files.exists(target, LinkOption.NOFOLLOW_LINKS),
          "output target appeared during write");
      try {
        Files.move(temporary, target, StandardCopyOption.ATOMIC_MOVE);
      } catch (AtomicMoveNotSupportedException error) {
        throw new IOException("atomic move is not supported for output target", error);
      }
      moved = true;
    } finally {
      if (!moved) {
        Files.deleteIfExists(temporary);
      }
    }
  }

  private static void verifySignature(String publicKeyBase64, String signatureBase64, byte[] bytes)
      throws GeneralSecurityException {
    byte[] rawPublicKey = decodeCanonicalBase64(publicKeyBase64, "public key");
    byte[] signatureBytes = decodeCanonicalBase64(signatureBase64, "signature");
    require(rawPublicKey.length == 32, "Ed25519 public key must contain 32 raw bytes");
    require(signatureBytes.length == 64, "Ed25519 signature must contain 64 bytes");
    byte[] encodedPublicKey =
        new byte[ED25519_SUBJECT_PUBLIC_KEY_INFO_PREFIX.length + rawPublicKey.length];
    System.arraycopy(
        ED25519_SUBJECT_PUBLIC_KEY_INFO_PREFIX,
        0,
        encodedPublicKey,
        0,
        ED25519_SUBJECT_PUBLIC_KEY_INFO_PREFIX.length);
    System.arraycopy(
        rawPublicKey,
        0,
        encodedPublicKey,
        ED25519_SUBJECT_PUBLIC_KEY_INFO_PREFIX.length,
        rawPublicKey.length);
    PublicKey publicKey =
        KeyFactory.getInstance("Ed25519").generatePublic(new X509EncodedKeySpec(encodedPublicKey));
    Signature verifier = Signature.getInstance("Ed25519");
    verifier.initVerify(publicKey);
    verifier.update(SIGNATURE_DOMAIN);
    verifier.update(bytes);
    require(verifier.verify(signatureBytes), "Ed25519 source signature is invalid");
  }

  private static byte[] decodeCanonicalBase64(String value, String name) {
    byte[] decoded;
    try {
      decoded = Base64.getDecoder().decode(value);
    } catch (IllegalArgumentException error) {
      throw new IllegalArgumentException(name + " is not valid Base64", error);
    }
    require(
        Base64.getEncoder().encodeToString(decoded).equals(value),
        name + " is not canonical Base64");
    return decoded;
  }

  private static String decodeUtf8Strict(byte[] bytes) throws CharacterCodingException {
    return StandardCharsets.UTF_8
        .newDecoder()
        .onMalformedInput(CodingErrorAction.REPORT)
        .onUnmappableCharacter(CodingErrorAction.REPORT)
        .decode(ByteBuffer.wrap(bytes))
        .toString();
  }

  private static String sha256(byte[] bytes) {
    try {
      return "sha256:"
          + HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    } catch (NoSuchAlgorithmException error) {
      throw new IllegalStateException("SHA-256 is unavailable", error);
    }
  }

  private static String jsonString(String value) {
    StringBuilder result = new StringBuilder(value.length() + 2).append('"');
    for (int index = 0; index < value.length(); ++index) {
      char character = value.charAt(index);
      switch (character) {
        case '"' -> result.append("\\\"");
        case '\\' -> result.append("\\\\");
        case '\b' -> result.append("\\b");
        case '\f' -> result.append("\\f");
        case '\n' -> result.append("\\n");
        case '\r' -> result.append("\\r");
        case '\t' -> result.append("\\t");
        default -> {
          if (character < 0x20) {
            result
                .append("\\u00")
                .append(HEX[(character >>> 4) & 0x0f])
                .append(HEX[character & 0x0f]);
          } else {
            result.append(character);
          }
        }
      }
    }
    return result.append('"').toString();
  }

  private static String safeMessage(Throwable error) {
    String message = error.getMessage();
    if (message == null || message.isBlank()) {
      message = error.getClass().getSimpleName();
    }
    return message.replace('\r', ' ').replace('\n', ' ');
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalArgumentException(message);
    }
  }

  private record Entry(
      int index,
      Path source,
      String destinationText,
      Path destination,
      String contentId,
      byte[] bytes) {}

  private record Output(String destinationText, String contentId, long sizeBytes) {}
}
