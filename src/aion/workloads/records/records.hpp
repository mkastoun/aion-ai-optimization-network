#pragma once
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

struct Record { std::uint32_t id, user, region, amount, status; };
struct Group { std::uint64_t count = 0, cents = 0; };
struct Aggregate { std::uint64_t records = 0, accepted = 0, ids = 0; std::vector<Group> groups; };
std::vector<Record> parse_records(std::string_view text);
Aggregate aggregate_records(const std::vector<Record>& rows);
std::string format_records(const Aggregate& data);
