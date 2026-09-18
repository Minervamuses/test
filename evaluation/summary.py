"""Averaging, under the inclusion rules GOALS.md fixes.

Two rules, both of them load-bearing and neither of them adjustable to make a
result look better:

- An image is averaged only if BOTH lines measured it. If either line failed,
  the image counts for neither, so the two averages always cover the same set.
- An infinite PSNR (identical images, MSE 0) drops that image from the PSNR
  average only. Its SSIM and LPIPS still count, and the report says how many
  images were dropped and why.
"""

import math
from dataclasses import dataclass

METRIC_NAMES = ("PSNR", "SSIM", "LPIPS")
# LPIPS is a distance: lower is more similar. The other two are fidelity scores.
HIGHER_IS_BETTER = {"PSNR": True, "SSIM": True, "LPIPS": False}


@dataclass(frozen=True)
class MetricSummary:
    name: str
    higher_is_better: bool
    sr_mean: float | None
    bicubic_mean: float | None
    counted: int
    excluded_infinite: int
    winner: str
    margin: float | None


@dataclass(frozen=True)
class Summary:
    included: int
    failed: int
    metrics: tuple[MetricSummary, ...]


def _field(scores, name: str) -> float:
    return getattr(scores, name.lower())


def decide_winner(name: str, sr_value: float | None, bicubic_value: float | None):
    """(winner, margin) for one metric. Used per image and for the averages."""
    if sr_value is None or bicubic_value is None:
        return "n/a", None
    if sr_value == bicubic_value:
        return "tie", 0.0
    sr_ahead = sr_value > bicubic_value if HIGHER_IS_BETTER[name] else sr_value < bicubic_value
    return ("SR" if sr_ahead else "bicubic"), abs(sr_value - bicubic_value)


def _summarise_metric(name: str, results) -> MetricSummary:
    usable = results
    excluded = 0
    if name == "PSNR":
        usable = [r for r in results if math.isfinite(_field(r.sr, name)) and math.isfinite(_field(r.bicubic, name))]
        excluded = len(results) - len(usable)

    if usable:
        sr_mean = sum(_field(r.sr, name) for r in usable) / len(usable)
        bicubic_mean = sum(_field(r.bicubic, name) for r in usable) / len(usable)
    else:
        sr_mean = bicubic_mean = None

    winner, margin = decide_winner(name, sr_mean, bicubic_mean)
    return MetricSummary(
        name=name,
        higher_is_better=HIGHER_IS_BETTER[name],
        sr_mean=sr_mean,
        bicubic_mean=bicubic_mean,
        counted=len(usable),
        excluded_infinite=excluded,
        winner=winner,
        margin=margin,
    )


def summarise(results, failures) -> Summary:
    return Summary(
        included=len(results),
        failed=len(failures),
        metrics=tuple(_summarise_metric(name, results) for name in METRIC_NAMES),
    )
