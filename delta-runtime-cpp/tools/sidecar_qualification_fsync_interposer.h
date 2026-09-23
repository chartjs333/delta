#ifndef DELTA_SIDECAR_QUALIFICATION_FSYNC_INTERPOSER_H
#define DELTA_SIDECAR_QUALIFICATION_FSYNC_INTERPOSER_H

#include <stdint.h>

#define DELTA_SIDECAR_QUALIFICATION_FSYNC_TARGET_ENV \
  "DELTA_SIDECAR_QUALIFICATION_FSYNC_TARGET"

#if defined(__linux__)
#if defined(DELTA_SIDECAR_QUALIFICATION_FSYNC_INTERPOSER_BUILD)
#define DELTA_SIDECAR_QUALIFICATION_FSYNC_INTERPOSER_API \
  __attribute__((visibility("default")))
#else
#define DELTA_SIDECAR_QUALIFICATION_FSYNC_INTERPOSER_API __attribute__((weak))
#endif
#else
#define DELTA_SIDECAR_QUALIFICATION_FSYNC_INTERPOSER_API
#endif

#if defined(__cplusplus)
#define DELTA_SIDECAR_QUALIFICATION_FSYNC_INTERPOSER_NOEXCEPT noexcept
extern "C" {
#else
#define DELTA_SIDECAR_QUALIFICATION_FSYNC_INTERPOSER_NOEXCEPT
#endif

/*
 * Returns one only when the preload library is configured for the exact
 * absolute runtime.wal path supplied by the qualification probe.
 */
DELTA_SIDECAR_QUALIFICATION_FSYNC_INTERPOSER_API uint32_t
delta_sidecar_qualification_fsync_interposer_armed_v1(
    const uint8_t* expected_runtime_wal_utf8,
    uint64_t expected_runtime_wal_utf8_length)
    DELTA_SIDECAR_QUALIFICATION_FSYNC_INTERPOSER_NOEXCEPT;

/* Validates the exact target and enables the one-shot crash at its next barrier. */
DELTA_SIDECAR_QUALIFICATION_FSYNC_INTERPOSER_API uint32_t
delta_sidecar_qualification_fsync_interposer_arm_v1(
    const uint8_t* expected_runtime_wal_utf8,
    uint64_t expected_runtime_wal_utf8_length)
    DELTA_SIDECAR_QUALIFICATION_FSYNC_INTERPOSER_NOEXCEPT;

#if defined(__cplusplus)
}
#endif

#undef DELTA_SIDECAR_QUALIFICATION_FSYNC_INTERPOSER_NOEXCEPT

#endif
