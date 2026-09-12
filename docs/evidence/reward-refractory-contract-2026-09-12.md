# Reward input delivery during refractory

Checked September 12, 2026 UTC. This is a native dynamics correction, not a
conditioning result or a new SCI-001 verdict. The drive gains, teaching channels,
plasticity equation, gain bounds and eligibility masks are unchanged.

The retained phase-1 kernel accepted synaptic conductance increments and teaching
voltage impulses while a target's integration and threshold were refractory.
Those increments were stored and could act at release. A teaching pulse at 0 ms
followed by an instantaneous pulse at 1 ms therefore produced spikes at 0 and
2.2 ms even though no pulse was scheduled at release. An excitatory arrival during
refractory could produce the same delayed extra spike; an inhibitory arrival
could leave a delayed negative voltage. The earlier teaching test stopped at
2 ms and could not detect the extra spike.

The reward kernel now discards both kinds of input when `t < ready[target]`.
Rejection is per target: other available targets still receive signed synaptic
input, and sensory cells retain their zero-refractory behavior. Scheduled pulse
metadata records the request; actual DAN counts and sampled spike bins record
its effect. Duplicate same-step pulses still produce at most one threshold event.
Recording and plasticity enablement do not change input acceptance.

## Reference and exact boundary

The inspected [Shiu model.py](https://github.com/philshiu/Drosophila_brain_model/blob/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960/model.py)
(commit `91bdd1e7dcf193f3e7ca5a8933497fcef63b7960`, checked September 12) declares both
voltage and conductance with `unless refractory`, uses `g += w` for synaptic
input and assigns sensory neurons zero refractory duration. The
[Brian 2 refractory documentation](https://brian2.readthedocs.io/en/stable/user/refractoriness.html)
(stable documentation, checked September 12) states that flagged state variables
are read-only during refractory, including incoming synaptic writes. These sources
support rejecting the stored inputs. This is an inspected contract, not a new
reproduction of the full Brian network.

This change deliberately retains the local integer-step release boundary:
`ready = spike_step + round(2.2 / dt)`; a target accepts input and may spike when
`step >= ready`. At the supported `dt = 0.2 ms`, a spike at step 0 rejects input
at steps 1 through 10, and accepts input at step 11 (2.2 ms) or later. Recurrent
transmission remains delayed by 9 steps (1.8 ms), delivered before integration;
teaching is applied after integration and before threshold evaluation. Brian's
published refractory explanation uses an elapsed-time `<= refractory` condition
with integer-timestep handling. That can differ at exact equality depending on
its scheduling contract. Brian 2 is not installed in this environment; no tiny
Brian boundary reproduction was run. We therefore make no claim of bit-exact
Brian timing alignment. Changing the release convention is a separate model
change and is not hidden inside this input-banking repair.

## Regression scope and limits

`tests/test_reward_brain.py` now runs through release and subsequent release,
covering early, middle, immediately-before, exact and after-release teaching,
repeated rejected pulses, duplicated pulses, independent DANs, frozen/learning
calls, recorded/unrecorded parity and an independent pair-sum gain expectation
using actual spikes. Recurrent delivery tests cover both signs, target-specific
acceptance, exact delay/release and sensory zero refractory. The pre-fix run
failed 25 cases and passed 19; the five sensory cases and accepted-boundary cases
already passed, so the tests distinguish rejection from blanket input suppression.

The v1 kernel and checkpoint remain unchanged. A retained synthetic constant-drive
case now explicitly records the intentional difference: historical v1 counts
`[7, 4, 4]`, repaired reward counts `[7, 4, 3]`. When inputs do not reach a
postsynaptic firing threshold, reward and v1 remain bit-exact for counts, voltage,
sampled bins and population. The broader claim that frozen reward always equals
v1 is no longer accurate because freezing plasticity does not restore the old
input-delivery defect.

This correction can alter endogenous spike histories. Its contribution to
full-circuit untaught drift, acquisition or reversal has not yet been measured.
Historical diagnostics and scientific holds retain their original verdicts.
