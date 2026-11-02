#include "graph.hpp"
#include <stdexcept>

Graph build_graph(std::uint32_t vertices, const std::vector<Edge>& edges) {
    Graph graph(vertices);
    for (const auto& edge : edges) {
        if (edge.from >= vertices || edge.to >= vertices || edge.weight == 0)
            throw std::invalid_argument("invalid graph edge");
        graph[edge.from].push_back({edge.to, edge.weight});
    }
    return graph;
}
