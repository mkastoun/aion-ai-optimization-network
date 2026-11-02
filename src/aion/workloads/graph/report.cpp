#include "graph.hpp"
#include <algorithm>
#include <limits>

RouteSummary summarize_routes(std::uint32_t source, const std::vector<std::uint64_t>& distances) {
    RouteSummary result{source, 0, 0, 0};
    for (std::size_t i = 0; i < distances.size(); ++i) {
        if (distances[i] == std::numeric_limits<std::uint64_t>::max()/4) continue;
        ++result.reachable;
        result.maximum = std::max(result.maximum, distances[i]);
        result.weighted_sum += distances[i] * (i%19 + 1);
    }
    return result;
}

std::string format_routes(std::uint32_t vertices, const std::vector<RouteSummary>& queries) {
    std::string text = "{\"vertices\":" + std::to_string(vertices) + ",\"queries\":[";
    bool first = true;
    for (const auto& query : queries) {
        if (!first) text += ',';
        first = false;
        text += "{\"source\":" + std::to_string(query.source) + ",\"sum\":" + std::to_string(query.weighted_sum) +
            ",\"max\":" + std::to_string(query.maximum) + ",\"reachable\":" + std::to_string(query.reachable) + '}';
    }
    return text + "]}";
}
