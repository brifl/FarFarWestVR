// Original Far Far West extension support; no engine SDK types or source.
#pragma once
#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <mutex>

namespace ffw {
using Clock=std::chrono::steady_clock;
class ReportHaptics {
    std::mutex mutex;
    Clock::time_point began{};
    bool running=false;
    std::array<int,2> sent{{-1,-1}};
public:
    void start(Clock::time_point now=Clock::now()) {
        std::lock_guard<std::mutex> lock(mutex);began=now;running=true;sent={{-1,-1}};
    }
    bool active(Clock::time_point now=Clock::now()) {
        std::lock_guard<std::mutex> lock(mutex);
        return running && now-began<std::chrono::milliseconds(650);
    }
    bool route(int hand,float& delay,float& duration,float& frequency,float& amplitude,
               Clock::time_point now=Clock::now()) {
        std::lock_guard<std::mutex> lock(mutex);
        if (!running) return true;
        const auto ms=std::chrono::duration_cast<std::chrono::milliseconds>(now-began).count();
        if (ms>=650) {running=false;return true;}
        if (hand<0 || hand>1) return false;
        const int phase=ms<120?0:ms<220?1:ms<400?2:ms<500?3:4;
        if (sent[hand]==phase) return false;
        sent[hand]=phase;delay=0;frequency=1;amplitude=(phase==1 || phase==3)?5.0f:0.0f;
        duration=amplitude>0?.1f:.02f;
        return true;
    }
};
inline ReportHaptics& report_haptics() {static ReportHaptics value;return value;}

enum CostGroup {pre,post,stereo,input,cost_groups};
struct Cost {std::atomic<uint64_t> peak{0};};
struct Costs {std::atomic<bool> enabled{false};std::array<Cost,cost_groups> group;};
inline Costs& costs() {static Costs value;return value;}
class ScopedCost {
    Cost* cost;
    Clock::time_point began;
public:
    explicit ScopedCost(CostGroup group):cost(costs().enabled.load(std::memory_order_relaxed)?&costs().group[group]:nullptr) {
        if (cost) began=Clock::now();
    }
    ~ScopedCost() {
        if (!cost) return;
        const auto ns=static_cast<uint64_t>(std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-began).count());
        auto old=cost->peak.load(std::memory_order_relaxed);
        while (old<ns && !cost->peak.compare_exchange_weak(old,ns,std::memory_order_relaxed)) {}
    }
};
}
