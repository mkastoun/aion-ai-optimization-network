#include "common.hpp"
#include <algorithm>
#include <vector>

int main(int argc, char** argv) {
    const auto args = input(argc, argv);
    const auto preparation = Clock::now();
    std::vector<std::vector<std::uint32_t>> original(args.rounds, std::vector<std::uint32_t>(args.n));
    for (std::uint32_t r = 0; r < args.rounds; ++r) {
        auto state = args.seed + r;
        for (auto& x : original[r]) x = next(state);
    }
    auto data = original;
    return finish(args, preparation, [&] { data = original; }, [&] {
        std::uint64_t checksum = 0;
        for (auto& row : data) {
            std::sort(row.begin(), row.end());
            for (std::size_t i = 0; i < row.size(); ++i)
                checksum += std::uint64_t(row[i]) * (i % 23 + 1);
        }
        return checksum;
    });
}
