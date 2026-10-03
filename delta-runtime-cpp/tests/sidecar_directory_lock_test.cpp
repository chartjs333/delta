#include <delta/runtime/sidecar_directory_lock.hpp>

#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <type_traits>
#include <utility>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <unistd.h>
#endif

namespace {

namespace sidecar = delta::runtime::sidecar;

static_assert(!std::is_copy_constructible_v<sidecar::DurableDirectoryLock>);
static_assert(!std::is_copy_assignable_v<sidecar::DurableDirectoryLock>);
static_assert(!std::is_move_constructible_v<sidecar::DurableDirectoryLock>);
static_assert(!std::is_move_assignable_v<sidecar::DurableDirectoryLock>);

[[noreturn]] void fail(std::string message) {
  throw std::runtime_error(std::move(message));
}

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

[[nodiscard]] unsigned long process_id() noexcept {
#if defined(_WIN32)
  return GetCurrentProcessId();
#else
  return static_cast<unsigned long>(::getpid());
#endif
}

[[nodiscard]] std::filesystem::path fresh_root() {
  const auto root = std::filesystem::temp_directory_path() /
                    "delta-sidecar-directory-lock-tests" /
                    std::to_string(process_id());
  std::error_code error;
  std::filesystem::remove_all(root, error);
  expect(!error, "cannot clean sidecar lock test root");
  std::filesystem::create_directories(root, error);
  expect(!error, "cannot create sidecar lock test root");
  return root;
}

template <typename Operation>
void expect_lock_error(
    sidecar::DurableDirectoryLockErrorCode expected_code,
    std::string_view expected_message,
    Operation operation) {
  try {
    operation();
  } catch (const sidecar::DurableDirectoryLockError& error) {
    expect(error.code() == expected_code, "sidecar lock error code differs");
    expect(error.what() == expected_message, "sidecar lock error message differs");
    return;
  }
  fail("expected sidecar directory lock error was not raised");
}

void test_invalid_directory_rejection(const std::filesystem::path& root) {
  expect_lock_error(
      sidecar::DurableDirectoryLockErrorCode::invalid_directory,
      "sidecar durable directory path is invalid",
      [] { sidecar::DurableDirectoryLock lock{std::filesystem::path{}}; });

  const auto missing = root / "missing";
  expect_lock_error(
      sidecar::DurableDirectoryLockErrorCode::directory_not_found,
      "sidecar durable directory does not exist",
      [&missing] { sidecar::DurableDirectoryLock lock(missing); });

  const auto regular_file = root / "regular-file";
  {
    std::ofstream output(regular_file, std::ios::binary);
    expect(output.good(), "cannot create regular-file fixture");
    output << "not-a-directory";
  }
  expect_lock_error(
      sidecar::DurableDirectoryLockErrorCode::not_a_directory,
      "sidecar durable path is not a directory",
      [&regular_file] { sidecar::DurableDirectoryLock lock(regular_file); });
}

void test_exclusive_raii_lock(const std::filesystem::path& root) {
  const auto durable = root / "durable";
  std::error_code error;
  std::filesystem::create_directory(durable, error);
  expect(!error, "cannot create durable lock fixture");

  const auto expected_lock_path =
      durable / std::filesystem::path(sidecar::durable_directory_lock_filename);
  {
    sidecar::DurableDirectoryLock first(durable);
    expect(first.owns_lock(), "first sidecar lock does not own the OS lock");
    expect(first.durable_directory() == durable, "durable directory identity changed");
    expect(first.path() == expected_lock_path, "lock file escaped durable directory");
    expect(std::filesystem::exists(expected_lock_path), "lock file was not created");

    expect_lock_error(
        sidecar::DurableDirectoryLockErrorCode::lock_unavailable,
        "sidecar durable directory is already locked",
        [&durable] { sidecar::DurableDirectoryLock second(durable); });
    expect(first.owns_lock(), "failed contender released the first lock");
  }

  sidecar::DurableDirectoryLock reacquired(durable);
  expect(reacquired.owns_lock(), "RAII destruction did not release the OS lock");
  expect(reacquired.path() == expected_lock_path, "reacquired lock path changed");
}

void test_invalid_lock_file_rejection(const std::filesystem::path& root) {
  const auto durable = root / "invalid-lock-file";
  std::error_code error;
  std::filesystem::create_directory(durable, error);
  expect(!error, "cannot create invalid-lock durable directory");
  std::filesystem::create_directory(
      durable / std::filesystem::path(sidecar::durable_directory_lock_filename),
      error);
  expect(!error, "cannot create invalid lock-file fixture");

  expect_lock_error(
      sidecar::DurableDirectoryLockErrorCode::lock_open_failed,
      "sidecar lock file open failed",
      [&durable] { sidecar::DurableDirectoryLock lock(durable); });

  std::filesystem::remove_all(
      durable / std::filesystem::path(sidecar::durable_directory_lock_filename),
      error);
  expect(!error, "cannot remove invalid lock-file fixture");
  sidecar::DurableDirectoryLock recovered(durable);
  expect(
      recovered.owns_lock(),
      "failed lock-file open leaked the durable-directory lock");
}

void test_runtime_wal_durability_preflight(const std::filesystem::path& root) {
  const auto durable = root / "wal-preflight";
  std::error_code error;
  std::filesystem::create_directory(durable, error);
  expect(!error, "cannot create WAL preflight fixture");

  sidecar::DurableDirectoryLock lock(durable);
  lock.prepare_runtime_wal();
  const auto wal_path =
      durable / std::filesystem::path(sidecar::runtime_wal_filename);
  expect(std::filesystem::is_regular_file(wal_path),
         "WAL preflight did not create a regular runtime.wal");
  expect(std::filesystem::file_size(wal_path) == 0U,
         "fresh WAL preflight created nonempty runtime.wal");

  {
    std::ofstream output(wal_path, std::ios::binary | std::ios::app);
    expect(output.good(), "cannot append WAL preflight sentinel");
    output << "sentinel";
  }
  lock.prepare_runtime_wal();
  expect(std::filesystem::file_size(wal_path) == 8U,
         "repeated WAL preflight truncated existing runtime.wal");
}

void test_invalid_runtime_wal_rejection(const std::filesystem::path& root) {
  const auto durable = root / "invalid-runtime-wal";
  std::error_code error;
  std::filesystem::create_directory(durable, error);
  expect(!error, "cannot create invalid WAL fixture");
  std::filesystem::create_directory(
      durable / std::filesystem::path(sidecar::runtime_wal_filename), error);
  expect(!error, "cannot create invalid runtime.wal fixture");

  sidecar::DurableDirectoryLock lock(durable);
  expect_lock_error(
      sidecar::DurableDirectoryLockErrorCode::lock_operation_failed,
      "sidecar runtime WAL durability preflight failed",
      [&lock] { lock.prepare_runtime_wal(); });
}

#if !defined(_WIN32)
void test_nested_parent_symlink_rejected_on_open(
    const std::filesystem::path& root) {
  const auto real_parent = root / "nested-parent-real";
  const auto linked_parent = root / "nested-parent-link";
  const auto durable = real_parent / "durable";
  std::error_code error;
  std::filesystem::create_directories(durable, error);
  expect(!error, "cannot create nested-parent durable fixture");
  std::filesystem::create_directory_symlink(real_parent, linked_parent, error);
  expect(!error, "cannot create nested-parent symlink fixture");

  const auto configured = linked_parent / "durable";
  expect_lock_error(
      sidecar::DurableDirectoryLockErrorCode::lock_open_failed,
      "sidecar durable directory lock open failed",
      [&configured] { sidecar::DurableDirectoryLock lock(configured); });
  expect(
      !std::filesystem::exists(
          durable / std::filesystem::path(sidecar::durable_directory_lock_filename)),
      "nested-parent symlink open created a lock file in the symlink target");
}

void test_unlinked_lock_file_cannot_bypass_directory_lock(
    const std::filesystem::path& root) {
  const auto durable = root / "unlinked-lock-file";
  std::error_code error;
  std::filesystem::create_directory(durable, error);
  expect(!error, "cannot create unlink lock fixture");

  sidecar::DurableDirectoryLock first(durable);
  const auto lock_path =
      durable / std::filesystem::path(sidecar::durable_directory_lock_filename);
  expect(std::filesystem::remove(lock_path, error), "cannot unlink lock-file fixture");
  expect(!error, "unlink lock-file fixture failed");

  expect_lock_error(
      sidecar::DurableDirectoryLockErrorCode::lock_unavailable,
      "sidecar durable directory is already locked",
      [&durable] { sidecar::DurableDirectoryLock second(durable); });
  expect(first.owns_lock(), "unlink contender released the directory lock");
}

void test_pathname_rebind_fails_closed_before_runtime_io(
    const std::filesystem::path& root) {
  const auto durable = root / "pathname-rebind";
  const auto original = root / "pathname-rebind-original";
  std::error_code error;
  std::filesystem::create_directory(durable, error);
  expect(!error, "cannot create pathname-rebind fixture");

  sidecar::DurableDirectoryLock lock(durable);
  const auto runtime_directory = lock.runtime_directory();
  expect(runtime_directory != durable,
         "POSIX runtime directory did not bind the locked descriptor");

  std::filesystem::rename(durable, original, error);
  expect(!error, "cannot rename locked durable directory fixture");
  std::filesystem::create_directory(durable, error);
  expect(!error, "cannot create replacement durable directory fixture");

  expect_lock_error(
      sidecar::DurableDirectoryLockErrorCode::lock_operation_failed,
      "sidecar durable directory pathname binding changed",
      [&lock] { lock.verify_path_binding(); });
  expect_lock_error(
      sidecar::DurableDirectoryLockErrorCode::lock_operation_failed,
      "sidecar durable directory pathname binding changed",
      [&lock] { lock.prepare_runtime_wal(); });
  const auto original_wal =
      original / std::filesystem::path(sidecar::runtime_wal_filename);
  const auto replacement_wal =
      durable / std::filesystem::path(sidecar::runtime_wal_filename);
  expect(!std::filesystem::exists(original_wal),
         "pathname rebind performed a post-rebind WAL write");
  expect(!std::filesystem::exists(replacement_wal),
         "pathname replacement received the locked runtime WAL");

  expect(std::filesystem::is_directory(runtime_directory),
         "locked descriptor no longer identifies the original directory inode");
  expect(!std::filesystem::exists(replacement_wal),
         "runtime write followed a rebound durable pathname");
}

void test_symlink_substitution_fails_closed(const std::filesystem::path& root) {
  const auto durable = root / "symlink-substitution";
  const auto original = root / "symlink-substitution-original";
  const auto replacement = root / "symlink-substitution-replacement";
  std::error_code error;
  std::filesystem::create_directory(durable, error);
  expect(!error, "cannot create symlink-substitution fixture");
  std::filesystem::create_directory(replacement, error);
  expect(!error, "cannot create symlink replacement fixture");

  sidecar::DurableDirectoryLock lock(durable);
  std::filesystem::rename(durable, original, error);
  expect(!error, "cannot rename symlink-substitution directory");
  std::filesystem::create_directory_symlink(replacement, durable, error);
  expect(!error, "cannot create durable-directory symlink substitution");
  expect_lock_error(
      sidecar::DurableDirectoryLockErrorCode::lock_operation_failed,
      "sidecar durable directory pathname binding changed",
      [&lock] { lock.verify_path_binding(); });
}

void test_same_inode_nested_parent_symlink_back_fails_closed(
    const std::filesystem::path& root) {
  const auto parent = root / "nested-parent-rebind";
  const auto displaced_parent = root / "nested-parent-rebind-original";
  const auto durable = parent / "durable";
  std::error_code error;
  std::filesystem::create_directories(durable, error);
  expect(!error, "cannot create nested-parent rebind fixture");

  sidecar::DurableDirectoryLock lock(durable);
  std::filesystem::rename(parent, displaced_parent, error);
  expect(!error, "cannot rename nested-parent rebind fixture");
  std::filesystem::create_directory_symlink(displaced_parent, parent, error);
  expect(!error, "cannot create same-inode nested-parent symlink-back fixture");

  expect_lock_error(
      sidecar::DurableDirectoryLockErrorCode::lock_operation_failed,
      "sidecar durable directory pathname binding changed",
      [&lock] { lock.verify_path_binding(); });
  expect_lock_error(
      sidecar::DurableDirectoryLockErrorCode::lock_operation_failed,
      "sidecar durable directory pathname binding changed",
      [&lock] { lock.prepare_runtime_wal(); });
  expect(
      !std::filesystem::exists(
          displaced_parent / "durable" /
          std::filesystem::path(sidecar::runtime_wal_filename)),
      "same-inode nested-parent symlink-back received a runtime WAL write");
}

void test_expected_identity_rejects_restart_rebind(
    const std::filesystem::path& root) {
  const auto durable = root / "restart-rebind";
  const auto original = root / "restart-rebind-original";
  std::error_code error;
  std::filesystem::create_directory(durable, error);
  expect(!error, "cannot create restart-rebind fixture");

  sidecar::DurableDirectoryIdentity expected{};
  {
    sidecar::DurableDirectoryLock first(durable);
    expected = first.identity();
  }
  std::filesystem::rename(durable, original, error);
  expect(!error, "cannot rename restart-rebind original");
  std::filesystem::create_directory(durable, error);
  expect(!error, "cannot create restart-rebind replacement");

  expect_lock_error(
      sidecar::DurableDirectoryLockErrorCode::lock_operation_failed,
      "sidecar durable directory identity mismatch",
      [&durable, expected] {
        sidecar::DurableDirectoryLock restarted(durable, expected);
      });
}

void test_recovery_to_ready_wal_substitution_fails_closed(
    const std::filesystem::path& root) {
  const auto durable = root / "recovery-ready-wal-substitution";
  const auto wal =
      durable / std::filesystem::path(sidecar::runtime_wal_filename);
  const auto preflighted = durable / "runtime.wal.preflighted";
  std::error_code error;
  std::filesystem::create_directory(durable, error);
  expect(!error, "cannot create recovery-to-READY substitution fixture");

  sidecar::DurableDirectoryLock lock(durable);
  lock.prepare_runtime_wal();
  const auto pinned_identity = lock.runtime_wal_identity();
  expect(pinned_identity.has_value(), "POSIX preflight did not retain the WAL identity");

  std::filesystem::rename(wal, preflighted, error);
  expect(!error, "cannot displace recovered WAL before READY barrier");
  {
    std::ofstream replacement(wal, std::ios::binary | std::ios::trunc);
    expect(replacement.good(), "cannot create replacement WAL before READY barrier");
  }

  expect_lock_error(
      sidecar::DurableDirectoryLockErrorCode::lock_operation_failed,
      "sidecar runtime WAL binding changed",
      [&lock] { lock.verify_runtime_wal_binding(); });
  expect_lock_error(
      sidecar::DurableDirectoryLockErrorCode::lock_operation_failed,
      "sidecar runtime WAL binding changed",
      [&lock] { lock.prepare_runtime_wal(); });
  expect(
      std::filesystem::file_size(wal) == 0U &&
          std::filesystem::file_size(preflighted) == 0U,
      "post-recovery barrier touched a substituted WAL inode");
}
#endif

}  // namespace

int main() {
  try {
    const auto root = fresh_root();
    test_invalid_directory_rejection(root);
    test_exclusive_raii_lock(root);
    test_invalid_lock_file_rejection(root);
    test_runtime_wal_durability_preflight(root);
    test_invalid_runtime_wal_rejection(root);
#if !defined(_WIN32)
    test_nested_parent_symlink_rejected_on_open(root);
    test_unlinked_lock_file_cannot_bypass_directory_lock(root);
    test_pathname_rebind_fails_closed_before_runtime_io(root);
    test_symlink_substitution_fails_closed(root);
    test_same_inode_nested_parent_symlink_back_fails_closed(root);
    test_expected_identity_rejects_restart_rebind(root);
    test_recovery_to_ready_wal_substitution_fails_closed(root);
#endif
  } catch (const std::exception& error) {
    std::cerr << "sidecar directory lock test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "sidecar directory lock tests passed\n";
  return 0;
}
