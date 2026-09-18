#!/usr/bin/env python3
"""Run the whole evaluation once and write one report.

    .venv/bin/python evaluation/run_evaluation.py [--limit N] [--input DIR] [--seed S]

Every artefact lands in a new evaluation/runs/<timestamp>/ directory. Nothing is
ever written into an existing run, and nothing outside evaluation/runs/ is
written at all - input/, output/, models/ and src/ are read-only to this tool.

The default limit is deliberately small. Running the whole dataset is not
authorized by the plan and needs the user's agreement; see evaluation/PLANS.md.
"""

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from perceptual import PerceptualMetric, fix_cudnn_determinism  # noqa: E402
from report import describe_environment, render_report, write_report  # noqa: E402
from runner import DEFAULT_LIMIT, run_batch, select_sources  # noqa: E402
from runs import RUNS_ROOT, allocate_run_directory  # noqa: E402
from sources import discover_sources  # noqa: E402
from summary import summarise  # noqa: E402


def _parse(argv):
    parser = argparse.ArgumentParser(description="Compare the SR line against a bicubic baseline.")
    parser.add_argument("--input", type=Path, default=PROJECT_ROOT / "input", help="source image directory")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"how many images (default {DEFAULT_LIMIT})")
    parser.add_argument("--seed", type=int, default=None, help="sample randomly with this seed instead of taking the first N")
    parser.add_argument("--runs-root", type=Path, default=RUNS_ROOT, help="where run directories are created")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    arguments = _parse(argv)
    fix_cudnn_determinism()

    if not arguments.input.is_dir():
        print(f"error: not a directory: {arguments.input}", file=sys.stderr)
        return 2

    discovered = len(discover_sources(arguments.input))
    selected = select_sources(arguments.input, limit=arguments.limit, seed=arguments.seed)
    if not selected:
        print(f"error: no .png/.jpg/.jpeg sources in {arguments.input}", file=sys.stderr)
        return 2

    started = datetime.now(timezone.utc).astimezone()
    run_dir = allocate_run_directory(arguments.runs_root)
    print(f"run directory : {run_dir}")
    print(f"sources       : {len(selected)} of {discovered} discovered in {arguments.input}")

    # The SR line picks its own device through the unmodified pipeline and
    # LPIPS follows it, so a run never mixes devices for the parts that depend
    # on one. PSNR and SSIM stay on CPU float64 by construction.
    from sr_line import SuperResolutionLine

    sr_line = SuperResolutionLine()
    perceptual = PerceptualMetric(device=sr_line.device)
    print(f"device        : {sr_line.device} (SR line and LPIPS; PSNR/SSIM always CPU float64)")
    print()

    def progress(index, total, name):
        print(f"[{index}/{total}] {name}", flush=True)

    clock = time.perf_counter()
    results, failures = run_batch(selected, run_dir, sr_line, perceptual, progress=progress)
    elapsed = time.perf_counter() - clock

    summary = summarise(results, failures)
    environment = describe_environment(
        started=started,
        run_dir=run_dir,
        project_root=PROJECT_ROOT,
        source_directory=arguments.input,
        sampling="sequential" if arguments.seed is None else f"random (seed {arguments.seed})",
        limit=arguments.limit,
        discovered=discovered,
        selected=len(selected),
        sr_line=sr_line,
        lpips_device=str(sr_line.device),
    )
    report_path = run_dir / "report.md"
    write_report(report_path, render_report(environment, results, failures, summary))

    print()
    print(f"measured      : {summary.included} image(s) on both lines; {summary.failed} excluded")
    for metric in summary.metrics:
        if metric.winner == "n/a":
            print(f"  {metric.name:6s} no comparison available")
        else:
            print(f"  {metric.name:6s} SR {metric.sr_mean:.6f} | bicubic {metric.bicubic_mean:.6f} -> {metric.winner}")
    print(f"elapsed       : {elapsed:.1f} s ({elapsed / max(len(selected), 1):.1f} s per image)")
    print(f"report        : {report_path}")
    if summary.included == 0:
        print("error: nothing was measured on both lines", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
