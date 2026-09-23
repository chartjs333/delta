// Independent amendment-0001 arithmetic oracle. Not linked into delta-core/runtime.
#include <cstdint>
#include <iostream>
#include <limits>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using I = __int128_t;
using U = __uint128_t;
void need(bool yes) { if (!yes) throw std::runtime_error("REJECT"); }
I bound(I x, int bits) {
  need(bits == 64 || bits == 128);
  if (bits == 64) need(x >= std::numeric_limits<std::int64_t>::min() &&
                       x <= std::numeric_limits<std::int64_t>::max());
  return x;
}
I add(I a, I b, int bits = 64) {
  I out; need(!__builtin_add_overflow(a, b, &out)); return bound(out, bits);
}
I sub(I a, I b, int bits = 64) {
  I out; need(!__builtin_sub_overflow(a, b, &out)); return bound(out, bits);
}
I mul(I a, I b, int bits = 64) {
  I out; need(!__builtin_mul_overflow(a, b, &out)); return bound(out, bits);
}
I number(std::istream& in) {
  std::string token; need(bool(in >> token));
  bool negative = token[0] == '-';
  std::size_t first = negative ? 1 : 0;
  need(first < token.size());
  need(token[first] != '0' || (token.size() == 1 && !negative));
  U limit = (U{1} << 127) - (negative ? 0 : 1), value = 0;
  for (std::size_t i = first; i < token.size(); ++i) {
    need(token[i] >= '0' && token[i] <= '9');
    unsigned digit = static_cast<unsigned>(token[i] - '0');
    need(value <= (limit - digit) / 10); value = value * 10 + digit;
  }
  if (!negative) return static_cast<I>(value);
  return -static_cast<I>(value - 1) - 1;
}
std::string decimal(I value) {
  if (!value) return "0";
  bool negative = value < 0;
  U magnitude = negative ? static_cast<U>(-(value + 1)) + 1 : static_cast<U>(value);
  std::string text;
  while (magnitude) { text.insert(text.begin(), static_cast<char>('0' + magnitude % 10)); magnitude /= 10; }
  return negative ? "-" + text : text;
}
I round_value(I n, I d) {
  need(d > 0);
  I q = n / d, r = n % d;
  if (r < 0) { q -= 1; r += d; }
  return r < d - r ? q : add(q, 1, 128);
}
struct Fraction { I a, b; };
Fraction fraction(std::istream& in, bool positive = false) {
  I a = bound(number(in), 64), b = bound(number(in), 64);
  need(a >= 0 && b > 0 && (!positive || a > 0));
  need(std::gcd(static_cast<std::uint64_t>(a), static_cast<std::uint64_t>(b)) == 1);
  return {a, b};
}
I scaled(I value, Fraction coefficient) {
  return bound(round_value(mul(value, coefficient.a), coefficient.b), 64);
}
int count(std::istream& in) { I n = number(in); need(n > 0 && n <= 4096); return static_cast<int>(n); }
std::string execute(std::istream& in) {
  std::string operation; need(bool(in >> operation));
  if (operation == "R") {
    I n = number(in), d = number(in); return decimal(round_value(n, d));
  }
  if (operation == "D") {
    I raw_bits = number(in); need(raw_bits == 64 || raw_bits == 128);
    int bits = static_cast<int>(raw_bits);
    I n = bound(number(in), bits), d = bound(number(in), bits); need(d > 0);
    auto q = fraction(in, true), model = fraction(in, true);
    I denominator = mul(mul(d, q.b, bits), model.a, bits);
    I numerator = mul(mul(n, q.a, bits), model.b, bits);
    return decimal(bound(round_value(numerator, denominator), 64));
  }
  if (operation == "P") {
    I raw_bits = number(in); need(raw_bits == 64 || raw_bits == 128);
    int bits = static_cast<int>(raw_bits);
    I d = bound(number(in), bits); need(d > 0);
    int terms = count(in); I sum = 0, coefficients = 0;
    for (int i = 0; i < terms; ++i) {
      auto weight = fraction(in); I q = bound(number(in), 64);
      need(d % weight.b == 0);
      I coefficient = mul(weight.a, d / weight.b, bits);
      coefficients = add(coefficients, coefficient, bits);
      sum = add(sum, mul(coefficient, q, bits), bits);
    }
    return decimal(sum);
  }
  if (operation == "A") {
    I theta = bound(number(in), 64), momentum = bound(number(in), 64);
    int domains = count(in); I denominator = 1;
    std::vector<I> gradients; std::vector<Fraction> weights;
    for (int i = 0; i < domains; ++i) {
      gradients.push_back(bound(number(in), 64)); auto weight = fraction(in);
      weights.push_back(weight);
      auto divisor = std::gcd(static_cast<std::uint64_t>(denominator), static_cast<std::uint64_t>(weight.b));
      denominator = mul(denominator / divisor, weight.b);
    }
    auto lr = fraction(in), mu = fraction(in), wd = fraction(in);
    I total = 0, weight_sum = 0;
    for (int i = 0; i < domains; ++i) {
      I multiplier = denominator / weights[i].b;
      weight_sum = add(weight_sum, mul(weights[i].a, multiplier));
      total = add(total, mul(mul(gradients[i], weights[i].a), multiplier));
    }
    need(weight_sum == denominator);
    I g = bound(round_value(total, denominator), 64);
    I next_m = add(scaled(momentum, mu), g);
    I direction = add(scaled(next_m, mu), g);
    I step = scaled(add(direction, scaled(theta, wd)), lr);
    I next = sub(theta, step);
    return decimal(next) + ";|" + decimal(next_m) + ";";
  }
  throw std::runtime_error("OPERATION");
}
int main() {
  std::string line;
  while (std::getline(std::cin, line)) {
    try {
      std::istringstream input(line); auto result = execute(input);
      std::string extra; need(!(input >> extra));
      std::cout << "OK " << result << '\n';
    } catch (const std::exception&) { std::cout << "REJECT\n"; }
  }
}
