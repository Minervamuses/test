"""Checks for the conversion that feeds images into the metrics."""

import tempfile
import unittest
from pathlib import Path

import torch
from PIL import Image

from metrics import load_metric_tensor, to_metric_tensor


class MetricInputTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def test_values_are_eight_bit_levels_not_a_unit_interval(self):
        white = to_metric_tensor(Image.new("RGB", (4, 3), (255, 255, 255)))

        self.assertEqual(white.dtype, torch.float32)
        self.assertEqual(white.shape, (1, 3, 3, 4))
        self.assertEqual(white.min().item(), 255.0)

    def test_channels_keep_their_order(self):
        tensor = to_metric_tensor(Image.new("RGB", (2, 2), (10, 20, 30)))

        self.assertEqual([tensor[0, c].unique().item() for c in range(3)], [10.0, 20.0, 30.0])

    def test_refuses_a_non_rgb_image_instead_of_converting_it(self):
        with self.assertRaises(ValueError) as raised:
            to_metric_tensor(Image.new("L", (4, 4), 128))

        self.assertIn("RGB", str(raised.exception))

    def test_loading_a_png_round_trips_the_pixels(self):
        path = self.root / "image.png"
        image = Image.new("RGB", (5, 4))
        image.putdata([(x * 9 % 256, y * 13 % 256, (x + y) * 7 % 256) for y in range(4) for x in range(5)])
        image.save(path, format="PNG")

        self.assertTrue(torch.equal(load_metric_tensor(path), to_metric_tensor(image)))


if __name__ == "__main__":
    unittest.main()
