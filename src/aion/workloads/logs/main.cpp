#include "../common.hpp"
#include "../application.hpp"
#include "logs.hpp"
#include <vector>

int main(int argc, char** argv) {
    const auto args = input(argc, argv, 200000);
    const auto preparation = Clock::now();
    const char* levels[] = {"INFO","WARN","ERROR"};
    const unsigned statuses[] = {200,404,500};
    std::vector<std::string> inputs(args.rounds);
    for (std::uint32_t r=0; r<args.rounds; ++r) {
        auto state = args.seed+r;
        auto& text = inputs[r];
        text.reserve(args.n*48);
        for (std::uint32_t i=0; i<args.n; ++i) {
            const auto stamp = 1700000000ull + std::uint64_t(i)*3 + next(state)%60;
            const auto level = (next(state)>>24)%3;
            const auto service = (next(state)>>16)%32;
            const auto status = statuses[(next(state)>>16)%3];
            const auto bytes = next(state)%8192;
            const auto latency = next(state)%50000;
            if (i%97 == 0) { text += "malformed line\n"; continue; }
            text += std::to_string(stamp) + '|' + levels[level] + "|svc" + std::to_string(service) + '|' +
                    std::to_string(status) + '|' + std::to_string(bytes) + '|' + std::to_string(latency) + '\n';
        }
    }
    return finish(args, preparation, [] {}, [&] {
        std::uint64_t checksum = 0;
        for (const auto& text : inputs) checksum += output_hash(format_logs(aggregate_logs(text)));
        return checksum;
    });
}
