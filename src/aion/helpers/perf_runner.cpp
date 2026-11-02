// Trusted single-thread workload launcher. Counters begin at the child's exec;
// the Python timing/promotion pipeline never invokes this helper.
#include <cerrno>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include <cstring>
#include <chrono>
#include <thread>
#include <iterator>
#if defined(__linux__)
#include <linux/perf_event.h>
#include <sys/syscall.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <unistd.h>
#include <sys/mman.h>

struct Event { const char* name; const char* kind; std::uint32_t type; std::uint64_t config; int fd=-1, error=0; };

std::string quoted(const std::string& value) {
    std::string out="\"";
    for(unsigned char c:value) {
        if(c=='\\'||c=='\"') {out+='\\';out+=char(c);}
        else if(c=='\n')out+="\\n";
        else if(c=='\r')out+="\\r";
        else if(c=='\t')out+="\\t";
        else if(c>=32)out+=char(c);
    }
    return out+'\"';
}

int main(int argc, char** argv) {
    const bool sampling=argc>1 && std::string(argv[1])=="--sample";
    const int target_index=sampling ? 3 : 2;
    if (argc<=target_index) return 2;
    int gate[2];
    if (pipe(gate) != 0) return 3;
    const pid_t child = fork();
    if (child < 0) return 3;
    if (child == 0) {
        close(gate[1]);
        char token;
        ssize_t got;
        do { got = read(gate[0], &token, 1); } while (got < 0 && errno == EINTR);
        close(gate[0]);
        if (got != 1) _exit(126);
        execv(argv[target_index], &argv[target_index]);
        _exit(127);
    }
    close(gate[0]);
    std::vector<Event> events = {
        {"cycles", "hardware", PERF_TYPE_HARDWARE, PERF_COUNT_HW_CPU_CYCLES},
        {"instructions", "hardware", PERF_TYPE_HARDWARE, PERF_COUNT_HW_INSTRUCTIONS},
        {"cache-references", "hardware", PERF_TYPE_HARDWARE, PERF_COUNT_HW_CACHE_REFERENCES},
        {"cache-misses", "hardware", PERF_TYPE_HARDWARE, PERF_COUNT_HW_CACHE_MISSES},
        {"branches", "hardware", PERF_TYPE_HARDWARE, PERF_COUNT_HW_BRANCH_INSTRUCTIONS},
        {"branch-misses", "hardware", PERF_TYPE_HARDWARE, PERF_COUNT_HW_BRANCH_MISSES},
        {"context-switches", "software", PERF_TYPE_SOFTWARE, PERF_COUNT_SW_CONTEXT_SWITCHES},
        {"cpu-migrations", "software", PERF_TYPE_SOFTWARE, PERF_COUNT_SW_CPU_MIGRATIONS},
        {"page-faults", "software", PERF_TYPE_SOFTWARE, PERF_COUNT_SW_PAGE_FAULTS},
    };
    if(sampling)events.resize(1);
    void* mapping=MAP_FAILED;
    const auto page_size=static_cast<std::size_t>(sysconf(_SC_PAGESIZE));
    const std::size_t ring_size=256*page_size;
    int mmap_error=0;
    for (auto& event : events) {
        perf_event_attr attr{};
        attr.type=event.type; attr.size=PERF_ATTR_SIZE_VER0; attr.config=event.config;
        attr.disabled=1; attr.enable_on_exec=1; attr.inherit=0;
        attr.exclude_kernel=1; attr.exclude_hv=1;
        attr.read_format=PERF_FORMAT_TOTAL_TIME_ENABLED | PERF_FORMAT_TOTAL_TIME_RUNNING;
        if(sampling) {attr.freq=1;attr.sample_freq=997;attr.sample_type=PERF_SAMPLE_IP;attr.wakeup_events=1;}
        event.fd=static_cast<int>(syscall(SYS_perf_event_open, &attr, child, -1, -1, PERF_FLAG_FD_CLOEXEC));
        if (event.fd < 0) event.error=errno;
        if(sampling && event.fd>=0) {
            mapping=mmap(nullptr,page_size+ring_size,PROT_READ|PROT_WRITE,MAP_SHARED,event.fd,0);
            if(mapping==MAP_FAILED)mmap_error=errno;
        }
    }
    const char token='x';
    const auto released=write(gate[1], &token, 1);
    close(gate[1]);
    (void)released;
    int status=0;
    rusage usage{};
    pid_t waited;
    std::string maps;
    if(sampling) {
        do {
            std::ifstream input("/proc/"+std::to_string(child)+"/maps");
            const std::string snapshot((std::istreambuf_iterator<char>(input)),std::istreambuf_iterator<char>());
            if(!snapshot.empty())maps=snapshot;
            waited=wait4(child,&status,WNOHANG,&usage);
            if(waited==0)std::this_thread::sleep_for(std::chrono::milliseconds(2));
        } while(waited==0 || (waited<0 && errno==EINTR));
    } else do { waited=wait4(child,&status,0,&usage); } while (waited < 0 && errno == EINTR);
    if (waited < 0) return 3;
    const int code=WIFEXITED(status) ? WEXITSTATUS(status) : -WTERMSIG(status);
    std::ofstream out(argv[sampling ? 2 : 1]);
    if (!out) return 3;
    out << "{\"protocol\":\"aion-perf-v1\",\"child_pid\":" << child
        << ",\"child_returncode\":" << code << ",\"events\":[";
    bool first=true;
    for (auto& event : events) {
        std::uint64_t data[3]{};
        bool counted=false;
        if (event.fd >= 0) {
            ssize_t got;
            do { got=read(event.fd,data,sizeof(data)); } while (got < 0 && errno == EINTR);
            if (got == sizeof(data)) counted=true;
            else event.error=got < 0 ? errno : EIO;
            close(event.fd);
        }
        if (!first) out << ',';
        first=false;
        out << "{\"name\":\"" << event.name << "\",\"kind\":\"" << event.kind
            << "\",\"type\":" << event.type << ",\"config\":" << event.config
            << ",\"errno\":" << event.error << ",\"raw_count\":";
        if (counted) out << data[0]; else out << "null";
        out << ",\"time_enabled_ns\":";
        if (counted) out << data[1]; else out << "null";
        out << ",\"time_running_ns\":";
        if (counted) out << data[2]; else out << "null";
        out << '}';
    }
    std::vector<std::uint64_t> ips;
    std::uint64_t lost=0;
    bool overrun=false;
    if(mapping!=MAP_FAILED) {
        auto* metadata=static_cast<perf_event_mmap_page*>(mapping);
        auto head=__atomic_load_n(&metadata->data_head,__ATOMIC_ACQUIRE);
        auto tail=metadata->data_tail;
        const auto* data=static_cast<const char*>(mapping)+page_size;
        const auto copy=[&](std::uint64_t offset,void* destination,std::size_t count) {
            auto* dest=static_cast<char*>(destination);
            for(std::size_t i=0;i<count;++i)dest[i]=data[(offset+i)%ring_size];
        };
        if(head-tail>ring_size) {overrun=true;tail=head;}
        while(tail<head) {
            perf_event_header header{};copy(tail,&header,sizeof(header));
            if(header.size<sizeof(header) || tail+header.size>head) {overrun=true;break;}
            if(header.type==PERF_RECORD_SAMPLE && header.size>=sizeof(header)+8) {
                std::uint64_t ip;copy(tail+sizeof(header),&ip,8);ips.push_back(ip);
            } else if(header.type==PERF_RECORD_LOST && header.size>=sizeof(header)+16) {
                std::uint64_t count;copy(tail+sizeof(header)+8,&count,8);lost+=count;
            }
            tail+=header.size;
        }
        __atomic_store_n(&metadata->data_tail,head,__ATOMIC_RELEASE);
        munmap(mapping,page_size+ring_size);
    }
    out << "],\"sampling\":{\"requested\":" << (sampling?"true":"false")
        << ",\"frequency_hz\":997,\"mmap_errno\":" << mmap_error << ",\"lost_samples\":" << lost
        << ",\"buffer_overrun\":" << (overrun?"true":"false") << ",\"maps\":" << quoted(maps) << ",\"ips\":[";
    for(std::size_t i=0;i<ips.size();++i) {if(i)out<<',';out<<ips[i];}
    out << "]},\"rusage\":{\"voluntary_context_switches\":" << usage.ru_nvcsw
        << ",\"involuntary_context_switches\":" << usage.ru_nivcsw
        << ",\"minor_page_faults\":" << usage.ru_minflt
        << ",\"major_page_faults\":" << usage.ru_majflt
        << ",\"user_seconds\":" << (usage.ru_utime.tv_sec + usage.ru_utime.tv_usec/1e6)
        << ",\"system_seconds\":" << (usage.ru_stime.tv_sec + usage.ru_stime.tv_usec/1e6) << "}}\n";
    return code < 0 ? 128-code : code;
}
#else
int main() { std::cerr << "Linux perf_event_open unavailable\n"; return 2; }
#endif
