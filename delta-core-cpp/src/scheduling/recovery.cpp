#include <delta/scheduling/recovery.hpp>

#include <delta/core/canonical.hpp>

#include <algorithm>
#include <array>
#include <cerrno>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <limits>
#include <map>
#include <span>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#ifdef _WIN32
#include <io.h>
#else
#include <unistd.h>
#endif

namespace delta::scheduling {
namespace {

constexpr std::array<std::byte, 4> journal_magic = {
    std::byte{'D'}, std::byte{'S'}, std::byte{'J'}, std::byte{'1'}};
constexpr std::size_t checksum_size = 64U;
constexpr std::size_t maximum_frame_size = 2U * 1024U * 1024U;

enum class EventKind : std::uint8_t { set_lease = 1U, commit = 2U };

struct Event {
  std::uint64_t sequence;
  EventKind kind;
  std::string request_id;
  LeaseRecord lease;
  std::string commitment_id;
};

[[noreturn]] void reject(ErrorCode code, std::string message) {
  throw SchedulingError(code, std::move(message));
}

void require(bool condition, ErrorCode code, const char* message) {
  if (!condition) {
    reject(code, message);
  }
}

[[nodiscard]] bool content_id_valid(std::string_view value) noexcept {
  if (value.size() != 71U || !value.starts_with("sha256:")) {
    return false;
  }
  return std::all_of(value.begin() + 7, value.end(), [](char character) {
    return (character >= '0' && character <= '9') ||
           (character >= 'a' && character <= 'f');
  });
}

[[nodiscard]] bool label_valid(std::string_view value) noexcept {
  return !value.empty() && value.size() <= 128U &&
         std::all_of(value.begin(), value.end(), [](char character) {
           const bool letter = (character >= 'A' && character <= 'Z') ||
                               (character >= 'a' && character <= 'z');
           const bool digit = character >= '0' && character <= '9';
           return letter || digit || character == '.' || character == '_' || character == ':' ||
                  character == '-';
         });
}

void append_u8(std::vector<std::byte>& output, std::uint8_t value) {
  output.push_back(static_cast<std::byte>(value));
}

void append_u16(std::vector<std::byte>& output, std::uint16_t value) {
  append_u8(output, static_cast<std::uint8_t>((value >> 8U) & 0xffU));
  append_u8(output, static_cast<std::uint8_t>(value & 0xffU));
}

void append_u32(std::vector<std::byte>& output, std::uint32_t value) {
  for (unsigned shift = 24U;; shift -= 8U) {
    append_u8(output, static_cast<std::uint8_t>((value >> shift) & 0xffU));
    if (shift == 0U) {
      break;
    }
  }
}

void append_u64(std::vector<std::byte>& output, std::uint64_t value) {
  for (unsigned shift = 56U;; shift -= 8U) {
    append_u8(output, static_cast<std::uint8_t>((value >> shift) & 0xffU));
    if (shift == 0U) {
      break;
    }
  }
}

void replace_u32(std::vector<std::byte>& output, std::size_t offset, std::uint32_t value) {
  for (std::size_t index = 0U; index < 4U; ++index) {
    const auto shift = static_cast<unsigned>((3U - index) * 8U);
    output[offset + index] = static_cast<std::byte>((value >> shift) & 0xffU);
  }
}

[[nodiscard]] std::uint16_t checked_u16(std::size_t value) {
  require(value <= UINT16_MAX, ErrorCode::input_too_large, "journal string exceeds u16");
  return static_cast<std::uint16_t>(value);
}

[[nodiscard]] std::uint32_t checked_u32(std::size_t value) {
  require(value <= UINT32_MAX, ErrorCode::input_too_large, "journal frame exceeds u32");
  return static_cast<std::uint32_t>(value);
}

void append_string(std::vector<std::byte>& output, std::string_view value) {
  append_u16(output, checked_u16(value.size()));
  for (const char character : value) {
    output.push_back(static_cast<std::byte>(character));
  }
}

[[nodiscard]] std::vector<std::byte> encode_event(const Event& event) {
  std::vector<std::byte> output(journal_magic.begin(), journal_magic.end());
  const auto length_offset = output.size();
  append_u32(output, 0U);
  append_u64(output, event.sequence);
  append_u8(output, static_cast<std::uint8_t>(event.kind));
  append_string(output, event.request_id);
  append_string(output, event.lease.lease.ticket_id);
  append_string(output, event.lease.lease.worker_id);
  append_string(output, event.lease.lease.region_route);
  append_string(output, event.lease.lease.plan_id);
  append_string(output, event.lease.lease.prior_lease_id);
  append_string(output, event.lease.lease.round_config_id);
  append_string(output, event.lease.lease.state);
  append_string(output, event.lease.lease.ticket_content_id);
  append_u64(output, event.lease.lease.lease_epoch);
  append_u64(output, event.lease.lease.issue_tick);
  append_u64(output, event.lease.lease.expiry_tick);
  append_u64(output, event.lease.lease.renewal_count);
  append_string(output, event.commitment_id);
  const auto total_size = checked_u32(output.size() + checksum_size);
  replace_u32(output, length_offset, total_size);
  const auto checksum = delta::core::canonical::sha256_hex(output);
  for (const char character : checksum) {
    output.push_back(static_cast<std::byte>(character));
  }
  return output;
}

class Reader final {
 public:
  explicit Reader(std::span<const std::byte> bytes) : bytes_(bytes) {}

