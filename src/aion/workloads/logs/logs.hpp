#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <string_view>

struct LogRecord { std::uint64_t timestamp; std::uint32_t level, service, status, bytes, latency; };
struct ServiceStats {
    std::uint64_t count=0, bytes=0, latency=0, errors=0;
    std::array<std::uint64_t,60> minutes{};
};
struct LogStats { std::uint64_t lines=0, invalid=0, selected=0; std::array<ServiceStats,32> services{}; };
bool parse_log(std::string_view text, LogRecord& record);
LogStats aggregate_logs(std::string_view text);
std::string format_logs(const LogStats& stats);
