#include "../common.hpp"
#include "../application.hpp"
#include "records.hpp"

int main(int argc, char** argv) {
    const auto args = input(argc, argv, 200000);
    const auto preparation = Clock::now();
    std::vector<std::string> inputs(args.rounds);
    for (std::uint32_t r = 0; r < args.rounds; ++r) {
        auto state = args.seed + r;
        auto& text = inputs[r];
        text.reserve(args.n*32);
        for (std::uint32_t i = 0; i < args.n; ++i) {
            const auto user = (next(state) >> 8) % 512;
            const auto region = (next(state) >> 16) % 8;
            const auto amount = next(state) % 100000;
            const auto status = (next(state) >> 24) % 3;
            text += std::to_string(i) + ',' + std::to_string(user) + ',' + std::to_string(region) + ',' +
                    std::to_string(amount) + ',' + std::to_string(status) + '\n';
        }
    }
    return finish(args, preparation, [] {}, [&] {
        std::uint64_t checksum = 0;
        for (const auto& text : inputs) checksum += output_hash(format_records(aggregate_records(parse_records(text))));
        return checksum;
    });
}