  [[nodiscard]] std::size_t remaining() const noexcept { return bytes_.size() - cursor_; }

  [[nodiscard]] std::span<const std::byte> take(std::size_t count) {
    require(count <= remaining(), ErrorCode::canonical_json_invalid, "journal frame is truncated");
    const auto result = bytes_.subspan(cursor_, count);
    cursor_ += count;
    return result;
  }

  [[nodiscard]] std::uint8_t u8() {
    return std::to_integer<std::uint8_t>(take(1U).front());
  }

  [[nodiscard]] std::uint16_t u16() {
    return static_cast<std::uint16_t>((static_cast<std::uint16_t>(u8()) << 8U) | u8());
  }

  [[nodiscard]] std::uint32_t u32() {
    std::uint32_t value = 0U;
    for (std::size_t index = 0U; index < 4U; ++index) {
      value = (value << 8U) | u8();
    }
    return value;
  }

  [[nodiscard]] std::uint64_t u64() {
    std::uint64_t value = 0U;
    for (std::size_t index = 0U; index < 8U; ++index) {
      value = (value << 8U) | u8();
    }
    return value;
  }

  [[nodiscard]] std::string string() {
    const auto raw = take(u16());
    std::string result;
    result.reserve(raw.size());
    for (const auto byte : raw) {
      const auto character = static_cast<char>(std::to_integer<unsigned char>(byte));
      require(
          character >= 0x20 && character <= 0x7e,
          ErrorCode::canonical_json_invalid,
          "journal string is outside printable ASCII");
      result.push_back(character);
    }
    return result;
  }

