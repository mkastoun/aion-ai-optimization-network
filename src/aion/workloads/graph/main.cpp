#include "../common.hpp"
#include "../application.hpp"
#include "graph.hpp"

int main(int argc, char** argv) {
    const auto args = input(argc, argv, 20000);
    const auto preparation = Clock::now();
    std::vector<std::vector<Edge>> inputs(args.rounds);
    std::vector<std::vector<std::uint32_t>> sources(args.rounds);
    for (std::uint32_t r = 0; r < args.rounds; ++r) {
        auto state = args.seed + r;
        for (std::uint32_t vertex = 0; vertex < args.n; ++vertex) {
            inputs[r].push_back({vertex, (vertex+1)%args.n, 1});
            inputs[r].push_back({vertex, (vertex+args.n-1)%args.n, 2});
            for (unsigned k = 0; k < 4; ++k) {
                const auto target = (next(state) >> 8) % args.n;
                const auto weight = (next(state) >> 16) % 97 + 1;
                inputs[r].push_back({vertex, target, weight});
            }
        }
        if (args.n) for (unsigned q = 0; q < 4; ++q)
            sources[r].push_back((std::uint64_t(std::uint32_t(args.seed+r)) + q*97) % args.n);
    }
    return finish(args, preparation, [] {}, [&] {
        std::uint64_t checksum = 0;
        for (std::uint32_t r = 0; r < args.rounds; ++r) {
            const auto graph = build_graph(args.n, inputs[r]);
            std::vector<RouteSummary> queries;
            for (auto source : sources[r]) queries.push_back(summarize_routes(source, shortest_paths(graph, source)));
            checksum += output_hash(format_routes(args.n, queries));
        }
        return checksum;
    });
}
