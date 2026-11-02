#include "../common.hpp"
#include "../application.hpp"
#include "image.hpp"

int main(int argc,char** argv) {
    const auto args=input(argc,argv,1024);
    const auto preparation=Clock::now();
    std::vector<Pixels> images(args.rounds,Pixels(std::size_t(args.n)*args.n));
    for (std::uint32_t r=0;r<args.rounds;++r) {
        auto state=args.seed+r;
        for (std::size_t i=0;i<images[r].size();++i) {
            const auto value=next(state)>>16;
            images[r][i]=args.seed==0 ? 32768 : args.seed==UINT32_MAX ? (((i/args.n+i%args.n)%2)*65535) : value;
        }
    }
    return finish(args,preparation,[]{},[&]{
        std::uint64_t checksum=0;
        for (const auto& image:images)
            checksum+=output_hash(format_image(edge_image(filter_image(image,args.n),args.n),args.n));
        return checksum;
    });
}
