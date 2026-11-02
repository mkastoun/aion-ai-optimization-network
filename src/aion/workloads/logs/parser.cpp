#include "logs.hpp"
#include <charconv>

template<class Number> static bool integer(std::string_view text, Number& value) {
    const auto parsed = std::from_chars(text.data(), text.data()+text.size(), value);
    return parsed.ec == std::errc{} && parsed.ptr == text.data()+text.size();
}

bool parse_log(std::string_view text, LogRecord& record) {
    std::array<std::string_view,6> fields;
    for (unsigned i=0; i<5; ++i) {
        const auto end = text.find('|');
        if (end == std::string_view::npos) return false;
        fields[i] = text.substr(0,end);
        text.remove_prefix(end+1);
    }
    fields[5] = text;
    if (fields[1] == "INFO") record.level=0;
    else if (fields[1] == "WARN") record.level=1;
    else if (fields[1] == "ERROR") record.level=2;
    else return false;
    if (fields[2].substr(0,3) != "svc") return false;
    fields[2].remove_prefix(3);
    return integer(fields[0],record.timestamp) && integer(fields[2],record.service) && record.service<32 &&
           integer(fields[3],record.status) && integer(fields[4],record.bytes) && integer(fields[5],record.latency);
}
