#!/usr/bin/env bash
# Runs inside a Hugging Face Job: fetch the working set, run one experiment command, upload every
# NEW output/associative directory to the PRIVATE results dataset repo.
# Usage inside the job:  bash scripts/hf/job.sh "<command relative to the bundle root>"
set -uo pipefail
WORK="${HF_WORK_REPO:-dmontgomery40/bet36fly-work}"
RESULTS="${HF_RESULTS_REPO:-dmontgomery40/bet36fly-results}"
pip install -q "huggingface_hub>=0.34" numpy scipy pandas pyarrow scikit-learn || exit 90
hf download "$WORK" --repo-type dataset --local-dir /work >/dev/null || exit 91
cd /work || exit 92
before="$(ls output/associative 2>/dev/null || true)"
bash -c "$1"
status=$?
for d in output/associative/*/; do
  [ -d "$d" ] || continue
  name="$(basename "$d")"
  echo "$before" | grep -qx "$name" && continue
  hf upload "$RESULTS" "$d" "output/associative/$name" --repo-type dataset --commit-message "$name" >/dev/null && echo "uploaded $name"
done
exit $status
