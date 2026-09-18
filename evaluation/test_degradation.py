"""Checks for mod-crop and the fixed bicubic downscale."""

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from degradation import RESAMPLE, SCALE, downscale, mod_crop, save_png

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _gradient(width, height):
    image = Image.new("RGB", (width, height))
    image.putdata([((x * 7) % 256, (y * 11) % 256, (x + y) % 256) for y in range(height) for x in range(width)])
    return image


class ModCropTests(unittest.TestCase):
    def test_trims_width_and_height_to_multiples_of_four(self):
        cropped, record = mod_crop(_gradient(203, 101))

        self.assertEqual(cropped.size, (200, 100))
        self.assertEqual(record.original, (203, 101))
        self.assertEqual(record.cropped, (200, 100))
        self.assertEqual(record.removed, (3, 1))

    def test_is_a_no_op_when_both_sides_are_already_aligned(self):
        original = _gradient(40, 20)

        cropped, record = mod_crop(original)

        self.assertEqual(cropped.size, (40, 20))
        self.assertEqual(record.removed, (0, 0))
        self.assertEqual(cropped.tobytes(), original.tobytes())

    def test_surviving_pixels_are_untouched(self):
        original = _gradient(203, 101)

        cropped, _ = mod_crop(original)

        self.assertEqual(cropped.tobytes(), original.crop((0, 0, 200, 100)).tobytes())

    def test_removes_at_most_three_pixels_per_side(self):
        for width, height in ((201, 102), (202, 103), (204, 104)):
            with self.subTest(size=(width, height)):
                _, record = mod_crop(_gradient(width, height))
                self.assertLess(record.removed[0], SCALE)
                self.assertLess(record.removed[1], SCALE)


class DownscaleTests(unittest.TestCase):
    def test_produces_exactly_a_quarter_of_each_side(self):
        cropped, _ = mod_crop(_gradient(203, 101))

        self.assertEqual(downscale(cropped).size, (50, 25))

    def test_uses_the_fixed_bicubic_resample(self):
        cropped, _ = mod_crop(_gradient(203, 101))

        expected = cropped.resize((50, 25), resample=Image.Resampling.BICUBIC)

        self.assertIs(RESAMPLE, Image.Resampling.BICUBIC)
        self.assertEqual(downscale(cropped).tobytes(), expected.tobytes())


class SavePngTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def test_writes_a_real_png_and_creates_parents(self):
        destination = self.root / "nested" / "image.png"

        save_png(_gradient(8, 8), destination)

        self.assertTrue(destination.exists())
        self.assertEqual(destination.read_bytes()[:8], PNG_MAGIC)

    def test_round_trip_through_disk_preserves_pixels(self):
        destination = self.root / "image.png"
        image = _gradient(8, 8)

        save_png(image, destination)

        with Image.open(destination) as reloaded:
            self.assertEqual(reloaded.mode, "RGB")
            self.assertEqual(reloaded.convert("RGB").tobytes(), image.tobytes())


if __name__ == "__main__":
    unittest.main()
