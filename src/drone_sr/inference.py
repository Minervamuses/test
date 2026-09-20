"""One architecture-independent Spandrel image inference path."""

from pathlib import Path

import torch
from spandrel import ImageModelDescriptor, ModelLoader

from .tiling import TILE_SIZE, upscale_tiled


MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "model.pth"


def load_model(model_path: Path | None = None) -> ImageModelDescriptor:
    path = MODEL_PATH if model_path is None else Path(model_path)
    if not path.is_file():
        label = "models/model.pth" if model_path is None else str(path)
        raise FileNotFoundError(f"SR model not found: {label}")
    try:
        descriptor = ModelLoader().load_from_file(path)
    except Exception as error:
        raise RuntimeError(f"Unable to load SR model: {error}") from error
    if (
        not isinstance(descriptor, ImageModelDescriptor)
        or descriptor.purpose != "SR"
        or descriptor.input_channels != 3
        or descriptor.output_channels != 3
        or descriptor.scale <= 1
    ):
        raise ValueError("The checkpoint must describe an RGB super-resolution model")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return descriptor.to(device=device, dtype=torch.float32).eval()


@torch.inference_mode()
def _upscale_direct(image: torch.Tensor, descriptor: ImageModelDescriptor) -> torch.Tensor:
    image = image.to(device=descriptor.device, dtype=descriptor.dtype)
    output = descriptor(image)
    expected = (1, 3, image.shape[-2] * descriptor.scale, image.shape[-1] * descriptor.scale)
    if tuple(output.shape) != expected:
        raise ValueError(f"Unexpected model output shape: {tuple(output.shape)}; expected {expected}")
    return output


@torch.inference_mode()
def upscale(image: torch.Tensor, descriptor: ImageModelDescriptor) -> torch.Tensor:
    if max(image.shape[-2:]) <= TILE_SIZE:
        return _upscale_direct(image, descriptor)
    return upscale_tiled(image, descriptor.scale, lambda tile: _upscale_direct(tile, descriptor))