 private:
  std::span<const std::byte> bytes_;
  std::size_t cursor_ = 0U;
};

[[nodiscard]] bool equal_magic(std::span<const std::byte> value) {
  return value.size() == journal_magic.size() &&
         std::equal(value.begin(), value.end(), journal_magic.begin());
}

[[nodiscard]] std::string ascii(std::span<const std::byte> value) {
  std::string result;
  result.reserve(value.size());
  for (const auto byte : value) {
    result.push_back(static_cast<char>(std::to_integer<unsigned char>(byte)));
  }
  return result;
}

[[nodiscard]] Event decode_event(std::span<const std::byte> frame) {
  require(
      frame.size() >= 4U + 4U + 8U + 1U + checksum_size &&
          frame.size() <= maximum_frame_size,
      ErrorCode::canonical_json_invalid,
      "journal frame size is invalid");
  const auto payload = frame.first(frame.size() - checksum_size);
  require(
      delta::core::canonical::sha256_hex(payload) ==
          ascii(frame.last(checksum_size)),
      ErrorCode::canonical_json_invalid,
      "journal checksum mismatch");
  Reader reader(payload);
  require(equal_magic(reader.take(4U)), ErrorCode::canonical_json_invalid, "journal magic mismatch");
  require(
      reader.u32() == frame.size(),
      ErrorCode::canonical_json_invalid,
      "journal frame length mismatch");
  Event event;
  event.sequence = reader.u64();
  const auto raw_kind = reader.u8();
  require(
      raw_kind == static_cast<std::uint8_t>(EventKind::set_lease) ||
          raw_kind == static_cast<std::uint8_t>(EventKind::commit),
      ErrorCode::canonical_json_invalid,
      "journal event kind is invalid");
  event.kind = static_cast<EventKind>(raw_kind);
  event.request_id = reader.string();
  TicketLease lease;
  lease.ticket_id = reader.string();
  lease.worker_id = reader.string();
  lease.region_route = reader.string();
  lease.plan_id = reader.string();
  lease.prior_lease_id = reader.string();
  lease.round_config_id = reader.string();
  lease.state = reader.string();
  lease.ticket_content_id = reader.string();
  lease.lease_epoch = reader.u64();
  lease.issue_tick = reader.u64();
  lease.expiry_tick = reader.u64();
  lease.renewal_count = reader.u64();
  event.commitment_id = reader.string();
  require(
      reader.remaining() == 0U,
      ErrorCode::canonical_json_invalid,
      "journal frame contains trailing bytes");
  auto canonical = canonical_ticket_lease(lease);
  event.lease = {std::move(lease), canonical, ticket_lease_content_id(canonical)};
  return event;
}

[[nodiscard]] std::vector<std::byte> read_file(const std::filesystem::path& path) {
  std::ifstream input(path, std::ios::binary);
  require(input.good(), ErrorCode::canonical_json_invalid, "cannot open scheduling journal");
  const std::vector<char> characters{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  std::vector<std::byte> result;
  result.reserve(characters.size());
  for (const unsigned char character : characters) {
    result.push_back(static_cast<std::byte>(character));
  }
  return result;
}

void sync_file(std::FILE* file) {
  require(std::fflush(file) == 0, ErrorCode::canonical_json_invalid, "journal flush failed");
#ifdef _WIN32
  require(_commit(_fileno(file)) == 0, ErrorCode::canonical_json_invalid, "journal commit failed");
#else
  require(::fsync(::fileno(file)) == 0, ErrorCode::canonical_json_invalid, "journal fsync failed");
#endif
}

[[nodiscard]] std::FILE* open_append(const std::filesystem::path& path) {
  std::FILE* file = nullptr;
#ifdef _WIN32
  static_cast<void>(fopen_s(&file, path.string().c_str(), "ab"));
#else
  file = std::fopen(path.string().c_str(), "ab");
#endif
  return file;
}

void append_file(const std::filesystem::path& path, std::span<const std::byte> value) {
  auto* file = open_append(path);
  require(file != nullptr, ErrorCode::canonical_json_invalid, "cannot open journal for append");
  const auto written = std::fwrite(value.data(), 1U, value.size(), file);
  if (written != value.size()) {
    static_cast<void>(std::fclose(file));
    reject(ErrorCode::canonical_json_invalid, "cannot append complete journal frame");
  }
  try {
    sync_file(file);
  } catch (...) {
    static_cast<void>(std::fclose(file));
    throw;
  }
  require(std::fclose(file) == 0, ErrorCode::canonical_json_invalid, "journal close failed");
}

[[nodiscard]] std::string quote(std::string_view value) {
  require(
      std::all_of(value.begin(), value.end(), [](char character) {
        return character >= 0x20 && character <= 0x7e && character != '"' && character != '\\';
      }),
      ErrorCode::identifier_invalid,
      "timer string is outside the canonical ASCII subset");
  return "\"" + std::string(value) + "\"";
}

void append_field(std::string& output, std::string_view key, std::string_view encoded_value) {
  if (output.size() > 1U) {
    output.push_back(',');
  }
  output += quote(key);
  output.push_back(':');
  output += encoded_value;
}

[[nodiscard]] std::vector<std::byte> bytes(std::string value) {
  const auto view = std::as_bytes(std::span(value.data(), value.size()));
  return {view.begin(), view.end()};
}

[[nodiscard]] std::string content_id_for(
    std::string_view domain,
    std::span<const std::byte> canonical_json) {
  std::vector<std::byte> input;
  input.reserve(domain.size() + 1U + canonical_json.size());
  for (const char character : domain) {
    input.push_back(static_cast<std::byte>(character));
  }
  input.push_back(std::byte{0});
  input.insert(input.end(), canonical_json.begin(), canonical_json.end());
  return "sha256:" + delta::core::canonical::sha256_hex(input);
}

[[nodiscard]] std::string plain_sha256(std::string_view value) {
  const auto view = std::as_bytes(std::span(value.data(), value.size()));
  return "sha256:" + delta::core::canonical::sha256_hex(view);
}

}  // namespace

class LeaseStateMachine::Impl final {
 public:
  Impl(
      std::filesystem::path directory,
      RoundTicketPlan plan,
      std::vector<LeaseRecord> initial_leases)
      : directory_(std::move(directory)),
        journal_path_(directory_ / "scheduling.wal"),
        plan_(std::move(plan)) {
    require(
        initial_leases.size() == plan_.tickets.size(),
        ErrorCode::policy_invalid,
        "initial lease set does not cover the ticket plan");
    for (std::size_t index = 0U; index < initial_leases.size(); ++index) {
      const auto& lease = initial_leases[index];
      const auto& ticket = plan_.tickets[index];
      require(
          lease.lease.ticket_id == ticket.ticket.ticket_id &&
              lease.lease.ticket_content_id == ticket.content_id &&
              lease.lease.plan_id == plan_.content_id && lease.lease.lease_epoch == 0U &&
              lease.lease.renewal_count == 0U && lease.lease.state == "ACTIVE" &&
              lease.content_id == ticket_lease_content_id(lease.canonical_bytes) &&
              lease.canonical_bytes == canonical_ticket_lease(lease.lease),
          ErrorCode::policy_invalid,
          "initial lease does not match the immutable ticket plan");
      initial_.emplace(lease.lease.ticket_id, lease);
    }
    std::error_code error;
    std::filesystem::create_directories(directory_, error);
    require(!error, ErrorCode::canonical_json_invalid, "cannot create scheduling journal directory");
    if (std::filesystem::exists(journal_path_) && std::filesystem::file_size(journal_path_) > 0U) {
      recover();
    } else {
      for (const auto& [ticket_id, lease] : initial_) {
        Event event{
            sequence_ + 1U,
            EventKind::set_lease,
            "init:" + lease.content_id,
            lease,
            "",
        };
        persist_and_apply(event, SchedulingCrashPoint::none);
      }
    }
  }

