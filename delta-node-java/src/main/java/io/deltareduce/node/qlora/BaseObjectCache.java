package io.deltareduce.node.qlora;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.Arrays;
import java.util.UUID;

/** Content-addressed immutable base/tokenizer/profile cache. */
public final class BaseObjectCache {
  private final Path root;
  private final long quotaBytes;
  private long accountedBytes;

  public BaseObjectCache(Path requestedRoot, long quotaBytes) throws IOException {
    QloraContracts.require(quotaBytes >= 0, "cache quota is negative");
    var absolute = requestedRoot.toAbsolutePath().normalize();
    Files.createDirectories(absolute);
    QloraContracts.require(!Files.isSymbolicLink(absolute), "cache root is a symbolic link");
    root = absolute.toRealPath();
    QloraContracts.require(root.equals(absolute), "cache root traverses a symbolic link");
    this.quotaBytes = quotaBytes;
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
    QloraContracts.require(accountedBytes <= quotaBytes, "existing cache exceeds quota");
  }

  public synchronized boolean contains(String objectId) throws IOException {
    var target = pathFor(objectId);
    return Files.isRegularFile(target, LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(target);
  }

  public synchronized CacheResult put(BaseArtifact artifact) throws IOException {
    artifact.validate();
    var target = pathFor(artifact.objectId());
    if (Files.exists(target, LinkOption.NOFOLLOW_LINKS)) {
      QloraContracts.require(
          !Files.isSymbolicLink(target) && Arrays.equals(Files.readAllBytes(target), artifact.bytes()),
          "immutable base cache collision");
      return new CacheResult(target, 0L, true);
    }
    QloraContracts.require(
        accountedBytes <= quotaBytes - artifact.bytes().length, "BASE_CACHE_QUOTA_EXCEEDED");
    var temporary = target.resolveSibling(target.getFileName() + ".tmp-" + UUID.randomUUID());
    Files.write(temporary, artifact.bytes());
    try {
      Files.move(temporary, target, StandardCopyOption.ATOMIC_MOVE);
    } catch (java.nio.file.AtomicMoveNotSupportedException ignored) {
      Files.move(temporary, target);
    }
    accountedBytes += artifact.bytes().length;
    return new CacheResult(target, artifact.bytes().length, false);
  }

  public synchronized byte[] read(String objectId) throws IOException {
    QloraContracts.require(contains(objectId), "base cache object is unavailable");
    return Files.readAllBytes(pathFor(objectId));
  }

  public synchronized long accountedBytes() {
    return accountedBytes;
  }

  private Path pathFor(String objectId) {
    QloraContracts.requireContentId(objectId, "base cache object ID");
    var path = root.resolve(objectId.substring(7)).normalize();
    QloraContracts.require(path.startsWith(root), "base cache path escaped root");
    return path;
  }

  public enum Kind {
    BASE,
    TOKENIZER,
    QUANTIZATION_PROFILE
  }

  public record BaseArtifact(
      Kind kind,
      String objectId,
      String payloadSha256,
      String mediaType,
      String licenseId,
      boolean redistributionAllowed,
      byte[] bytes) {
    public BaseArtifact {
      QloraContracts.require(kind != null, "base artifact kind is missing");
      QloraContracts.requireContentId(objectId, "base artifact object ID");
      QloraContracts.requireContentId(payloadSha256, "base artifact payload hash");
      QloraContracts.require(licenseId != null && !licenseId.isBlank(), "base license is missing");
      QloraContracts.require(bytes != null, "base artifact bytes are missing");
      bytes = Arrays.copyOf(bytes, bytes.length);
    }

    void validate() {
      QloraContracts.require(
          QloraContracts.rawSha256(bytes).equals(payloadSha256), "base payload hash mismatch");
      var expected =
          switch (kind) {
            case BASE -> QloraContracts.BASE_MEDIA;
            case TOKENIZER -> QloraContracts.TOKENIZER_MEDIA;
            case QUANTIZATION_PROFILE -> QloraContracts.PROFILE_MEDIA;
          };
      QloraContracts.require(expected.equals(mediaType), "base media registry mismatch");
    }

    @Override
    public byte[] bytes() {
      return Arrays.copyOf(bytes, bytes.length);
    }
  }

  public record CacheResult(Path path, long transferredBytes, boolean reused) {}
}
