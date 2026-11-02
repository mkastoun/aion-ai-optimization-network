#include "records.hpp"

std::string format_records(const Aggregate& data) {
    std::string text = "{\"records\":" + std::to_string(data.records) + ",\"accepted\":" +
        std::to_string(data.accepted) + ",\"ids\":" + std::to_string(data.ids) + ",\"groups\":[";
    bool first = true;
    for (std::size_t key = 0; key < data.groups.size(); ++key) {
        const auto& group = data.groups[key];
        if (!group.count) continue;
        if (!first) text += ',';
        first = false;
        text += '[' + std::to_string(key) + ',' + std::to_string(group.count) + ',' + std::to_string(group.cents) + ']';
    }
    return text + "]}";
}
