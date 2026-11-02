#include "image.hpp"
#include <algorithm>
#include <cstdlib>

Pixels edge_image(const Pixels& input,std::uint32_t width) {
    const int n=static_cast<int>(width);
    Pixels result(input.size());
    for (int y=0;y<n;++y) for (int x=0;x<n;++x) {
        const auto pixel=[&](int dy,int dx)->int {
            return input[std::size_t(std::clamp(y+dy,0,n-1))*width+std::clamp(x+dx,0,n-1)];
        };
        const int dx=-pixel(-1,-1)+pixel(-1,1)-2*pixel(0,-1)+2*pixel(0,1)-pixel(1,-1)+pixel(1,1);
        const int dy=-pixel(-1,-1)-2*pixel(-1,0)-pixel(-1,1)+pixel(1,-1)+2*pixel(1,0)+pixel(1,1);
        result[std::size_t(y)*width+x]=std::min(65535,std::abs(dx)+std::abs(dy));
    }
    return result;
}
