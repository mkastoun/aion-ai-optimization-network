#include "common.hpp"
#include <algorithm>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    const auto args = input(argc, argv);
    const auto preparation = Clock::now();
    std::vector<std::string> original(args.rounds, std::string(args.n, 'a'));
    for (std::uint32_t r = 0; r < args.rounds; ++r) {
        auto state = args.seed + r;
        for (auto& c : original[r]) c = static_cast<char>('a' + next(state) % 26);
    }
    auto data = original;
    return finish(args, preparation, [&] { data = original; }, [&] {
        std::uint64_t checksum = 0;
        for (auto& text : data) {
            std::transform(text.begin(), text.end(), text.begin(),
                           [](char c) { return static_cast<char>(c - 'a' + 'A'); });
            for (std::size_t i = 0; i < text.size(); ++i)
                checksum += static_cast<unsigned char>(text[i]) * (i % 11 + 1);
            std::size_t position = 0;
            while ((position = text.find("AB", position)) != std::string::npos) {
                checksum += 97;
                position += 2;
            }
        }
        return checksum;
    });
}
