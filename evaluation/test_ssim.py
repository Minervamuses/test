"""Property checks for the hand-written SSIM under the fixed metric conventions."""

import math
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


def _naive_ssim(first, second):
    """A deliberately slow, independent re-derivation of the same definition.

    scikit-image and torchmetrics are outside this plan's authorization, so no
    third-party SSIM is available to compare against. This walks every 11x11
    window explicitly in plain Python instead of convolving, and builds the
    Gaussian straight from the isotropic 2-D formula rather than as an outer
    product of a normalised 1-D kernel. It shares no code path with metrics.ssim
    beyond the definition itself, so it catches the failure modes that matter
    here: a mis-normalised window, wrong boundary handling, or averaging the
    channels the wrong way. It is not independent evidence of the definition
    being the right one - only that the fast implementation computes it.
    """
    weights = [
        [math.exp(-(((i - 5) ** 2) + ((j - 5) ** 2)) / (2 * SSIM_SIGMA**2)) for j in range(SSIM_WINDOW)]
        for i in range(SSIM_WINDOW)
    ]
    total = sum(sum(row) for row in weights)
    weights = [[value / total for value in row] for row in weights]

    c1 = (0.01 * 255.0) ** 2
    c2 = (0.03 * 255.0) ** 2
    left = first[0].to(torch.float64).tolist()
    right = second[0].to(torch.float64).tolist()
    height, width = len(left[0]), len(left[0][0])

    channel_means = []
    for channel in range(3):
        window_values = []
        for top in range(height - SSIM_WINDOW + 1):
            for start in range(width - SSIM_WINDOW + 1):
                mx = my = mxx = myy = mxy = 0.0
                for i in range(SSIM_WINDOW):
                    for j in range(SSIM_WINDOW):
                        weight = weights[i][j]
                        a = left[channel][top + i][start + j]
                        b = right[channel][top + i][start + j]
                        mx += weight * a
                        my += weight * b
                        mxx += weight * a * a
                        myy += weight * b * b
                        mxy += weight * a * b
                variance_x = mxx - mx * mx
                variance_y = myy - my * my
                covariance = mxy - mx * my
                window_values.append(
                    ((2 * mx * my + c1) * (2 * covariance + c2))
                    / ((mx * mx + my * my + c1) * (variance_x + variance_y + c2))
                )
        channel_means.append(sum(window_values) / len(window_values))
    return sum(channel_means) / 3


class SsimCrossCheckTests(unittest.TestCase):
    def test_matches_a_naive_per_window_reference(self):
        cases = (
            ("random", _image(20, 24, seed=5), _image(20, 24, seed=6)),
            ("smooth vs noisy", _smooth_image(20, 24), (_smooth_image(20, 24) + 12.0).clamp(0, 255)),
            ("identical", _smooth_image(20, 24), _smooth_image(20, 24)),
        )

        for label, first, second in cases:
            with self.subTest(case=label):
                self.assertAlmostEqual(ssim(first, second), _naive_ssim(first, second), delta=1e-9)


if __name__ == "__main__":
    unittest.main()
