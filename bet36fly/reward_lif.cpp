// Scheduled-input variant of the retained-connectome LIF kernel.
// The separate reward ABI keeps the accepted v1 kernel and its ABI unchanged.
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

// Instrumentation layout (filled only when record != 0; recording never alters dynamics):
//   signal_bins[bin][compartment][4]  = {sum of compartment-mean DAN spikes, DAN trace at bin end,
//                                        sum of the reference-subtracted DAN signal, reference per step}
//   kc_signal_bins[bin][2]            = {KC spikes in bin, sum of KC traces at bin end}
//   rule_bins[bin][group][7]          = {sum eta*Dbar*K, sum -eta*Kbar*D, applied gain change,
//                                        edges clipped low, edges clipped high, KC events on group edges,
//                                        sum of Kbar over group edges at bin end}
//   kc_trace_bins[bin][kc]            = KC trace at bin end
enum { SIGNAL_WIDTH = 4, KC_SIGNAL_WIDTH = 2, RULE_WIDTH = 7 };

extern "C" int simulate_reward(
    int n, const int64_t* ptr, const int32_t* post, const float* weights,
    int n_input, const int32_t* inputs, const float* rates, int rate_bin_steps,
    int steps, float dt, uint64_t seed,
    int n_kc, const int32_t* kc_indices,
    int n_dan, const int32_t* dan_indices, const int32_t* dan_compartments,
    int n_plastic, const int64_t* plastic_edges, const int32_t* plastic_kc,
    const int32_t* plastic_compartments, int n_compartments,
    float tau_ms, float learning_rate, float gain_min, float gain_max, float* gains,
    int onset_steps, int baseline_steps, float* tonic,
    int n_pulses, const int32_t* pulse_steps, const int32_t* pulse_dans,
    int n_sample, const int32_t* sample, int bin_steps,
    int32_t* counts, float* voltages, int32_t* trace, int32_t* population,
    int32_t* dan_counts, int32_t* compartment_dan_counts,
    int record, int n_groups, const int32_t* plastic_groups,
    double* signal_bins, double* kc_signal_bins, double* rule_bins, float* kc_trace_bins
) {
    try {
        Random rng{seed ? seed : 1};
        const int delay = int(std::round(1.8f / dt));
        const int refractory = int(std::round(2.2f / dt));
        const float em = std::exp(-dt / 20.0f), es = std::exp(-dt / 5.0f);
        const float coupled = 5.0f / (5.0f - 20.0f) * (es - em);
        std::vector<float> v(n, 0.0f), g(n, 0.0f);
        const float trace_decay = std::exp(-dt / tau_ms);
        std::vector<int> ready(n, 0), sample_index(n, -1), kc_index(n, -1), dan_index(n, -1);
        std::vector<int> edge_plastic(ptr[n], -1), dan_population_size(n_compartments, 0);
        std::vector<float> kc_trace(n_kc, 0.0f), dan_trace(n_compartments, 0.0f);
        // Phasic modulation is measured against the compartment's own tonic rate,
        // sampled in the window that ends at the declared plasticity onset.
        std::vector<float> dan_baseline(n_compartments, 0.0f), phasic(n_compartments, 0.0f);
        std::vector<int> dan_spikes(n_compartments, 0), baseline_spikes(n_compartments, 0);
        std::vector<unsigned char> spiked(n, 0);
        std::vector<unsigned char> is_input(n, 0);
        std::vector<std::vector<int>> events(delay + 1);
        // Per-bin accumulators for the optional instrumentation.
        std::vector<double> rule_acc(record ? size_t(n_groups) * RULE_WIDTH : 0, 0.0);
        std::vector<double> signal_acc(record ? size_t(n_compartments) * SIGNAL_WIDTH : 0, 0.0);
        double kc_spike_acc = 0.0;
        for (int k=0; k<n_input; ++k) is_input[inputs[k]] = 1;
        for (int k=0; k<n_sample; ++k) sample_index[sample[k]] = k;
        for (int k=0; k<n_kc; ++k) kc_index[kc_indices[k]] = k;
        for (int k=0; k<n_dan; ++k) {
            dan_index[dan_indices[k]] = k;
            ++dan_population_size[dan_compartments[k]];
        }
        for (int k=0; k<n_plastic; ++k) edge_plastic[plastic_edges[k]] = k;
        int pulse_cursor = 0;
        for (int t=0; t<steps; ++t) {
            const bool learning = t >= onset_steps;
            if (learning) {
                for (float& value : kc_trace) value *= trace_decay;
                for (float& value : dan_trace) value *= trace_decay;
            }
            auto& due = events[t % (delay + 1)];
            for (int pre : due)
                for (int64_t edge=ptr[pre]; edge<ptr[pre+1]; ++edge) {
                    const int plastic = edge_plastic[edge];
                    const float gain = plastic >= 0 ? gains[plastic] : 1.0f;
                    g[post[edge]] += weights[edge] * gain;
                }
            due.clear();
            for (int i=0; i<n; ++i) {
                if (t < ready[i]) continue;
                v[i] = v[i] * em + g[i] * coupled;
                g[i] *= es;
            }
            const int rate_bin = t / rate_bin_steps;
            const float* step_rates = rates + int64_t(rate_bin) * n_input;
            for (int k=0; k<n_input; ++k)
                if (rng.uniform() < step_rates[k] * dt / 1000.0f) v[inputs[k]] += 68.75f;
            while (pulse_cursor < n_pulses && pulse_steps[pulse_cursor] == t) {
                v[dan_indices[pulse_dans[pulse_cursor]]] += 68.75f;
                ++pulse_cursor;
            }
            std::fill(spiked.begin(), spiked.end(), 0);
            std::fill(dan_spikes.begin(), dan_spikes.end(), 0);
            for (int i=0; i<n; ++i) {
                if (t >= ready[i] && v[i] > 7.0f) {
                    spiked[i] = 1;
                    const int dan = dan_index[i];
                    if (dan >= 0) ++dan_spikes[dan_compartments[dan]];
                }
            }
            if (t >= onset_steps - baseline_steps && t < onset_steps)
                for (int compartment=0; compartment<n_compartments; ++compartment)
                    baseline_spikes[compartment] += dan_spikes[compartment];
            if (t == onset_steps)
                for (int compartment=0; compartment<n_compartments; ++compartment) {
                    const int population_size = dan_population_size[compartment];
                    dan_baseline[compartment] = (baseline_steps && population_size)
                        ? float(baseline_spikes[compartment]) / (float(baseline_steps) * population_size)
                        : 0.0f;
                }
            if (record) {
                for (int compartment=0; compartment<n_compartments; ++compartment) {
                    const int population_size = dan_population_size[compartment];
                    signal_acc[compartment * SIGNAL_WIDTH + 0] +=
                        population_size ? double(dan_spikes[compartment]) / population_size : 0.0;
                }
                for (int k=0; k<n_kc; ++k) kc_spike_acc += spiked[kc_indices[k]] ? 1.0 : 0.0;
            }
            if (learning) {
                for (int compartment=0; compartment<n_compartments; ++compartment) {
                    const int population_size = dan_population_size[compartment];
                    phasic[compartment] = population_size
                        ? float(dan_spikes[compartment]) / population_size - dan_baseline[compartment]
                        : 0.0f;
                    if (record) {
                        signal_acc[compartment * SIGNAL_WIDTH + 2] += phasic[compartment];
                        signal_acc[compartment * SIGNAL_WIDTH + 3] = dan_baseline[compartment];
                    }
                }
                for (int k=0; k<n_plastic; ++k) {
                    const int compartment = plastic_compartments[k];
                    const int kc = plastic_kc[k];
                    const float kc_spike = spiked[kc_indices[kc]] ? 1.0f : 0.0f;
                    const float delta = learning_rate
                        * (dan_trace[compartment] * kc_spike - kc_trace[kc] * phasic[compartment]);
                    const float before = gains[k];
                    const float proposed = before + delta;
                    gains[k] = std::clamp(proposed, gain_min, gain_max);
                    if (record) {
                        double* acc = rule_acc.data() + size_t(plastic_groups[k]) * RULE_WIDTH;
                        acc[0] += double(learning_rate) * double(dan_trace[compartment]) * double(kc_spike);
                        acc[1] -= double(learning_rate) * double(kc_trace[kc]) * double(phasic[compartment]);
                        acc[2] += double(gains[k]) - double(before);
                        if (proposed < gain_min) acc[3] += 1.0;
                        if (proposed > gain_max) acc[4] += 1.0;
                        acc[5] += kc_spike;
                    }
                }
                for (int k=0; k<n_kc; ++k)
                    if (spiked[kc_indices[k]]) kc_trace[k] += 1.0f;
                for (int compartment=0; compartment<n_compartments; ++compartment)
                    dan_trace[compartment] += phasic[compartment];
            }
            const int bin = t / bin_steps;
            auto& later = events[(t + delay) % (delay + 1)];
            for (int i=0; i<n; ++i) {
                if (!spiked[i]) continue;
                ++counts[i]; ++population[bin];
                const int sampled = sample_index[i];
                if (sampled >= 0) ++trace[bin * n_sample + sampled];
                const int dan = dan_index[i];
                if (dan >= 0) ++dan_counts[dan];
                later.push_back(i);
                v[i] = 0.0f; g[i] = 0.0f;
                ready[i] = t + (is_input[i] ? 0 : refractory);
            }
            if (record && (t + 1) % bin_steps == 0) {
                for (int compartment=0; compartment<n_compartments; ++compartment) {
                    double* out = signal_bins + (size_t(bin) * n_compartments + compartment) * SIGNAL_WIDTH;
                    out[0] = signal_acc[compartment * SIGNAL_WIDTH + 0];
                    out[1] = dan_trace[compartment];
                    out[2] = signal_acc[compartment * SIGNAL_WIDTH + 2];
                    out[3] = signal_acc[compartment * SIGNAL_WIDTH + 3];
                }
                double kc_mass = 0.0;
                for (int k=0; k<n_kc; ++k) {
                    kc_mass += kc_trace[k];
                    kc_trace_bins[size_t(bin) * n_kc + k] = kc_trace[k];
                }
                kc_signal_bins[size_t(bin) * KC_SIGNAL_WIDTH + 0] = kc_spike_acc;
                kc_signal_bins[size_t(bin) * KC_SIGNAL_WIDTH + 1] = kc_mass;
                for (int k=0; k<n_plastic; ++k)
                    rule_acc[size_t(plastic_groups[k]) * RULE_WIDTH + 6] += kc_trace[plastic_kc[k]];
                for (int group=0; group<n_groups; ++group)
                    for (int term=0; term<RULE_WIDTH; ++term)
                        rule_bins[(size_t(bin) * n_groups + group) * RULE_WIDTH + term] =
                            rule_acc[size_t(group) * RULE_WIDTH + term];
                std::fill(rule_acc.begin(), rule_acc.end(), 0.0);
                std::fill(signal_acc.begin(), signal_acc.end(), 0.0);
                kc_spike_acc = 0.0;
            }
        }
        for (int k=0; k<n_dan; ++k)
            compartment_dan_counts[dan_compartments[k]] += dan_counts[k];
        for (int compartment=0; compartment<n_compartments; ++compartment)
            tonic[compartment] = dan_baseline[compartment];
        for (int i=0; i<n; ++i) voltages[i] = v[i] - 52.0f;
        return 0;
    } catch (...) { return 1; }
}
