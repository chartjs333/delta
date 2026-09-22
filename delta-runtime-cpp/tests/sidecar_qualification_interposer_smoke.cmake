if(NOT DEFINED SMOKE_EXECUTABLE OR
   NOT DEFINED INTERPOSER_LIBRARY OR
   NOT DEFINED INSPECTOR_EXECUTABLE OR
   NOT DEFINED SMOKE_DIRECTORY)
  message(FATAL_ERROR "qualification interposer smoke arguments are incomplete")
endif()

file(REMOVE_RECURSE "${SMOKE_DIRECTORY}")
file(MAKE_DIRECTORY "${SMOKE_DIRECTORY}")
set(runtime_wal "${SMOKE_DIRECTORY}/runtime.wal")

set(unarmed_directory "${SMOKE_DIRECTORY}-unarmed")
file(REMOVE_RECURSE "${unarmed_directory}")
file(MAKE_DIRECTORY "${unarmed_directory}")
execute_process(
  COMMAND "${SMOKE_EXECUTABLE}" "${unarmed_directory}"
  RESULT_VARIABLE unarmed_result
  OUTPUT_VARIABLE unarmed_stdout
  ERROR_VARIABLE unarmed_stderr)
if(NOT unarmed_result EQUAL 87)
  message(
    FATAL_ERROR
    "qualification point 3 did not fail closed without preload: result=${unarmed_result}; stdout=${unarmed_stdout}; stderr=${unarmed_stderr}")
endif()
if(EXISTS "${unarmed_directory}/runtime.wal")
  message(FATAL_ERROR "unarmed qualification point 3 opened runtime.wal")
endif()

set(mismatch_directory "${SMOKE_DIRECTORY}-mismatch")
file(REMOVE_RECURSE "${mismatch_directory}")
file(MAKE_DIRECTORY "${mismatch_directory}")
execute_process(
  COMMAND
    "${CMAKE_COMMAND}" -E env
    "LD_PRELOAD=${INTERPOSER_LIBRARY}"
    "DELTA_SIDECAR_QUALIFICATION_FSYNC_TARGET=${SMOKE_DIRECTORY}/runtime.wal"
    "${SMOKE_EXECUTABLE}" "${mismatch_directory}"
  RESULT_VARIABLE mismatch_result
  OUTPUT_VARIABLE mismatch_stdout
  ERROR_VARIABLE mismatch_stderr)
if(NOT mismatch_result EQUAL 87)
  message(
    FATAL_ERROR
    "qualification point 3 accepted a mismatched preload target: result=${mismatch_result}; stdout=${mismatch_stdout}; stderr=${mismatch_stderr}")
endif()
if(EXISTS "${mismatch_directory}/runtime.wal")
  message(FATAL_ERROR "mismatched qualification point 3 opened runtime.wal")
endif()

execute_process(
  COMMAND
    "${CMAKE_COMMAND}" -E env
    "LD_PRELOAD=${INTERPOSER_LIBRARY}"
    "DELTA_SIDECAR_QUALIFICATION_FSYNC_TARGET=${runtime_wal}"
    "${SMOKE_EXECUTABLE}" "${SMOKE_DIRECTORY}"
  RESULT_VARIABLE crash_result
  OUTPUT_VARIABLE crash_stdout
  ERROR_VARIABLE crash_stderr)
if(NOT crash_result EQUAL 86)
  message(
    FATAL_ERROR
    "qualification interposer did not exit at the exact cut: result=${crash_result}; stdout=${crash_stdout}; stderr=${crash_stderr}")
endif()

if(NOT EXISTS "${runtime_wal}")
  message(FATAL_ERROR "qualification interposer cut did not leave runtime.wal")
endif()
file(SIZE "${runtime_wal}" wal_size)
if(wal_size EQUAL 0)
  message(FATAL_ERROR "qualification interposer cut left an empty runtime.wal")
endif()

execute_process(
  COMMAND
    "${INSPECTOR_EXECUTABLE}"
    --directory "${SMOKE_DIRECTORY}"
    --initial-state-file "${SMOKE_DIRECTORY}/qualification.initial"
    --retry-command-file "${SMOKE_DIRECTORY}/qualification.command"
  RESULT_VARIABLE inspect_result
  OUTPUT_VARIABLE inspect_stdout
  ERROR_VARIABLE inspect_stderr)
if(NOT inspect_result EQUAL 0)
  message(
    FATAL_ERROR
    "qualification durable inspection failed: result=${inspect_result}; stderr=${inspect_stderr}")
endif()
string(STRIP "${inspect_stdout}" inspect_json)
if(NOT inspect_json MATCHES "\"recovered_durable_sequence\":1")
  message(FATAL_ERROR "qualification cut did not recover the complete appended frame: ${inspect_json}")
endif()
if(NOT inspect_json MATCHES "\"native_replay\":true")
  message(FATAL_ERROR "qualification retry was not an exact native replay: ${inspect_json}")
endif()

message(STATUS "qualification fsync interposer smoke passed: ${inspect_json}")
