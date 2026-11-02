#include "kv.hpp"

bool mutate(Store& store,const Operation& op) {
    if (op.kind==0) {store.insert_or_assign(op.key,op.value);return true;}
    if (op.kind==3) return store.erase(op.key)!=0;
    const auto found=store.find(op.key);
    if (found==store.end()) return false;
    found->second=op.value;return true;
}
const std::string* lookup(const Store& store,std::uint32_t key) {
    const auto found=store.find(key);
    return found==store.end() ? nullptr : &found->second;
}
