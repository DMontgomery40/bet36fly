"""Synthetic native-return fixtures transcribed from RewardEngine.run, not writer helpers."""

import copy
import json

import numpy as np


def numeric_fixture(*, plasticity=True, record=True, duration=400):
    from bet36fly.conditioning import NumericSchema

    schema = NumericSchema(
        neurons=32,
        samples=4,
        kcs=4,
        dans=24,
        edges=6,
        groups=8,
        bins=duration // 10,
        steps=duration * 5,
        duration_ms=duration,
        learning_rule="rate-bridge-v1",
        record=record,
        plasticity=plasticity,
    )
    b, t = duration // 10, duration * 5
    mapping = np.array([0, 0, 0, 4, 4, 4], np.int32)
    compartments = np.array([0, 0, 0, 1, 1, 1], np.int32)
    arrays = {
        "counts": ((32,), np.int32),
        "rates": ((32,), np.float32),
        "rates_hz": ((32,), np.float32),
        "voltage": ((32,), np.float32),
        "trace": ((b, 4), np.int32),
        "population": ((b,), np.int32),
        "dan_counts": ((24,), np.int32),
        "compartment_dan_counts": ((2,), np.int32),
        "compartment_tonic_hz": ((2,), np.float32),
        "gain_delta": ((6,), np.float32),
        "pulse_times_ms": ((0,), np.float32),
        "pulse_dan_indices": ((0,), np.int32),
    }
    result = {k: np.zeros(shape, dtype) for k, (shape, dtype) in arrays.items()}
    result.update(
        gains=np.ones(6, np.float32),
        duration_ms=float(duration),
        dt=0.2,
        bin_ms=10.0,
        wall_seconds=0.1,
        instrumentation=None,
    )
    if record:
        rec_arrays = {
            "signal_bins": ((b, 2, 4), np.float64),
            "kc_signal_bins": ((b, 2), np.float64),
            "step_signals": ((t, 5), np.float32),
            "bridge_signals": ((t, 2, 2), np.float64),
            "bridge_kc_bins": ((b, 4, 2), np.float64),
            "bridge_kc_used": ((t, 8, 2), np.float64),
            "bridge_rule": ((t, 8, 8), np.float64),
            "bridge_tail": ((8, 8), np.float64),
        }
        fields = [
            "positive_integral",
            "negative_integral",
            "attempted",
            "double_applied",
            "published_applied",
            "bound_low",
            "bound_high",
            "q_used",
        ]
        layout = dict(
            bridge_signals=["dan_rate_after_injection", "dan_eligibility_prior"],
            bridge_kc_bins=["kc_rate_bin_end", "kc_eligibility_bin_end"],
            bridge_kc_used=["eligible_edge_kc_rate_mass", "eligible_edge_kc_eligibility_mass"],
            bridge_rule=fields,
            bridge_tail=fields,
            step_signals=["kc_spikes", "dan_mean_spikes per compartment", "unused zeros"],
            signal_bins=["dan_mean_spikes", "unused zero", "raw_dan_spikes", "zero_reference"],
            kc_signal_bins=["kc_spikes", "unused zero"],
        )
        rec = {k: np.zeros(shape, dtype) for k, (shape, dtype) in rec_arrays.items()}
        rec.update(
            plastic_groups=mapping.copy(),
            plastic_compartments=compartments.copy(),
            learning_rule="rate-bridge-v1",
            layout_version="rate-bridge-v1/1",
            event_rule_applicable=False,
            layout=layout,
            config=dict(
                h_ms=0.2,
                tau_ms=500.0,
                rate_tau_ms=100.0,
                effective_eta=0.0005 if plasticity else 0.0,
                normalization=0.96,
                tail="analytic_no_new_event_tail",
                checkpoint="float32; double remainder discarded",
            ),
        )
        result["instrumentation"] = rec
    kwargs = dict(mask=np.ones(6, np.uint8), groups=mapping, compartments=compartments)
    return result, np.ones(6, np.float32), schema, kwargs


