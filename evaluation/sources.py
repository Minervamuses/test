"""Source discovery and decoding for the evaluation's fixed degradation contract.

The contract lives in ../GOALS.md, "固定的退化與放大契約" step 1. This module
deliberately does not call drone_sr.read_image(): that function rejects
multi-frame images, and every source in input/ is a two-frame MPO JPEG, so
routing ground-truth decoding through it would reject the whole dataset. The SR
line still goes through read_image() unchanged, because it only ever receives
the single-frame LR PNG this pipeline writes.
"""

from pathlib import Path

from PIL import Image, ImageOps

SOURCE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg"})


class UnsupportedSource(Exception):
    """A source image the fixed contract says to skip rather than convert."""


def discover_sources(directory: Path) -> list[Path]:
    """Direct children of *directory* with a source suffix, sorted by name.

    Subdirectories and every other suffix are ignored, so a nested copy of the
    dataset or a stray sidecar file cannot silently enter the comparison.
    """
    found = [
        entry
        for entry in directory.iterdir()
        if entry.is_file() and entry.suffix.lower() in SOURCE_SUFFIXES
    ]
    return sorted(found, key=lambda entry: entry.name)


def _bits_per_sample(image: Image.Image, path: Path) -> int:
    """Bits per sample in the file itself, read before anything decodes.

    Pillow maps deeper colour onto 8-bit modes during decode, so asking the
    decoded image is too late. Only PNG carries a bit depth the contract can
    encounter here: discovery admits PNG and JPEG only, and Pillow's JPEG
    decoder is 8-bit.
    """
    if image.format != "PNG":
        return 8
    with path.open("rb") as stream:
        header = stream.read(26)
    # Bit depth sits at a fixed offset in IHDR, the first chunk of every PNG.
    return header[24] if header[12:16] == b"IHDR" else 8


def decode_source(path: Path) -> Image.Image:
    """Decode a ground-truth source: first frame, EXIF-oriented, RGB, 8-bit.

    Raises UnsupportedSource for anything deeper than 8 bits per sample, which
    the contract skips rather than truncating.
    """
    with Image.open(path) as image:
        bits = _bits_per_sample(image, path)
        if bits > 8:
            raise UnsupportedSource(f"{path.name}: {bits} bits per sample, more than 8")
        # Multi-frame sources (the dataset's MPO JPEGs) carry the full-resolution
        # main image in frame 0 and a thumbnail after it.
        if getattr(image, "n_frames", 1) != 1:
            image.seek(0)
        oriented = ImageOps.exif_transpose(image)
        return oriented.convert("RGB")
