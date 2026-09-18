"""The fixed degradation half of the contract: mod-crop and bicubic downscale.

See ../GOALS.md, "固定的退化與放大契約" steps 2, 3 and 5. Changing SCALE or
RESAMPLE invalidates every number measured before the change; they are not
tuning knobs.
"""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

SCALE = 4
RESAMPLE = Image.Resampling.BICUBIC


@dataclass(frozen=True)
class CropRecord:
    """What mod-crop did to one source, in (width, height) pairs."""

    original: tuple[int, int]
    cropped: tuple[int, int]
    removed: tuple[int, int]


def mod_crop(image: Image.Image) -> tuple[Image.Image, CropRecord]:
    """Trim right and bottom until both sides are multiples of SCALE.

    The cropped image, not the original, is the ground truth for the run. The
    alternative to cropping would be resizing a result back to the source size,
    which would add a second resample the contract forbids. Cropping changes no
    surviving pixel.
    """
    width, height = image.size
    kept_width = width - width % SCALE
    kept_height = height - height % SCALE
    record = CropRecord(
        original=(width, height),
        cropped=(kept_width, kept_height),
        removed=(width - kept_width, height - kept_height),
    )
    if record.removed == (0, 0):
        return image, record
    return image.crop((0, 0, kept_width, kept_height)), record


def downscale(image: Image.Image) -> Image.Image:
    """The synthetic low-resolution input: exactly 1/SCALE of each side."""
    width, height = image.size
    return image.resize((width // SCALE, height // SCALE), resample=RESAMPLE)


def save_png(image: Image.Image, destination: Path) -> None:
    """Write PNG only. Every intermediate the evaluation reads back is lossless."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="PNG")
