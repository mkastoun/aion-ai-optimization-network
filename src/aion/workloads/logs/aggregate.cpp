#include "logs.hpp"

LogStats aggregate_logs(std::string_view text) {
    LogStats result;
    while (!text.empty()) {
        const auto end = text.find('\n');
        const auto line = text.substr(0,end);
        text = end == std::string_view::npos ? std::string_view{} : text.substr(end+1);
        ++result.lines;
        LogRecord row{};
        if (!parse_log(line,row)) { ++result.invalid; continue; }
        if (row.level != 2 && row.status < 400) continue;
        ++result.selected;
        auto& stats = result.services[row.service];
        ++stats.count;
        stats.bytes += row.bytes;
        stats.latency += row.latency;
        stats.errors += row.status >= 500;
        ++stats.minutes[(row.timestamp/60)%60];
    }
    return result;
}
