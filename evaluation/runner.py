"""Running both upscale lines over a bounded sample of source images.

One image at a time: decode, mod-crop to the ground truth, downscale to the LR
PNG, then upscale that same file twice - once with bicubic, once with the
unmodified SR pipeline - and measure both against the ground truth. Nothing here
changes the degradation contract or the metric conventions; those are settled in
degradation.py, bicubic.py, metrics.py and perceptual.py and were verified
before this module existed.

A failure on one image is recorded and the batch carries on. Losing a whole run
to one unreadable file would be worse than a report that says which file dropped
out and why.
"""

import random
from dataclasses import dataclass
from pathlib import Path

import torch
from PIL import Image

from bicubic import upscale_bicubic
from degradation import downscale, mod_crop, save_png
from metrics import load_metric_tensor, psnr, ssim, to_metric_tensor
from sources import decode_source, discover_sources

DEFAULT_LIMIT = 5


@dataclass(frozen=True)
class LineScores:
    psnr: float
    ssim: float
    lpips: float


@dataclass(frozen=True)
class ImageResult:
    """One image measured successfully on both lines. Sizes are (width, height)."""

    source_name: str
    original: tuple[int, int]
    cropped: tuple[int, int]
    low: tuple[int, int]
    sr: LineScores
    bicubic: LineScores


@dataclass(frozen=True)
class ImageFailure:
    source_name: str
    stage: str
    reason: str


def select_sources(directory: Path, limit: int = DEFAULT_LIMIT, seed: int | None = None) -> list[Path]:
    """The first *limit* sources in name order, or a reproducible random sample.

    Sequential by default so that a rerun with the same arguments compares the
    same images; a seed is required for the random path for the same reason.
    """
    found = discover_sources(directory)
    if limit is not None and limit < len(found):
        if seed is None:
            found = found[:limit]
        else:
            found = sorted(random.Random(seed).sample(found, limit), key=lambda path: path.name)
    return found


def release_device_memory() -> None:
    """Hand freed GPU blocks back to the driver. A no-op on CPU."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def _score(truth, candidate, perceptual) -> LineScores:
    return LineScores(psnr=psnr(truth, candidate), ssim=ssim(truth, candidate), lpips=perceptual(truth, candidate))


def process_image(source: Path, run_dir: Path, sr_line, perceptual) -> ImageResult:
    """Decode, degrade, upscale both ways, measure. Raises _StageError on failure."""
    name = source.stem + ".png"
    hr_path, lr_path = run_dir / "hr" / name, run_dir / "lr" / name
    bicubic_path, sr_path = run_dir / "bicubic" / name, run_dir / "sr" / name

    with _stage("decode", source):
        image = decode_source(source)
    with _stage("degrade", source):
        cropped, record = mod_crop(image)
        save_png(cropped, hr_path)
        save_png(downscale(cropped), lr_path)
        low_size = _size_of(lr_path)
    with _stage("bicubic", source):
        upscale_bicubic(lr_path, record.cropped, bicubic_path)
    with _stage("sr", source):
        sr_line.run(lr_path, sr_path, record.cropped)
    # GOALS.md asks for this explicitly: on a 12227 MiB card, SR activations
    # still held while LPIPS allocates its own is the shape of an OOM.
    release_device_memory()
    with _stage("metrics", source):
        truth = to_metric_tensor(cropped)
        scores = {
            "bicubic": _score(truth, load_metric_tensor(bicubic_path), perceptual),
            "sr": _score(truth, load_metric_tensor(sr_path), perceptual),
        }

    return ImageResult(
        source_name=source.name,
        original=record.original,
        cropped=record.cropped,
        low=low_size,
        sr=scores["sr"],
        bicubic=scores["bicubic"],
    )


def run_batch(sources, run_dir: Path, sr_line, perceptual, progress=None):
    """Every source in order; returns (results, failures) and never raises for one image."""
    results, failures = [], []
    for index, source in enumerate(sources, start=1):
        if progress is not None:
            progress(index, len(sources), source.name)
        try:
            results.append(process_image(source, run_dir, sr_line, perceptual))
        except _StageError as error:
            failures.append(ImageFailure(source.name, error.stage, error.reason))
        release_device_memory()
    return results, failures


class _StageError(Exception):
    def __init__(self, stage: str, reason: str):
        super().__init__(f"{stage}: {reason}")
        self.stage = stage
        self.reason = reason


class _stage:
    """Turns whatever a step raises into a recordable (stage, reason) pair."""

    def __init__(self, name: str, source: Path):
        self.name = name
        self.source = source

    def __enter__(self):
        return self

    def __exit__(self, kind, value, traceback):
        if value is None or isinstance(value, _StageError):
            return False
        raise _StageError(self.name, f"{type(value).__name__}: {value}") from value


def _size_of(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size
