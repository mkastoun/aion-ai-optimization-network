#include "logs.hpp"

std::string format_logs(const LogStats& data) {
    std::string text = "{\"lines\":" + std::to_string(data.lines) + ",\"invalid\":" + std::to_string(data.invalid) +
                       ",\"selected\":" + std::to_string(data.selected) + ",\"services\":[";
    bool first = true;
    for (unsigned id=0; id<data.services.size(); ++id) {
        const auto& stats = data.services[id];
        if (!stats.count) continue;
        if (!first) text += ',';
        first = false;
        text += '[' + std::to_string(id) + ',' + std::to_string(stats.count) + ',' + std::to_string(stats.bytes) + ',' +
                std::to_string(stats.latency) + ',' + std::to_string(stats.errors) + ",[";
        for (unsigned minute=0; minute<60; ++minute) {
            if (minute) text += ',';
            text += std::to_string(stats.minutes[minute]);
        }
        text += "]]";
    }
    return text + "]}";
}