  [[nodiscard]] const LeaseRecord& lease(std::string_view ticket_id) const {
    const auto found = leases_.find(std::string(ticket_id));
    require(found != leases_.end(), ErrorCode::ticket_invalid, "ticket lease is unknown");
    return found->second;
  }

  [[nodiscard]] std::string commitment(std::string_view ticket_id) const {
    static_cast<void>(lease(ticket_id));
    const auto found = commitments_.find(std::string(ticket_id));
    return found == commitments_.end() ? std::string{} : found->second;
  }

  [[nodiscard]] TimerTokenRecord timer_token(std::string_view ticket_id) const {
    const auto& current = lease(ticket_id);
    require(
        current.lease.state == "ACTIVE",
        ErrorCode::ticket_invalid,
        "timer token requires an active lease");
    LeaseTimerToken token{
        "LEASE_EXPIRY",
        current.lease.expiry_tick,
        current.lease.lease_epoch,
        current.content_id,
        current.lease.plan_id,
        current.lease.round_config_id,
        current.lease.ticket_id,
        plain_sha256(current.content_id),
        current.lease.worker_id,
    };
    auto canonical = canonical_lease_timer_token(token);
    return {std::move(token), canonical, lease_timer_token_content_id(canonical)};
  }

  [[nodiscard]] LeaseTransitionReceipt renew(
      std::string_view ticket_id,
      std::string_view worker_id,
      std::uint64_t lease_epoch,
      std::uint64_t expected_renewal_count,
      std::uint64_t logical_tick,
      SchedulingCrashPoint crash_point) {
    const auto request = "renew:" + std::string(ticket_id) + ":" + std::string(worker_id) + ":" +
                         std::to_string(lease_epoch) + ":" +
                         std::to_string(expected_renewal_count) + ":" +
                         std::to_string(logical_tick);
    if (const auto replay = replay_sequence(request); replay != 0U) {
      return {TransitionStatus::replay, lease(ticket_id), replay};
    }
    const auto& current = lease(ticket_id);
    require(
        commitment(ticket_id).empty(),
        ErrorCode::ticket_invalid,
        "committed ticket lease cannot be renewed");
    require(
        current.lease.state == "ACTIVE" && current.lease.worker_id == worker_id &&
            current.lease.lease_epoch == lease_epoch &&
            current.lease.renewal_count == expected_renewal_count,
        ErrorCode::ticket_invalid,
        "renewal does not match the current lease");
    require(
        logical_tick <= current.lease.expiry_tick,
        ErrorCode::ticket_invalid,
        "expired lease cannot be renewed");
    require(
        current.lease.renewal_count < plan_.lease_policy.maximum_renewals,
        ErrorCode::policy_invalid,
        "maximum lease renewals reached");
    require(
        current.lease.expiry_tick <=
            std::numeric_limits<std::uint64_t>::max() - plan_.lease_policy.lease_duration_ticks,
        ErrorCode::policy_invalid,
        "renewed lease expiry overflows");
    auto next = current.lease;
    next.expiry_tick += plan_.lease_policy.lease_duration_ticks;
    ++next.renewal_count;
    require(
        next.expiry_tick <= plan_.lease_policy.hard_deadline_tick,
        ErrorCode::policy_invalid,
        "renewed lease exceeds hard deadline");
    return persist_lease(request, std::move(next), crash_point);
  }

