#include "../workloads/records/records.hpp"
[[clang::noinline]] Aggregate aggregate_records(const std::vector<Record>& rows);
#include "../workloads/records/aggregate.cpp"
