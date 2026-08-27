#include <delta_abi.h>

_Static_assert(sizeof(void*) == 8, "DeltaReduce ABI v1 requires a 64-bit process");
_Static_assert(sizeof(delta_bytes_view_t) == 16, "byte view layout changed");
_Static_assert(sizeof(delta_output_buffer_t) == DELTA_ABI_OUTPUT_BUFFER_SIZE,
               "output buffer layout changed");
_Static_assert(sizeof(delta_runtime_descriptor_t) == DELTA_ABI_DESCRIPTOR_SIZE,
               "descriptor layout changed");
_Static_assert(sizeof(delta_runtime_open_options_t) == DELTA_ABI_OPEN_OPTIONS_SIZE,
               "open options layout changed");
_Static_assert(DELTA_STATUS_OK == 0, "status taxonomy changed");
_Static_assert(DELTA_STATUS_INTERNAL_ERROR == 14, "status taxonomy changed");

int delta_abi_header_c_smoke(void) {
  delta_runtime_t* runtime = 0;
  delta_runtime_descriptor_t descriptor = {0};
  return runtime == 0 && descriptor.struct_size == 0 ? 0 : 1;
}
