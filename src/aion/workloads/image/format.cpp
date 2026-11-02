#include "image.hpp"
#include <array>

std::string format_image(const Pixels& pixels,std::uint32_t width) {
    std::array<std::uint64_t,16> histogram{};
    std::uint64_t sum=0,weighted=0;
    std::string rows;
    for (std::uint32_t y=0;y<width;++y) {
        std::uint64_t hash=14695981039346656037ull;
        for (std::uint32_t x=0;x<width;++x) {
            const auto i=std::size_t(y)*width+x;
            const auto value=pixels[i];
            sum+=value;weighted+=std::uint64_t(value)*(i%251+1);++histogram[value>>12];
            hash=(hash^(value&255))*1099511628211ull;
            hash=(hash^(value>>8))*1099511628211ull;
        }
        if (y) rows+=',';
        rows+=std::to_string(hash);
    }
    std::string bins;
    for (unsigned i=0;i<16;++i) { if(i)bins+=',';bins+=std::to_string(histogram[i]); }
    return "{\"width\":"+std::to_string(width)+",\"sum\":"+std::to_string(sum)+",\"weighted\":"+std::to_string(weighted)+
           ",\"histogram\":["+bins+"],\"rows\":["+rows+"]}";
}
