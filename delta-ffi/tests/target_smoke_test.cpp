#include <delta/core/canonical.hpp>

int main() {
  using delta::core::canonical::Type;
  return Type::runtime_descriptor == static_cast<Type>(9) ? 0 : 1;
}
