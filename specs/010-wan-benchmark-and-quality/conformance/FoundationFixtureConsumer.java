import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Standalone TEST_FIXTURE byte/hash consumer; it has no node-runtime authority. */
public final class FoundationFixtureConsumer {
  private static final String[] ARTIFACT_NAMES = {
      "arm", "attestation", "definition", "evidence_manifest", "evidence_node", "result",
      "run_manifest"
  };
  private static final String[] EXPECTED_IDS = {
      "sha256:476b466992370b989ac24ef63569bb179b1c3ac9e215b8ce01fe68054c5c9b73",
      "sha256:0ce29dfbdab797db41850031ec6ee4fdd01fe8ea34ec1e4e0a63ba31ced39892",
      "sha256:32c8e884d1d93a3de77881d30df2bf78ed45d59017b38ca1318664e77485a449",
      "sha256:4ae1806f1ce4fb165d698f6d28648e4287b47689332c8859df008695ad8b6308",
      "sha256:50c42bee228b98c5bb58238251ef897fdc2a2286027f4f2f011dfc86b6e8efbb",
      "sha256:1f29322d968fd99538395765dafea1cc37c6d052cdb5160ca543b289d7b95faa",
      "sha256:e837f264cc59a92a1537aa24d44cefe9410008f2c826a5c50e3172455309e2cc"
  };
  private static final String[] EXPECTED_TYPES = {
      "BENCHMARK_ARM",
      "BENCHMARK_ATTESTATION_MANIFEST",
      "BENCHMARK_DEFINITION",
      "BENCHMARK_EVIDENCE_MANIFEST",
      "BENCHMARK_EVIDENCE_NODE",
      "BENCHMARK_RESULT",
      "BENCHMARK_RUN_MANIFEST"
  };
  private static final String FORMAL_SEMANTICS_ID =
      "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
  private static final String AUTHORITY_SCOPE = "BENCHMARK_GOVERNANCE_ONLY";
  private static final Comparator<String> CODE_POINT_ORDER =
      FoundationFixtureConsumer::compareCodePoints;
  private static final String EXPECTED_CANONICAL =
      "{\"adapter_id\":\"sha256:4c2b37696dd07c8b7defff21cd9248e987b5d4a397a65bd59540a8e2723756c6\","
          + "\"arm_kind\":\"DELTAREDUCE\",\"authority_scope\":\"BENCHMARK_GOVERNANCE_ONLY\","
          + "\"deployment_profile\":\"EMBEDDED_FFM\",\"evidence_class\":\"TEST_FIXTURE\","
          + "\"formal_semantics_id\":\"sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6\","
          + "\"gate_eligible\":false,\"model_mode\":\"QLORA_ADAPTER\","
          + "\"primary_eligible\":false,\"schema_version\":\"1.0.0\","
          + "\"topology\":\"HIERARCHICAL\",\"type_name\":\"BENCHMARK_ARM\"}";
  private static final String CORPUS =
      "{\"artifact_ids\":[\"sha256:476b466992370b989ac24ef63569bb179b1c3ac9e215b8ce01fe68054c5c9b73\","
          + "\"sha256:0ce29dfbdab797db41850031ec6ee4fdd01fe8ea34ec1e4e0a63ba31ced39892\","
          + "\"sha256:32c8e884d1d93a3de77881d30df2bf78ed45d59017b38ca1318664e77485a449\","
          + "\"sha256:4ae1806f1ce4fb165d698f6d28648e4287b47689332c8859df008695ad8b6308\","
          + "\"sha256:50c42bee228b98c5bb58238251ef897fdc2a2286027f4f2f011dfc86b6e8efbb\","
          + "\"sha256:1f29322d968fd99538395765dafea1cc37c6d052cdb5160ca543b289d7b95faa\","
          + "\"sha256:e837f264cc59a92a1537aa24d44cefe9410008f2c826a5c50e3172455309e2cc\"],"
          + "\"execution_class\":\"CONFORMANCE_SAFETY_ONLY\","
          + "\"formal_semantics_id\":\"sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6\","
          + "\"negative_statuses\":[{\"case_id\":\"definition-leading-space\","
          + "\"status\":\"JSON_BYTES_NOT_CANONICAL\"},{\"case_id\":\"run-primary-promotion\","
          + "\"status\":\"PRIMARY_ELIGIBILITY_FORBIDDEN\"}],"
          + "\"primary_observation_count\":0,\"schema_version\":\"1.0.0\","
          + "\"status\":\"PASS\",\"type_name\":\"FEATURE010_EXACTNESS_CORPUS\"}";

