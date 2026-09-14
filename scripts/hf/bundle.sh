#!/usr/bin/env bash
# Stage the minimal working set for Hugging Face Jobs and upload it to a PRIVATE dataset repo.
# Contains: code, configs, the prepared MaleCNS arrays (CC-BY-4.0 derived), development games,
# the frozen sensory candidate. Never contains ledgers, the v1 checkpoint, keys or web/.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REPO="${HF_WORK_REPO:-dmontgomery40/bet36fly-work}"
STAGE="$(mktemp -d /tmp/bet36fly-hf-bundle.XXXXXX)"
rsync -a --include='*/' --include='*.py' --include='*.cpp' --exclude='*' "$ROOT/bet36fly/" "$STAGE/bet36fly/"
rsync -a --include='*/' --include='*.py' --include='*.sh' --exclude='*' "$ROOT/scripts/" "$STAGE/scripts/"
rsync -a "$ROOT/configs/" "$STAGE/configs/"
cp "$ROOT/pyproject.toml" "$STAGE/"
mkdir -p "$STAGE/data/brain" "$STAGE/data/sensory-sports/development-2019-2022-v2" \
  "$STAGE/docs/evidence/sensory-backtest-goal-2026-09-13" "$STAGE/output/associative"
for f in ids indptr post counts signs kc mbon sensory; do cp "$ROOT/data/brain/$f.npy" "$STAGE/data/brain/"; done
cp "$ROOT/data/brain/nodes.feather" "$ROOT/data/brain/manifest.json" "$STAGE/data/brain/"
cp "$ROOT/data/sensory-sports/development-2019-2022-v2/games.json" \
   "$ROOT/data/sensory-sports/development-2019-2022-v2/manifest.json" "$STAGE/data/sensory-sports/development-2019-2022-v2/"
cp "$ROOT/docs/evidence/sensory-backtest-goal-2026-09-13/frozen-candidate.json" "$STAGE/docs/evidence/sensory-backtest-goal-2026-09-13/"
cp "$ROOT/docs/connectome-source-lock.json" "$STAGE/docs/"
touch "$STAGE/output/associative/.keep"
du -sh "$STAGE"
# Content audit before every upload: no env files, credentials, ledgers, production checkpoints or web/.
bad="$(find "$STAGE" \( -name '.env*' -o -name '*.env' -o -name '*.sqlite3*' -o -name 'checkpoint.npz' -o -name '*.pem' -o -name '*.key' -o -name 'current-model.json' -o -path '*/web/*' -o -path '*/output/runs/*' -o -path '*/data/picks*' \) -print)"
if [ -n "$bad" ]; then echo "REFUSING upload; disallowed paths:"; echo "$bad"; exit 1; fi
if grep -rIlE 'hf_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH) PRIVATE KEY|Authorization: Bearer [A-Za-z0-9]' "$STAGE" --exclude=job.sh | grep -v '^$'; then echo "REFUSING upload; credential-like content found"; exit 1; fi
echo "bundle audit passed: $(find "$STAGE" -type f | wc -l | tr -d ' ') files"
hf repo create "$REPO" --repo-type dataset --private 2>/dev/null || true
hf upload "$REPO" "$STAGE" . --repo-type dataset --commit-message "bet36fly working set $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "staged at $STAGE (temporary; safe to delete)"
