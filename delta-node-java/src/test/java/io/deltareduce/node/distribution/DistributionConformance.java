package io.deltareduce.node.distribution;

import io.netty.buffer.CompositeByteBuf;
import io.netty.buffer.Unpooled;
import io.netty.util.ResourceLeakDetector;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

/** Offline JDK 25/26 acceptance harness for the complete feature-005 data plane. */
public final class DistributionConformance {
  private static final String PROJECT = "deltareduce-pilot-v1";
  private static final Pattern HEX_FIELD =
      Pattern.compile("\"%s\":\\{\"bytes_hex\":\"([0-9a-f]+)\"");

  private DistributionConformance() {}

  public static void main(String[] arguments) throws Exception {
    require(arguments.length == 3, "expected native library, golden fixture and scratch root");
    require(Runtime.version().feature() == 25 || Runtime.version().feature() == 26,
        "distribution requires JDK 25 or 26 compatibility lane");
    ResourceLeakDetector.setLevel(ResourceLeakDetector.Level.PARANOID);
    var fixture = Fixture.load(Path.of(arguments[1]));
    var scratch = Path.of(arguments[2]).toAbsolutePath();
    Files.createDirectories(scratch);
    try (var policy = new NativePolicy(Path.of(arguments[0]))) {
      testFrozenIdentities(fixture);
      testNativeLifetimeAndPolicy(policy, fixture);
      testPublicationCasAndQuota(policy, fixture, scratch.resolve("publication"));
      testThreePeerRepairAndSeedLoss(policy, fixture, scratch.resolve("peer"));
      testRestartBitRotAndIncompleteUnion(policy, fixture, scratch.resolve("restart"));
      testTransportGuards(policy, fixture, scratch.resolve("guards"));
    }
    System.out.println(
        "distribution conformance passed on JDK " + Runtime.version().feature()
            + ": native-policy/CAS/P2P/restart/backpressure");
  }

  private static void testFrozenIdentities(Fixture fixture) {
    var manifest = DistributionModel.parseManifest(fixture.manifest());
    require(
        manifest.manifestId().equals(
            "sha256:d48ff2208becabd6b380503c2de6746dbbe4ec0c450fe67308a9a17d726fc254"),
        "golden object ID drifted");
    var chunks = DistributionModel.chunk(fixture.payload());
    require(chunks.size() == 3 && chunks.get(2).length == 17, "piece boundary drifted");
    var ids = chunks.stream().map(DistributionModel::pieceId).toList();
    require(ids.equals(manifest.pieces().stream().map(DistributionModel.PieceDescriptor::contentId).toList()),
        "piece identities drifted");
    require(DistributionModel.pieceTreeRoot(ids).equals(manifest.pieceTreeRoot()),
        "piece tree root drifted");
  }

