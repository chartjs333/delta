package io.deltareduce.node.distribution;

import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;

/** Deterministic bounded multi-peer downloader with exact piece repair and restart state. */
public final class Downloader {
  private final NativePolicy nativePolicy;
  private final CasStore cas;
  private final Telemetry telemetry;
  private final int maxPeerRetries;

  public Downloader(NativePolicy nativePolicy, CasStore cas, Telemetry telemetry, int maxPeerRetries) {
    DistributionModel.require(maxPeerRetries > 0 && maxPeerRetries <= 64,
        "peer retry bound is outside limits");
    this.nativePolicy = nativePolicy;
    this.cas = cas;
    this.telemetry = telemetry;
    this.maxPeerRetries = maxPeerRetries;
  }

  public FetchResult fetch(
      String projectId,
      String requestId,
      byte[] canonicalManifest,
      byte[] canonicalCertificate,
      List<PeerPlane.Advertisement> snapshot,
      Map<String, PeerPlane.PeerService> services,
      long nowTick,
      long deadlineTick)
      throws IOException {
    var decision = evaluate(canonicalManifest, canonicalCertificate, false);
    if (!decision.accepted()) {
      telemetry.increment("certification.failures." + decision.code().toLowerCase());
      throw new Publisher.PolicyRejectedException(decision.code());
    }
    var manifest = DistributionModel.parseManifest(canonicalManifest);
    DistributionModel.require(decision.manifestId().equals(manifest.manifestId()),
        "native/Java manifest ID mismatch");
    var journal = DownloadJournal.open(cas.journalPath(requestId), manifest.manifestId());
    var verified = new HashMap<>(journal.reverify(manifest, cas));
    var cancellation = new PeerPlane.Cancellation();
    var attempts = 0;

    for (var descriptor : manifest.pieces()) {
      if (verified.containsKey(descriptor.ordinal())) {
        continue;
      }
      var candidates = new ArrayList<PeerPlane.Advertisement>();
      for (var advertisement : snapshot) {
        if (advertisement.projectId().equals(projectId)
            && advertisement.manifestId().equals(manifest.manifestId())
            && advertisement.leaseExpiresAtTick() > nowTick
            && advertisement.availableOrdinals().contains(descriptor.ordinal())
            && services.containsKey(advertisement.peerId())) {
          candidates.add(advertisement);
        }
      }
      candidates.sort(
          Comparator.comparing(
                  (PeerPlane.Advertisement item) ->
                      scheduleKey(requestId, descriptor.ordinal(), item.peerId()))
              .thenComparing(PeerPlane.Advertisement::peerId));
      var completed = false;
      for (var candidate : candidates) {
        if (attempts >= maxPeerRetries * Math.max(1, manifest.pieces().size())) {
          break;
        }
        ++attempts;
        var service = services.get(candidate.peerId());
        var envelope =
            new PeerPlane.TransportEnvelope(
                projectId,
                manifest.manifestId(),
                descriptor.ordinal(),
                descriptor.length(),
                requestId + "-piece-" + descriptor.ordinal(),
                "permission:" + candidate.peerId(),
                deadlineTick);
        ByteBuf response = null;
        try {
          response = service.fetch(envelope, nowTick, cancellation);
          if (response.readableBytes() != descriptor.length()) {
            telemetry.add("corrupt.bytes", response.readableBytes());
            telemetry.increment("retries");
            journal.recordAttempt(descriptor.ordinal(), candidate.peerId(), "WRONG_LENGTH");
            continue;
          }
          var bytes = new byte[response.readableBytes()];
          response.getBytes(response.readerIndex(), bytes);
          if (!DistributionModel.pieceId(bytes).equals(descriptor.contentId())) {
            telemetry.add("corrupt.bytes", bytes.length);
            telemetry.increment("retries");
            journal.recordAttempt(descriptor.ordinal(), candidate.peerId(), "CORRUPT");
            continue;
          }
          cas.putPiece(descriptor, bytes);
          journal.markVerified(descriptor);
          journal.recordAttempt(descriptor.ordinal(), candidate.peerId(), "VERIFIED");
          telemetry.add("peer.bytes", bytes.length);
          verified.put(descriptor.ordinal(), descriptor.contentId());
          completed = true;
          break;
        } catch (IllegalArgumentException error) {
          telemetry.increment("retries");
          journal.recordAttempt(descriptor.ordinal(), candidate.peerId(), "REJECTED");
        } finally {
          if (response != null) {
            response.release();
          }
        }
      }
      if (!completed) {
        telemetry.increment("piece.unavailable");
        throw new PieceUnavailableException(descriptor.ordinal(), journal.pathForEvidence());
      }
    }

    // Revalidate policy and every local piece before final atomic visibility.
    var finalDecision = evaluate(canonicalManifest, canonicalCertificate, true);
    if (!finalDecision.accepted()) {
      throw new Publisher.PolicyRejectedException(finalDecision.code());
    }
    for (var descriptor : manifest.pieces()) {
      DistributionModel.require(cas.hasVerifiedPiece(descriptor), "verified piece changed before commit");
    }
    cas.putManifest(manifest);
    var object = cas.materialize(manifest);
    telemetry.increment("fetch.completed");
    return new FetchResult(manifest, object, journal.attemptCount());
  }

  private NativePolicy.NativeDecision evaluate(
      byte[] manifest, byte[] certificate, boolean forceCopy) {
    var manifestBuffer =
        forceCopy
            ? Unpooled.wrappedBuffer(manifest)
            : Unpooled.directBuffer(manifest.length).writeBytes(manifest);
    var certificateBuffer =
        forceCopy
            ? Unpooled.wrappedBuffer(certificate)
            : Unpooled.directBuffer(certificate.length).writeBytes(certificate);
    try {
      return nativePolicy.evaluate(manifestBuffer, certificateBuffer, false, forceCopy);
    } finally {
      certificateBuffer.release();
      manifestBuffer.release();
    }
  }

  private static String scheduleKey(String requestId, int ordinal, String peerId) {
    try {
      var digest = MessageDigest.getInstance("SHA-256");
      var input = (requestId + ":" + ordinal + ":" + peerId).getBytes(StandardCharsets.US_ASCII);
      return HexFormat.of().formatHex(digest.digest(input));
    } catch (java.security.NoSuchAlgorithmException error) {
      throw new IllegalStateException(error);
    }
  }

  public record FetchResult(
      DistributionModel.Manifest manifest, Path objectPath, int attemptCount) {}

  public static final class PieceUnavailableException extends IOException {
    private static final long serialVersionUID = 1L;
    private final int ordinal;
    private final transient Path journal;

    public PieceUnavailableException(int ordinal, Path journal) {
      super("PIECE_UNAVAILABLE: " + ordinal);
      this.ordinal = ordinal;
      this.journal = journal;
    }

    public int ordinal() {
      return ordinal;
    }

    public Path journal() {
      return journal;
    }
  }
}
