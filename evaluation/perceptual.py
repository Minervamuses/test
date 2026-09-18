"""LPIPS, wrapped so the evaluation always calls it the same way.

See ../GOALS.md, "固定的度量約定" items 4 and 6: the lpips package, net='alex',
inputs normalised to [-1, 1], RGB, with the device fixed for the whole run and
recorded in the report. LPIPS measures perceptual similarity and moves in the
opposite direction to PSNR and SSIM - lower is better - which matters because a
GAN-trained super-resolver is expected to lose on the pixel-fidelity metrics and
win here.

CPU and GPU results are not guaranteed bit-identical (TF32, cuDNN algorithm
choice), so figures from the two devices belong to different batches and must
not be listed side by side.
"""

import lpips
import torch

from metrics import DATA_RANGE, validate_pair

LPIPS_NET = "alex"


def fix_cudnn_determinism() -> None:
    """Stop cuDNN re-benchmarking kernels, which makes repeated runs drift.

    Harmless on CPU. Called on construction so no caller can forget it, and
    exported so the SR line can apply the same setting.
    """
    torch.backends.cudnn.benchmark = False


class PerceptualMetric:
    """One loaded LPIPS model, pinned to one device for the whole run."""

    def __init__(self, device: torch.device | str = "cpu") -> None:
        fix_cudnn_determinism()
        self._device = torch.device(device)
        model = lpips.LPIPS(net=LPIPS_NET)
        # eval() and inference_mode() below are what make repeated calls agree.
        model.eval()
        self._model = model.to(self._device)

    @property
    def device(self) -> torch.device:
        return self._device

    def __call__(self, first: torch.Tensor, second: torch.Tensor) -> float:
        """Distance between two [0, 255] RGB BCHW tensors. Lower is more similar."""
        validate_pair(first, second)
        with torch.inference_mode():
            left = self._to_signed_unit(first)
            right = self._to_signed_unit(second)
            distance = self._model(left, right)
        # Nothing here is kept: the caller may be about to run super-resolution
        # on the same GPU, and held activations are what turns a tight VRAM
        # budget into an out-of-memory failure.
        return float(distance.reshape(()).detach().cpu())

    def _to_signed_unit(self, tensor: torch.Tensor) -> torch.Tensor:
        return tensor.to(device=self._device, dtype=torch.float32) / (DATA_RANGE / 2.0) - 1.0
