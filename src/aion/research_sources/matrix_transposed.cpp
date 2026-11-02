#include "../workloads/common.hpp"
#include <algorithm>
#include <vector>

int main(int argc, char** argv) {
    const auto args = input(argc, argv, 256);
    const auto n = args.n;
    const auto preparation = Clock::now();
    std::vector<std::vector<std::uint32_t>> a(args.rounds, std::vector<std::uint32_t>(n*n)), b = a;
    std::vector<std::vector<std::uint64_t>> c(args.rounds, std::vector<std::uint64_t>(n*n));
    for (std::uint32_t r = 0; r < args.rounds; ++r) {
        auto state = args.seed + r;
        for (std::size_t i = 0; i < a[r].size(); ++i) {
            a[r][i] = next(state) % 17;
            const auto value = next(state) % 17;
            b[r][(i%n)*n+i/n] = value;
        }
    }
    return finish(args, preparation, [&] {
        for (auto& row : c) std::fill(row.begin(), row.end(), 0);
    }, [&] {
        std::uint64_t checksum = 0;
        for (std::uint32_t r = 0; r < args.rounds; ++r) {
            for (std::uint32_t i = 0; i < n; ++i)
                for (std::uint32_t j = 0; j < n; ++j) {
                    std::uint64_t sum = 0;
                    for (std::uint32_t k = 0; k < n; ++k)
                        sum += std::uint64_t(a[r][i*n+k]) * b[r][j*n+k];
                    c[r][i*n+j] = sum;
                }
            for (std::size_t i = 0; i < c[r].size(); ++i) checksum += c[r][i] * (i % 19 + 1);
        }
        return checksum;
    });
}