  private static void testNativeLifetimeAndPolicy(NativePolicy policy, Fixture fixture) {
    var directManifest = Unpooled.directBuffer(fixture.manifest().length).writeBytes(fixture.manifest());
    var directCertificate =
        Unpooled.directBuffer(fixture.certificate().length).writeBytes(fixture.certificate());
    var direct = policy.evaluate(directManifest, directCertificate, false, false);
    require(direct.accepted() && direct.borrowedDirect(), "direct native path was not used");
    require(directManifest.refCnt() == 1 && directCertificate.refCnt() == 1,
        "native call changed caller reference ownership");
    directCertificate.release();
    directManifest.release();

    var heapManifest = Unpooled.wrappedBuffer(fixture.manifest());
    var heapCertificate = Unpooled.wrappedBuffer(fixture.certificate());
    var copied = policy.evaluate(heapManifest, heapCertificate, false, false);
    require(copied.accepted() && !copied.borrowedDirect(), "heap fallback did not use copy path");
    require(copied.canonicalEffect().equals(direct.canonicalEffect()), "direct/copy effects differ");
    heapCertificate.release();
    heapManifest.release();

    CompositeByteBuf composite = Unpooled.compositeBuffer();
    var split = fixture.manifest().length / 2;
    composite.addComponents(
        true,
        Unpooled.wrappedBuffer(Arrays.copyOfRange(fixture.manifest(), 0, split)),
        Unpooled.wrappedBuffer(Arrays.copyOfRange(fixture.manifest(), split, fixture.manifest().length)));
    var compositeCertificate = Unpooled.wrappedBuffer(fixture.certificate());
    var compositeDecision = policy.evaluate(composite, compositeCertificate, false, false);
    require(compositeDecision.accepted() && !compositeDecision.borrowedDirect(),
        "composite fallback did not use bounded copy path");
    compositeCertificate.release();
    composite.release();

    var currentManifest = Unpooled.wrappedBuffer(fixture.manifest());
    var currentCertificate = Unpooled.wrappedBuffer(fixture.certificate());
    var current = policy.evaluate(currentManifest, currentCertificate, true, true);
    require(!current.accepted() && current.code().equals("CURRENT_REQUIRES_APPLY_QC"),
        "aggregate object was treated as current");
    currentCertificate.release();
    currentManifest.release();

    var forbiddenBytes =
        new String(fixture.manifest(), StandardCharsets.US_ASCII)
            .replace(
                "application/vnd.deltareduce.aggregate-bundle;version=1",
                "application/vnd.deltareduce.worker-q-shard;version=1")
            .getBytes(StandardCharsets.US_ASCII);
    var forbiddenManifest = Unpooled.wrappedBuffer(forbiddenBytes);
    var forbiddenCertificate = Unpooled.wrappedBuffer(fixture.certificate());
    var forbidden = policy.evaluate(forbiddenManifest, forbiddenCertificate, false, true);
    require(!forbidden.accepted() && forbidden.code().equals("MEDIA_FORBIDDEN"),
        "forbidden worker-local media escaped native policy");
    forbiddenCertificate.release();
    forbiddenManifest.release();
  }

  private static void testPublicationCasAndQuota(
      NativePolicy policy, Fixture fixture, Path root) throws Exception {
    var telemetry = new Telemetry();
    var cas = new CasStore(root.resolve("cas"), 32L * 1024 * 1024);
    var publisher = new Publisher(policy, cas, telemetry);
    var first = publisher.publish(fixture.manifest(), fixture.certificate(), fixture.payload(), false);
    var second = publisher.publish(fixture.manifest(), fixture.certificate(), fixture.payload(), true);
    require(first.manifest().manifestId().equals(second.manifest().manifestId()),
        "idempotent publication changed identity");
    require(first.objectPath().equals(second.objectPath()), "idempotent publication changed CAS path");
    require(Arrays.equals(Files.readAllBytes(first.objectPath()), fixture.payload()),
        "published object bytes changed");
    var service = new SwarmService(publisher, new Downloader(policy, cas, telemetry, 8), cas);
    require(service.inspect(first.manifest()).verifiedPieces() == 3, "inspect lost verified pieces");
    require(service.verify(first.manifest()), "verify command rejected valid object");
    require(telemetry.snapshot().containsKey("source.bytes"), "source byte telemetry is missing");

    var quotaCas = new CasStore(root.resolve("quota"), 16);
    var quotaPublisher = new Publisher(policy, quotaCas, new Telemetry());
    expectFailure(
        "CAS_QUOTA_EXCEEDED",
        () -> quotaPublisher.publish(
            fixture.manifest(), fixture.certificate(), fixture.payload(), false));
    expectFailure("request ID", () -> quotaCas.journalPath("../escape"));

    var target = root.resolve("symlink-target");
    Files.createDirectories(target);
    var link = root.resolve("symlink-cas");
    try {
      Files.createSymbolicLink(link, target);
      expectFailure("symbolic link", () -> new CasStore(link, 1024));
    } catch (UnsupportedOperationException | SecurityException | java.nio.file.FileSystemException error) {
      // The path traversal assertion above remains mandatory on platforms without symlink privilege.
    }
  }

