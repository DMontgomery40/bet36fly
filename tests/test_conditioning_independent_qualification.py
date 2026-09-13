"""Real diagnostic validator and qualifier on a labeled temporary synthetic pair."""

from pathlib import Path
import pytest
from conditioning_independent_gate_probes import run


def test_real_validator_positive_pair_and_qualification_binding_mutations():
    repository = next(
        (p for p in Path(__file__).resolve().parents if (p / "bet36fly/reward_evidence.py").is_file()), None
    )
    assert repository is not None
    archive = repository / "output/diagnostics/diag-rate-bridge-v1-maskgamma-de050d773763/trials.npz"
    if not archive.is_file():
        pytest.skip(
            "Requires preserved real diagnostic/anatomical identity inputs; all generated measurements remain synthetic."
        )
    result = run(repository)
    assert result["synthetic_only"] and result["native_calls"] == 0
    assert len(result["results"]) == 15
    assert result["all_expectations_met"], result