  [[nodiscard]] LeaseTransitionReceipt expire(
      const TimerTokenRecord& token,
      std::uint64_t logical_tick,
      SchedulingCrashPoint crash_point) {
    require(
        token.canonical_bytes == canonical_lease_timer_token(token.token) &&
            token.content_id == lease_timer_token_content_id(token.canonical_bytes),
        ErrorCode::ticket_invalid,
        "lease timer token identity is invalid");
    const auto request = "expire:" + token.content_id;
    if (const auto replay = replay_sequence(request); replay != 0U) {
      return {TransitionStatus::replay, lease(token.token.ticket_id), replay};
    }
    const auto& current = lease(token.token.ticket_id);
    if (!commitment(token.token.ticket_id).empty()) {
      return {TransitionStatus::committed_noop, current, sequence_};
    }
    const auto expected = timer_token(token.token.ticket_id);
    if (token != expected) {
      return {TransitionStatus::stale_noop, current, sequence_};
    }
    if (logical_tick < current.lease.expiry_tick) {
      return {TransitionStatus::early_noop, current, sequence_};
    }
    auto next = current.lease;
    next.state = "EXPIRED";
    return persist_lease(request, std::move(next), crash_point);
  }

  [[nodiscard]] LeaseTransitionReceipt reassign(
      std::string_view ticket_id,
      std::string_view prior_lease_id,
      std::string new_worker_id,
      std::string new_region_route,
      std::uint64_t logical_tick,
      SchedulingCrashPoint crash_point) {
    const auto request = "reassign:" + std::string(ticket_id) + ":" +
                         std::string(prior_lease_id) + ":" + new_worker_id + ":" +
                         new_region_route + ":" + std::to_string(logical_tick);
    if (const auto replay = replay_sequence(request); replay != 0U) {
      return {TransitionStatus::replay, lease(ticket_id), replay};
    }
    const auto& current = lease(ticket_id);
    require(
        commitment(ticket_id).empty(),
        ErrorCode::ticket_invalid,
        "committed ticket lease cannot be reassigned");
    require(
        current.lease.state == "EXPIRED" && current.content_id == prior_lease_id,
        ErrorCode::ticket_invalid,
        "reassignment does not follow the finalized expired lease");
    require(
        label_valid(new_worker_id) && label_valid(new_region_route),
        ErrorCode::identifier_invalid,
        "reassignment worker or region is invalid");
    require(
        current.lease.lease_epoch + 1U < plan_.lease_policy.maximum_lease_epochs,
        ErrorCode::policy_invalid,
        "maximum lease epoch reached");
    require(
        logical_tick <= std::numeric_limits<std::uint64_t>::max() -
                            plan_.lease_policy.lease_duration_ticks,
        ErrorCode::policy_invalid,
        "reassignment expiry overflows");
    const auto expiry = logical_tick + plan_.lease_policy.lease_duration_ticks;
    require(
        expiry <= plan_.lease_policy.hard_deadline_tick,
        ErrorCode::policy_invalid,
        "reassignment exceeds hard deadline");
    auto next = current.lease;
    next.expiry_tick = expiry;
    next.issue_tick = logical_tick;
    ++next.lease_epoch;
    next.prior_lease_id = current.content_id;
    next.region_route = std::move(new_region_route);
    next.renewal_count = 0U;
    next.state = "ACTIVE";
    next.worker_id = std::move(new_worker_id);
    return persist_lease(request, std::move(next), crash_point);
  }

