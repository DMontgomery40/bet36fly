"""Small harmless child processes and synthetic parent lifecycle tests."""

import importlib
import json
from pathlib import Path
import sys

import pytest
from test_run_darela_shadow import plan


def module():
    return importlib.import_module("launch_darela_shadow")


def test_supervisor_kills_and_reaps_timed_out_child(tmp_path):
    result = module().supervise(
        [sys.executable, "-c", "import time; time.sleep(2)"], tmp_path, tmp_path, 0.03
    )
    assert result == dict(timed_out=True, exit_code=None, child_reaped=True)


@pytest.mark.parametrize("code", [0, 1, 7])
def test_supervisor_retains_exit_code(tmp_path, code):
    result = module().supervise([sys.executable, "-c", f"raise SystemExit({code})"], tmp_path, tmp_path, 2)
    assert result == dict(timed_out=False, exit_code=code, child_reaped=True)


@pytest.mark.parametrize(
    "failure", [None, "exit", "timeout", "late", "changed_plan", "validation", "persist"]
)
def test_parent_terminal_conjunction_and_interpreter(tmp_path, monkeypatch, failure):
    launch = module()
    p = plan(tmp_path)
    pp = tmp_path / "plan.json"
    pp.write_text(json.dumps(p))
    out = tmp_path / p["run_id"]
    now = [0.0]
    seen = []

    def child(command, cwd, output, timeout):
        seen.append(command)
        if failure == "late":
            now[0] = 1200
        if failure == "changed_plan":
            pp.write_text("{}")
        return dict(
            timed_out=failure == "timeout", exit_code=1 if failure == "exit" else 0, child_reaped=True
        )

    monkeypatch.setattr(launch, "supervise", child)

    def validate(*args, **kwargs):
        if failure == "validation":
            raise ValueError("synthetic invalid child")
        return dict(screen="pending_independent_audit", provisional_screen="rejected_fixed_hypothesis")

    monkeypatch.setattr(launch.runner, "validate_saved", validate)
    real = launch.runner.reader.atomic_json

    def persist(path, value):
        real(path, value)
        if failure == "persist" and Path(path).name == "parent-result.json":
            now[0] = 1200

    monkeypatch.setattr(launch.runner.reader, "atomic_json", persist)
    result = launch.execute(pp, out, clock=lambda: now[0])
    assert result["status"] == ("completed" if failure is None else "failed")
    assert seen[0][0] == str(launch.runner.ROOT / ".venv/bin/python")
    assert result["child_reaped"] is True
    if failure:
        assert (out / "terminal-error.json").is_file()
    else:
        with pytest.raises(FileExistsError):
            launch.execute(pp, out)


@pytest.mark.parametrize(
    "field,value", [("exit_code", False), ("exit_code", 0.0), ("timed_out", 0), ("child_reaped", 1)]
)
def test_subprocess_status_must_have_exact_types(tmp_path, monkeypatch, field, value):
    launch = module()
    p = plan(tmp_path)
    pp = tmp_path / "plan.json"
    pp.write_text(json.dumps(p))
    out = tmp_path / p["run_id"]

    def child(*args):
        result = dict(timed_out=False, exit_code=0, child_reaped=True)
        result[field] = value
        return result

    monkeypatch.setattr(launch, "supervise", child)
    monkeypatch.setattr(
        launch.runner,
        "validate_saved",
        lambda *a, **kw: dict(
            screen="pending_independent_audit", provisional_screen="rejected_fixed_hypothesis"
        ),
    )
    result = launch.execute(pp, out)
    assert result["status"] == "failed" and (out / "terminal-error.json").is_file()


def test_reviewed_output_modules_are_the_executed_modules():
    launch = module()
    assert Path(launch.__file__).resolve().parent == Path(__file__).resolve().parent
    assert Path(launch.runner.__file__).resolve().parent == Path(__file__).resolve().parent