  private FoundationFixtureConsumer() {}

  public static void main(String[] args) throws Exception {
    if (args.length != 1 && args.length != 2) {
      throw new IllegalArgumentException("fixture path required");
    }
    String fixture = Files.readString(Path.of(args[0]), StandardCharsets.UTF_8);
    byte[] definitionCanonical = null;
    byte[] runCanonical = null;
    for (int index = 0; index < ARTIFACT_NAMES.length; index++) {
      String prefix = "\"" + ARTIFACT_NAMES[index] + "\":{\"bytes_hex\":\"";
      int start = fixture.indexOf(prefix);
      if (start < 0) {
        throw new IllegalStateException(ARTIFACT_NAMES[index] + " vector missing");
      }
      start += prefix.length();
      int end = fixture.indexOf('"', start);
      byte[] canonical = HexFormat.of().parseHex(fixture.substring(start, end));
      Map<?, ?> document = parseCanonicalObject(canonical);
      admit(index, document);
      if ("definition".equals(ARTIFACT_NAMES[index])) {
        definitionCanonical = canonical.clone();
      }
      if ("run_manifest".equals(ARTIFACT_NAMES[index])) {
        runCanonical = canonical.clone();
      }
      if (index == 0
          && !Arrays.equals(EXPECTED_CANONICAL.getBytes(StandardCharsets.UTF_8), canonical)) {
        throw new IllegalStateException("canonical bytes differ");
      }
      String digest = "sha256:" + HexFormat.of().formatHex(
          MessageDigest.getInstance("SHA-256").digest(canonical));
      if (!EXPECTED_IDS[index].equals(digest)) {
        throw new IllegalStateException(ARTIFACT_NAMES[index] + " content ID differs");
      }
      String storedPrefix = ",\"content_id\":\"";
      int storedStart = fixture.indexOf(storedPrefix, end);
      if (storedStart < 0) {
        throw new IllegalStateException(ARTIFACT_NAMES[index] + " stored content ID missing");
      }
      storedStart += storedPrefix.length();
      int storedEnd = fixture.indexOf('"', storedStart);
      if (!digest.equals(fixture.substring(storedStart, storedEnd))) {
        throw new IllegalStateException(ARTIFACT_NAMES[index] + " stored content ID differs");
      }
    }
    if (args.length == 2) {
      if (!"--emit-corpus".equals(args[1])) {
        throw new IllegalArgumentException("unknown mode");
      }
      if (definitionCanonical == null || runCanonical == null) {
        throw new IllegalStateException("negative corpus target missing");
      }
      byte[] noncanonical = new byte[definitionCanonical.length + 1];
      noncanonical[0] = ' ';
      System.arraycopy(
          definitionCanonical, 0, noncanonical, 1, definitionCanonical.length);
      String canonicalStatus = rejectionStatus(() -> parseCanonicalObject(noncanonical));

      Map<String, Object> promotedDocument = parseCanonicalObject(runCanonical);
      Object previousPrimaryEligibility =
          promotedDocument.put("primary_eligible", Boolean.TRUE);
      if (!Boolean.FALSE.equals(previousPrimaryEligibility)) {
        throw new IllegalStateException("run policy field invalid");
      }
      byte[] promoted = canonicalBytes(promotedDocument);
      String primaryStatus =
          rejectionStatus(
              () -> {
                Map<?, ?> reparsedPromotedDocument = parseCanonicalObject(promoted);
                admit(ARTIFACT_NAMES.length - 1, reparsedPromotedDocument);
              });
      if (!"JSON_BYTES_NOT_CANONICAL".equals(canonicalStatus)
          || !"PRIMARY_ELIGIBILITY_FORBIDDEN".equals(primaryStatus)) {
        throw new IllegalStateException("negative corpus mutation was not rejected");
      }
      System.out.println(CORPUS);
    } else {
      System.out.println(EXPECTED_IDS[0]);
    }
  }

