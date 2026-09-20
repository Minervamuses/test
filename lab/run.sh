#!/usr/bin/env bash
# Evaluate local checkpoints on the same small checked-in sample.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON="$ROOT/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  echo "error: create .venv and install the dependencies first; see README.md (Lab server)." >&2
  exit 2
fi

# One GPU per run. Preserve an explicitly empty CUDA_VISIBLE_DEVICES so the
# preflight rejects it instead of unexpectedly using a GPU.
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES-0}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-8}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-8}"

"$PYTHON" - <<'PY'
import os
import torch

print(f"torch: {torch.__version__}; runtime CUDA: {torch.version.cuda}", flush=True)
print(f"CUDA_VISIBLE_DEVICES: {os.environ['CUDA_VISIBLE_DEVICES']}", flush=True)
if not torch.cuda.is_available():
    raise SystemExit("error: CUDA is unavailable; fix GPU access before running evaluation.")
print(f"device: {torch.cuda.get_device_name(0)}", flush=True)
torch.ones(1, device="cuda").sum().item()
PY

"$PYTHON" -m pip check

# A named checkpoint overrides the default of evaluating every local checkpoint.
MODEL_ARGS=(--all)
for argument in "$@"; do
  case "$argument" in
    --model|--model=*|--all) MODEL_ARGS=(); break ;;
  esac
done

# Later CLI arguments override these defaults through the existing argparse.
exec "$PYTHON" evaluation/run_evaluation.py \
  --input "$ROOT/lab/sample" --limit 1 "${MODEL_ARGS[@]}" "$@"
