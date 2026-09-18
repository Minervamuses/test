"""Everything on the build log's GPU handover list, in one pass.

Driven by run_on_user_shell.sh. Do not run this directly unless you know the
.venv is the interpreter; the wrapper exists to make that automatic.

Three things the coding agent's sandbox session cannot measure, because it
cannot see the GPU, plus the real small-sample run that produces the figures
the report will quote:

  1. LPIPS on a full-size 4056x3040 pair: time, peak RSS, peak VRAM, device.
  2. LPIPS determinism on the GPU, with cudnn.benchmark off.
  3. The SR line on one image: time, peak RSS, peak VRAM.
  4. A bounded real run, written as its own report.md.

Read-only with respect to the project: it reads input/, models/ and the
evaluation modules, and writes only inside the run directory it creates.
"""

import argparse
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "evaluation"))

import torch  # noqa: E402
from PIL import Image  # noqa: E402

from bicubic import upscale_bicubic  # noqa: E402
from degradation import downscale, mod_crop, save_png  # noqa: E402
from metrics import load_metric_tensor, psnr, ssim, to_metric_tensor  # noqa: E402
from perceptual import PerceptualMetric, fix_cudnn_determinism  # noqa: E402
from report import describe_environment, render_report, write_report  # noqa: E402
from runner import release_device_memory, run_batch, select_sources  # noqa: E402
from runs import RUNS_ROOT, allocate_run_directory  # noqa: E402
from sources import decode_source, discover_sources  # noqa: E402
from sr_line import SuperResolutionLine  # noqa: E402
from summary import summarise  # noqa: E402


class Tee:
    """Everything printed also lands in the run directory's log."""

    def __init__(self, stream, path):
        self.stream = stream
        self.log = path.open("w", encoding="utf-8")

    def write(self, text):
        self.stream.write(text)
        self.log.write(text)

    def flush(self):
        self.stream.flush()
        self.log.flush()


def _peak_rss() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def _vram(available: bool) -> str:
    if not available:
        return "n/a (CPU)"
    return (
        f"allocated {torch.cuda.max_memory_allocated() / 1024**2:.0f} MiB, "
        f"reserved {torch.cuda.max_memory_reserved() / 1024**2:.0f} MiB"
    )


def _reset(available: bool) -> None:
    if available:
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()