  private static Map<String, Object> parseCanonicalObject(byte[] value) {
    if (value.length >= 3
        && (value[0] & 0xff) == 0xef
        && (value[1] & 0xff) == 0xbb
        && (value[2] & 0xff) == 0xbf) {
      throw new ContractException("JSON_BOM_FORBIDDEN");
    }
    String text = decodeUtf8(value);
    Object document = new JsonParser(text).parse();
    if (!(document instanceof Map<?, ?> parsedMap)) {
      throw new ContractException("JSON_ROOT_NOT_OBJECT");
    }
    Map<String, Object> map = new LinkedHashMap<>();
    for (Map.Entry<?, ?> entry : parsedMap.entrySet()) {
      if (!(entry.getKey() instanceof String key)) {
        throw new ContractException("JSON_NOT_CANONICALIZABLE");
      }
      map.put(key, entry.getValue());
    }
    byte[] canonical = canonicalBytes(map);
    if (!Arrays.equals(canonical, value)) {
      throw new ContractException("JSON_BYTES_NOT_CANONICAL");
    }
    return map;
  }

  private static String decodeUtf8(byte[] value) {
    try {
      return StandardCharsets.UTF_8
          .newDecoder()
          .onMalformedInput(CodingErrorAction.REPORT)
          .onUnmappableCharacter(CodingErrorAction.REPORT)
          .decode(ByteBuffer.wrap(value))
          .toString();
    } catch (CharacterCodingException error) {
      throw new ContractException("JSON_INVALID", error);
    }
  }

  private static byte[] canonicalBytes(Object value) {
    StringBuilder builder = new StringBuilder();
    appendCanonical(value, builder);
    return builder.toString().getBytes(StandardCharsets.UTF_8);
  }

  private static void appendCanonical(Object value, StringBuilder builder) {
    if (value == null) {
      builder.append("null");
    } else if (value instanceof Boolean bool) {
      builder.append(bool.booleanValue() ? "true" : "false");
    } else if (value instanceof BigInteger integer) {
      builder.append(integer.toString());
    } else if (value instanceof String string) {
      appendCanonicalString(string, builder);
    } else if (value instanceof List<?> list) {
      builder.append('[');
      for (int index = 0; index < list.size(); index++) {
        if (index > 0) {
          builder.append(',');
        }
        appendCanonical(list.get(index), builder);
      }
      builder.append(']');
    } else if (value instanceof Map<?, ?> map) {
      List<String> keys = new ArrayList<>(map.size());
      for (Object key : map.keySet()) {
        if (!(key instanceof String stringKey)) {
          throw new ContractException("JSON_NOT_CANONICALIZABLE");
        }
        keys.add(stringKey);
      }
      keys.sort(CODE_POINT_ORDER);
      builder.append('{');
      for (int index = 0; index < keys.size(); index++) {
        if (index > 0) {
          builder.append(',');
        }
        String key = keys.get(index);
        appendCanonicalString(key, builder);
        builder.append(':');
        appendCanonical(map.get(key), builder);
      }
      builder.append('}');
    } else {
      throw new ContractException("JSON_NOT_CANONICALIZABLE");
    }
  }

  private static void appendCanonicalString(String value, StringBuilder builder) {
    builder.append('"');
    for (int index = 0; index < value.length(); ) {
      int codePoint = value.codePointAt(index);
      index += Character.charCount(codePoint);
      switch (codePoint) {
        case '"' -> builder.append("\\\"");
        case '\\' -> builder.append("\\\\");
        case '\b' -> builder.append("\\b");
        case '\f' -> builder.append("\\f");
        case '\n' -> builder.append("\\n");
        case '\r' -> builder.append("\\r");
        case '\t' -> builder.append("\\t");
        default -> {
          if (codePoint < 0x20) {
            builder.append("\\u00");
            builder.append(Character.forDigit((codePoint >>> 4) & 0xf, 16));
            builder.append(Character.forDigit(codePoint & 0xf, 16));
          } else if (codePoint >= Character.MIN_SURROGATE
              && codePoint <= Character.MAX_SURROGATE) {
            throw new ContractException("JSON_NOT_CANONICALIZABLE");
          } else {
            builder.appendCodePoint(codePoint);
          }
        }
      }
    }
    builder.append('"');
  }

  private static int compareCodePoints(String left, String right) {
    int leftIndex = 0;
    int rightIndex = 0;
    while (leftIndex < left.length() && rightIndex < right.length()) {
      int leftCodePoint = left.codePointAt(leftIndex);
      int rightCodePoint = right.codePointAt(rightIndex);
      int comparison = Integer.compare(leftCodePoint, rightCodePoint);
      if (comparison != 0) {
        return comparison;
      }
      leftIndex += Character.charCount(leftCodePoint);
      rightIndex += Character.charCount(rightCodePoint);
    }
    return Integer.compare(left.length() - leftIndex, right.length() - rightIndex);
  }

