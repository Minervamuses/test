"""Checks that the SR line runs through the unmodified pipeline."""

import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import torch
from PIL import Image

import drone_sr.image_io
import drone_sr.inference
import drone_sr.tiling
from degradation import downscale, mod_crop, save_png
from sr_line import EXPECTED_SCALE, SuperResolutionLine

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


class _StubDescriptor:
    def __init__(self, scale):
        self.scale = scale
        self.device = torch.device("cpu")


class ScaleAssertionTests(unittest.TestCase):
    def test_selected_checkpoint_and_architecture_are_preserved(self):
        checkpoint = Path("models/alternate.pth")
        descriptor = _StubDescriptor(4)
        descriptor.architecture = SimpleNamespace(name="SwinIR")
        with patch("sr_line.load_model", return_value=descriptor) as loader:
            line = SuperResolutionLine(checkpoint)
        loader.assert_called_once_with(checkpoint)
        self.assertEqual(line.model_path, checkpoint)
        self.assertEqual(line.architecture, "SwinIR")

    def test_a_model_that_is_not_four_times_is_refused(self):
        for scale in (2, 3, 8):
            with self.subTest(scale=scale):
                with patch("sr_line.load_model", return_value=_StubDescriptor(scale)):
                    with self.assertRaises(ValueError) as raised:
                        SuperResolutionLine()

                message = str(raised.exception)
                self.assertIn(str(EXPECTED_SCALE), message)
                self.assertIn(str(scale), message)

    def test_wrong_scale_error_identifies_selected_checkpoint(self):
        with patch("sr_line.load_model", return_value=_StubDescriptor(2)):
            with self.assertRaisesRegex(ValueError, "alternate.pth is 2x"):
                SuperResolutionLine(Path("models/alternate.pth"))

    def test_the_expected_scale_matches_the_degradation_contract(self):
        from degradation import SCALE

        self.assertEqual(EXPECTED_SCALE, SCALE)


class SuperResolutionLineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.line = SuperResolutionLine()

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.lr_path = self.root / "lr.png"
        self.destination = self.root / "sr.png"

        cropped, self.record = mod_crop(_gradient(203, 101))
        self.truth_size = cropped.size
        save_png(downscale(cropped), self.lr_path)

    def test_the_loaded_model_is_a_four_times_super_resolver(self):
        self.assertEqual(self.line.scale, 4)

    def test_output_size_equals_the_ground_truth_size(self):
        self.line.run(self.lr_path, self.destination, self.truth_size)

        with Image.open(self.lr_path) as low:
            self.assertEqual(low.size, (50, 25))
        with Image.open(self.destination) as restored:
            self.assertEqual(restored.size, self.truth_size)
            self.assertEqual(restored.size, (200, 100))

    def test_output_is_a_png(self):
        self.line.run(self.lr_path, self.destination, self.truth_size)

        self.assertEqual(self.destination.read_bytes()[:8], PNG_MAGIC)

    def test_output_follows_the_lr_file_when_that_file_is_overwritten(self):
        self.line.run(self.lr_path, self.destination, self.truth_size)
        first = self.destination.read_bytes()

        save_png(_gradient(50, 25, shift=97), self.lr_path)
        second = self.root / "sr-after.png"
        self.line.run(self.lr_path, second, self.truth_size)

        self.assertNotEqual(first, second.read_bytes())

    def test_a_wrong_expected_size_is_reported_rather_than_resized(self):
        with self.assertRaises(ValueError) as raised:
            self.line.run(self.lr_path, self.destination, (200, 99))

        self.assertIn("200", str(raised.exception))

    def test_the_pipeline_modules_are_untouched_by_running_the_line(self):
        modules = [drone_sr.image_io, drone_sr.inference, drone_sr.tiling]
        before = [hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in modules]

        self.line.run(self.lr_path, self.destination, self.truth_size)

        after = [hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in modules]
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
