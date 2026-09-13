#!/usr/bin/env python3
"""Execute the frozen conditioning plan only after exact mechanism qualification."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bet36fly.conditioning_runner import run_conditioning


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair-id", required=True)
    args = parser.parse_args()
    result = run_conditioning(Path(__file__).resolve().parents[1], args.pair_id)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