  private static void admit(int artifactIndex, Map<?, ?> document) {
    requireField(document, "schema_version", "1.0.0", "SCHEMA_VERSION_MISMATCH");
    requireField(
        document, "type_name", EXPECTED_TYPES[artifactIndex], "TYPE_NAME_MISMATCH");
    requireField(
        document, "formal_semantics_id", FORMAL_SEMANTICS_ID, "FORMAL_SEMANTICS_MISMATCH");
    requireField(document, "authority_scope", AUTHORITY_SCOPE, "AUTHORITY_SCOPE_INVALID");
    requireField(document, "evidence_class", "TEST_FIXTURE", "TEST_FIXTURE_EVIDENCE_REQUIRED");
    requireField(document, "primary_eligible", Boolean.FALSE, "PRIMARY_ELIGIBILITY_FORBIDDEN");
    requireField(document, "gate_eligible", Boolean.FALSE, "GATE_ELIGIBILITY_FORBIDDEN");

    String artifactName = ARTIFACT_NAMES[artifactIndex];
    if ("run_manifest".equals(artifactName)) {
      requireField(
          document, "execution_mode", "CONFORMANCE_FIXTURE", "EXECUTION_MODE_FORBIDDEN");
      requireNullField(
          document, "execution_authorization_id", "EXECUTION_AUTHORIZATION_FORBIDDEN");
    } else if ("result".equals(artifactName)) {
      requireField(document, "decision", "NOT_EVALUATED", "RESULT_DECISION_FORBIDDEN");
    }
  }

  private static void requireField(
      Map<?, ?> document, String key, Object expected, String errorCode) {
    if (!document.containsKey(key) || !expected.equals(document.get(key))) {
      throw new ContractException(errorCode);
    }
  }

  private static void requireNullField(Map<?, ?> document, String key, String errorCode) {
    if (!document.containsKey(key) || document.get(key) != null) {
      throw new ContractException(errorCode);
    }
  }

  private static String rejectionStatus(CheckedAction action) {
    try {
      action.run();
    } catch (ContractException error) {
      return error.getMessage();
    }
    throw new IllegalStateException("negative corpus mutation was accepted");
  }

  @FunctionalInterface
  private interface CheckedAction {
    void run();
  }

  private static final class ContractException extends IllegalArgumentException {
    private static final long serialVersionUID = 1L;

    ContractException(String message) {
      super(message);
    }

    ContractException(String message, Throwable cause) {
      super(message, cause);
    }
  }

  private static final class JsonParser {
    private final String input;
    private int index;

    JsonParser(String input) {
      this.input = input;
    }

    Object parse() {
      skipWhitespace();
      Object value = parseValue();
      skipWhitespace();
      if (index != input.length()) {
        throw invalidJson();
      }
      return value;
    }

    private Object parseValue() {
      if (index >= input.length()) {
        throw invalidJson();
      }
      return switch (input.charAt(index)) {
        case '{' -> parseObject();
        case '[' -> parseArray();
        case '"' -> parseString();
        case 't' -> parseLiteral("true", Boolean.TRUE);
        case 'f' -> parseLiteral("false", Boolean.FALSE);
        case 'n' -> parseLiteral("null", null);
        default -> parseNumber();
      };
    }

    private Map<String, Object> parseObject() {
      index++;
      skipWhitespace();
      Map<String, Object> result = new LinkedHashMap<>();
      if (consume('}')) {
        return result;
      }
      while (true) {
        if (index >= input.length() || input.charAt(index) != '"') {
          throw invalidJson();
        }
        String key = parseString();
        if (result.containsKey(key)) {
          throw new ContractException("DUPLICATE_JSON_KEY:" + key);
        }
        skipWhitespace();
        require(':');
        skipWhitespace();
        result.put(key, parseValue());
        skipWhitespace();
        if (consume('}')) {
          return result;
        }
        require(',');
        skipWhitespace();
      }
    }

    private List<Object> parseArray() {
      index++;
      skipWhitespace();
      List<Object> result = new ArrayList<>();
      if (consume(']')) {
        return result;
      }
      while (true) {
        result.add(parseValue());
        skipWhitespace();
        if (consume(']')) {
          return result;
        }
        require(',');
        skipWhitespace();
      }
    }

