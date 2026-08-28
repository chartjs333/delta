package io.deltareduce.node.distribution;

import java.io.IOException;
import java.nio.file.Files;
import java.util.List;
import java.util.Map;

/** Service-command facade for publish, seed, fetch, inspect and verify operations. */
public final class SwarmService {
  private final Publisher publisher;
  private final Downloader downloader;
  private final CasStore cas;

  public SwarmService(Publisher publisher, Downloader downloader, CasStore cas) {
    this.publisher = publisher;
    this.downloader = downloader;
    this.cas = cas;
  }

  public Publisher.Publication publish(
      byte[] manifest, byte[] certificate, byte[] payload, boolean forceCopy) throws IOException {
    return publisher.publish(manifest, certificate, payload, forceCopy);
  }

  public PeerPlane.Advertisement seed(
      PeerPlane.PeerService service, String requestId, long leaseEpoch, long expiresAtTick)
      throws IOException {
    return service.advertisement(requestId, leaseEpoch, expiresAtTick);
  }

  public Downloader.FetchResult fetch(
      String projectId,
      String requestId,
      byte[] manifest,
      byte[] certificate,
      List<PeerPlane.Advertisement> snapshot,
      Map<String, PeerPlane.PeerService> services,
      long nowTick,
      long deadlineTick)
      throws IOException {
    return downloader.fetch(
        projectId,
        requestId,
        manifest,
        certificate,
        snapshot,
        services,
        nowTick,
        deadlineTick);
  }

  public Inspection inspect(DistributionModel.Manifest manifest) throws IOException {
    var verified = 0;
    for (var piece : manifest.pieces()) {
      if (cas.hasVerifiedPiece(piece)) {
        ++verified;
      }
    }
    return new Inspection(
        manifest.manifestId(),
        manifest.totalLength(),
        verified,
        manifest.pieces().size(),
        Files.isRegularFile(cas.objectPath(manifest.manifestId())));
  }

  public boolean verify(DistributionModel.Manifest manifest) throws IOException {
    var inspection = inspect(manifest);
    if (inspection.verifiedPieces() != inspection.pieceCount() || !inspection.materialized()) {
      return false;
    }
    var bytes = Files.readAllBytes(cas.objectPath(manifest.manifestId()));
    return bytes.length == manifest.totalLength()
        && DistributionModel.rawSha256(bytes).equals(manifest.payloadSha256());
  }

  public record Inspection(
      String manifestId,
      long totalLength,
      int verifiedPieces,
      int pieceCount,
      boolean materialized) {}
}
