#pragma once
#include <charconv>
#include <chrono>
#include <atomic>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string_view>
#include <string>
#if defined(__linux__)
#include <sched.h>
#include <unistd.h>
#endif

using Clock = std::chrono::steady_clock;
struct Input { std::uint32_t n, seed, rounds, batches = 1; bool measure = false; std::uint32_t control_delay_ns = 0; };

inline std::uint32_t number(const char* text) {
    const std::string_view view(text);
    std::uint32_t value = 0;
    auto result = std::from_chars(view.data(), view.data() + view.size(), value);
    if (result.ec != std::errc{} || result.ptr != view.data() + view.size())
        throw std::invalid_argument("expected unsigned integer");
    return value;
}

inline Input input(int argc, char** argv, std::uint32_t maximum = 2000000) {
    if (argc != 4 && argc != 6 && argc != 8)
        throw std::invalid_argument("usage: workload size seed rounds [--measure batches]");
    Input result{number(argv[1]), number(argv[2]), number(argv[3])};
    if (result.n > maximum || result.rounds == 0 || result.rounds > 1000)
        throw std::invalid_argument("workload size or rounds out of range");
    if (argc >= 6) {
        if (std::string_view(argv[4]) != "--measure")
            throw std::invalid_argument("expected --measure");
        result.measure = true;
        result.batches = number(argv[5]);
        if (result.batches == 0 || result.batches > 65536)
            throw std::invalid_argument("batches must be 1..65536");
    }
    if (argc == 8) {
        if (std::string_view(argv[6]) != "--control-delay-ns")
            throw std::invalid_argument("expected --control-delay-ns");
        result.control_delay_ns = number(argv[7]);
        if (result.control_delay_ns > 250000000)
            throw std::invalid_argument("control delay exceeds 250 ms per unit");
    }
    return result;
}

inline void compiler_barrier() {
#if defined(__clang__) || defined(__GNUC__)
    __asm__ __volatile__("" ::: "memory");
#else
    std::atomic_signal_fence(std::memory_order_seq_cst);
#endif
}

inline std::uint64_t nanoseconds(Clock::duration elapsed) {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(elapsed).count();
}

inline std::string effective_affinity_json() {
#if defined(__linux__)
    for (int count = 1024; count <= 65536; count *= 2) {
        cpu_set_t* mask = CPU_ALLOC(count);
        if (!mask) return "null";
        const auto bytes = CPU_ALLOC_SIZE(count);
        CPU_ZERO_S(bytes, mask);
        if (sched_getaffinity(0, bytes, mask) == 0) {
            std::string result = "[";
            for (int cpu = 0; cpu < count; ++cpu) if (CPU_ISSET_S(cpu, bytes, mask)) {
                if (result.size() > 1) result += ',';
                result += std::to_string(cpu);
            }
            CPU_FREE(mask);
            return result + ']';
        }
        CPU_FREE(mask);
    }
#endif
    return "null";
}

inline int observed_cpu() {
#if defined(__linux__)
    return sched_getcpu();
#else
    return -1;
#endif
}

inline long workload_pid() {
#if defined(__linux__)
    return getpid();
#else
    return -1;
#endif
}

// Explicit negative control only. It consumes actual measured time and leaves
// the application's checksum untouched; no timing subtraction is performed.
inline std::uint64_t controlled_delay(std::uint32_t requested_ns) {
    if (!requested_ns) return 0;
    const auto start = Clock::now();
    volatile std::uint64_t state = 1;
    do {
        state = state * 1664525u + 1013904223u;
    } while (nanoseconds(Clock::now() - start) < requested_ns);
    return nanoseconds(Clock::now() - start);
}

// Setup prepares identical inputs before every timed batch. The checksum scan
// remains in the timed region so the computation's result is observable.
template<class Reset, class Compute>
int finish(const Input& args, Clock::time_point preparation_start, Reset reset, Compute compute) {
    std::uint64_t setup_ns = nanoseconds(Clock::now() - preparation_start);
    const auto affinity_start = effective_affinity_json();
    const auto cpu_start = observed_cpu();
    std::uint64_t compute_ns = 0, checksum = 0, injected_control_ns = 0;
    for (std::uint32_t batch = 0; batch < args.batches; ++batch) {
        auto start = Clock::now();
        reset();
        setup_ns += nanoseconds(Clock::now() - start);
        compiler_barrier();
        start = Clock::now();
        compiler_barrier();
        checksum += compute();
        injected_control_ns += controlled_delay(args.control_delay_ns);
        compiler_barrier();
        compute_ns += nanoseconds(Clock::now() - start);
    }
    if (args.measure)
        std::cout << "{\"protocol\":\"aion-compute-v1\",\"checksum\":\"" << checksum
                  << "\",\"compute_ns\":" << compute_ns << ",\"setup_ns\":" << setup_ns
                  << ",\"batches\":" << args.batches
                  << ",\"affinity_start\":" << affinity_start
                  << ",\"affinity_end\":" << effective_affinity_json()
                  << ",\"cpu_start\":" << cpu_start << ",\"cpu_end\":" << observed_cpu()
                  << ",\"pid\":" << workload_pid()
                  << ",\"control_delay_ns\":" << args.control_delay_ns
                  << ",\"injected_control_ns\":" << injected_control_ns << "}\n";
    else
        std::cout << checksum << '\n';
    return 0;
}

inline std::uint32_t next(std::uint32_t& state) {
    state = state * 1664525u + 1013904223u;
    return state;
}