def _sync(available: bool) -> None:
    if available:
        torch.cuda.synchronize()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the GPU handover checks and a bounded sample.")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260919)
    parser.add_argument("--input", type=Path, default=PROJECT_ROOT / "input")
    arguments = parser.parse_args(argv)

    fix_cudnn_determinism()
    started = datetime.now(timezone.utc).astimezone()
    run_dir = allocate_run_directory(RUNS_ROOT)
    sys.stdout = Tee(sys.__stdout__, run_dir / "gpu-checks.log")

    available = torch.cuda.is_available()
    print("=" * 72)
    print("evaluation — GPU handover checks")
    print("=" * 72)
    print(f"run directory         : {run_dir}")
    print(f"log                   : {run_dir / 'gpu-checks.log'}")
    print(f"started               : {started.strftime('%Y-%m-%d %H:%M:%S %z')}")
    print(f"torch                 : {torch.__version__}")
    print(f"cuda available        : {available}")
    if available:
        print(f"device name           : {torch.cuda.get_device_name(0)}")
        print(f"total VRAM            : {torch.cuda.get_device_properties(0).total_memory / 1024**2:.0f} MiB")
    else:
        print("device name           : CPU  <-- NOT the delivery device.")
        print("                        If you meant to measure the GPU, this output is not it.")
    print(f"cudnn.benchmark       : {torch.backends.cudnn.benchmark}  (must be False)")
    print()

    sources = discover_sources(arguments.input)
    if not sources:
        print(f"error: no sources in {arguments.input}", file=sys.stderr)
        return 2

    # ---------------------------------------------------------------- item 1/2
    print("-" * 72)
    print("A. LPIPS at full size: cost and determinism")
    print("-" * 72)
    source = sources[0]
    cropped, record = mod_crop(decode_source(source))
    lr_path = run_dir / "lr" / (source.stem + ".png")
    probe_bicubic = run_dir / "bicubic" / (source.stem + ".png")
    save_png(cropped, run_dir / "hr" / (source.stem + ".png"))
    save_png(downscale(cropped), lr_path)
    upscale_bicubic(lr_path, record.cropped, probe_bicubic)
    with Image.open(probe_bicubic) as restored:
        pair = (to_metric_tensor(cropped), to_metric_tensor(restored.convert("RGB")))
    print(f"source                : {source.name}")
    print(f"ground truth          : {record.cropped[0]}x{record.cropped[1]}")

    sr_line = SuperResolutionLine()
    perceptual = PerceptualMetric(device=sr_line.device)
    print(f"SR line device        : {sr_line.device}")
    print(f"LPIPS device          : {perceptual.device}")
    print("PSNR/SSIM device      : cpu, float64 (by construction; inputs are never moved)")
    print()

    _reset(available)
    clock = time.perf_counter()
    first = perceptual(*pair)
    _sync(available)
    lpips_elapsed = time.perf_counter() - clock
    print(f"LPIPS (bicubic vs GT) : {first!r}")
    print(f"  elapsed             : {lpips_elapsed:.2f} s")
    print(f"  peak VRAM           : {_vram(available)}")
    print(f"  peak RSS            : {_peak_rss():.0f} MiB")

    second = perceptual(*pair)
    third = perceptual(*pair)
    print(f"  repeat 2            : {second!r}")
    print(f"  repeat 3            : {third!r}")
    print(f"  DETERMINISTIC       : {first == second == third}   <-- must be True")
    release_device_memory()
    print()

    # ------------------------------------------------------------------ item 3
    print("-" * 72)
    print("B. SR line on one full-size image: cost and determinism")
    print("-" * 72)
    sr_path = run_dir / "sr" / (source.stem + ".png")
    _reset(available)
    clock = time.perf_counter()
    sr_line.run(lr_path, sr_path, record.cropped)
    _sync(available)
    sr_elapsed = time.perf_counter() - clock
    first_bytes = sr_path.read_bytes()
    print(f"LR {record.cropped[0] // 4}x{record.cropped[1] // 4} -> SR {record.cropped[0]}x{record.cropped[1]}")
    print(f"  elapsed             : {sr_elapsed:.2f} s")
    print(f"  peak VRAM           : {_vram(available)}")
    print(f"  peak RSS            : {_peak_rss():.0f} MiB")

    again = run_dir / "sr" / (source.stem + "-again.png")
    sr_line.run(lr_path, again, record.cropped)
    identical = again.read_bytes() == first_bytes
    again.unlink()
    print(f"  DETERMINISTIC       : {identical}   <-- must be True")
    release_device_memory()
    print()

    # Free the probe artefacts so the real run below starts from a clean slate.
    for path in (lr_path, probe_bicubic, sr_path, run_dir / "hr" / (source.stem + ".png")):
        path.unlink(missing_ok=True)
    del pair
    release_device_memory()

    # ------------------------------------------------------------------ item 4
    print("-" * 72)
    print(f"C. Real run: {arguments.limit} image(s), seed {arguments.seed}")
    print("-" * 72)
    selected = select_sources(arguments.input, limit=arguments.limit, seed=arguments.seed)
    for path in selected:
        print(f"  {path.name}")
    print()
    _reset(available)
    clock = time.perf_counter()
    results, failures = run_batch(
        selected, run_dir, sr_line, perceptual, progress=lambda i, n, name: print(f"[{i}/{n}] {name}", flush=True)
    )
    _sync(available)
    batch_elapsed = time.perf_counter() - clock

    summary = summarise(results, failures)
    environment = describe_environment(
        started=started,
        run_dir=run_dir,
        project_root=PROJECT_ROOT,
        source_directory=arguments.input,
        sampling=f"random (seed {arguments.seed})",
        limit=arguments.limit,
        discovered=len(sources),
        selected=len(selected),
        sr_line=sr_line,
        lpips_device=str(perceptual.device),
    )
    report_path = run_dir / "report.md"
    write_report(report_path, render_report(environment, results, failures, summary))

    print()
    print(f"measured              : {summary.included} on both lines, {summary.failed} excluded")
    for metric in summary.metrics:
        if metric.winner == "n/a":
            print(f"  {metric.name:6s} no comparison available")
        else:
            print(f"  {metric.name:6s} SR {metric.sr_mean:.6f} | bicubic {metric.bicubic_mean:.6f} -> {metric.winner}")
    print(f"  batch elapsed       : {batch_elapsed:.1f} s ({batch_elapsed / max(len(selected), 1):.1f} s per image)")
    print(f"  peak VRAM (batch)   : {_vram(available)}")
    print(f"  peak RSS (process)  : {_peak_rss():.0f} MiB")
    print(f"  report              : {report_path}")
    print()

    print("-" * 72)
    print("D. Cross-device check (paste this too)")
    print("-" * 72)
    print("The bicubic line is pure Pillow CPU and PSNR/SSIM always run on CPU")
    print("float64, so these must match the sandbox CPU batch digit for digit.")
    print("Only the SR line's numbers and LPIPS are allowed to differ.")
    for item in results:
        print(f"  {item.source_name}  bicubic PSNR {item.bicubic.psnr!r}  bicubic SSIM {item.bicubic.ssim!r}")
    print()
    print("=" * 72)
    print("Done. Paste everything above back to the agent.")
    print("=" * 72)
    return 0 if summary.included else 1


if __name__ == "__main__":
    raise SystemExit(main())
