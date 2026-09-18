"""Checks that report.md carries everything GOALS.md needs to make it traceable."""

import re
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from report import REQUIRED_HEADER_FIELDS, RunEnvironment, render_report
from runner import ImageFailure, ImageResult, LineScores
from summary import summarise


def _environment(run_dir):
    return RunEnvironment(
        started=datetime(2026, 9, 19, 2, 30, 0, tzinfo=timezone.utc),
        run_dir=run_dir,
        git_head="0123456789abcdef0123456789abcdef01234567",
        worktree_clean=True,
        source_directory=Path("input"),
        discovery_rule="direct children with suffix .png/.jpg/.jpeg",
        sampling="sequential",
        limit=5,
        discovered=738,
        selected=2,
        pillow_version="12.3.0",
        model_target="realesr-general-x4v3.pth",
        model_sha256="8dc7edb9ac80ccdc30c3a5dca6616509367f05fbc184ad95b731f05bece96292",
        architecture="RealESRGAN Compact",
        model_scale=4,
        tile_size=512,
        sr_device="cpu",
        lpips_device="cpu",
        cudnn_benchmark=False,
        lpips_version="0.1.4",
        lpips_net="alex",
        lpips_linear_sha256="df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0",
        lpips_backbone_url="https://download.pytorch.org/models/alexnet-owt-7be5be79.pth",
        lpips_backbone_sha256="7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02",
    )


def _result(name, sr, bicubic):
    return ImageResult(
        source_name=name,
        original=(4056, 3040),
        cropped=(4056, 3040),
        low=(1014, 760),
        sr=LineScores(*sr),
        bicubic=LineScores(*bicubic),
    )


class ReportTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.run_dir = Path(directory.name) / "20260919T023000Z"
        self.results = [
            _result("a.JPG", sr=(27.5, 0.78, 0.21), bicubic=(29.1, 0.84, 0.36)),
            _result("b.JPG", sr=(26.0, 0.74, 0.25), bicubic=(28.4, 0.81, 0.39)),
        ]
        self.failures = [ImageFailure("c.JPG", "sr", "out of memory"), ImageFailure("d.png", "decode", "16 bits per sample")]
        self.text = render_report(_environment(self.run_dir), self.results, self.failures, summarise(self.results, self.failures))

    def test_every_required_header_field_is_present_with_a_value(self):
        for field in REQUIRED_HEADER_FIELDS:
            with self.subTest(field=field):
                match = re.search(rf"^\| {re.escape(field)} \| (.+?) \|$", self.text, re.MULTILINE)
                self.assertIsNotNone(match, f"header field missing: {field}")
                value = match.group(1).strip()
                self.assertNotIn(value, ("", "None", "nan", "—", "-"), f"header field empty: {field}")

    def test_the_header_records_what_makes_a_number_traceable(self):
        self.assertIn("0123456789abcdef0123456789abcdef01234567", self.text)
        self.assertIn(str(self.run_dir), self.text)
        self.assertIn("2026-09-19", self.text)

    def test_the_header_separates_the_device_each_metric_runs_on(self):
        self.assertIn("| PSNR／SSIM device | CPU、float64", self.text)
        self.assertIn("| LPIPS device | cpu", self.text)

    def test_the_interpretation_caveats_are_not_omitted(self):
        self.assertIn("RGB", self.text)
        self.assertIn("Y ", self.text)
        self.assertIn("bicubic", self.text)
        self.assertIn("GAN", self.text)
        self.assertIn("LPIPS", self.text)

    def test_there_is_one_row_per_successful_image(self):
        rows = [line for line in self.text.splitlines() if line.startswith("| a.JPG |") or line.startswith("| b.JPG |")]

        self.assertEqual(len(rows), len(self.results))
        for row in rows:
            self.assertIn("4056×3040", row)
            self.assertIn("1014×760", row)

    def test_the_average_section_states_counts_and_a_winner_per_metric(self):
        for metric in ("PSNR", "SSIM", "LPIPS"):
            with self.subTest(metric=metric):
                row = re.search(rf"^\| {metric} \| .+ \|$", self.text, re.MULTILINE)
                self.assertIsNotNone(row, f"no average row for {metric}")
                self.assertIn(row.group(0).split("|")[5].strip(), ("SR", "bicubic", "tie"))
        self.assertIn("納入 2", self.text)
        self.assertIn("排除 2", self.text)

    def test_failures_are_listed_with_stage_and_reason(self):
        self.assertIn("| c.JPG | sr | out of memory |", self.text)
        self.assertIn("| d.png | decode | 16 bits per sample |", self.text)

    def test_nothing_renders_as_none_or_nan(self):
        for token in ("None", "nan", "NaN"):
            self.assertNotIn(token, self.text)

    def test_a_run_with_no_successful_image_still_produces_a_report(self):
        text = render_report(_environment(self.run_dir), [], self.failures, summarise([], self.failures))

        self.assertIn("納入 0", text)
        self.assertIn("| c.JPG | sr | out of memory |", text)
        self.assertNotIn("nan", text)

    def test_an_infinite_psnr_is_shown_and_explained(self):
        results = [
            _result("flat.JPG", sr=(30.0, 0.9, 0.1), bicubic=(float("inf"), 1.0, 0.0)),
            _result("b.JPG", sr=(26.0, 0.74, 0.25), bicubic=(28.4, 0.81, 0.39)),
        ]

        text = render_report(_environment(self.run_dir), results, [], summarise(results, []))

        self.assertIn("inf", text)
        self.assertIn("排除於 PSNR 平均", text)


if __name__ == "__main__":
    unittest.main()
