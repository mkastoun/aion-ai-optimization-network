#include "image.hpp"
#include <algorithm>

Pixels filter_image(const Pixels& input,std::uint32_t width) {
    const int n=static_cast<int>(width);
    constexpr unsigned weights[]={1,4,6,4,1};
    Pixels horizontal(input.size()),output(input.size());
    for (int y=0;y<n;++y) for (int x=0;x<n;++x) {
        std::uint32_t sum=0;
        for (int k=-2;k<=2;++k) sum+=weights[k+2]*input[std::size_t(y)*width+std::clamp(x+k,0,n-1)];
        horizontal[std::size_t(y)*width+x]=sum/16;
    }
    for (int y=0;y<n;++y) for (int x=0;x<n;++x) {
        std::uint32_t sum=0;
        for (int k=-2;k<=2;++k) sum+=weights[k+2]*horizontal[std::size_t(std::clamp(y+k,0,n-1))*width+x];
        output[std::size_t(y)*width+x]=sum/16;
    }
    return output;
}
