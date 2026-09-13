// Isolated plasticity-off sensory engine. Historical engines remain unchanged.
// Dynamics follow the inspected Shiu-style implementation; injected events are
// counted separately from actual sensory spikes, including recurrent effects.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>

struct SensoryRandom {
    uint64_t state;
    float uniform() {
        state ^= state >> 12; state ^= state << 25; state ^= state >> 27;
        return float((state * 2685821657736338717ULL) >> 40) / 16777216.0f;
    }
};

extern "C" int simulate_sensory(
    int n, const int64_t* ptr, const int32_t* post, const float* weights,
    int ni, const int32_t* inputs, const float* rates, int bin_steps,
    int steps, float dt, uint64_t seed, int ns, const int32_t* sample,
    int32_t* counts, float* voltage, int32_t* trace, int32_t* input_events,
    int32_t* population, double* extrema
) {
    try {
        SensoryRandom rng{seed ? seed : 1};
        const int delay = int(std::round(1.8f / dt));
        const int refractory = int(std::round(2.2f / dt));
        const float em = std::exp(-dt / 20.0f), es = std::exp(-dt / 5.0f);
        const float coupled = 5.0f / (5.0f - 20.0f) * (es - em);
        std::vector<float> v(n, 0), g(n, 0);
        std::vector<int> ready(n, 0), sampled(n, -1);
        std::vector<unsigned char> is_input(n, 0);
        std::vector<std::vector<int>> events(delay + 1);
        for (int k=0;k<ni;++k) is_input[inputs[k]]=1;
        for (int k=0;k<ns;++k) sampled[sample[k]]=k;
        for (int t=0;t<steps;++t) {
            auto& due=events[t % (delay+1)];
            for (int pre: due) for (int64_t e=ptr[pre];e<ptr[pre+1];++e) {
                const int target=post[e];
                if (t >= ready[target]) g[target]+=weights[e];
            }
            due.clear();
            for (int i=0;i<n;++i) if (t >= ready[i]) {
                v[i]=v[i]*em+g[i]*coupled;
                g[i]*=es;
            }
            const int bin=t/bin_steps;
            for (int k=0;k<ni;++k) {
                if (rng.uniform() < rates[int64_t(bin)*ni+k]*dt/1000.0f) {
                    ++input_events[int64_t(bin)*ni+k];
                    v[inputs[k]]+=68.75f;
                }
            }
            auto& later=events[(t+delay) % (delay+1)];
            for (int i=0;i<n;++i) {
                if (!std::isfinite(v[i]) || !std::isfinite(g[i])) return 2;
                extrema[0]=std::max(extrema[0],double(std::abs(v[i])));
                extrema[1]=std::max(extrema[1],double(std::abs(g[i])));
                if (extrema[0]>1e6 || extrema[1]>1e6) return 3;
                if (t >= ready[i] && v[i]>7.0f) {
                    ++counts[i]; ++population[bin];
                    if (sampled[i]>=0) ++trace[int64_t(bin)*ns+sampled[i]];
                    later.push_back(i);
                    v[i]=0; g[i]=0;
                    ready[i]=t+(is_input[i] ? 0 : refractory);
                }
            }
        }
        for (int i=0;i<n;++i) voltage[i]=v[i]-52.0f;
        return 0;
    } catch (...) { return 1; }
}
