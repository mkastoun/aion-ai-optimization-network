#pragma once
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>
struct Operation { unsigned kind; std::uint32_t key; std::string value; };
using Store=std::unordered_map<std::uint32_t,std::string>;
struct State { Store values; std::uint64_t queries=0,hits=0,updates=0,deletes=0,query_checksum=0; };
bool mutate(Store&,const Operation&);
const std::string* lookup(const Store&,std::uint32_t key);
State process_operations(const std::vector<Operation>&);
std::string format_state(const State&);
