"""Property checks for the hand-written SSIM under the fixed metric conventions."""

import unittest

import torch

from metrics import SSIM_SIGMA, SSIM_WINDOW, ssim


def _image(height=48, width=64, seed=0):
    generator = torch.Generator().manual_seed(seed)
    return torch.randint(0, 256, (1, 3, height, width), generator=generator).to(torch.float32)


def _smooth_image(height=48, width=64):
    y = torch.linspace(0, 255, height).view(1, 1, height, 1)
    x = torch.linspace(0, 255, width).view(1, 1, 1, width)
    return ((y + x) / 2).expand(1, 3, height, width).contiguous()


class SsimTests(unittest.TestCase):
    def test_the_fixed_window_parameters_are_what_the_contract_says(self):
        self.assertEqual(SSIM_WINDOW, 11)
        self.assertEqual(SSIM_SIGMA, 1.5)

    def test_an_image_against_itself_is_one(self):
        for image in (_image(), _smooth_image()):
            with self.subTest(image=tuple(image.shape)):
                self.assertAlmostEqual(ssim(image, image), 1.0, delta=1e-6)

    def test_falls_monotonically_as_noise_grows(self):
        image = _smooth_image()
        generator = torch.Generator().manual_seed(11)
        noise = torch.randn((1, 3, 48, 64), generator=generator)

        values = [ssim(image, (image + noise * level).clamp(0, 255)) for level in (1, 2, 4, 8, 16)]

        self.assertEqual(values, sorted(values, reverse=True), values)

    def test_stays_inside_the_closed_unit_interval(self):
        pairs = (
            (_image(seed=1), _image(seed=2)),
            (_smooth_image(), 255.0 - _smooth_image()),
            (_smooth_image(), _image(seed=3)),
        )

        for first, second in pairs:
            with self.subTest():
                value = ssim(first, second)
                self.assertGreaterEqual(value, -1.0)
                self.assertLessEqual(value, 1.0)

    def test_an_inverted_image_scores_far_below_a_noisy_one(self):
        image = _smooth_image()
        generator = torch.Generator().manual_seed(13)
        mild = (image + torch.randn((1, 3, 48, 64), generator=generator)).clamp(0, 255)

        self.assertLess(ssim(image, 255.0 - image), ssim(image, mild))

    def test_is_symmetric(self):
        first, second = _image(seed=1), _image(seed=2)

        self.assertEqual(ssim(first, second), ssim(second, first))

    def test_is_deterministic(self):
        first, second = _image(seed=1), _image(seed=2)

        self.assertEqual(ssim(first, second), ssim(first, second))

    def test_refuses_mismatched_shapes_instead_of_resizing(self):
        with self.assertRaises(ValueError) as raised:
            ssim(_image(48, 64), _image(48, 60))

        self.assertIn("shape", str(raised.exception).lower())

    def test_refuses_images_smaller_than_the_window(self):
        with self.assertRaises(ValueError) as raised:
            ssim(_image(10, 64), _image(10, 64))

        self.assertIn("11", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
