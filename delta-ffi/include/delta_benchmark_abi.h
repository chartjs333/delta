#ifndef DELTA_BENCHMARK_ABI_H
#define DELTA_BENCHMARK_ABI_H

#include <delta_abi.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DELTA_BENCHMARK_ABI_MAJOR UINT16_C(1)
#define DELTA_BENCHMARK_ABI_MINOR UINT16_C(0)
#define DELTA_BENCHMARK_METRICS_V1_SIZE UINT32_C(80)

typedef struct delta_benchmark_metrics_v1 {
  uint32_t struct_size;
  uint32_t reserved;
  uint64_t java_queue_us;
  uint64_t boundary_us;
  uint64_t native_transition_us;
  uint64_t wal_us;
  uint64_t network_us;
  uint64_t artifact_us;
  uint64_t zero_copy_eligible;
  uint64_t zero_copy_hits;
  uint64_t copy_fallback_bytes;
} delta_benchmark_metrics_v1_t;

DELTA_API delta_status_t delta_benchmark_metrics_canonical(
    const delta_benchmark_metrics_v1_t* metrics,
    delta_output_buffer_t* output);

DELTA_API delta_status_t delta_benchmark_sidecar_echo(
    delta_bytes_view_t request,
    size_t maximum_payload_bytes,
    delta_output_buffer_t* output);

#ifdef __cplusplus
}
#endif

#endif
