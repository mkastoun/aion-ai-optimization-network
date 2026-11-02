#pragma once
#include <cstdint>
#include <string>
#include <vector>
using Pixels=std::vector<std::uint16_t>;
Pixels filter_image(const Pixels&,std::uint32_t width);
Pixels edge_image(const Pixels&,std::uint32_t width);
std::string format_image(const Pixels&,std::uint32_t width);
