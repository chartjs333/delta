#include <array>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
constexpr std::array<std::string_view, 7> kArtifactNames = {
    "arm", "attestation", "definition", "evidence_manifest", "evidence_node", "result",
    "run_manifest",
};
constexpr std::array<std::string_view, 7> kExpectedIds = {
    "sha256:476b466992370b989ac24ef63569bb179b1c3ac9e215b8ce01fe68054c5c9b73",
    "sha256:0ce29dfbdab797db41850031ec6ee4fdd01fe8ea34ec1e4e0a63ba31ced39892",
    "sha256:32c8e884d1d93a3de77881d30df2bf78ed45d59017b38ca1318664e77485a449",
    "sha256:4ae1806f1ce4fb165d698f6d28648e4287b47689332c8859df008695ad8b6308",
    "sha256:50c42bee228b98c5bb58238251ef897fdc2a2286027f4f2f011dfc86b6e8efbb",
    "sha256:1f29322d968fd99538395765dafea1cc37c6d052cdb5160ca543b289d7b95faa",
    "sha256:e837f264cc59a92a1537aa24d44cefe9410008f2c826a5c50e3172455309e2cc",
};
constexpr auto kExpectedHex =
    "7b22616461707465725f6964223a227368613235363a34633262333736393664643037633862376465666666323163643932343865393837623564346133393761363562643539353430613865323732333735366336222c2261726d5f6b696e64223a2244454c5441524544554345222c22617574686f726974795f73636f7065223a2242454e43484d41524b5f474f5645524e414e43455f4f4e4c59222c226465706c6f796d656e745f70726f66696c65223a22454d4245444445445f46464d222c2265766964656e63655f636c617373223a22544553545f46495854555245222c22666f726d616c5f73656d616e746963735f6964223a227368613235363a63633938663135616332306663336564323635636237363638326361313561393336653234363630613635316532623866383136333861626233323635636236222c22676174655f656c696769626c65223a66616c73652c226d6f64656c5f6d6f6465223a22514c4f52415f41444150544552222c227072696d6172795f656c696769626c65223a66616c73652c22736368656d615f76657273696f6e223a22312e302e30222c22746f706f6c6f6779223a2248494552415243484943414c222c22747970655f6e616d65223a2242454e43484d41524b5f41524d227d";
constexpr auto kExpectedCanonical =
    R"json({"adapter_id":"sha256:4c2b37696dd07c8b7defff21cd9248e987b5d4a397a65bd59540a8e2723756c6","arm_kind":"DELTAREDUCE","authority_scope":"BENCHMARK_GOVERNANCE_ONLY","deployment_profile":"EMBEDDED_FFM","evidence_class":"TEST_FIXTURE","formal_semantics_id":"sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6","gate_eligible":false,"model_mode":"QLORA_ADAPTER","primary_eligible":false,"schema_version":"1.0.0","topology":"HIERARCHICAL","type_name":"BENCHMARK_ARM"})json";

constexpr std::array<std::uint32_t, 64> kSha256Constants = {
    0x428a2f98U, 0x71374491U, 0xb5c0fbcfU, 0xe9b5dba5U, 0x3956c25bU, 0x59f111f1U,
    0x923f82a4U, 0xab1c5ed5U, 0xd807aa98U, 0x12835b01U, 0x243185beU, 0x550c7dc3U,
    0x72be5d74U, 0x80deb1feU, 0x9bdc06a7U, 0xc19bf174U, 0xe49b69c1U, 0xefbe4786U,
    0x0fc19dc6U, 0x240ca1ccU, 0x2de92c6fU, 0x4a7484aaU, 0x5cb0a9dcU, 0x76f988daU,
    0x983e5152U, 0xa831c66dU, 0xb00327c8U, 0xbf597fc7U, 0xc6e00bf3U, 0xd5a79147U,
    0x06ca6351U, 0x14292967U, 0x27b70a85U, 0x2e1b2138U, 0x4d2c6dfcU, 0x53380d13U,
    0x650a7354U, 0x766a0abbU, 0x81c2c92eU, 0x92722c85U, 0xa2bfe8a1U, 0xa81a664bU,
    0xc24b8b70U, 0xc76c51a3U, 0xd192e819U, 0xd6990624U, 0xf40e3585U, 0x106aa070U,
    0x19a4c116U, 0x1e376c08U, 0x2748774cU, 0x34b0bcb5U, 0x391c0cb3U, 0x4ed8aa4aU,
    0x5b9cca4fU, 0x682e6ff3U, 0x748f82eeU, 0x78a5636fU, 0x84c87814U, 0x8cc70208U,
    0x90befffaU, 0xa4506cebU, 0xbef9a3f7U, 0xc67178f2U,
};

std::uint32_t rotate_right(std::uint32_t value, unsigned count) {
  return (value >> count) | (value << (32U - count));
}

