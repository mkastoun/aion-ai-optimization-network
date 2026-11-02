#include "../common.hpp"
#include "../application.hpp"
#include "kv.hpp"

int main(int argc,char** argv) {
    const auto args=input(argc,argv,200000);
    const auto preparation=Clock::now();
    constexpr unsigned actions[]={0,0,1,1,2,1,3,0};
    std::vector<std::vector<Operation>> inputs(args.rounds);
    for (std::uint32_t r=0;r<args.rounds;++r) {
        auto state=args.seed+r;
        auto& operations=inputs[r];operations.reserve(args.n);
        for (std::uint32_t i=0;i<args.n;++i) {
            const auto random_key=next(state);
            const auto length=8+(next(state)>>16)%89;
            const auto key=args.seed==0 ? (i/8)%64 : args.seed==UINT32_MAX ? i%(args.n/4+1) : random_key%((i%5==0)?64:(args.n/4+1));
            std::string value;value.reserve(length);
            for (unsigned j=0;j<length;++j) value+=char('a'+(next(state)>>24)%26);
            operations.push_back({actions[i%8],key,std::move(value)});
        }
    }
    return finish(args,preparation,[]{},[&]{
        std::uint64_t checksum=0;
        for (const auto& operations:inputs) checksum+=output_hash(format_state(process_operations(operations)));
        return checksum;
    });
}
