"""Assemble non-overlapping cores, using a halo only as model context."""

from collections.abc import Callable

import torch


TILE_SIZE = 512
OVERLAP = 32


@torch.inference_mode()
def upscale_tiled(
    image: torch.Tensor,
    scale: int,
    predict: Callable[[torch.Tensor], torch.Tensor],
    *,
    tile_size: int = TILE_SIZE,
    overlap: int = OVERLAP,
) -> torch.Tensor:
    if tile_size <= 0 or overlap < 0:
        raise ValueError("Tile size must be positive and overlap non-negative")
    image = image.cpu()
    height, width = image.shape[-2:]
    output = torch.empty((1, 3, height * scale, width * scale), dtype=image.dtype, device="cpu")
    for top in range(0, height, tile_size):
        bottom = min(top + tile_size, height)
        for left in range(0, width, tile_size):
            right = min(left + tile_size, width)
            y0, y1 = max(0, top - overlap), min(height, bottom + overlap)
            x0, x1 = max(0, left - overlap), min(width, right + overlap)
            # Copy back immediately; no previous tile output stays on the GPU.
            prediction = predict(image[..., y0:y1, x0:x1]).cpu()
            expected = (1, 3, (y1 - y0) * scale, (x1 - x0) * scale)
            if tuple(prediction.shape) != expected:
                raise ValueError(f"Unexpected tile output shape: {tuple(prediction.shape)}; expected {expected}")
            crop_top, crop_left = (top - y0) * scale, (left - x0) * scale
            output[..., top * scale:bottom * scale, left * scale:right * scale] = prediction[
                ..., crop_top:crop_top + (bottom - top) * scale,
                crop_left:crop_left + (right - left) * scale,
            ]
            del prediction
    return output
