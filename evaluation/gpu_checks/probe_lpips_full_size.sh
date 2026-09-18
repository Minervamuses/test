#!/usr/bin/env bash
# Probe: can LPIPS run on one full-size 4056x3040 pair, and what does it cost?
#
# Run this in your own WSL shell, where the GPU is visible. The coding agent's
# sandbox session cannot see /dev/dxg, so anything it measures is a CPU number
# and says nothing about the delivery device.
#
#     bash evaluation/gpu_checks/probe_lpips_full_size.sh
#
# It takes roughly half a minute and answers one question only: does the
# perceptual metric fit in VRAM at full resolution. It does not produce any
# figure for the report - that comes later, from the phase 05 script.
#
# Read-only with respect to the project: it reads one image from input/ and the
# evaluation modules, writes only into a fresh temporary directory, and touches
# nothing under src/, tests/, input/, output/ or models/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK="$(mktemp -d)"
LOG="$WORK/probe.log"
trap 'rm -rf "$WORK"' EXIT

echo "project root : $ROOT"
echo "work dir     : $WORK"
echo "log          : $LOG"
echo

"$ROOT/.venv/bin/python" - "$ROOT" "$WORK" 2>&1 <<'PY' | tee "$LOG"
import os
import resource
import sys
import time
from pathlib import Path

root, work = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(root / "evaluation"))

import torch
from PIL import Image

from bicubic import upscale_bicubic
from degradation import downscale, mod_crop
from metrics import to_metric_tensor
from perceptual import PerceptualMetric, fix_cudnn_determinism
from sources import decode_source, discover_sources

fix_cudnn_determinism()
available = torch.cuda.is_available()
device = "cuda:0" if available else "cpu"
print(f"torch                 : {torch.__version__}")
print(f"cuda available        : {available}")
if available:
    name = torch.cuda.get_device_name(0)
    total = torch.cuda.get_device_properties(0).total_memory / 1024**2
    print(f"device                : {name}")
    print(f"total VRAM            : {total:.0f} MiB")
else:
    print("device                : CPU  <-- not the delivery device; see GOALS.md")
print(f"cudnn.benchmark       : {torch.backends.cudnn.benchmark}")
print()

sources = discover_sources(root / "input")
if not sources:
    raise SystemExit("no source images found in input/")
source = sources[0]
cropped, record = mod_crop(decode_source(source))
print(f"source                : {source.name}")
print(f"ground truth size     : {record.cropped[0]}x{record.cropped[1]}")

lr_path, restored_path = work / "lr.png", work / "bicubic.png"
from degradation import save_png

save_png(downscale(cropped), lr_path)
upscale_bicubic(lr_path, record.cropped, restored_path)
with Image.open(restored_path) as restored:
    pair = (to_metric_tensor(cropped), to_metric_tensor(restored.convert("RGB")))
print(f"tensor shape          : {tuple(pair[0].shape)}")
print()

metric = PerceptualMetric(device=device)
if available:
    torch.cuda.reset_peak_memory_stats()
    torch.cuda.synchronize()
started = time.perf_counter()
value = metric(*pair)
if available:
    torch.cuda.synchronize()
elapsed = time.perf_counter() - started

print(f"LPIPS (bicubic vs GT) : {value:.6f}")
print(f"elapsed               : {elapsed:.2f} s")
print(f"peak RSS              : {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.0f} MiB")
if available:
    print(f"peak VRAM allocated   : {torch.cuda.max_memory_allocated() / 1024**2:.0f} MiB")
    print(f"peak VRAM reserved    : {torch.cuda.max_memory_reserved() / 1024**2:.0f} MiB")
    torch.cuda.empty_cache()
    print(f"after empty_cache     : {torch.cuda.memory_reserved() / 1024**2:.0f} MiB reserved")
else:
    print("peak VRAM             : n/a (ran on CPU)")
print()
print(f"measured on           : {'GPU' if available else 'CPU'}")
PY

echo
echo "Paste the block above back to the agent."
