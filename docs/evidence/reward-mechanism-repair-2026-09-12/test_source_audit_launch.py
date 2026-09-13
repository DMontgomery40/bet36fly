"""Regression family: symlinked Python must retain its environment identity."""

import json
from pathlib import Path

import pytest

from source_audit_launch import command, environment_python, probe_environment

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("alias", ["plain", "repo with spaces", "repo $literal"])
def test_child_imports_and_prefix_use_invoked_environment_through_repository_alias(tmp_path, alias):
    repository = tmp_path / alias
    repository.symlink_to(ROOT, target_is_directory=True)
    interpreter = environment_python(repository)
    assert interpreter == repository / ".venv/bin/python"
    assert str(interpreter) != str(interpreter.resolve())
    result = json.loads(probe_environment(repository).stdout)
    assert Path(result["prefix"]).samefile(ROOT / ".venv")
    assert not Path(result["prefix"]).samefile(result["base_prefix"])
    assert result["numpy"] and result["pandas"]


def test_relative_repository_preserves_virtual_environment_invocation(monkeypatch):
    monkeypatch.chdir(ROOT)
    assert environment_python(Path(".")) == ROOT / ".venv/bin/python"


@pytest.mark.parametrize("argument", ["file with spaces.py", "$literal", "`literal`", "line\nbreak"])
def test_arguments_remain_literal_argv_values(argument):
    assert command(ROOT, [argument, "--run"]) == [str(ROOT / ".venv/bin/python"), argument, "--run"]


@pytest.mark.parametrize("condition", ["missing", "broken_symlink", "no_config", "not_executable"])
def test_missing_or_invalid_environment_is_rejected_before_child(tmp_path, condition):
    interpreter = tmp_path / ".venv/bin/python"
    interpreter.parent.mkdir(parents=True)
    if condition == "broken_symlink":
        interpreter.symlink_to(tmp_path / "absent-python")
    elif condition == "no_config":
        interpreter.symlink_to(ROOT / ".venv/bin/python")
    elif condition == "not_executable":
        interpreter.write_text("not executable")
        interpreter.chmod(0o600)
        (interpreter.parent.parent / "pyvenv.cfg").write_text("home = /unused\n")
    with pytest.raises(ValueError):
        environment_python(tmp_path)
