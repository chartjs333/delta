#include <delta/runtime/benchmark.hpp>

#include <algorithm>
#include <utility>

namespace delta::runtime::benchmark {

SidecarServer::SidecarServer(std::size_t queue_capacity, std::size_t maximum_payload_bytes)
    : queue_capacity_(queue_capacity), maximum_payload_bytes_(maximum_payload_bytes) {
  if (queue_capacity_ == 0U || maximum_payload_bytes_ == 0U) {
    throw BenchmarkError("sidecar bounds must be positive");
  }
}

SidecarReceipt SidecarServer::execute(
    std::string request_id,
    std::span<const std::byte> payload) {
  if (!accepting_) {
    throw BenchmarkError("sidecar is not accepting requests");
  }
  if (request_id.empty() || payload.size() > maximum_payload_bytes_) {
    throw BenchmarkError("invalid sidecar request");
  }
  if (const auto found = receipts_.find(request_id); found != receipts_.end()) {
    if (found->second.response.size() != payload.size() ||
        !std::ranges::equal(found->second.response, payload)) {
      throw BenchmarkError("conflicting sidecar replay");
    }
    auto replay = found->second;
    replay.replay = true;
    return replay;
  }
  if (receipts_.size() >= queue_capacity_) {
    throw BenchmarkError("sidecar replay journal capacity reached");
  }
  auto receipt = SidecarReceipt{
      next_sequence_++,
      std::vector<std::byte>(payload.begin(), payload.end()),
      false,
  };
  receipts_.emplace(std::move(request_id), receipt);
  return receipt;
}

void SidecarServer::crash() noexcept { accepting_ = false; }

void SidecarServer::restart() noexcept { accepting_ = true; }

bool SidecarServer::accepting() const noexcept { return accepting_; }

std::size_t SidecarServer::replay_entry_count() const noexcept { return receipts_.size(); }

}  // namespace delta::runtime::benchmark
