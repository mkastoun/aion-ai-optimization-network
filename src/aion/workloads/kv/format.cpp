#include "kv.hpp"
#include <algorithm>

std::string format_state(const State& state) {
    std::vector<std::uint32_t> keys;keys.reserve(state.values.size());
    for(const auto& entry:state.values)keys.push_back(entry.first);
    std::sort(keys.begin(),keys.end());
    std::string entries;
    for(auto key:keys) {
        if(!entries.empty())entries+=',';
        entries+='['+std::to_string(key)+",\""+state.values.at(key)+"\"]";
    }
    return "{\"queries\":"+std::to_string(state.queries)+",\"hits\":"+std::to_string(state.hits)+
           ",\"updates\":"+std::to_string(state.updates)+",\"deletes\":"+std::to_string(state.deletes)+
           ",\"query_checksum\":"+std::to_string(state.query_checksum)+",\"entries\":["+entries+"]}";
}
