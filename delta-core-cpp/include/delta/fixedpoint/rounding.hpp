#pragma once

#include <cstdint>

#include <delta/fixedpoint/scale.hpp>

namespace delta::fixedpoint {

[[nodiscard]] std::int16_t quantize(const Rational& source, const Scale& quantum);

}  // namespace delta::fixedpoint
