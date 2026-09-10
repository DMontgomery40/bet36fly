// Full retained-connectome leaky integrate-and-fire simulation on CPU.
// Shiu et al. (Nature 2024) equations/parameter values; independently implemented.
// Exact subthreshold integration between discrete events; dt=0.2 ms preserves
// 1.8 ms transmission delay and 2.2 ms refractory duration without rounding.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>

struct Random {
    uint64_t state;
    float uniform() {
        state ^= state >> 12; state ^= state << 25; state ^= state >> 27;
        return float((state * 2685821657736338717ULL) >> 40) / 16777216.0f;
    }
};

extern "C" int simulate(
    int n, const int64_t* ptr, const int32_t* post, const float* weights,
    int n_input, const int32_t* inputs, const float* rates,
    int steps, float dt, uint64_t seed, int n_sample, const int32_t* sample,
    int bin_steps, int32_t* counts, float* voltages, int32_t* trace, int32_t* population
) {
    try {
        Random rng{seed ? seed : 1};
        const int delay = int(std::round(1.8f / dt));
        const int refractory = int(std::round(2.2f / dt));
        const float em = std::exp(-dt / 20.0f), es = std::exp(-dt / 5.0f);
        const float coupled = 5.0f / (5.0f - 20.0f) * (es - em);
        std::vector<float> v(n, 0.0f), g(n, 0.0f);
        std::vector<int> ready(n, 0), sample_index(n, -1);
        std::vector<unsigned char> is_input(n, 0);
        std::vector<std::vector<int>> events(delay + 1);
        for (int k=0; k<n_input; ++k) is_input[inputs[k]] = 1;
        for (int k=0; k<n_sample; ++k) sample_index[sample[k]] = k;
        for (int t=0; t<steps; ++t) {
            auto& due = events[t % (delay + 1)];
            for (int pre : due)
                for (int64_t edge=ptr[pre]; edge<ptr[pre+1]; ++edge)
                    g[post[edge]] += weights[edge];
            due.clear();
            for (int i=0; i<n; ++i) {
                if (t < ready[i]) continue;
                v[i] = v[i] * em + g[i] * coupled;
                g[i] *= es;
            }
            // Artificial Poisson sensory stimulation of the declared ALPN ports.
            // Reference stimulation adds .275 mV * 250 to v and disables input refractory.
            for (int k=0; k<n_input; ++k)
                if (rng.uniform() < rates[k] * dt / 1000.0f) v[inputs[k]] += 68.75f;
            const int bin = t / bin_steps;
            auto& later = events[(t + delay) % (delay + 1)];
            for (int i=0; i<n; ++i) {
                if (t < ready[i] || v[i] <= 7.0f) continue; // -45 minus -52 mV
                ++counts[i]; ++population[bin];
                int k = sample_index[i];
                if (k >= 0) ++trace[bin * n_sample + k];
                later.push_back(i);
                v[i] = 0.0f; g[i] = 0.0f;
                ready[i] = t + (is_input[i] ? 0 : refractory);
            }
        }
        for (int i=0; i<n; ++i) voltages[i] = v[i] - 52.0f;
        return 0;
    } catch (...) { return 1; }
}
