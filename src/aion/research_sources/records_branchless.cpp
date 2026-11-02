#include "../workloads/records/records.hpp"

// Trusted generated records have user < 512 and region < 8, as in the original.
Aggregate aggregate_records(const std::vector<Record>& rows) {
    Aggregate result;
    result.records = rows.size();
    result.groups.resize(4096);
    for (const auto& row : rows) {
        const std::uint64_t accepted = row.status == 1;
        result.accepted += accepted;
        result.ids += row.id * accepted;
        auto& group = result.groups[row.user*8 + row.region];
        group.count += accepted;
        group.cents += row.amount * accepted;
    }
    return result;
}