def review_cases():
    from bet36fly.conditioning import validate_gain_evidence, validate_numeric_result

    observations = []

    def run(name, expected, fixture, numeric_only=False):
        result, before, schema, kwargs = fixture
        try:
            if numeric_only:
                validate_numeric_result(result, schema)
            else:
                validate_gain_evidence(result, before, schema, **kwargs)
            accepted, error = True, None
        except (ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
            accepted, error = False, str(exc)
        observations.append(
            dict(
                case=name,
                expected_acceptance=expected,
                actual_acceptance=accepted,
                matches=accepted == expected,
                error=error,
            )
        )

    run("valid_complete_quiet_recorded_return", True, numeric_fixture())
    run("valid_complete_frozen_recorded_return", True, numeric_fixture(plasticity=False))
    run("valid_complete_unrecorded_return", True, numeric_fixture(record=False))
    for phase in ("bridge_rule", "bridge_tail"):
        f = numeric_fixture(plasticity=False)
        a = f[0]["instrumentation"][phase]
        row = a[10, 0] if a.ndim == 3 else a[0]
        row[0], row[1] = 0.1, -0.1
        run(f"frozen_cancelling_nonzero_products_{phase}", False, f)
        f = numeric_fixture()
        a = f[0]["instrumentation"][phase]
        row = a[10, 0] if a.ndim == 3 else a[0]
        row[0], row[2] = 0.1, 0.1
        run(f"attempted_without_double_applied_or_bound_{phase}", False, f)
    f = numeric_fixture()
    f[0]["instrumentation"]["bridge_rule"][10, 0, 4] = 0.01
    f[0]["instrumentation"]["bridge_rule"][11, 0, 4] = -0.01
    run("publication_moves_without_double_gain_movement", False, f)
    f = numeric_fixture()
    f[0]["gains"][0] = np.nextafter(np.float32(1), np.float32(1.5))
    f[0]["gain_delta"] = f[0]["gains"] - f[1]
    run("one_ulp_active_gain_change_without_recorded_publication", False, f)
    for name in ("bridge_signals", "bridge_kc_bins", "bridge_kc_used", "step_signals"):
        f = numeric_fixture()
        f[0]["instrumentation"][name].flat[0] = -1
        run(f"negative_nonnegative_signal_{name}", False, f, numeric_only=True)
    for name in ("step_signals", "signal_bins", "kc_signal_bins"):
        f = numeric_fixture()
        a = f[0]["instrumentation"][name]
        if name == "step_signals":
            a[0, -1] = 1
        elif name == "signal_bins":
            a[0, 0, 1] = 1
        else:
            a[0, 1] = 1
        run(f"nonzero_unused_bridge_field_{name}", False, f, numeric_only=True)
    f = numeric_fixture(plasticity=False)
    f[0]["instrumentation"]["config"]["effective_eta"] = False
    run("boolean_effective_eta_is_not_numeric_contract", False, f, numeric_only=True)
    # A matching malformed replay must not become valid through equality alone.
    from bet36fly.conditioning import compare_numeric_results

    f = numeric_fixture()
    f[0]["instrumentation"]["bridge_signals"].flat[0] = -1
    try:
        accepted = compare_numeric_results(f[0], copy.deepcopy(f[0]), schema=f[2])["passed"]
    except (ValueError, TypeError, KeyError, IndexError, OverflowError):
        accepted = False
    observations.append(
        dict(
            case="matching_invalid_signal_replay",
            expected_acceptance=False,
            actual_acceptance=accepted,
            matches=not accepted,
            error=None,
        )
    )
    return observations


if __name__ == "__main__":
    rows = review_cases()
    print(
        json.dumps(
            dict(
                scope="Synthetic current-writer API probe; no engine/native calls.",
                cases=rows,
                discrepancies=sum(not x["matches"] for x in rows),
            ),
            indent=2,
        )
    )
