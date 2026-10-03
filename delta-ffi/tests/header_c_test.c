#include <delta_abi.h>

_Static_assert(sizeof(void*) == 8, "DeltaReduce ABI v1 requires a 64-bit process");
_Static_assert(sizeof(delta_bytes_view_t) == 16, "byte view layout changed");
_Static_assert(sizeof(delta_output_buffer_t) == DELTA_ABI_OUTPUT_BUFFER_SIZE,
               "output buffer layout changed");
_Static_assert(sizeof(delta_runtime_descriptor_t) == DELTA_ABI_DESCRIPTOR_SIZE,
               "descriptor layout changed");
_Static_assert(sizeof(delta_runtime_open_options_t) == DELTA_ABI_OPEN_OPTIONS_SIZE,
               "open options layout changed");
_Static_assert(sizeof(delta_vote_receipt_v1_t) == DELTA_VOTE_RECEIPT_V1_SIZE,
               "opaque vote receipt layout changed");
_Static_assert(sizeof(delta_submit_receipt_v1_t) == DELTA_SUBMIT_RECEIPT_V1_SIZE,
               "submit receipt layout changed");
_Static_assert(offsetof(delta_submit_receipt_v1_t, struct_size) == 0,
               "submit receipt struct-size offset changed");
_Static_assert(offsetof(delta_submit_receipt_v1_t, reserved) == 4,
               "submit receipt reserved offset changed");
_Static_assert(offsetof(delta_submit_receipt_v1_t, journal_sequence) == 8,
               "submit receipt sequence offset changed");
_Static_assert(offsetof(delta_submit_receipt_v1_t, canonical_effect) == 16,
               "submit receipt effect offset changed");
_Static_assert((DELTA_ABI_FEATURE_BITS & DELTA_ABI_FEATURE_RECORD_VOTE_V1) != 0,
               "record-vote feature bit is not advertised");
_Static_assert((DELTA_ABI_FEATURE_BITS & DELTA_ABI_FEATURE_SUBMIT_RECEIPT_V1) != 0,
               "submit-receipt feature bit is not advertised");
_Static_assert(DELTA_STATUS_OK == 0, "status taxonomy changed");
_Static_assert(DELTA_STATUS_INTERNAL_ERROR == 14, "status taxonomy changed");

int delta_abi_header_c_smoke(void) {
  delta_runtime_t* runtime = 0;
  delta_runtime_descriptor_t descriptor = {0};
  return runtime == 0 && descriptor.struct_size == 0 ? 0 : 1;
}
