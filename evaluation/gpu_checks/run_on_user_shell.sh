#!/usr/bin/env bash
# The GPU handover run. Do this in YOUR OWN WSL shell, not through the agent:
# the agent's sandbox session cannot see /dev/dxg, so anything it measures is a
# CPU number and says nothing about the delivery device.
#
#     bash evaluation/gpu_checks/run_on_user_shell.sh
#
# Optional: pass through arguments, e.g. --limit 3 for a shorter run.
#
# It does everything on the build log's "待 GPU 補測" list in one pass -
# LPIPS cost and determinism at full size, SR line cost and determinism, and a
# bounded real run that writes its own report.md - then prints a block to paste
# back. Expect a few minutes.
#
# Read-only against the project: reads input/, models/ and the evaluation
# modules, writes only inside the run directory it creates under
# evaluation/runs/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  echo "error: no interpreter at $PYTHON" >&2
  echo "This script needs the project's own .venv. Create it first." >&2
  exit 2
fi

exec "$PYTHON" "$ROOT/evaluation/gpu_checks/run_on_user_shell.py" "$@"
