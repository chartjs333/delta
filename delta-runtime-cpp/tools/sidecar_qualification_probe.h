#ifndef DELTA_SIDECAR_QUALIFICATION_PROBE_H
#define DELTA_SIDECAR_QUALIFICATION_PROBE_H

#include <stdint.h>

#if defined(_WIN32)
#if defined(DELTA_SIDECAR_QUALIFICATION_BUILD)
#define DELTA_SIDECAR_QUALIFICATION_API __declspec(dllexport)
#else
#define DELTA_SIDECAR_QUALIFICATION_API __declspec(dllimport)
#endif
#else
#define DELTA_SIDECAR_QUALIFICATION_API __attribute__((visibility("default")))
#endif

#if defined(__cplusplus)
#define DELTA_SIDECAR_QUALIFICATION_NOEXCEPT noexcept
extern "C" {
#else
#define DELTA_SIDECAR_QUALIFICATION_NOEXCEPT
#endif

/*
 * This is a test-only FFM surface. It is deliberately separate from delta_abi.h
 * and is available only when DELTA_BUILD_SIDECAR_QUALIFICATION=ON.
 */
#define DELTA_SIDECAR_QUALIFICATION_PROBE_ABI_MAJOR 1U
#define DELTA_SIDECAR_QUALIFICATION_MAX_DIRECTORY_UTF8_BYTES 4096U
#define DELTA_SIDECAR_QUALIFICATION_MAX_CANONICAL_BYTES 16777216U

typedef uint32_t delta_sidecar_qualification_crash_point_t;

enum {
  DELTA_SIDECAR_QUALIFICATION_BEFORE_WAL_APPEND = 1U,
  DELTA_SIDECAR_QUALIFICATION_DURING_WAL_APPEND = 2U,
  DELTA_SIDECAR_QUALIFICATION_AFTER_APPEND_BEFORE_DURABILITY = 3U,
  DELTA_SIDECAR_QUALIFICATION_AFTER_DURABILITY_BEFORE_COMMIT = 4U,
  DELTA_SIDECAR_QUALIFICATION_AFTER_COMMIT_BEFORE_EFFECT_RETURN = 5U,
  DELTA_SIDECAR_QUALIFICATION_AFTER_EFFECT_COPY_BEFORE_RETURN = 6U,
  DELTA_SIDECAR_QUALIFICATION_AFTER_NATIVE_RETURN_BEFORE_JAVA_SEND = 7U
};

/*
 * Opens the native runtime, submits one command at the requested cut, and
 * terminates the calling process. It never returns and never lets an exception
 * cross the C boundary. On Linux, point 3 requires the qualification fsync
 * interposer to be preloaded and armed for the exact runtime.wal path; the
 * probe fails before opening Runtime if that safeguard is absent. Exit 86 means
 * the requested cut was reached; exit 87 means validation/runtime setup failed;
 * exit 88 means a selected cut unexpectedly returned instead of firing.
 */
DELTA_SIDECAR_QUALIFICATION_API void delta_sidecar_qualification_crash_v1(
    const uint8_t* directory_utf8,
    uint64_t directory_utf8_length,
    const uint8_t* initial_state,
    uint64_t initial_state_length,
    const uint8_t* canonical_command,
    uint64_t canonical_command_length,
    delta_sidecar_qualification_crash_point_t crash_point)
    DELTA_SIDECAR_QUALIFICATION_NOEXCEPT;

/*
 * Opens a vote-enabled native runtime, then arms the exact runtime.wal
 * interposer and records one opaque canonical vote. The process must terminate
 * at the real post-append/pre-fsync cut with exit 86. The immutable policy and
 * vote use the production bounded v1 codecs; no test-only vote semantics are
 * introduced.
 */
DELTA_SIDECAR_QUALIFICATION_API void
delta_sidecar_qualification_vote_pre_durability_crash_v1(
    const uint8_t* directory_utf8,
    uint64_t directory_utf8_length,
    const uint8_t* initial_state,
    uint64_t initial_state_length,
    const uint8_t* canonical_vote_policy,
    uint64_t canonical_vote_policy_length,
    const uint8_t* canonical_vote,
    uint64_t canonical_vote_length)
    DELTA_SIDECAR_QUALIFICATION_NOEXCEPT;

#if defined(__cplusplus)
}
#endif

#undef DELTA_SIDECAR_QUALIFICATION_NOEXCEPT

#endif
