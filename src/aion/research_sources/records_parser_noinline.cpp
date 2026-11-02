#include "../workloads/records/records.hpp"
[[clang::noinline]] std::vector<Record> parse_records(std::string_view text);
#include "../workloads/records/parser.cpp"
