package io.deltareduce.node.distribution;

import io.netty.buffer.Unpooled;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;

/** Native-authorized deterministic publication into the immutable CAS. */
public final class Publisher {
  private final NativePolicy nativePolicy;
  private final CasStore cas;
  private final Telemetry telemetry;

  public Publisher(NativePolicy nativePolicy, CasStore cas, Telemetry telemetry) {
    this.nativePolicy = nativePolicy;
    this.cas = cas;
    this.telemetry = telemetry;
  }

  public Publication publish(
      byte[] canonicalManifest,
      byte[] canonicalCertificate,
      byte[] payload,
      boolean forceCopy)
      throws IOException {
    var manifestBuffer =
        forceCopy
            ? Unpooled.wrappedBuffer(canonicalManifest)
            : Unpooled.directBuffer(canonicalManifest.length).writeBytes(canonicalManifest);
    var certificateBuffer =
        forceCopy
            ? Unpooled.wrappedBuffer(canonicalCertificate)
            : Unpooled.directBuffer(canonicalCertificate.length).writeBytes(canonicalCertificate);
    NativePolicy.NativeDecision decision;
    try {
      decision = nativePolicy.evaluate(manifestBuffer, certificateBuffer, false, forceCopy);
    } finally {
      certificateBuffer.release();
      manifestBuffer.release();
    }
    if (!decision.accepted()) {
      telemetry.increment("certification.failures." + decision.code().toLowerCase());
      throw new PolicyRejectedException(decision.code());
    }

    // Parsing, chunking and all writes occur only after an unforgeable native ACCEPT decision.
    var manifest = DistributionModel.parseManifest(canonicalManifest);
    DistributionModel.require(
        decision.manifestId().equals(manifest.manifestId()), "native/Java manifest ID mismatch");
    DistributionModel.require(payload.length == manifest.totalLength(), "payload length mismatch");
    DistributionModel.require(
        DistributionModel.rawSha256(payload).equals(manifest.payloadSha256()),
        "payload SHA-256 mismatch");
    var chunks = DistributionModel.chunk(payload);
    DistributionModel.require(chunks.size() == manifest.pieces().size(), "piece count mismatch");
    var pieceIds = new ArrayList<String>();
    for (var index = 0; index < chunks.size(); ++index) {
      var descriptor = manifest.pieces().get(index);
      var piece = chunks.get(index);
      DistributionModel.require(piece.length == descriptor.length(), "piece length drift");
      var pieceId = DistributionModel.pieceId(piece);
      DistributionModel.require(pieceId.equals(descriptor.contentId()), "piece identity drift");
      pieceIds.add(pieceId);
      cas.putPiece(descriptor, piece);
    }
    DistributionModel.require(
        DistributionModel.pieceTreeRoot(pieceIds).equals(manifest.pieceTreeRoot()),
        "piece tree root drift");
    var manifestPath = cas.putManifest(manifest);
    var objectPath = cas.materialize(manifest);
    telemetry.add("source.bytes", payload.length);
    telemetry.increment("publication.completed");
    return new Publication(manifest, manifestPath, objectPath, decision.canonicalEffect());
  }

  public record Publication(
      DistributionModel.Manifest manifest,
      Path manifestPath,
      Path objectPath,
      String nativeEffect) {}

  public static final class PolicyRejectedException extends IllegalArgumentException {
    private static final long serialVersionUID = 1L;
    private final String code;

    public PolicyRejectedException(String code) {
      super("native certification rejected publication: " + code);
      this.code = code;
    }

    public String code() {
      return code;
    }
  }
}
