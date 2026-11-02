#pragma once
#include <cstdint>
#include <string_view>

inline std::uint64_t output_hash(std::string_view text) {
    std::uint64_t value = 14695981039346656037ull;
    for (unsigned char c : text) value = (value ^ c) * 1099511628211ull;
    return value;
}
