"""Keep virtual-environment identity when launching bounded audit children."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Sequence


def environment_python(repository: Path) -> Path:
    """Return an absolute invocation path without dereferencing its symlink.

    Python discovers pyvenv.cfg from the invoked environment path. Resolving
    .venv/bin/python can instead launch the shared base installation.
    """
    interpreter = Path(repository).absolute() / ".venv" / "bin" / "python"
    if not interpreter.is_file() or not os.access(interpreter, os.X_OK):
        raise ValueError("Repository virtual-environment Python is not executable")
    if not (interpreter.parent.parent / "pyvenv.cfg").is_file():
        raise ValueError("Repository virtual-environment configuration is missing")
    return interpreter


def command(repository: Path, arguments: Sequence[str]) -> list[str]:
    """Use an argv vector, preserving spaces and interpreter invocation path."""
    return [str(environment_python(repository)), *arguments]


def probe_environment(repository: Path) -> subprocess.CompletedProcess[str]:
    """Read the child prefix and required imports before any scientific run."""
    return subprocess.run(
        command(repository, ["-c", "import json,sys,numpy,pandas; "
                 "print(json.dumps({'executable':sys.executable,'prefix':sys.prefix,"
                 "'base_prefix':sys.base_prefix,'numpy':numpy.__version__,"
                 "'pandas':pandas.__version__}))"]),
        capture_output=True, text=True, check=True, timeout=10,
    )