  private static void testThreePeerRepairAndSeedLoss(
      NativePolicy policy, Fixture fixture, Path root) throws Exception {
    var manifest = DistributionModel.parseManifest(fixture.manifest());
    var chunks = DistributionModel.chunk(fixture.payload());
    var registry = new PeerPlane.DiscoveryRegistry(Set.of("peer-a", "peer-b", "peer-c"));
    var services = new HashMap<String, PeerPlane.PeerService>();
    var advertisements = new ArrayList<PeerPlane.Advertisement>();
    for (var index = 0; index < 3; ++index) {
      var peerId = "peer-" + (char) ('a' + index);
      var cas = new CasStore(root.resolve(peerId), 16L * 1024 * 1024);
      for (var pieceIndex = 0; pieceIndex < chunks.size(); ++pieceIndex) {
        cas.putPiece(manifest.pieces().get(pieceIndex), chunks.get(pieceIndex));
      }
      var fault = index == 0 ? PeerPlane.Fault.CORRUPT : index == 1 ? PeerPlane.Fault.SLOW : PeerPlane.Fault.NONE;
      var faultOrdinal = index == 0 ? 0 : 1;
      var service =
          new PeerPlane.PeerService(
              PROJECT, peerId, manifest, cas, new Telemetry(), 2, fault, faultOrdinal);
      services.put(peerId, service);
      var advertisement = service.advertisement("advertise-" + index, 1, 200);
      registry.publish(advertisement, 1);
      advertisements.add(advertisement);
    }
    var snapshot = registry.snapshot(PROJECT, manifest.manifestId(), 2);
    registry.setAvailable(false);
    var request = requestFavoringFaults(snapshot);
    var destination = new CasStore(root.resolve("destination"), 16L * 1024 * 1024);
    var telemetry = new Telemetry();
    var downloader = new Downloader(policy, destination, telemetry, 8);
    var result =
        downloader.fetch(
            PROJECT, request, fixture.manifest(), fixture.certificate(), snapshot, services, 2, 100);
    require(Arrays.equals(Files.readAllBytes(result.objectPath()), fixture.payload()),
        "three-peer reconstruction changed bytes");
    require(result.attemptCount() >= 3, "fault retries were not journaled");
    require(telemetry.snapshot().getOrDefault("retries", 0L) > 0, "retry telemetry is missing");

    // Initial publisher disappears; the remaining verified union still covers every piece.
    var unionServices = new HashMap<String, PeerPlane.PeerService>();
    var unionAds = new ArrayList<PeerPlane.Advertisement>();
    for (var index = 0; index < 2; ++index) {
      var peerId = "union-" + index;
      var cas = new CasStore(root.resolve(peerId), 16L * 1024 * 1024);
      for (var pieceIndex = 0; pieceIndex < chunks.size(); ++pieceIndex) {
        if ((index == 0 && pieceIndex < 2) || (index == 1 && pieceIndex == 2)) {
          cas.putPiece(manifest.pieces().get(pieceIndex), chunks.get(pieceIndex));
        }
      }
      var service = new PeerPlane.PeerService(
          PROJECT, peerId, manifest, cas, new Telemetry(), 2, PeerPlane.Fault.NONE, -1);
      unionServices.put(peerId, service);
      unionAds.add(service.advertisement("union-ad-" + index, 1, 200));
    }
    var unionDestination = new CasStore(root.resolve("union-destination"), 16L * 1024 * 1024);
    var unionResult = new Downloader(policy, unionDestination, new Telemetry(), 8)
        .fetch(PROJECT, "seed-loss", fixture.manifest(), fixture.certificate(), unionAds,
            unionServices, 2, 100);
    require(Arrays.equals(Files.readAllBytes(unionResult.objectPath()), fixture.payload()),
        "remaining peer union did not reconstruct object");
  }

