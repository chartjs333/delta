#include <delta/runtime/benchmark.hpp>

#include <algorithm>
#include <iterator>
#include <set>
#include <utility>

namespace delta::runtime::benchmark {

FaultController::FaultController(std::vector<FaultEvent> events) : events_(std::move(events)) {
  std::set<std::string, std::less<>> ids;
  for (const auto& event : events_) {
    if (event.event_id.empty() || event.actor_class.empty() || !ids.insert(event.event_id).second) {
      throw BenchmarkError("invalid or duplicate fault event");
    }
  }
  std::ranges::sort(events_, {}, [](const FaultEvent& event) {
    return std::pair{event.logical_step, event.event_id};
  });
}

std::vector<FaultEvent> FaultController::events_at(std::uint64_t logical_step) const {
  std::vector<FaultEvent> result;
  std::ranges::copy_if(events_, std::back_inserter(result), [logical_step](const FaultEvent& event) {
    return event.logical_step == logical_step;
  });
  return result;
}

const std::vector<FaultEvent>& FaultController::events() const noexcept { return events_; }

}  // namespace delta::runtime::benchmark
