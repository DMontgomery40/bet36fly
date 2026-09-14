// Associative (dopamine-gated) full-graph LIF engine with persistent KC->MBON gains.
//
// New identity: it does not modify sensory_lif.cpp, lif.cpp or reward_lif.cpp.
// Electrical dynamics follow the same Shiu-style contract as sensory_lif.cpp
// (0.2 ms step, 20/5 ms constants, 1.8 ms delay, 2.2 ms refractory, 7 mV
// threshold above rest, 68.75 mV external events, designated sensory inputs
// exempt from refractory delay). Differences from sensory_lif.cpp:
//   * listed plastic edges transmit weights[e] * gains[k];
//   * a separate Poisson reinforcer drive can excite listed cells (normally
//     dopamine neurons); those cells keep their ordinary refractory period and
//     the delivered events are counted separately from sensory input events;
//   * per-step dopamine-gated plasticity with explicit eligibility traces;
//   * an active-set integrator: neurons whose membrane and synaptic state are
//     both below 1e-6 mV are exactly zeroed and skipped until input arrives.
//
// Plasticity rule (per step, eligible edge k from KC j into compartment c):
//   D_c        = spikes of compartment-c DAN cells this step / cell count * coupling_c
//   delta_k    = eta * (Dbar_c * K_j - Kbar_j * D_c)
//   gain_k     = clamp(gain_k + delta_k, gain_min, gain_max)
//   then Kbar_j += K_j, Dbar_c += D_c (traces decay by exp(-dt/tau) at step start).
// KC activity followed by dopamine depresses; dopamine followed by KC activity
// potentiates; an isolated coincident pair is neutral. This is the inspected
// Jiang & Litwin-Kumar opposing-term form in event units, not a receptor model.
//
// Optional continual-learning term (version 2, recovery[c] > 0), after Jiang & Litwin-Kumar
// 2021 Eq. 5 (dw/dt = ... + beta * rbar_DAN): dopamine-gated non-specific potentiation. Deviations
// (documented in docs/EXPERIMENT_ASSOCIATIVE.md): it is applied only to eligible edges whose KC has
// exactly zero eligibility trace this step (dopamine WITHOUT that KC's activity), and it moves the gain
// toward the resting gain, never past it:
//   if Kbar_j == 0 and gain_k < rest:  gain_k += beta_c * Dbar_c * (rest - gain_k)
// comp_bins[bin][c][8] = {sum of coupled D_c, sum of potentiation terms,
//   sum of depression terms, applied gain change (float32 endpoints), low-bound
//   contacts, high-bound contacts, Kbar mass over eligible edges at bin end,
//   sum of recovery terms}.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>

struct AssociativeRandom {
    uint64_t state;
    float uniform() {
        state ^= state >> 12; state ^= state << 25; state ^= state >> 27;
        return float((state * 2685821657736338717ULL) >> 40) / 16777216.0f;
    }
};

