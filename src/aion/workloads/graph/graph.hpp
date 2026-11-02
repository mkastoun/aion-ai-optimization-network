#pragma once
#include <cstdint>
#include <string>
#include <utility>
#include <vector>

struct Edge { std::uint32_t from, to, weight; };
using Graph = std::vector<std::vector<std::pair<std::uint32_t, std::uint32_t>>>;
struct RouteSummary { std::uint32_t source; std::uint64_t weighted_sum, maximum, reachable; };
Graph build_graph(std::uint32_t vertices, const std::vector<Edge>& edges);
std::vector<std::uint64_t> shortest_paths(const Graph& graph, std::uint32_t source);
RouteSummary summarize_routes(std::uint32_t source, const std::vector<std::uint64_t>& distances);
std::string format_routes(std::uint32_t vertices, const std::vector<RouteSummary>& queries);
