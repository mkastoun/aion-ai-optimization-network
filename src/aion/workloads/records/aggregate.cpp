#include "records.hpp"

Aggregate aggregate_records(const std::vector<Record>& rows) {
    Aggregate result;
    result.records = rows.size();
    result.groups.resize(4096);
    for (const auto& row : rows) if (row.status == 1) {
        ++result.accepted;
        result.ids += row.id;
        auto& group = result.groups[row.user*8 + row.region];
        ++group.count;
        group.cents += row.amount;
    }
    return result;
}