  private static void testRestartBitRotAndIncompleteUnion(
      NativePolicy policy, Fixture fixture, Path root) throws Exception {
    var manifest = DistributionModel.parseManifest(fixture.manifest());
    var chunks = DistributionModel.chunk(fixture.payload());
    var partialCas = new CasStore(root.resolve("partial-peer"), 16L * 1024 * 1024);
    partialCas.putPiece(manifest.pieces().get(0), chunks.get(0));
    partialCas.putPiece(manifest.pieces().get(1), chunks.get(1));
    var partial = new PeerPlane.PeerService(
        PROJECT, "partial", manifest, partialCas, new Telemetry(), 2, PeerPlane.Fault.NONE, -1);
    var ads = new ArrayList<PeerPlane.Advertisement>();
    ads.add(partial.advertisement("partial-ad", 1, 200));
    var services = new HashMap<String, PeerPlane.PeerService>();
    services.put("partial", partial);
    var destination = new CasStore(root.resolve("destination"), 16L * 1024 * 1024);
    var downloader = new Downloader(policy, destination, new Telemetry(), 8);
    Downloader.PieceUnavailableException unavailable = null;
    try {
      downloader.fetch(PROJECT, "restart", fixture.manifest(), fixture.certificate(), ads, services, 2, 100);
    } catch (Downloader.PieceUnavailableException error) {
      unavailable = error;
    }
    require(unavailable != null && unavailable.ordinal() == 2 && Files.exists(unavailable.journal()),
        "incomplete union did not preserve resumable PIECE_UNAVAILABLE journal");

    var repairCas = new CasStore(root.resolve("repair-peer"), 16L * 1024 * 1024);
    for (var index = 0; index < chunks.size(); ++index) {
      repairCas.putPiece(manifest.pieces().get(index), chunks.get(index));
    }
    var repair = new PeerPlane.PeerService(
        PROJECT, "repair", manifest, repairCas, new Telemetry(), 2, PeerPlane.Fault.NONE, -1);
    ads.add(repair.advertisement("repair-ad", 1, 200));
    services.put("repair", repair);
    var repaired = downloader.fetch(
        PROJECT, "restart", fixture.manifest(), fixture.certificate(), ads, services, 2, 100);
    require(Arrays.equals(Files.readAllBytes(repaired.objectPath()), fixture.payload()),
        "restart did not complete exact object");

    // Flip a verified local piece. A fresh request must detect and repair it before materialization.
    var first = manifest.pieces().get(0);
    var piecePath = destination.root().resolve("pieces").resolve(first.contentId().substring(7));
    var corrupt = Files.readAllBytes(piecePath);
    corrupt[0] ^= 1;
    Files.write(piecePath, corrupt, StandardOpenOption.TRUNCATE_EXISTING);
    var bitRotResult = downloader.fetch(
        PROJECT, "bit-rot", fixture.manifest(), fixture.certificate(), ads, services, 2, 100);
    require(destination.hasVerifiedPiece(first), "bit rot was not repaired");
    require(Arrays.equals(Files.readAllBytes(bitRotResult.objectPath()), fixture.payload()),
        "bit-rot repair changed object");
  }

  private static void testTransportGuards(
      NativePolicy policy, Fixture fixture, Path root) throws Exception {
    var manifest = DistributionModel.parseManifest(fixture.manifest());
    var chunks = DistributionModel.chunk(fixture.payload());
    var cas = new CasStore(root.resolve("peer"), 16L * 1024 * 1024);
    cas.putPiece(manifest.pieces().get(2), chunks.get(2));
    var service = new PeerPlane.PeerService(
        PROJECT, "guard", manifest, cas, new Telemetry(), 1, PeerPlane.Fault.NONE, -1);
    var envelope = new PeerPlane.TransportEnvelope(
        PROJECT, manifest.manifestId(), 2, 17, "guard-fetch", "permission:guard", 10);
    var cancelled = new PeerPlane.Cancellation();
    cancelled.cancel();
    expectFailure("CANCELLED", () -> service.fetch(envelope, 1, cancelled));
    expectFailure(
        "TRANSPORT_PAYLOAD_TOO_LARGE",
        () -> new PeerPlane.TransportEnvelope(
            PROJECT, manifest.manifestId(), 2, DistributionModel.MAX_PIECE_BYTES + 1,
            "oversize", "permission:guard", 10));
    var priorName = Thread.currentThread().getName();
    try {
      Thread.currentThread().setName("netty-eventloop-test");
      expectFailure(
          "EVENT_LOOP_BLOCKING_GUARD",
          () -> service.fetch(envelope, 1, new PeerPlane.Cancellation()));
    } finally {
      Thread.currentThread().setName(priorName);
    }

    // Discovery snapshots are hints: replay and stale epochs fail, trusted manifest remains unchanged.
    var registry = new PeerPlane.DiscoveryRegistry(Set.of("guard"));
    var advertisement = service.advertisement("guard-ad", 2, 20);
    registry.publish(advertisement, 1);
    expectFailure("ADVERTISEMENT_REPLAY", () -> registry.publish(advertisement, 1));
    expectFailure(
        "LEASE_EPOCH_REPLAY",
        () -> registry.publish(service.advertisement("guard-ad-2", 1, 20), 1));

    // Validate native policy is still required even when transport state is locally available.
    var invalid = fixture.manifest().clone();
    invalid[1] = (byte) ' ';
    var invalidManifest = Unpooled.wrappedBuffer(invalid);
    var certificate = Unpooled.wrappedBuffer(fixture.certificate());
    var decision = policy.evaluate(invalidManifest, certificate, false, true);
    require(!decision.accepted() && decision.code().equals("CANONICAL_JSON_INVALID"),
        "transport path bypassed canonical native parser");
    certificate.release();
    invalidManifest.release();
  }

