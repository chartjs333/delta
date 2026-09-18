#include <delta/runtime/benchmark.hpp>

#include <charconv>
#include <set>

namespace delta::runtime::benchmark {
namespace {

void require_token(std::string_view value) {
  if (value.empty() || value.find_first_of("\n\r|=") != std::string_view::npos) {
    throw BenchmarkError("invalid trace token");
  }
}

void append_sequence(std::string& output, std::uint64_t value) {
  char buffer[32]{};
  const auto result = std::to_chars(buffer, buffer + sizeof(buffer), value);
  if (result.ec != std::errc{}) {
    throw BenchmarkError("trace sequence encoding failed");
  }
  output.append(buffer, result.ptr);
}

}  // namespace

void TraceExporter::append(TraceEntry entry) {
  require_token(entry.action_id);
  require_token(entry.state_id);
  require_token(entry.effect_id);
  require_token(entry.terminal_outcome);
  const auto expected = entries_.empty() ? 1U : entries_.back().sequence + 1U;
  if (entry.sequence != expected) {
    throw BenchmarkError("non-contiguous trace sequence");
  }
  entries_.push_back(std::move(entry));
}

const std::vector<TraceEntry>& TraceExporter::entries() const noexcept { return entries_; }

std::string TraceExporter::canonical_text() const {
  std::string output;
  for (const auto& entry : entries_) {
    append_sequence(output, entry.sequence);
    output.push_back('|');
    output.append(entry.action_id);
    output.push_back('|');
    output.append(entry.state_id);
    output.push_back('|');
    output.append(entry.effect_id);
    output.push_back('|');
    output.append(entry.terminal_outcome);
    output.push_back('\n');
  }
  return output;
}

}  // namespace delta::runtime::benchmark