  [[nodiscard]] CommitReceipt commit(
      std::string_view ticket_id,
      std::string_view worker_id,
      std::uint64_t lease_epoch,
      std::string commitment_id,
      std::uint64_t logical_tick,
      SchedulingCrashPoint crash_point) {
    require(content_id_valid(commitment_id), ErrorCode::identifier_invalid, "commitment ID is invalid");
    const auto request = "commit:" + std::string(ticket_id) + ":" + commitment_id;
    if (const auto replay = replay_sequence(request); replay != 0U) {
      return {TransitionStatus::replay, std::move(commitment_id), replay};
    }
    const auto existing = commitment(ticket_id);
    require(existing.empty(), ErrorCode::ticket_invalid, "conflicting ticket commitment exists");
    const auto& current = lease(ticket_id);
    require(
        current.lease.state == "ACTIVE" && current.lease.worker_id == worker_id &&
            current.lease.lease_epoch == lease_epoch,
        ErrorCode::ticket_invalid,
        "commitment does not match the current active lease");
    require(
        logical_tick <= current.lease.expiry_tick &&
            logical_tick <= plan_.lease_policy.hard_deadline_tick,
        ErrorCode::ticket_invalid,
        "commitment arrived after the lease deadline");
    Event event{
        sequence_ + 1U,
        EventKind::commit,
        request,
        current,
        commitment_id,
    };
    persist_and_apply(event, crash_point);
    return {TransitionStatus::applied, std::move(commitment_id), event.sequence};
  }

  [[nodiscard]] std::uint64_t sequence() const noexcept { return sequence_; }

 private:
  [[nodiscard]] std::uint64_t replay_sequence(std::string_view request) const {
    const auto found = requests_.find(std::string(request));
    return found == requests_.end() ? 0U : found->second;
  }

  [[nodiscard]] LeaseTransitionReceipt persist_lease(
      std::string request,
      TicketLease lease,
      SchedulingCrashPoint crash_point) {
    auto canonical = canonical_ticket_lease(lease);
    LeaseRecord record{std::move(lease), canonical, ticket_lease_content_id(canonical)};
    Event event{
        sequence_ + 1U,
        EventKind::set_lease,
        std::move(request),
        record,
        "",
    };
    persist_and_apply(event, crash_point);
    return {TransitionStatus::applied, std::move(record), event.sequence};
  }

  void persist_and_apply(const Event& event, SchedulingCrashPoint crash_point) {
#if defined(DELTA_SCHEDULING_MUTANT_EXPOSE_BEFORE_DURABILITY)
    apply_event(event, false);
#endif
    if (crash_point == SchedulingCrashPoint::before_wal_append) {
      reject(ErrorCode::canonical_json_invalid, "simulated crash before scheduling WAL append");
    }
    const auto encoded = encode_event(event);
    append_file(journal_path_, encoded);
    if (crash_point == SchedulingCrashPoint::after_durability_before_apply) {
      reject(ErrorCode::canonical_json_invalid, "simulated crash after scheduling WAL durability");
    }
#if !defined(DELTA_SCHEDULING_MUTANT_EXPOSE_BEFORE_DURABILITY)
    apply_event(event, false);
#endif
  }

