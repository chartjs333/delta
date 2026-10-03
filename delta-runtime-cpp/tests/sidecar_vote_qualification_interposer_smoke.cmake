if(NOT DEFINED SMOKE_EXECUTABLE OR
   NOT DEFINED INTERPOSER_LIBRARY OR
   NOT DEFINED SMOKE_DIRECTORY)
  message(FATAL_ERROR "vote qualification interposer smoke arguments are incomplete")
endif()

file(REMOVE_RECURSE "${SMOKE_DIRECTORY}")
file(MAKE_DIRECTORY "${SMOKE_DIRECTORY}")
set(runtime_wal "${SMOKE_DIRECTORY}/runtime.wal")

set(unarmed_directory "${SMOKE_DIRECTORY}-unarmed")
file(REMOVE_RECURSE "${unarmed_directory}")
file(MAKE_DIRECTORY "${unarmed_directory}")
execute_process(
  COMMAND "${SMOKE_EXECUTABLE}" crash "${unarmed_directory}"
  RESULT_VARIABLE unarmed_result
  OUTPUT_VARIABLE unarmed_stdout
  ERROR_VARIABLE unarmed_stderr)
if(NOT unarmed_result EQUAL 87)
  message(
    FATAL_ERROR
    "vote pre-durability cut did not fail closed without preload: result=${unarmed_result}; stdout=${unarmed_stdout}; stderr=${unarmed_stderr}")
endif()
if(EXISTS "${unarmed_directory}/runtime.wal")
  message(FATAL_ERROR "unarmed vote pre-durability cut opened runtime.wal")
endif()

set(mismatch_directory "${SMOKE_DIRECTORY}-mismatch")
file(REMOVE_RECURSE "${mismatch_directory}")
file(MAKE_DIRECTORY "${mismatch_directory}")
execute_process(
  COMMAND
    "${CMAKE_COMMAND}" -E env
    "LD_PRELOAD=${INTERPOSER_LIBRARY}"
    "DELTA_SIDECAR_QUALIFICATION_FSYNC_TARGET=${runtime_wal}"
    "${SMOKE_EXECUTABLE}" crash "${mismatch_directory}"
  RESULT_VARIABLE mismatch_result
  OUTPUT_VARIABLE mismatch_stdout
  ERROR_VARIABLE mismatch_stderr)
if(NOT mismatch_result EQUAL 87)
  message(
    FATAL_ERROR
    "vote pre-durability cut accepted a mismatched preload target: result=${mismatch_result}; stdout=${mismatch_stdout}; stderr=${mismatch_stderr}")
endif()
if(EXISTS "${mismatch_directory}/runtime.wal")
  message(FATAL_ERROR "mismatched vote pre-durability cut opened runtime.wal")
endif()

execute_process(
  COMMAND
    "${CMAKE_COMMAND}" -E env
    "LD_PRELOAD=${INTERPOSER_LIBRARY}"
    "DELTA_SIDECAR_QUALIFICATION_FSYNC_TARGET=${runtime_wal}"
    "${SMOKE_EXECUTABLE}" crash "${SMOKE_DIRECTORY}"
  RESULT_VARIABLE crash_result
  OUTPUT_VARIABLE crash_stdout
  ERROR_VARIABLE crash_stderr)
if(NOT crash_result EQUAL 86)
  message(
    FATAL_ERROR
    "vote interposer did not exit at the real post-append/pre-fsync cut: result=${crash_result}; stdout=${crash_stdout}; stderr=${crash_stderr}")
endif()
if(NOT EXISTS "${runtime_wal}")
  message(FATAL_ERROR "vote pre-durability cut did not leave runtime.wal")
endif()
file(SIZE "${runtime_wal}" wal_size)
if(wal_size EQUAL 0)
  message(FATAL_ERROR "vote pre-durability cut left an empty runtime.wal")
endif()

execute_process(
  COMMAND "${SMOKE_EXECUTABLE}" inspect "${SMOKE_DIRECTORY}"
  RESULT_VARIABLE inspect_result
  OUTPUT_VARIABLE inspect_stdout
  ERROR_VARIABLE inspect_stderr)
if(NOT inspect_result EQUAL 0)
  message(
    FATAL_ERROR
    "vote pre-durability recovery inspection failed: result=${inspect_result}; stderr=${inspect_stderr}")
endif()
string(STRIP "${inspect_stdout}" inspect_json)
if(NOT inspect_json MATCHES "\"recovered_durable_sequence\":1")
  message(FATAL_ERROR "vote real-cut frame did not recover at sequence one: ${inspect_json}")
endif()
if(NOT inspect_json MATCHES "\"recovered_vote_count\":1")
  message(FATAL_ERROR "vote real-cut frame was lost or duplicated: ${inspect_json}")
endif()
if(NOT inspect_json MATCHES "\"native_replay\":true")
  message(FATAL_ERROR "vote real-cut retry was not a native replay: ${inspect_json}")
endif()
if(NOT inspect_json MATCHES "\"canonical_receipt_sha256\":\"sha256:[0-9a-f]+\"")
  message(FATAL_ERROR "vote real-cut canonical receipt evidence is absent: ${inspect_json}")
endif()

message(STATUS "qualification vote fsync interposer smoke passed: ${inspect_json}")
