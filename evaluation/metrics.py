"""PSNR and SSIM, hand-written in torch under the fixed metric conventions.

See ../GOALS.md, "固定的度量約定". The conventions are fixed for the whole
plan: RGB rather than the Y channel that papers usually report, 8-bit values
with data_range 255, and the same treatment for both lines being compared.
Numbers produced here are therefore not directly comparable with published
figures, and nothing in this module may be adjusted to make a score look
better.

Only lpips is an authorized dependency, so scikit-image and torchmetrics are
not available to lean on; these two metrics are implemented here and carry
property checks in test_psnr.py and test_ssim.py as their correctness evidence.
"""

from pathlib import Path

import torch
from PIL import Image
from torchvision.transforms.functional import pil_to_tensor

DATA_RANGE = 255.0


def to_metric_tensor(image: Image.Image) -> torch.Tensor:
    """(1, 3, H, W) float32 holding 8-bit levels, i.e. [0, 255] and not [0, 1]."""
    if image.mode != "RGB":
        raise ValueError(f"Expected an RGB image, got mode {image.mode}")
    return pil_to_tensor(image).to(torch.float32).unsqueeze(0)


def load_metric_tensor(path: Path) -> torch.Tensor:
    with Image.open(path) as image:
        return to_metric_tensor(image)


def _validate(first: torch.Tensor, second: torch.Tensor) -> None:
    for tensor in (first, second):
        if tensor.ndim != 4 or tensor.shape[0] != 1 or tensor.shape[1] != 3:
            raise ValueError(f"Expected RGB BCHW input, got shape {tuple(tensor.shape)}")
    if first.shape != second.shape:
        # Resizing here would silently compare something other than what the
        # degradation contract produced.
        raise ValueError(f"Mismatched shapes: {tuple(first.shape)} and {tuple(second.shape)}")


def psnr(first: torch.Tensor, second: torch.Tensor) -> float:
    """10 * log10(255^2 / MSE) over all three channels, inf when identical.

    float64 throughout: the squared error over a 4056x3040 image accumulates far
    past float32's exact-integer range, so float32 would quietly lose precision.
    """
    _validate(first, second)
    mse = torch.mean((first.to(torch.float64) - second.to(torch.float64)) ** 2)
    if mse.item() == 0.0:
        return float("inf")
    return float(10.0 * torch.log10(DATA_RANGE**2 / mse))