  void apply_event(const Event& event, bool recovery) {
    require(
        event.sequence == sequence_ + 1U,
        ErrorCode::canonical_json_invalid,
        "scheduling journal sequence is invalid");
    require(
        !event.request_id.empty() && !requests_.contains(event.request_id),
        ErrorCode::canonical_json_invalid,
        "scheduling journal request is empty or duplicated");
    const auto ticket = std::lower_bound(
        plan_.tickets.begin(),
        plan_.tickets.end(),
        event.lease.lease.ticket_id,
        [](const auto& item, const auto& id) { return item.ticket.ticket_id < id; });
    require(
        ticket != plan_.tickets.end() && ticket->ticket.ticket_id == event.lease.lease.ticket_id &&
            event.lease.lease.ticket_content_id == ticket->content_id &&
            event.lease.lease.plan_id == plan_.content_id &&
            event.lease.canonical_bytes == canonical_ticket_lease(event.lease.lease) &&
            event.lease.content_id == ticket_lease_content_id(event.lease.canonical_bytes),
        ErrorCode::canonical_json_invalid,
        "scheduling journal lease does not match the ticket plan");
    if (event.kind == EventKind::set_lease) {
      require(
          event.commitment_id.empty(),
          ErrorCode::canonical_json_invalid,
          "lease event contains a commitment");
      if (!leases_.contains(event.lease.lease.ticket_id)) {
        const auto initial = initial_.find(event.lease.lease.ticket_id);
        require(
            initial != initial_.end() && initial->second == event.lease,
            ErrorCode::canonical_json_invalid,
            "initial journal lease differs from configured lease");
      } else if (recovery) {
        validate_recovered_transition(leases_.at(event.lease.lease.ticket_id), event.lease);
      }
      leases_[event.lease.lease.ticket_id] = event.lease;
    } else {
      require(
          content_id_valid(event.commitment_id) &&
              leases_.contains(event.lease.lease.ticket_id) &&
              leases_.at(event.lease.lease.ticket_id) == event.lease &&
              event.lease.lease.state == "ACTIVE" &&
              !commitments_.contains(event.lease.lease.ticket_id),
          ErrorCode::canonical_json_invalid,
          "recovered commitment is inconsistent with lease state");
      commitments_[event.lease.lease.ticket_id] = event.commitment_id;
    }
    requests_[event.request_id] = event.sequence;
    sequence_ = event.sequence;
  }

  void validate_recovered_transition(
      const LeaseRecord& prior,
      const LeaseRecord& next) const {
    require(
        prior.lease.ticket_id == next.lease.ticket_id &&
            prior.lease.ticket_content_id == next.lease.ticket_content_id &&
            prior.lease.plan_id == next.lease.plan_id &&
            prior.lease.round_config_id == next.lease.round_config_id,
        ErrorCode::canonical_json_invalid,
        "recovered lease mutated immutable ticket context");
    auto expired = prior.lease;
    expired.state = "EXPIRED";
    const bool expiry = prior.lease.state == "ACTIVE" && next.lease == expired;
    auto renewed = prior.lease;
    renewed.expiry_tick += plan_.lease_policy.lease_duration_ticks;
    ++renewed.renewal_count;
    const bool renewal =
        prior.lease.state == "ACTIVE" && next.lease == renewed &&
        renewed.renewal_count <= plan_.lease_policy.maximum_renewals &&
        renewed.expiry_tick <= plan_.lease_policy.hard_deadline_tick;
    const bool reassignment = prior.lease.state == "EXPIRED" && next.lease.state == "ACTIVE" &&
                              next.lease.lease_epoch == prior.lease.lease_epoch + 1U &&
                              next.lease.prior_lease_id == prior.content_id &&
                              next.lease.renewal_count == 0U &&
                              next.lease.issue_tick + plan_.lease_policy.lease_duration_ticks ==
                                  next.lease.expiry_tick &&
                              next.lease.expiry_tick <= plan_.lease_policy.hard_deadline_tick;
    require(
        expiry || renewal || reassignment,
        ErrorCode::canonical_json_invalid,
        "recovered lease transition is illegal");
  }

  void recover() {
    const auto bytes = read_file(journal_path_);
    std::size_t cursor = 0U;
    while (cursor < bytes.size()) {
      require(
          bytes.size() - cursor >= 8U,
          ErrorCode::canonical_json_invalid,
          "scheduling journal has a partial header");
      Reader header(std::span<const std::byte>(bytes.data(), bytes.size()).subspan(cursor, 8U));
      require(equal_magic(header.take(4U)), ErrorCode::canonical_json_invalid, "journal magic mismatch");
      const auto length = static_cast<std::size_t>(header.u32());
      require(
          length <= maximum_frame_size && length <= bytes.size() - cursor,
          ErrorCode::canonical_json_invalid,
          "scheduling journal frame is truncated");
      const auto event = decode_event(
          std::span<const std::byte>(bytes.data(), bytes.size()).subspan(cursor, length));
      apply_event(event, true);
      cursor += length;
    }
    require(
        leases_.size() == initial_.size(),
        ErrorCode::canonical_json_invalid,
        "recovered journal lacks initial leases");
  }

