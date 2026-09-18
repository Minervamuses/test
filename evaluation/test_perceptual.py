"""Property checks for the LPIPS wrapper under the fixed metric conventions."""

import unittest

import torch
from PIL import Image

from bicubic import upscale_bicubic
from degradation import downscale, mod_crop, save_png
from metrics import to_metric_tensor
from perceptual import LPIPS_NET, PerceptualMetric


def _gradient(width, height, seed=0):
    generator = torch.Generator().manual_seed(seed)
    base = torch.linspace(0, 255, width).view(1, width).expand(height, width)
    ripple = 40 * torch.sin(torch.linspace(0, 12, height)).view(height, 1)
    speckle = torch.rand((height, width), generator=generator) * 30
    channel = (base + ripple + speckle).clamp(0, 255).to(torch.uint8)
    image = Image.new("RGB", (width, height))
    image.putdata([(int(v), int(v * 0.8), int(255 - v)) for v in channel.flatten().tolist()])
    return image


class PerceptualMetricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metric = PerceptualMetric(device="cpu")
        cls.image = _gradient(160, 128)
        cls.truth = to_metric_tensor(cls.image)

    def test_the_network_is_the_one_the_contract_names(self):
        self.assertEqual(LPIPS_NET, "alex")
        self.assertEqual(str(self.metric.device), "cpu")

    def test_an_image_against_itself_is_essentially_zero(self):
        self.assertLessEqual(self.metric(self.truth, self.truth), 1e-4)

    def test_rises_monotonically_as_noise_grows(self):
        generator = torch.Generator().manual_seed(3)
        noise = torch.randn(self.truth.shape, generator=generator)

        values = [self.metric(self.truth, (self.truth + noise * level).clamp(0, 255)) for level in (2, 6, 18, 54)]

        self.assertEqual(values, sorted(values), values)

    def test_a_real_bicubic_round_trip_lands_strictly_inside_zero_and_one(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cropped, record = mod_crop(self.image)
            lr_path, restored_path = root / "lr.png", root / "bicubic.png"
            save_png(downscale(cropped), lr_path)
            upscale_bicubic(lr_path, record.cropped, restored_path)
            with Image.open(restored_path) as restored:
                value = self.metric(to_metric_tensor(cropped), to_metric_tensor(restored.convert("RGB")))

        self.assertGreater(value, 0.0)
        self.assertLess(value, 1.0)

    def test_is_symmetric(self):
        other = to_metric_tensor(_gradient(160, 128, seed=9))

        self.assertEqual(self.metric(self.truth, other), self.metric(other, self.truth))

    def test_is_deterministic_on_the_device_it_runs_on(self):
        other = to_metric_tensor(_gradient(160, 128, seed=9))

        self.assertEqual(self.metric(self.truth, other), self.metric(self.truth, other))
        self.assertFalse(torch.backends.cudnn.benchmark)

    def test_refuses_mismatched_shapes_instead_of_resizing(self):
        with self.assertRaises(ValueError) as raised:
            self.metric(self.truth, to_metric_tensor(_gradient(160, 120)))

        self.assertIn("shape", str(raised.exception).lower())


if __name__ == "__main__":
    unittest.main()
