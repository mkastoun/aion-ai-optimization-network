#include "kv.hpp"
#include "../application.hpp"

State process_operations(const std::vector<Operation>& operations) {
    State result;
    for (const auto& op:operations) {
        if (op.kind==1) {
            ++result.queries;
            if (const auto value=lookup(result.values,op.key)) {
                ++result.hits;result.query_checksum+=output_hash(*value)^op.key;
            }
        } else {
            const auto changed=mutate(result.values,op);
            if(op.kind==2)result.updates+=changed;
            if(op.kind==3)result.deletes+=changed;
        }
    }
    return result;
}
