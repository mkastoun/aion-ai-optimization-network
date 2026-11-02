#include "common.hpp"
#include <unordered_map>
#include <vector>

int main(int argc, char** argv) {
    const auto args = input(argc, argv, 1000000);
    const auto preparation = Clock::now();
    std::vector<std::vector<std::uint32_t>> values(args.rounds, std::vector<std::uint32_t>(args.n));
    std::vector<std::unordered_map<std::uint32_t, std::uint64_t>> maps(args.rounds);
    for (std::uint32_t r = 0; r < args.rounds; ++r) {
        auto state = args.seed + r;
        for (auto& x : values[r]) x = next(state);
    }
    return finish(args, preparation, [&] {
        // Fresh containers also reset bucket capacity; merely clearing them
        // would silently remove rehash costs after the first batch.
        for (auto& entries : maps) {
            std::unordered_map<std::uint32_t, std::uint64_t> fresh;
            entries.swap(fresh);
        }
    }, [&] {
        std::uint64_t checksum = 0;
        const auto keyspace = args.n / 2 + 1;
        for (std::uint32_t r = 0; r < args.rounds; ++r) {
            auto& entries = maps[r];
            for (auto x : values[r]) entries[x % keyspace] += x;
            for (std::uint32_t key = 0; key < keyspace; ++key) {
                const auto found = entries.find(key);
                if (found != entries.end()) checksum += found->second * (key % 13 + 1);
                if (key % 3 == 0) entries.erase(key);
            }
            checksum += entries.size();
        }
        return checksum;
    });
}
