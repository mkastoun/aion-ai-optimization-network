#include "records.hpp"
#include <charconv>
#include <stdexcept>

std::vector<Record> parse_records(std::string_view text) {
    std::vector<Record> rows;
    const char* current = text.data();
    const char* end = current + text.size();
    while (current != end) {
        Record row{};
        std::uint32_t* fields[] = {&row.id, &row.user, &row.region, &row.amount, &row.status};
        for (int index = 0; index < 5; ++index) {
            auto parsed = std::from_chars(current, end, *fields[index]);
            if (parsed.ec != std::errc{} || parsed.ptr == end || *parsed.ptr != (index == 4 ? '\n' : ','))
                throw std::invalid_argument("invalid structured record");
            current = parsed.ptr + 1;
        }
        if (row.user >= 512 || row.region >= 8 || row.status >= 3)
            throw std::invalid_argument("record field out of range");
        rows.push_back(row);
    }
    return rows;
}