  std::filesystem::path directory_;
  std::filesystem::path journal_path_;
  RoundTicketPlan plan_;
  std::map<std::string, LeaseRecord> initial_;
  std::map<std::string, LeaseRecord> leases_;
  std::map<std::string, std::string> commitments_;
  std::map<std::string, std::uint64_t> requests_;
  std::uint64_t sequence_ = 0U;
};

LeaseStateMachine::LeaseStateMachine(
    std::filesystem::path directory,
    RoundTicketPlan plan,
    std::vector<LeaseRecord> initial_leases)
    : impl_(std::make_unique<Impl>(
          std::move(directory), std::move(plan), std::move(initial_leases))) {}

LeaseStateMachine::~LeaseStateMachine() = default;

TimerTokenRecord LeaseStateMachine::timer_token(std::string_view ticket_id) const {
  return impl_->timer_token(ticket_id);
}

LeaseTransitionReceipt LeaseStateMachine::renew(
    std::string_view ticket_id,
    std::string_view worker_id,
    std::uint64_t lease_epoch,
    std::uint64_t expected_renewal_count,
    std::uint64_t logical_tick,
    SchedulingCrashPoint crash_point) {
  return impl_->renew(
      ticket_id, worker_id, lease_epoch, expected_renewal_count, logical_tick, crash_point);
}

LeaseTransitionReceipt LeaseStateMachine::expire(
    const TimerTokenRecord& token,
    std::uint64_t logical_tick,
    SchedulingCrashPoint crash_point) {
  return impl_->expire(token, logical_tick, crash_point);
}

LeaseTransitionReceipt LeaseStateMachine::reassign(
    std::string_view ticket_id,
    std::string_view prior_lease_id,
    std::string new_worker_id,
    std::string new_region_route,
    std::uint64_t logical_tick,
    SchedulingCrashPoint crash_point) {
  return impl_->reassign(
      ticket_id,
      prior_lease_id,
      std::move(new_worker_id),
      std::move(new_region_route),
      logical_tick,
      crash_point);
}

CommitReceipt LeaseStateMachine::commit(
    std::string_view ticket_id,
    std::string_view worker_id,
    std::uint64_t lease_epoch,
    std::string commitment_id,
    std::uint64_t logical_tick,
    SchedulingCrashPoint crash_point) {
  return impl_->commit(
      ticket_id,
      worker_id,
      lease_epoch,
      std::move(commitment_id),
      logical_tick,
      crash_point);
}

const LeaseRecord& LeaseStateMachine::lease(std::string_view ticket_id) const {
  return impl_->lease(ticket_id);
}

std::string LeaseStateMachine::commitment(std::string_view ticket_id) const {
  return impl_->commitment(ticket_id);
}

std::uint64_t LeaseStateMachine::journal_sequence() const noexcept {
  return impl_->sequence();
}

std::vector<std::byte> canonical_lease_timer_token(const LeaseTimerToken& token) {
  std::string output{"{"};
  append_field(output, "effect_kind", quote(token.effect_kind));
  append_field(output, "expiry_tick", std::to_string(token.expiry_tick));
  append_field(output, "formal_semantics_id", quote(formal_semantics_id));
  append_field(output, "lease_epoch", std::to_string(token.lease_epoch));
  append_field(output, "lease_id", quote(token.lease_id));
  append_field(output, "plan_id", quote(token.plan_id));
  append_field(output, "round_config_id", quote(token.round_config_id));
  append_field(output, "schema_version", quote(schema_version));
  append_field(output, "ticket_id", quote(token.ticket_id));
  append_field(output, "token_nonce", quote(token.token_nonce));
  append_field(output, "type_name", quote("LEASE_TIMER_TOKEN"));
  append_field(output, "worker_id", quote(token.worker_id));
  output.push_back('}');
  return bytes(std::move(output));
}

std::string lease_timer_token_content_id(std::span<const std::byte> canonical_json) {
  return content_id_for("deltareduce.007.lease-timer-token.v1", canonical_json);
}

}  // namespace delta::scheduling
