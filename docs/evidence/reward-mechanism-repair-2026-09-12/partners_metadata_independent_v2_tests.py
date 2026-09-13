"""Run preserved independent regressions against v2 without changing any v1 file."""

from pathlib import Path
import sys

import pytest

import partners_metadata_inventory_v2 as candidate


if __name__ == "__main__":
    sys.modules["partners_metadata_inventory"] = candidate
    directory = Path(__file__).resolve().parent
    names = [
        "test_partners_metadata_independent.py",
        "test_partners_metadata_independent_client.py",
        "test_partners_metadata_independent_transport.py",
        "test_partners_metadata_independent_headers_v2.py",
    ]
    raise SystemExit(pytest.main(["-q", *(str(directory / name) for name in names)]))
