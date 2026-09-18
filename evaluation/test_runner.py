"""Checks for the batch runner: sampling, per-image isolation, and both lines."""

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from metrics import load_metric_tensor
from perceptual import PerceptualMetric
from runner import ImageFailure, ImageResult, process_image, run_batch, select_sources
from runs import allocate_run_directory


def _write_source(directory, name, width=64, height=48, uniform=None):
    path = directory / name
    image = Image.new("RGB", (width, height))
    if uniform is not None:
        image.paste(uniform, (0, 0, width, height))
    else:
        image.putdata(
            [((x * 5) % 256, (y * 9) % 256, (x * y) % 256) for y in range(height) for x in range(width)]
        )
    image.save(path, format="PNG")
    return path


class _BicubicStubLine:
    """Stands in for the SR model: same interface, a plain resize instead."""

    scale = 4

    def __init__(self, failing=()):
        self.failing = set(failing)
        self.device = "stub"

    def run(self, lr_path, destination, expected_size):
        if lr_path.name in self.failing:
            raise RuntimeError("stub model refused this image")
        with Image.open(lr_path) as low:
            low.load()
            low.resize(expected_size, resample=Image.Resampling.BICUBIC).save(destination, format="PNG")


class SelectSourcesTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        for index in range(6):
            _write_source(self.root, f"img{index}.png", 16, 16)

    def test_takes_the_first_n_in_stable_order_by_default(self):
        selected = select_sources(self.root, limit=3)

        self.assertEqual([p.name for p in selected], ["img0.png", "img1.png", "img2.png"])

    def test_a_seed_samples_randomly_but_reproducibly(self):
        first = select_sources(self.root, limit=3, seed=42)
        again = select_sources(self.root, limit=3, seed=42)

        self.assertEqual([p.name for p in first], [p.name for p in again])
        self.assertEqual(len(first), 3)
        self.assertEqual(len(set(p.name for p in first)), 3)

    def test_a_limit_beyond_the_directory_returns_everything(self):
        self.assertEqual(len(select_sources(self.root, limit=99)), 6)


class RunBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.perceptual = PerceptualMetric(device="cpu")

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.sources = self.root / "sources"
        self.sources.mkdir()
        self.run_dir = allocate_run_directory(self.root / "runs")

    def test_one_image_produces_scores_on_both_lines(self):
        source = _write_source(self.sources, "a.png", 67, 51)

        result = process_image(source, self.run_dir, _BicubicStubLine(), self.perceptual)

        self.assertIsInstance(result, ImageResult)
        self.assertEqual(result.original, (67, 51))
        self.assertEqual(result.cropped, (64, 48))
        self.assertEqual(result.low, (16, 12))
        for line in (result.sr, result.bicubic):
            self.assertGreater(line.psnr, 0)
            self.assertLessEqual(line.ssim, 1.0)
            self.assertGreaterEqual(line.lpips, 0.0)

    def test_both_lines_read_the_same_low_resolution_file(self):
        source = _write_source(self.sources, "a.png", 64, 48)

        process_image(source, self.run_dir, _BicubicStubLine(), self.perceptual)

        produced = sorted(p.relative_to(self.run_dir).as_posix() for p in self.run_dir.rglob("*.png"))
        self.assertEqual(produced, ["bicubic/a.png", "hr/a.png", "lr/a.png", "sr/a.png"])

    def test_a_failing_image_is_isolated_and_the_batch_continues(self):
        sources = [
            _write_source(self.sources, "good1.png"),
            _write_source(self.sources, "bad.png"),
            _write_source(self.sources, "good2.png"),
        ]

        results, failures = run_batch(sources, self.run_dir, _BicubicStubLine(failing={"bad.png"}), self.perceptual)

        self.assertEqual([r.source_name for r in results], ["good1.png", "good2.png"])
        self.assertEqual(len(failures), 1)
        self.assertIsInstance(failures[0], ImageFailure)
        self.assertEqual(failures[0].source_name, "bad.png")
        self.assertEqual(failures[0].stage, "sr")
        self.assertIn("refused", failures[0].reason)

    def test_an_unreadable_source_is_recorded_rather_than_crashing_the_batch(self):
        deep = self.sources / "deep.png"
        Image.new("I;16", (32, 32), 1000).save(deep, format="PNG")
        good = _write_source(self.sources, "ok.png")

        results, failures = run_batch(sorted([deep, good]), self.run_dir, _BicubicStubLine(), self.perceptual)

        self.assertEqual([r.source_name for r in results], ["ok.png"])
        self.assertEqual([(f.source_name, f.stage) for f in failures], [("deep.png", "decode")])
        self.assertIn("16", failures[0].reason)

    def test_a_flat_image_makes_the_bicubic_line_exact_and_psnr_infinite(self):
        # A constant image survives downscale and bicubic upscale unchanged, so
        # its MSE is 0 and PSNR must be recorded as inf rather than dividing.
        source = _write_source(self.sources, "flat.png", 64, 48, uniform=(120, 130, 140))

        result = process_image(source, self.run_dir, _BicubicStubLine(), self.perceptual)

        self.assertEqual(result.bicubic.psnr, float("inf"))
        self.assertAlmostEqual(result.bicubic.ssim, 1.0, delta=1e-6)

    def test_the_real_sr_line_wires_up(self):
        from sr_line import SuperResolutionLine

        source = _write_source(self.sources, "real.png", 64, 48)

        result = process_image(source, self.run_dir, SuperResolutionLine(), self.perceptual)

        with Image.open(self.run_dir / "sr" / "real.png") as restored:
            self.assertEqual(restored.size, (64, 48))
        self.assertEqual(load_metric_tensor(self.run_dir / "sr" / "real.png").shape, (1, 3, 48, 64))
        self.assertGreater(result.sr.psnr, 0)


if __name__ == "__main__":
    unittest.main()
