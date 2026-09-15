"""RGB tensor conversion and PNG output that preserves the source image."""

import os
import tempfile
from pathlib import Path

import torch
from PIL import Image
from torchvision.transforms.functional import pil_to_tensor, to_pil_image


def read_image(path: Path) -> torch.Tensor:
    with Image.open(path) as image:
        if image.mode not in {"1", "L", "LA", "P", "RGB", "RGBA", "CMYK"}:
            raise ValueError(f"Unsupported image mode: {image.mode}")
        if getattr(image, "n_frames", 1) != 1:
            raise ValueError("Only single-frame images are supported")
        return pil_to_tensor(image.convert("RGB")).to(torch.float32).div_(255).unsqueeze(0)


def write_png(tensor: torch.Tensor, destination: Path, source: Path) -> None:
    if tensor.ndim != 4 or tensor.shape[:2] != (1, 3):
        raise ValueError(f"Expected RGB BCHW output, got {tuple(tensor.shape)}")
    if not torch.isfinite(tensor).all():
        raise ValueError("Model output contains non-finite values")
    if destination.resolve() == source.resolve() or (
        destination.exists() and destination.samefile(source)
    ):
        raise ValueError(f"Refusing to overwrite input image: {source}")

    pixels = tensor.detach().cpu().squeeze(0).clamp(0, 1).mul(255).round().to(torch.uint8)
    image = to_pil_image(pixels, mode="RGB")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        # Encode completely before replacing a previous successful result.
        with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".png", delete=False) as stream:
            temporary = Path(stream.name)
            image.save(stream, format="PNG")
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
