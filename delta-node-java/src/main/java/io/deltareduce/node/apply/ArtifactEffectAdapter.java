package io.deltareduce.node.apply;

import io.deltareduce.node.certificates.NativeCertificateVerifier;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.Arrays;
import java.util.Objects;

/** Executes a bounded native-authored artifact effect without choosing checkpoint semantics. */
public final class ArtifactEffectAdapter {
  private final Path root;
  private final int maximumBytes;

  public ArtifactEffectAdapter(Path root, int maximumBytes) throws IOException {
    this.root = root.toAbsolutePath().normalize();
    NativeCertificateVerifier.require(maximumBytes > 0, "artifact bound must be positive");
    this.maximumBytes = maximumBytes;
    Files.createDirectories(this.root);
  }

  public Path execute(NativeEffect effect) throws IOException {
    Objects.requireNonNull(effect, "effect");
    NativeCertificateVerifier.require(
        effect.bytes().length <= maximumBytes, "artifact effect exceeds byte bound");
    var target = root.resolve(effect.relativePath()).normalize();
    NativeCertificateVerifier.require(target.startsWith(root), "artifact path escapes root");
    Files.createDirectories(target.getParent());
    var temporary = target.resolveSibling(target.getFileName() + ".native-tmp");
    Files.write(temporary, effect.bytes());
    try {
      Files.move(
          temporary,
          target,
          StandardCopyOption.ATOMIC_MOVE,
          StandardCopyOption.REPLACE_EXISTING);
    } catch (java.nio.file.AtomicMoveNotSupportedException ignored) {
      Files.move(temporary, target, StandardCopyOption.REPLACE_EXISTING);
    }
    return target;
  }

  public record NativeEffect(
      Action action, String contentId, String relativePath, byte[] bytes, byte[] authorization) {
    public NativeEffect {
      Objects.requireNonNull(action, "action");
      NativeCertificateVerifier.requireContentId(contentId, "artifact content ID");
      NativeCertificateVerifier.require(
          relativePath != null && !relativePath.isBlank(), "artifact path is empty");
      Objects.requireNonNull(bytes, "bytes");
      Objects.requireNonNull(authorization, "authorization");
      NativeCertificateVerifier.require(authorization.length > 0, "native authorization is empty");
      bytes = Arrays.copyOf(bytes, bytes.length);
      authorization = Arrays.copyOf(authorization, authorization.length);
    }

    @Override
    public byte[] bytes() {
      return Arrays.copyOf(bytes, bytes.length);
    }

    @Override
    public byte[] authorization() {
      return Arrays.copyOf(authorization, authorization.length);
    }
  }

  public enum Action {
    WRITE,
    REPAIR
  }
}
