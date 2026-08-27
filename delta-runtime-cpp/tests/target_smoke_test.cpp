#include <delta/core/canonical.hpp>

int main() {
  using delta::core::canonical::Type;
  return Type::round_config == static_cast<Type>(1) ? 0 : 1;
}
