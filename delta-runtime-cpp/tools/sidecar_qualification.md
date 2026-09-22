# Sidecar qualification helpers

These helpers are test-only and are not part of the production C ABI. Build
them explicitly with:

```text
-DDELTA_BUILD_SIDECAR_QUALIFICATION=ON
```

The option is `OFF` by default. It produces:

- `delta_sidecar_qualification_probe`, a shared library exposing only
  `delta_sidecar_qualification_crash_v1` from
  `sidecar_qualification_probe.h`. A child JVM may call the symbol through FFM
  to exercise the paired native cuts or the post-native-return/pre-Java-send
  cut. The call always terminates that child process; exit code 86 means the
  requested cut was reached, 87 means setup or validation failed, and 88 means
  a selected cut unexpectedly returned.
- `delta_sidecar_durable_inspector`, invoked as
  `--directory PATH --initial-state-file FILE` with an optional
  `--retry-command-file FILE`. It prints one deterministic single-line JSON
  record. The recovered sequence, state, and WAL digest/size are all captured
  before the optional retry so the record exposes what actually persisted at
  the injected cut.
- On Linux only, `delta_sidecar_qualification_fsync_interposer`, an
  `LD_PRELOAD` library for the exact `after_wal_append_before_durability` cut.
  It intercepts `fsync` and `fdatasync`, verifies by device and inode that the
  descriptor is the configured `runtime.wal`, and calls `_exit(86)` before the
  real durability syscall after the versioned qualification hook explicitly
  arms the one-shot cut. Unrelated descriptors and pre-arm WAL synchronization
  pass through by direct Linux syscalls.

The runtime's legacy crash-point enum named
`after_wal_append_before_durability` fires before the append. Qualification
point 3 therefore deliberately submits with `Runtime::CrashPoint::none` and
requires the Linux interposer. The child must be launched with an absolute WAL
path, for example:

```text
DELTA_SIDECAR_QUALIFICATION_FSYNC_TARGET=/tmp/delta-case/runtime.wal \
LD_PRELOAD=/build/libdelta_sidecar_qualification_fsync_interposer.so \
<child JVM or qualification probe driver using crash point 3>
```

The probe resolves a weak, versioned arm hook from the preload library and
enables the cut for exactly `<probe directory>/runtime.wal` before it constructs
`Runtime`. Missing preload or a mismatched target exits 87 without a native
submission. For an isolated-sidecar process, use the same environment and the
`after-wal-append-before-durability` fault option. Its OPEN preflight may safely
create and synchronize the WAL name before the server arms the interposer at
SUBMIT admission.

This injection proves the process-order boundary after `fwrite` plus `fflush`
and before entry to `fsync`; it is not a physical power-loss simulator. The
complete unsynced frame normally remains visible in the kernel page cache after
process exit and may be recovered on immediate restart.

The inspector is recovery-only when no retry command is supplied, but it is not
filesystem-read-only: constructing `Runtime` may truncate a torn WAL tail as
part of normal recovery. With `--retry-command-file`, the exact retry may also
append when the inspected command was not durable at the injected cut.

With `BUILD_TESTING=ON` on Linux, the small
`delta_sidecar.qualification_fsync_interposer` CTest launches point 3 under
`LD_PRELOAD`, requires exit 86, then verifies that the complete frame recovers
and the exact retry is reported as a native replay.
