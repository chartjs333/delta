package io.deltareduce.node.distribution;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.TreeMap;
import java.util.UUID;

/** Atomic resumable journal containing verified piece references and bounded attempt history. */
public final class DownloadJournal {
  private static final int MAX_ATTEMPTS = 65_536;
  private final Path path;
  private final String manifestId;
  private final TreeMap<Integer, String> verified;
  private final ArrayList<String> attempts;

  private DownloadJournal(
      Path path,
      String manifestId,
      TreeMap<Integer, String> verified,
      ArrayList<String> attempts) {
    this.path = path;
    this.manifestId = manifestId;
    this.verified = verified;
    this.attempts = attempts;
  }

  public static DownloadJournal open(Path path, String manifestId) throws IOException {
    DistributionModel.requireContentId(manifestId, "journal manifest ID");
    if (!Files.exists(path)) {
      var result = new DownloadJournal(path, manifestId, new TreeMap<>(), new ArrayList<>());
      result.persist();
      return result;
    }
    DistributionModel.require(!Files.isSymbolicLink(path), "journal is a symbolic link");
    var lines = Files.readAllLines(path, StandardCharsets.US_ASCII);
    DistributionModel.require(!lines.isEmpty() && lines.get(0).equals("manifest=" + manifestId),
        "journal manifest mismatch");
    var verified = new TreeMap<Integer, String>();
    var attempts = new ArrayList<String>();
    for (var index = 1; index < lines.size(); ++index) {
      var line = lines.get(index);
      if (line.startsWith("piece=")) {
        var fields = line.substring(6).split(":", 2);
        DistributionModel.require(fields.length == 2, "journal piece entry is malformed");
        var ordinal = Integer.parseInt(fields[0]);
        DistributionModel.requireContentId(fields[1], "journal piece ID");
        DistributionModel.require(verified.put(ordinal, fields[1]) == null,
            "journal contains duplicate ordinal");
      } else if (line.startsWith("attempt=")) {
        DistributionModel.require(attempts.size() < MAX_ATTEMPTS, "journal attempt limit exceeded");
        attempts.add(line.substring(8));
      } else {
        throw new IllegalArgumentException("journal contains an unknown entry");
      }
    }
    return new DownloadJournal(path, manifestId, verified, attempts);
  }

  public synchronized Map<Integer, String> reverify(
      DistributionModel.Manifest manifest, CasStore cas) throws IOException {
    var retained = new TreeMap<Integer, String>();
    for (var entry : verified.entrySet()) {
      if (entry.getKey() >= 0 && entry.getKey() < manifest.pieces().size()) {
        var descriptor = manifest.pieces().get(entry.getKey());
        if (descriptor.contentId().equals(entry.getValue()) && cas.hasVerifiedPiece(descriptor)) {
          retained.put(entry.getKey(), entry.getValue());
        }
      }
    }
    if (!retained.equals(verified)) {
      verified.clear();
      verified.putAll(retained);
      persist();
    }
    return Map.copyOf(retained);
  }

  public synchronized void recordAttempt(int ordinal, String peerId, String result)
      throws IOException {
    DistributionModel.require(attempts.size() < MAX_ATTEMPTS, "journal attempt limit exceeded");
    DistributionModel.require(peerId.matches("[a-zA-Z0-9._-]{1,128}"), "invalid journal peer ID");
    DistributionModel.require(result.matches("[A-Z_]{1,64}"), "invalid journal result");
    attempts.add(ordinal + ":" + peerId + ":" + result);
    persist();
  }

  public synchronized void markVerified(DistributionModel.PieceDescriptor descriptor)
      throws IOException {
    var prior = verified.put(descriptor.ordinal(), descriptor.contentId());
    DistributionModel.require(prior == null || prior.equals(descriptor.contentId()),
        "journal ordinal conflict");
    persist();
  }

  public synchronized int attemptCount() {
    return attempts.size();
  }

  public Path pathForEvidence() {
    return path;
  }

  private void persist() throws IOException {
    var output = new StringBuilder("manifest=").append(manifestId).append('\n');
    for (var entry : verified.entrySet()) {
      output.append("piece=").append(entry.getKey()).append(':').append(entry.getValue()).append('\n');
    }
    for (var attempt : attempts) {
      output.append("attempt=").append(attempt).append('\n');
    }
    var bytes = output.toString().getBytes(StandardCharsets.US_ASCII);
    var temporary = path.resolveSibling(path.getFileName() + ".tmp-" + UUID.randomUUID());
    var committed = false;
    try (var channel =
        FileChannel.open(temporary, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
      var buffer = ByteBuffer.wrap(bytes);
      while (buffer.hasRemaining()) {
        channel.write(buffer);
      }
      channel.force(true);
      Files.move(
          temporary,
          path,
          StandardCopyOption.ATOMIC_MOVE,
          StandardCopyOption.REPLACE_EXISTING);
      committed = true;
    } finally {
      if (!committed) {
        Files.deleteIfExists(temporary);
      }
    }
  }
}
