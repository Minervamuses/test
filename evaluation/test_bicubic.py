"""Checks that the bicubic baseline is computed from the LR file on disk."""

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from bicubic import upscale_bicubic
from degradation import downscale, mod_crop, save_png

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _gradient(width, height, shift=0):
    image = Image.new("RGB", (width, height))
    image.putdata(
        [
            (((x * 7) + shift) % 256, ((y * 11) + shift) % 256, ((x + y) + shift) % 256)
            for y in range(height)
            for x in range(width)
        ]
    )
    return image


class BicubicBaselineTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.lr_path = self.root / "lr.png"
        self.destination = self.root / "bicubic.png"

        cropped, self.record = mod_crop(_gradient(203, 101))
        self.truth_size = cropped.size
        save_png(downscale(cropped), self.lr_path)

    def test_the_full_size_chain_lines_up(self):
        upscale_bicubic(self.lr_path, self.truth_size, self.destination)

        with Image.open(self.lr_path) as low:
            self.assertEqual(low.size, (50, 25))
        self.assertEqual(self.truth_size, (200, 100))
        with Image.open(self.destination) as restored:
            self.assertEqual(restored.size, (200, 100))

    def test_output_is_a_png(self):
        upscale_bicubic(self.lr_path, self.truth_size, self.destination)

        self.assertEqual(self.destination.read_bytes()[:8], PNG_MAGIC)

    def test_output_follows_the_lr_file_when_that_file_is_overwritten(self):
        upscale_bicubic(self.lr_path, self.truth_size, self.destination)
        first = self.destination.read_bytes()

        # Same dimensions, clearly different content. If the baseline were being
        # computed from anything but this file, the result would not move.
        save_png(_gradient(50, 25, shift=97), self.lr_path)
        second_destination = self.root / "bicubic-after.png"
        upscale_bicubic(self.lr_path, self.truth_size, second_destination)

        self.assertNotEqual(first, second_destination.read_bytes())

    def test_matches_an_independent_recomputation_from_the_same_file(self):
        upscale_bicubic(self.lr_path, self.truth_size, self.destination)

        with Image.open(self.lr_path) as low:
            expected = low.convert("RGB").resize(self.truth_size, resample=Image.Resampling.BICUBIC)
        with Image.open(self.destination) as produced:
            self.assertEqual(list(produced.convert("RGB").getdata()), list(expected.getdata()))

    def test_refuses_to_overwrite_the_lr_file(self):
        with self.assertRaises(ValueError):
            upscale_bicubic(self.lr_path, self.truth_size, self.lr_path)


if __name__ == "__main__":
    unittest.main()