    private String parseString() {
      require('"');
      StringBuilder result = new StringBuilder();
      while (index < input.length()) {
        char character = input.charAt(index++);
        if (character == '"') {
          return result.toString();
        }
        if (character == '\\') {
          appendEscape(result);
        } else if (character < 0x20) {
          throw invalidJson();
        } else if (Character.isHighSurrogate(character)) {
          if (index >= input.length() || !Character.isLowSurrogate(input.charAt(index))) {
            throw invalidJson();
          }
          result.append(character).append(input.charAt(index++));
        } else if (Character.isLowSurrogate(character)) {
          throw invalidJson();
        } else {
          result.append(character);
        }
      }
      throw invalidJson();
    }

    private void appendEscape(StringBuilder result) {
      if (index >= input.length()) {
        throw invalidJson();
      }
      char escape = input.charAt(index++);
      switch (escape) {
        case '"', '\\', '/' -> result.append(escape);
        case 'b' -> result.append('\b');
        case 'f' -> result.append('\f');
        case 'n' -> result.append('\n');
        case 'r' -> result.append('\r');
        case 't' -> result.append('\t');
        case 'u' -> appendUnicodeEscape(result);
        default -> throw invalidJson();
      }
    }

    private void appendUnicodeEscape(StringBuilder result) {
      char first = parseHexCodeUnit();
      if (Character.isHighSurrogate(first)) {
        if (index + 2 > input.length()
            || input.charAt(index) != '\\'
            || input.charAt(index + 1) != 'u') {
          throw invalidJson();
        }
        index += 2;
        char second = parseHexCodeUnit();
        if (!Character.isLowSurrogate(second)) {
          throw invalidJson();
        }
        result.append(first).append(second);
      } else if (Character.isLowSurrogate(first)) {
        throw invalidJson();
      } else {
        result.append(first);
      }
    }

    private char parseHexCodeUnit() {
      if (index + 4 > input.length()) {
        throw invalidJson();
      }
      int value = 0;
      for (int offset = 0; offset < 4; offset++) {
        int digit = Character.digit(input.charAt(index++), 16);
        if (digit < 0) {
          throw invalidJson();
        }
        value = (value << 4) | digit;
      }
      return (char) value;
    }

    private Object parseLiteral(String literal, Object value) {
      if (!input.startsWith(literal, index)) {
        throw invalidJson();
      }
      index += literal.length();
      return value;
    }

    private BigInteger parseNumber() {
      int start = index;
      if (consume('-') && index >= input.length()) {
        throw invalidJson();
      }
      if (consume('0')) {
        if (index < input.length() && isDigit(input.charAt(index))) {
          throw invalidJson();
        }
      } else {
        if (index >= input.length()
            || input.charAt(index) < '1'
            || input.charAt(index) > '9') {
          throw invalidJson();
        }
        do {
          index++;
        } while (index < input.length() && isDigit(input.charAt(index)));
      }

      boolean floatingPoint = false;
      if (consume('.')) {
        floatingPoint = true;
        requireDigitSequence();
      }
      if (index < input.length()
          && (input.charAt(index) == 'e' || input.charAt(index) == 'E')) {
        floatingPoint = true;
        index++;
        if (index < input.length()
            && (input.charAt(index) == '+' || input.charAt(index) == '-')) {
          index++;
        }
        requireDigitSequence();
      }
      if (floatingPoint) {
        throw new ContractException("JSON_NOT_CANONICALIZABLE");
      }
      try {
        return new BigInteger(input.substring(start, index));
      } catch (NumberFormatException error) {
        throw new ContractException("JSON_INVALID", error);
      }
    }

    private void requireDigitSequence() {
      if (index >= input.length() || !isDigit(input.charAt(index))) {
        throw invalidJson();
      }
      do {
        index++;
      } while (index < input.length() && isDigit(input.charAt(index)));
    }

    private static boolean isDigit(char character) {
      return character >= '0' && character <= '9';
    }

    private void skipWhitespace() {
      while (index < input.length()) {
        char character = input.charAt(index);
        if (character != ' ' && character != '\t' && character != '\n' && character != '\r') {
          return;
        }
        index++;
      }
    }

    private boolean consume(char expected) {
      if (index < input.length() && input.charAt(index) == expected) {
        index++;
        return true;
      }
      return false;
    }

    private void require(char expected) {
      if (!consume(expected)) {
        throw invalidJson();
      }
    }

    private static ContractException invalidJson() {
      return new ContractException("JSON_INVALID");
    }
  }
}
