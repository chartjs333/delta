package io.deltareduce.node.qlora;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Objects;

/** Runtime-neutral QLoRA transport identities; this class has no certificate authority. */
public final class QloraContracts {
  public static final String BASE_MEDIA =
      "application/vnd.deltareduce.qlora-base;version=1";
  public static final String TOKENIZER_MEDIA =
      "application/vnd.deltareduce.qlora-tokenizer;version=1";
  public static final String PROFILE_MEDIA =
      "application/vnd.deltareduce.qlora-quantization-profile;version=1";
  public static final String ADAPTER_MEDIA =
      "application/vnd.deltareduce.qlora-adapter-checkpoint;version=1";

  private QloraContracts() {}

  public static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalArgumentException(message);
    }
  }

  public static void requireContentId(String value, String name) {
    require(
        value != null && value.matches("sha256:[0-9a-f]{64}"),
        name + " is not a canonical content ID");
  }

  public static String rawSha256(byte[] bytes) {
    Objects.requireNonNull(bytes, "bytes");
    try {
      return "sha256:" + HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    } catch (NoSuchAlgorithmException error) {
      throw new IllegalStateException(error);
    }
  }

  public record CertifiedContext(
      String adapterParameterSchemaId,
      String baseModelManifestId,
      String parentAdapterId,
      String quantizedBaseProfileId,
      String tokenizerHash,
      String trainingModeId) {
    public CertifiedContext {
      requireContentId(adapterParameterSchemaId, "adapter schema ID");
      requireContentId(baseModelManifestId, "base manifest ID");
      requireContentId(parentAdapterId, "parent adapter ID");
      requireContentId(quantizedBaseProfileId, "quantized profile ID");
      requireContentId(tokenizerHash, "tokenizer hash");
      requireContentId(trainingModeId, "training mode ID");
    }
  }
}
