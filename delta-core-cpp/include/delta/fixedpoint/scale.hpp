#pragma once

#include <cstdint>

namespace delta::fixedpoint {

struct Rational {
  std::int64_t numerator;
  std::uint32_t denominator;

  bool operator==(const Rational&) const = default;
};

struct Scale {
  std::uint32_t numerator;
  std::uint32_t denominator;

  bool operator==(const Scale&) const = default;
};

void validate_rational(const Rational& value);
void validate_scale(const Scale& value);

}  // namespace delta::fixedpoint