  private static String requestFavoringFaults(List<PeerPlane.Advertisement> snapshot) {
    for (var candidate = 0; candidate < 100_000; ++candidate) {
      var request = "faults-" + candidate;
      var first0 = orderedPeers(snapshot, request, 0).get(0);
      var first1 = orderedPeers(snapshot, request, 1).get(0);
      if (first0.equals("peer-a") && first1.equals("peer-b")) {
        return request;
      }
    }
    throw new IllegalStateException("could not derive deterministic fault schedule");
  }

  private static List<String> orderedPeers(
      List<PeerPlane.Advertisement> snapshot, String request, int ordinal) {
    return snapshot.stream()
        .map(PeerPlane.Advertisement::peerId)
        .sorted(Comparator.comparing(peer -> scheduleKey(request, ordinal, peer)))
        .toList();
  }

  private static String scheduleKey(String request, int ordinal, String peer) {
    try {
      var digest = java.security.MessageDigest.getInstance("SHA-256");
      return HexFormat.of().formatHex(
          digest.digest((request + ":" + ordinal + ":" + peer).getBytes(StandardCharsets.US_ASCII)));
    } catch (java.security.NoSuchAlgorithmException error) {
      throw new IllegalStateException(error);
    }
  }

  private static void expectFailure(String message, ThrowingOperation operation) throws Exception {
    try {
      operation.run();
    } catch (Exception error) {
      if (String.valueOf(error.getMessage()).contains(message)) {
        return;
      }
      throw error;
    }
    throw new IllegalStateException("expected failure containing " + message);
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalStateException(message);
    }
  }

  @FunctionalInterface
  private interface ThrowingOperation {
    void run() throws Exception;
  }

  private record Fixture(byte[] manifest, byte[] certificate, byte[] payload) {
    private static Fixture load(Path path) throws IOException {
      var document = Files.readString(path, StandardCharsets.US_ASCII);
      var manifest = extractHex(document, "manifest");
      var certificate = extractHex(document, "certificate");
      var lengthMatcher = Pattern.compile("\"source\":\\{\"length\":([0-9]+),\"pattern\":\"COUNTER_MOD_251\"\\}")
          .matcher(document);
      require(lengthMatcher.find(), "golden source descriptor is missing");
      var length = Integer.parseInt(lengthMatcher.group(1));
      require(!lengthMatcher.find(), "golden source descriptor is duplicated");
      var payload = new byte[length];
      for (var index = 0; index < length; ++index) {
        payload[index] = (byte) (index % 251);
      }
      return new Fixture(manifest, certificate, payload);
    }

    private static byte[] extractHex(String document, String field) {
      var matcher = Pattern.compile(String.format(HEX_FIELD.pattern(), field)).matcher(document);
      require(matcher.find(), field + " bytes are missing");
      var value = matcher.group(1);
      require(!matcher.find(), field + " bytes are duplicated");
      return HexFormat.of().parseHex(value);
    }

    @Override
    public byte[] manifest() {
      return manifest.clone();
    }

    @Override
    public byte[] certificate() {
      return certificate.clone();
    }

    @Override
    public byte[] payload() {
      return payload.clone();
    }
  }
}
