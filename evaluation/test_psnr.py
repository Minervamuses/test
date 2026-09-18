"""Property checks for PSNR under the fixed metric conventions."""

import math
import unittest

import torch

from metrics import DATA_RANGE, psnr


def _image(height=48, width=64, seed=0):
    generator = torch.Generator().manual_seed(seed)
    return torch.randint(0, 256, (1, 3, height, width), generator=generator).to(torch.float32)


class PsnrTests(unittest.TestCase):
    def test_an_image_against_itself_is_infinite(self):
        image = _image()

        self.assertEqual(psnr(image, image), float("inf"))

    def test_a_constant_difference_of_one_level_matches_the_hand_calculation(self):
        image = _image().clamp(0, 254)
        shifted = image + 1

        expected = 10 * math.log10(DATA_RANGE**2 / 1.0)

        self.assertAlmostEqual(psnr(image, shifted), expected, places=9)
        self.assertAlmostEqual(expected, 48.13080361, places=6)

    def test_falls_monotonically_as_noise_grows(self):
        image = _image()
        generator = torch.Generator().manual_seed(7)
        noise = torch.randn((1, 3, 48, 64), generator=generator)

        values = [psnr(image, (image + noise * level).clamp(0, 255)) for level in (1, 2, 4, 8, 16)]

        self.assertEqual(values, sorted(values, reverse=True), values)

    def test_is_symmetric(self):
        first, second = _image(seed=1), _image(seed=2)

        self.assertEqual(psnr(first, second), psnr(second, first))

    def test_is_deterministic(self):
        first, second = _image(seed=1), _image(seed=2)

        self.assertEqual(psnr(first, second), psnr(first, second))

    def test_refuses_mismatched_shapes_instead_of_resizing(self):
        with self.assertRaises(ValueError) as raised:
            psnr(_image(48, 64), _image(48, 60))

        self.assertIn("shape", str(raised.exception).lower())

    def test_refuses_input_that_is_not_rgb_bchw(self):
        with self.assertRaises(ValueError):
            psnr(torch.zeros(3, 48, 64), torch.zeros(3, 48, 64))


if __name__ == "__main__":
    unittest.main()