extern "C" int simulate_associative(
    int n, const int64_t* ptr, const int32_t* post, const float* weights,
    int ni, const int32_t* inputs, const float* rates,
    int nd, const int32_t* drive, const float* drive_rates,
    int bin_steps, int steps, float dt, uint64_t seed,
    int n_kc, const int32_t* kc_indices,
    int n_dan, const int32_t* dan_indices, const int32_t* dan_comp, int n_comp, const float* coupling,
    int n_plastic, const int64_t* plastic_edges, const int32_t* plastic_kc,
    const int32_t* plastic_comp, const uint8_t* plastic_mask,
    float* gains, float tau_kc, float tau_dan, float eta, float gain_min, float gain_max,
    float* kc_trace, float* dan_trace, const float* recovery, float rest_gain,
    int ns, const int32_t* sample,
    int32_t* counts, float* voltage, int32_t* trace, int32_t* input_events, int32_t* drive_events,
    int32_t* population, double* comp_bins, double* extrema, double* audit
) {
    try {
        AssociativeRandom rng{seed ? seed : 1};
        const int delay = int(std::round(1.8f / dt));
        const int refractory = int(std::round(2.2f / dt));
        const float em = std::exp(-dt / 20.0f), es = std::exp(-dt / 5.0f);
        const float coupled = 5.0f / (5.0f - 20.0f) * (es - em);
        const float dk = std::exp(-dt / tau_kc), dd = std::exp(-dt / tau_dan);
        const float prune = 1e-6f;
        std::vector<float> v(n, 0), g(n, 0);
        std::vector<int> ready(n, 0), sampled(n, -1), kc_of(n, -1), dan_of(n, -1);
        std::vector<int> edge_plastic(ptr[n], -1), comp_size(n_comp, 0), comp_spikes(n_comp, 0);
        std::vector<unsigned char> is_input(n, 0), active_flag(n, 0), spiked_kc(n_kc, 0);
        std::vector<int> active, next_active, spikes;
        std::vector<float> D(n_comp, 0);
        std::vector<std::vector<int>> events(delay + 1);
        for (int k=0;k<ni;++k) is_input[inputs[k]]=1;
        for (int k=0;k<ns;++k) sampled[sample[k]]=k;
        for (int k=0;k<n_kc;++k) kc_of[kc_indices[k]]=k;
        for (int k=0;k<n_dan;++k) { dan_of[dan_indices[k]]=k; ++comp_size[dan_comp[k]]; }
        for (int k=0;k<n_plastic;++k) edge_plastic[plastic_edges[k]]=k;
        const bool learning = eta > 0.0f;
        auto activate = [&](int i) { if (!active_flag[i]) { active_flag[i]=1; active.push_back(i); } };
        double active_steps = 0.0;
        for (int t=0;t<steps;++t) {
            const int bin = t / bin_steps;
            if (learning) {
                for (int j=0;j<n_kc;++j) kc_trace[j]*=dk;
                for (int c=0;c<n_comp;++c) dan_trace[c]*=dd;
            }
            auto& due=events[t % (delay+1)];
            for (int pre: due) for (int64_t e=ptr[pre];e<ptr[pre+1];++e) {
                const int target=post[e];
                if (t < ready[target]) continue;
                const int k=edge_plastic[e];
                g[target]+= k>=0 ? weights[e]*gains[k] : weights[e];
                activate(target);
            }
            due.clear();
            for (int k=0;k<ni;++k) {
                if (rng.uniform() < rates[int64_t(bin)*ni+k]*dt/1000.0f) {
                    ++input_events[int64_t(bin)*ni+k];
                    v[inputs[k]]+=68.75f;
                    activate(inputs[k]);
                }
            }
            for (int k=0;k<nd;++k) {
                // A zero-rate drive cell consumes no randomness, so a schedule without
                // reinforcer drive reproduces the sensory engine's event stream exactly.
                const float rate=drive_rates[int64_t(bin)*nd+k];
                if (rate>0.0f && rng.uniform() < rate*dt/1000.0f) {
                    ++drive_events[int64_t(bin)*nd+k];
                    const int target=drive[k];
                    if (t >= ready[target]) { v[target]+=68.75f; activate(target); }
                }
            }
            active_steps += double(active.size());
            spikes.clear();
            next_active.clear();
            std::fill(comp_spikes.begin(), comp_spikes.end(), 0);
            for (int i: active) {
                if (t >= ready[i]) {
                    v[i]=v[i]*em+g[i]*coupled;
                    g[i]*=es;
                }
                if (!std::isfinite(v[i]) || !std::isfinite(g[i])) return 2;
                const double av=std::abs(v[i]), ag=std::abs(g[i]);
                extrema[0]=std::max(extrema[0],av);
                extrema[1]=std::max(extrema[1],ag);
                if (extrema[0]>1e6 || extrema[1]>1e6) return 3;
                if (t >= ready[i] && v[i]>7.0f) {
                    spikes.push_back(i);
                    const int d=dan_of[i];
                    if (d>=0) ++comp_spikes[dan_comp[d]];
                    v[i]=0; g[i]=0;
                    ready[i]=t+(is_input[i] ? 0 : refractory);
                    active_flag[i]=0;
                    continue;
                }
                if (av<prune && ag<prune) { v[i]=0; g[i]=0; active_flag[i]=0; continue; }
                next_active.push_back(i);
            }
            active.swap(next_active);
            auto& later=events[(t+delay) % (delay+1)];
            for (int i: spikes) {
                ++counts[i]; ++population[bin];
                if (sampled[i]>=0) ++trace[int64_t(bin)*ns+sampled[i]];
                later.push_back(i);
                const int j=kc_of[i];
                if (j>=0) spiked_kc[j]=1;
            }
            for (int c=0;c<n_comp;++c) {
                D[c]= comp_size[c] ? float(comp_spikes[c])/float(comp_size[c])*coupling[c] : 0.0f;
                comp_bins[(int64_t(bin)*n_comp+c)*8+0]+=D[c];
            }
            if (learning) {
                for (int k=0;k<n_plastic;++k) {
                    if (!plastic_mask[k]) continue;
                    const int j=plastic_kc[k], c=plastic_comp[k];
                    const float K=spiked_kc[j] ? 1.0f : 0.0f;
                    double* row=comp_bins+(int64_t(bin)*n_comp+c)*8;
                    if (K==0.0f && kc_trace[j]==0.0f && recovery[c]>0.0f && dan_trace[c]>0.0f) {
                        // Dopamine without this KC's activity: recover a depressed synapse toward rest.
                        const float before=gains[k];
                        if (before<rest_gain) {
                            const float rec=eta*recovery[c]*dan_trace[c]*(rest_gain-before);
                            gains[k]=std::min(before+rec,rest_gain);
                            row[7]+=rec; row[3]+=double(gains[k])-double(before);
                        }
                        continue;
                    }
                    if (K==0.0f && D[c]==0.0f) continue;
                    const float pot=eta*dan_trace[c]*K, dep=-eta*kc_trace[j]*D[c];
                    const float before=gains[k];
                    const float proposed=before+(pot+dep);
                    gains[k]=std::clamp(proposed,gain_min,gain_max);
                    row[1]+=pot; row[2]+=dep; row[3]+=double(gains[k])-double(before);
                    if (proposed<=gain_min) row[4]+=1.0;
                    if (proposed>=gain_max) row[5]+=1.0;
                }
                for (int j=0;j<n_kc;++j) if (spiked_kc[j]) kc_trace[j]+=1.0f;
                for (int c=0;c<n_comp;++c) dan_trace[c]+=D[c];
                if ((t+1) % bin_steps == 0)
                    for (int k=0;k<n_plastic;++k)
                        if (plastic_mask[k])
                            comp_bins[(int64_t(bin)*n_comp+plastic_comp[k])*8+6]+=kc_trace[plastic_kc[k]];
            }
            for (int i: spikes) { const int j=kc_of[i]; if (j>=0) spiked_kc[j]=0; }
        }
        for (int i=0;i<n;++i) voltage[i]=v[i]-52.0f;
        audit[0]=active_steps; audit[1]=double(active.size());
        return 0;
    } catch (...) { return 1; }
}
