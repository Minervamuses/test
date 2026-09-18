"""The bicubic baseline line of the comparison.

See ../GOALS.md, "固定的退化與放大契約" step 4. The one property this module
exists to guarantee: the baseline is computed from the LR PNG on disk, the same
file the SR line reads, and never from the ground truth or anything derived
from it in memory. An in-memory shortcut here would not crash and would not
change any output size; it would only make the comparison unfair.
"""

from pathlib import Path

from PIL import Image

from degradation import RESAMPLE, save_png


def upscale_bicubic(lr_path: Path, size: tuple[int, int], destination: Path) -> None:
    """Re-open the LR PNG from disk and resize it to *size* (width, height)."""
    if destination.resolve() == lr_path.resolve():
        raise ValueError(f"Refusing to overwrite the low-resolution input: {lr_path}")
    with Image.open(lr_path) as low:
        if low.mode != "RGB":
            raise ValueError(f"Expected an RGB low-resolution PNG, got mode {low.mode}")
        # load() before the context manager closes the file; resize() is lazy
        # about pulling pixels otherwise.
        low.load()
        restored = low.resize(size, resample=RESAMPLE)
    save_png(restored, destination)
