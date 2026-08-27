#pragma once

#include <condition_variable>
#include <cstddef>
#include <deque>
#include <mutex>
#include <optional>
#include <stdexcept>
#include <utility>

namespace delta::runtime {

template <typename Value>
class BoundedMpscQueue {
 public:
  explicit BoundedMpscQueue(std::size_t capacity) : capacity_(capacity) {
    if (capacity == 0U) {
      throw std::invalid_argument("bounded MPSC capacity must be positive");
    }
  }

  BoundedMpscQueue(const BoundedMpscQueue&) = delete;
  BoundedMpscQueue& operator=(const BoundedMpscQueue&) = delete;

  [[nodiscard]] bool try_push(Value value) {
    {
      std::lock_guard lock(mutex_);
      if (closed_ || queue_.size() == capacity_) {
        return false;
      }
      queue_.push_back(std::move(value));
    }
    available_.notify_one();
    return true;
  }

  [[nodiscard]] std::optional<Value> wait_pop() {
    std::unique_lock lock(mutex_);
    available_.wait(lock, [this] { return closed_ || !queue_.empty(); });
    if (queue_.empty()) {
      return std::nullopt;
    }
    auto value = std::move(queue_.front());
    queue_.pop_front();
    return value;
  }

  void close() noexcept {
    {
      std::lock_guard lock(mutex_);
      closed_ = true;
    }
    available_.notify_all();
  }

  [[nodiscard]] std::size_t size() const noexcept {
    std::lock_guard lock(mutex_);
    return queue_.size();
  }

  [[nodiscard]] std::size_t capacity() const noexcept { return capacity_; }

  [[nodiscard]] bool closed() const noexcept {
    std::lock_guard lock(mutex_);
    return closed_;
  }

 private:
  const std::size_t capacity_;
  mutable std::mutex mutex_;
  std::condition_variable available_;
  std::deque<Value> queue_;
  bool closed_ = false;
};

}  // namespace delta::runtime