std::string sha256_hex(std::string_view input) {
  std::vector<std::uint8_t> bytes(input.begin(), input.end());
  const auto bit_length = static_cast<std::uint64_t>(bytes.size()) * 8U;
  bytes.push_back(0x80U);
  while (bytes.size() % 64U != 56U) bytes.push_back(0U);
  for (int shift = 56; shift >= 0; shift -= 8) {
    bytes.push_back(static_cast<std::uint8_t>((bit_length >> shift) & 0xffU));
  }

  std::array<std::uint32_t, 8> hash = {
      0x6a09e667U, 0xbb67ae85U, 0x3c6ef372U, 0xa54ff53aU,
      0x510e527fU, 0x9b05688cU, 0x1f83d9abU, 0x5be0cd19U,
  };
  for (std::size_t offset = 0; offset < bytes.size(); offset += 64U) {
    std::array<std::uint32_t, 64> words{};
    for (std::size_t index = 0; index < 16U; ++index) {
      const auto base = offset + index * 4U;
      words[index] = (static_cast<std::uint32_t>(bytes[base]) << 24U) |
                     (static_cast<std::uint32_t>(bytes[base + 1U]) << 16U) |
                     (static_cast<std::uint32_t>(bytes[base + 2U]) << 8U) |
                     static_cast<std::uint32_t>(bytes[base + 3U]);
    }
    for (std::size_t index = 16U; index < words.size(); ++index) {
      const auto s0 = rotate_right(words[index - 15U], 7U) ^
                      rotate_right(words[index - 15U], 18U) ^ (words[index - 15U] >> 3U);
      const auto s1 = rotate_right(words[index - 2U], 17U) ^
                      rotate_right(words[index - 2U], 19U) ^ (words[index - 2U] >> 10U);
      words[index] = words[index - 16U] + s0 + words[index - 7U] + s1;
    }

    auto a = hash[0];
    auto b = hash[1];
    auto c = hash[2];
    auto d = hash[3];
    auto e = hash[4];
    auto f = hash[5];
    auto g = hash[6];
    auto h = hash[7];
    for (std::size_t index = 0; index < words.size(); ++index) {
      const auto sum1 = rotate_right(e, 6U) ^ rotate_right(e, 11U) ^ rotate_right(e, 25U);
      const auto choose = (e & f) ^ ((~e) & g);
      const auto temp1 = h + sum1 + choose + kSha256Constants[index] + words[index];
      const auto sum0 = rotate_right(a, 2U) ^ rotate_right(a, 13U) ^ rotate_right(a, 22U);
      const auto majority = (a & b) ^ (a & c) ^ (b & c);
      const auto temp2 = sum0 + majority;
      h = g;
      g = f;
      f = e;
      e = d + temp1;
      d = c;
      c = b;
      b = a;
      a = temp1 + temp2;
    }
    hash[0] += a;
    hash[1] += b;
    hash[2] += c;
    hash[3] += d;
    hash[4] += e;
    hash[5] += f;
    hash[6] += g;
    hash[7] += h;
  }

  std::ostringstream output;
  output << std::hex << std::setfill('0');
  for (const auto word : hash) output << std::setw(8) << word;
  return output.str();
}

int nibble(char value) {
  if (value >= '0' && value <= '9') return value - '0';
  if (value >= 'a' && value <= 'f') return value - 'a' + 10;
  throw std::runtime_error("non-lowercase hex");
}

std::string decode_hex(const std::string& value) {
  if (value.size() % 2 != 0) throw std::runtime_error("odd hex length");
  std::string result;
  result.reserve(value.size() / 2);
  for (std::size_t index = 0; index < value.size(); index += 2) {
    result.push_back(static_cast<char>((nibble(value[index]) << 4) | nibble(value[index + 1])));
  }
  return result;
}
}  // namespace

int main(int argc, char** argv) {
  if (argc != 2) throw std::runtime_error("fixture path required");
  std::ifstream input(argv[1], std::ios::binary);
  if (!input) throw std::runtime_error("fixture unavailable");
  const std::string fixture((std::istreambuf_iterator<char>(input)), {});
  for (std::size_t index = 0; index < kArtifactNames.size(); ++index) {
    const auto prefix_text = std::string("\"") + std::string(kArtifactNames[index]) +
                             "\":{\"bytes_hex\":\"";
    const auto prefix = fixture.find(prefix_text);
    if (prefix == std::string::npos) throw std::runtime_error("artifact vector missing");
    const auto start = prefix + prefix_text.size();
    const auto end = fixture.find('"', start);
    const auto encoded = fixture.substr(start, end - start);
    if (index == 0 && encoded != kExpectedHex) throw std::runtime_error("fixture hex differs");
    const auto canonical = decode_hex(encoded);
    if (index == 0 && canonical != kExpectedCanonical) {
      throw std::runtime_error("canonical bytes differ");
    }
    const auto actual_id = std::string("sha256:") + sha256_hex(canonical);
    if (actual_id != kExpectedIds[index]) throw std::runtime_error("content ID differs");
    const auto stored_prefix = fixture.find(",\"content_id\":\"", end);
    if (stored_prefix == std::string::npos) {
      throw std::runtime_error("stored content ID missing");
    }
    const auto stored_start = stored_prefix + std::string(",\"content_id\":\"").size();
    const auto stored_end = fixture.find('"', stored_start);
    if (fixture.substr(stored_start, stored_end - stored_start) != actual_id) {
      throw std::runtime_error("stored content ID differs");
    }
  }
  std::cout << kExpectedIds[0] << '\n';
}
