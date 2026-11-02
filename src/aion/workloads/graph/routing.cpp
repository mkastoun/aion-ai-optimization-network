#include "graph.hpp"
#include <functional>
#include <limits>
#include <queue>

std::vector<std::uint64_t> shortest_paths(const Graph& graph, std::uint32_t source) {
    constexpr auto infinity = std::numeric_limits<std::uint64_t>::max()/4;
    std::vector<std::uint64_t> distance(graph.size(), infinity);
    if (source >= graph.size()) return distance;
    using Item = std::pair<std::uint64_t, std::uint32_t>;
    std::priority_queue<Item, std::vector<Item>, std::greater<Item>> pending;
    distance[source] = 0;
    pending.push({0, source});
    while (!pending.empty()) {
        auto [cost, vertex] = pending.top();
        pending.pop();
        if (distance[vertex] != cost) continue;
        for (auto [target, weight] : graph[vertex]) {
            const auto candidate = cost + weight;
            if (candidate < distance[target]) {
                distance[target] = candidate;
                pending.push({candidate, target});
            }
        }
    }
    return distance;
}
