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
import torch.nn.functional as F
from PIL import Image
from torchvision.transforms.functional import pil_to_tensor

DATA_RANGE = 255.0
SSIM_WINDOW = 11
SSIM_SIGMA = 1.5
SSIM_K1 = 0.01
SSIM_K2 = 0.03


def to_metric_tensor(image: Image.Image) -> torch.Tensor:
    """(1, 3, H, W) float32 holding 8-bit levels, i.e. [0, 255] and not [0, 1]."""
    if image.mode != "RGB":
        raise ValueError(f"Expected an RGB image, got mode {image.mode}")
    return pil_to_tensor(image).to(torch.float32).unsqueeze(0)


def load_metric_tensor(path: Path) -> torch.Tensor:
    with Image.open(path) as image:
        return to_metric_tensor(image)


def validate_pair(first: torch.Tensor, second: torch.Tensor) -> None:
    """Shared by every metric: same RGB BCHW shape, or an error naming the shapes."""
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
    validate_pair(first, second)
    mse = torch.mean((first.to(torch.float64) - second.to(torch.float64)) ** 2)
    if mse.item() == 0.0:
        return float("inf")
    return float(10.0 * torch.log10(DATA_RANGE**2 / mse))


def _gaussian_line(device: torch.device, dtype: torch.dtype) -> torch.Tensor:
    """The normalised 1-D Gaussian. The 11x11 window is its outer product."""
    offsets = torch.arange(SSIM_WINDOW, device=device, dtype=dtype) - (SSIM_WINDOW - 1) / 2
    line = torch.exp(-(offsets**2) / (2 * SSIM_SIGMA**2))
    return line / line.sum()


def ssim(first: torch.Tensor, second: torch.Tensor) -> float:
    """Wang et al. SSIM: 11x11 Gaussian window, sigma 1.5, K1 0.01, K2 0.03.

    Boundary handling is 'valid' - the window is never padded, so the SSIM map is
    (H-10) x (W-10) and no edge value is computed from invented pixels. Variances
    are the Gaussian-weighted (biased) estimates of the original formulation, not
    scikit-image's sample-covariance correction. Each channel is measured on its
    own and the three results are averaged.

    Runs in float64 on whatever device the input tensors are on, which for this
    tool is always the CPU: the metric inputs are decoded by Pillow and never
    moved. That makes PSNR and SSIM device-independent and exactly reproducible,
    unlike LPIPS. The report header has to say so.
    """
    validate_pair(first, second)
    height, width = first.shape[-2:]
    if height < SSIM_WINDOW or width < SSIM_WINDOW:
        raise ValueError(f"Images must be at least {SSIM_WINDOW}x{SSIM_WINDOW}, got {height}x{width}")

    line = _gaussian_line(first.device, torch.float64)
    horizontal = line.view(1, 1, 1, SSIM_WINDOW)
    vertical = line.view(1, 1, SSIM_WINDOW, 1)

    def filtered(tensor: torch.Tensor) -> torch.Tensor:
        # Two 1-D passes rather than one 11x11 pass. The 2-D window is exactly
        # the outer product of this line, so the result is the same convolution;
        # only the summation order differs, which in float64 moves the answer by
        # a few 1e-15. The reason to do it is cost: at 4056x3040 the 11x11 form
        # peaks at 15.4 GiB of RSS and takes 21.8 s, against 3.1 GiB and 5.4 s
        # here. That is the difference between fitting on a laptop and not.
        return F.conv2d(F.conv2d(tensor, horizontal), vertical)

    c1 = (SSIM_K1 * DATA_RANGE) ** 2
    c2 = (SSIM_K2 * DATA_RANGE) ** 2

    channel_means = []
    for channel in range(3):
        # One channel at a time: three full-size float64 intermediates instead
        # of nine.
        x = first[:, channel : channel + 1].to(torch.float64)
        y = second[:, channel : channel + 1].to(torch.float64)
        mu_x, mu_y = filtered(x), filtered(y)
        mu_x2, mu_y2, mu_xy = mu_x * mu_x, mu_y * mu_y, mu_x * mu_y
        sigma_x2 = filtered(x * x) - mu_x2
        sigma_y2 = filtered(y * y) - mu_y2
        sigma_xy = filtered(x * y) - mu_xy
        numerator = (2 * mu_xy + c1) * (2 * sigma_xy + c2)
        denominator = (mu_x2 + mu_y2 + c1) * (sigma_x2 + sigma_y2 + c2)
        channel_means.append(float((numerator / denominator).mean()))

    return sum(channel_means) / len(channel_means)
