if(NOT DEFINED SIDECAR_EXECUTABLE)
  message(FATAL_ERROR "SIDECAR_EXECUTABLE is required")
endif()

execute_process(
  COMMAND
    "${SIDECAR_EXECUTABLE}"
    --session 11111111111111111111111111111111
    --generation 1
    --fault before-wal-append
  RESULT_VARIABLE sidecar_result
  OUTPUT_VARIABLE sidecar_stdout
  ERROR_VARIABLE sidecar_stderr)

if(NOT sidecar_result EQUAL 2)
  message(FATAL_ERROR
    "production sidecar did not reject --fault: result=${sidecar_result}; stdout=${sidecar_stdout}; stderr=${sidecar_stderr}")
endif()

if(NOT sidecar_stderr MATCHES
    "usage: delta_runtime_sidecar --session <hex128> --generation <u64>")
  message(FATAL_ERROR
    "production sidecar exposed qualification CLI syntax: ${sidecar_stderr}")
endif()

if(sidecar_stderr MATCHES "\\[--fault")
  message(FATAL_ERROR
    "production sidecar usage advertises qualification-only --fault: ${sidecar_stderr}")
endif()

if(NOT WIN32)
  execute_process(
    COMMAND
      "${SIDECAR_EXECUTABLE}"
      --session 11111111111111111111111111111111
      --generation 1
    RESULT_VARIABLE missing_identity_result
    OUTPUT_VARIABLE missing_identity_stdout
    ERROR_VARIABLE missing_identity_stderr)

  if(NOT missing_identity_result EQUAL 2)
    message(FATAL_ERROR
      "production POSIX sidecar accepted missing durable identity: result=${missing_identity_result}; stdout=${missing_identity_stdout}; stderr=${missing_identity_stderr}")
  endif()

  if(NOT missing_identity_stderr MATCHES
      "durable device and inode are required on POSIX")
    message(FATAL_ERROR
      "production POSIX sidecar returned the wrong missing-identity failure: ${missing_identity_stderr}")
  endif()
  message(STATUS
    "production sidecar rejected qualification-only --fault and missing POSIX durable identity")
else()
  message(STATUS "production sidecar rejected qualification-only --fault")
endif()
