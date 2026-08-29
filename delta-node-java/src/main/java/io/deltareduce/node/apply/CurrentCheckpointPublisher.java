package io.deltareduce.node.apply;

import io.deltareduce.node.certificates.NativeCertificateVerifier;
import java.util.Arrays;
import java.util.Objects;

/** Publishes only an already validated native AdvanceCurrent effect. */
public final class CurrentCheckpointPublisher {
  private final PointerSink sink;

  public CurrentCheckpointPublisher(PointerSink sink) {
    this.sink = Objects.requireNonNull(sink, "sink");
  }

  public void publish(NativeAdvanceCurrent effect) {
    Objects.requireNonNull(effect, "effect");
    sink.publish(effect.copy());
  }

  public record NativeAdvanceCurrent(
      String applyQcId, String checkpointId, String optimizerId, byte[] authorization) {
    public NativeAdvanceCurrent {
      NativeCertificateVerifier.requireContentId(applyQcId, "ApplyQC ID");
      NativeCertificateVerifier.requireContentId(checkpointId, "checkpoint ID");
      NativeCertificateVerifier.requireContentId(optimizerId, "optimizer ID");
      Objects.requireNonNull(authorization, "authorization");
      NativeCertificateVerifier.require(authorization.length > 0, "native authorization is empty");
      authorization = Arrays.copyOf(authorization, authorization.length);
    }

    @Override
    public byte[] authorization() {
      return Arrays.copyOf(authorization, authorization.length);
    }

    NativeAdvanceCurrent copy() {
      return new NativeAdvanceCurrent(applyQcId, checkpointId, optimizerId, authorization);
    }
  }

  @FunctionalInterface
  public interface PointerSink {
    void publish(NativeAdvanceCurrent effect);
  }
}
