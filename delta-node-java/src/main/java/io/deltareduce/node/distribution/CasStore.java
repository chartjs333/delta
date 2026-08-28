package io.deltareduce.node.distribution;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;

/** Path-safe immutable piece/manifest/object CAS with atomic visibility. */
public final class CasStore {
  private final Path root;
  private final long quotaBytes;
  private long accountedBytes;

  public CasStore(Path requestedRoot, long quotaBytes) throws IOException {
    DistributionModel.require(quotaBytes >= 0, "CAS quota is negative");
    var absolute = requestedRoot.toAbsolutePath().normalize();
    Files.createDirectories(absolute);
    DistributionModel.require(!Files.isSymbolicLink(absolute), "CAS root is a symbolic link");
    var real = absolute.toRealPath();
    DistributionModel.require(real.equals(absolute), "CAS root traverses a symbolic link");
    root = real;
    this.quotaBytes = quotaBytes;
    for (var directory : List.of("pieces", "manifests", "objects", "journals")) {
      var child = root.resolve(directory);
      Files.createDirectories(child);
      DistributionModel.require(!Files.isSymbolicLink(child), "CAS child is a symbolic link");
    }
    try (var paths = Files.walk(root)) {
      accountedBytes =
          paths.filter(path -> Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS))
              .mapToLong(
                  path -> {
                    try {
                      return Files.size(path);
                    } catch (IOException error) {
                      throw new java.io.UncheckedIOException(error);
                    }
                  })
              .sum();
    } catch (java.io.UncheckedIOException error) {
      throw error.getCause();
    }
    DistributionModel.require(accountedBytes <= quotaBytes, "existing CAS exceeds quota");
  }

  public synchronized Path putPiece(DistributionModel.PieceDescriptor descriptor, byte[] bytes)
      throws IOException {
    DistributionModel.require(bytes.length == descriptor.length(), "piece length mismatch");
    DistributionModel.require(
        DistributionModel.pieceId(bytes).equals(descriptor.contentId()), "piece hash mismatch");
    var target = pathFor("pieces", descriptor.contentId());
    if (Files.exists(target, LinkOption.NOFOLLOW_LINKS)
        && !Files.isSymbolicLink(target)
        && !Arrays.equals(Files.readAllBytes(target), bytes)) {
      return repairCorruptPiece(target, bytes);
    }
    return writeImmutable("pieces", descriptor.contentId(), bytes);
  }

  public synchronized Path putManifest(DistributionModel.Manifest manifest) throws IOException {
    DistributionModel.require(
        DistributionModel.domainId(
                "deltareduce.005.object-manifest.v1", manifest.canonicalBytes())
            .equals(manifest.manifestId()),
        "manifest identity mismatch");
    return writeImmutable("manifests", manifest.manifestId(), manifest.canonicalBytes());
  }

  public synchronized boolean hasVerifiedPiece(DistributionModel.PieceDescriptor descriptor)
      throws IOException {
    var path = pathFor("pieces", descriptor.contentId());
    if (!Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(path)) {
      return false;
    }
    var bytes = Files.readAllBytes(path);
    return bytes.length == descriptor.length()
        && DistributionModel.pieceId(bytes).equals(descriptor.contentId());
  }

  public synchronized byte[] readVerifiedPiece(DistributionModel.PieceDescriptor descriptor)
      throws IOException {
    DistributionModel.require(hasVerifiedPiece(descriptor), "piece is absent or corrupt");
    return Files.readAllBytes(pathFor("pieces", descriptor.contentId()));
  }

  public synchronized Path materialize(DistributionModel.Manifest manifest) throws IOException {
    var target = pathFor("objects", manifest.manifestId());
    if (Files.exists(target, LinkOption.NOFOLLOW_LINKS)) {
      DistributionModel.require(
          !Files.isSymbolicLink(target)
              && Files.size(target) == manifest.totalLength()
              && DistributionModel.rawSha256(Files.readAllBytes(target)).equals(manifest.payloadSha256()),
          "existing materialized object conflicts with manifest");
      return target;
    }
    reserve(manifest.totalLength());
    var temporary = temporarySibling(target);
    var committed = false;
    try (var channel =
        FileChannel.open(temporary, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
      for (var descriptor : manifest.pieces()) {
        var piece = readVerifiedPiece(descriptor);
        var buffer = ByteBuffer.wrap(piece);
        while (buffer.hasRemaining()) {
          channel.write(buffer);
        }
      }
      channel.force(true);
      DistributionModel.require(
          Files.size(temporary) == manifest.totalLength(), "materialized length mismatch");
      DistributionModel.require(
          DistributionModel.rawSha256(Files.readAllBytes(temporary)).equals(manifest.payloadSha256()),
          "materialized payload hash mismatch");
      Files.move(temporary, target, StandardCopyOption.ATOMIC_MOVE);
      committed = true;
      accountedBytes += manifest.totalLength();
      return target;
    } finally {
      if (!committed) {
        Files.deleteIfExists(temporary);
      }
    }
  }

  public Path journalPath(String requestId) {
    DistributionModel.require(
        requestId != null && requestId.matches("[a-zA-Z0-9._-]{1,128}"),
        "request ID is not a safe token");
    return root.resolve("journals").resolve(requestId + ".journal");
  }

  public Path objectPath(String manifestId) {
    return pathFor("objects", manifestId);
  }

  public Path root() {
    return root;
  }

  private Path writeImmutable(String kind, String contentId, byte[] bytes) throws IOException {
    var target = pathFor(kind, contentId);
    if (Files.exists(target, LinkOption.NOFOLLOW_LINKS)) {
      DistributionModel.require(
          !Files.isSymbolicLink(target) && Arrays.equals(Files.readAllBytes(target), bytes),
          "immutable CAS collision");
      return target;
    }
    reserve(bytes.length);
    var temporary = temporarySibling(target);
    var committed = false;
    try (var channel =
        FileChannel.open(temporary, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
      var buffer = ByteBuffer.wrap(bytes);
      while (buffer.hasRemaining()) {
        channel.write(buffer);
      }
      channel.force(true);
      Files.move(temporary, target, StandardCopyOption.ATOMIC_MOVE);
      committed = true;
      accountedBytes += bytes.length;
      return target;
    } finally {
      if (!committed) {
        Files.deleteIfExists(temporary);
      }
    }
  }

  private Path repairCorruptPiece(Path target, byte[] verifiedBytes) throws IOException {
    var priorLength = Files.size(target);
    reserve(Math.max(0L, verifiedBytes.length - priorLength));
    var temporary = temporarySibling(target);
    var committed = false;
    try (var channel =
        FileChannel.open(temporary, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
      var buffer = ByteBuffer.wrap(verifiedBytes);
      while (buffer.hasRemaining()) {
        channel.write(buffer);
      }
      channel.force(true);
      Files.move(
          temporary,
          target,
          StandardCopyOption.ATOMIC_MOVE,
          StandardCopyOption.REPLACE_EXISTING);
      committed = true;
      accountedBytes += verifiedBytes.length - priorLength;
      return target;
    } finally {
      if (!committed) {
        Files.deleteIfExists(temporary);
      }
    }
  }

  private void reserve(long bytes) {
    DistributionModel.require(
        bytes >= 0 && accountedBytes <= quotaBytes - bytes, "CAS_QUOTA_EXCEEDED");
  }

  private Path pathFor(String kind, String contentId) {
    DistributionModel.requireContentId(contentId, "CAS content ID");
    var path = root.resolve(kind).resolve(contentId.substring(7)).normalize();
    DistributionModel.require(path.startsWith(root.resolve(kind)), "CAS path escaped root");
    return path;
  }

  private static Path temporarySibling(Path target) {
    return target.resolveSibling(target.getFileName() + ".tmp-" + UUID.randomUUID());
  }
}
