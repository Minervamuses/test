"""Checks for the averaging rules fixed by GOALS.md item 5 and the inf rule in item 2."""

import math
import unittest

from runner import ImageFailure, ImageResult, LineScores
from summary import summarise


def _result(name, sr, bicubic):
    return ImageResult(
        source_name=name,
        original=(64, 48),
        cropped=(64, 48),
        low=(16, 12),
        sr=LineScores(*sr),
        bicubic=LineScores(*bicubic),
    )


def _by_name(summary):
    return {metric.name: metric for metric in summary.metrics}


class SummaryTests(unittest.TestCase):
    def test_averages_are_arithmetic_means_over_the_included_images(self):
        results = [
            _result("a", sr=(30.0, 0.80, 0.20), bicubic=(32.0, 0.90, 0.30)),
            _result("b", sr=(20.0, 0.60, 0.10), bicubic=(28.0, 0.70, 0.50)),
        ]

        metrics = _by_name(summarise(results, []))

        self.assertEqual(metrics["PSNR"].sr_mean, 25.0)
        self.assertEqual(metrics["PSNR"].bicubic_mean, 30.0)
        self.assertAlmostEqual(metrics["SSIM"].sr_mean, 0.70)
        self.assertAlmostEqual(metrics["LPIPS"].bicubic_mean, 0.40)

    def test_failed_images_are_counted_but_never_averaged(self):
        results = [_result("a", sr=(30.0, 0.8, 0.2), bicubic=(32.0, 0.9, 0.3))]
        failures = [ImageFailure("b", "sr", "model refused"), ImageFailure("c", "decode", "16 bits")]

        summary = summarise(results, failures)

        self.assertEqual(summary.included, 1)
        self.assertEqual(summary.failed, 2)
        self.assertEqual(_by_name(summary)["PSNR"].counted, 1)

    def test_an_infinite_psnr_drops_that_image_from_the_psnr_mean_only(self):
        results = [
            _result("a", sr=(30.0, 0.80, 0.20), bicubic=(float("inf"), 1.00, 0.00)),
            _result("b", sr=(20.0, 0.60, 0.10), bicubic=(28.0, 0.70, 0.50)),
        ]

        metrics = _by_name(summarise(results, []))

        self.assertEqual(metrics["PSNR"].counted, 1)
        self.assertEqual(metrics["PSNR"].excluded_infinite, 1)
        self.assertEqual(metrics["PSNR"].sr_mean, 20.0)
        self.assertEqual(metrics["PSNR"].bicubic_mean, 28.0)
        # SSIM and LPIPS still see both images.
        self.assertEqual(metrics["SSIM"].counted, 2)
        self.assertAlmostEqual(metrics["SSIM"].sr_mean, 0.70)
        self.assertEqual(metrics["LPIPS"].counted, 2)
        self.assertAlmostEqual(metrics["LPIPS"].bicubic_mean, 0.25)

    def test_an_image_infinite_on_either_line_is_dropped_from_psnr(self):
        results = [
            _result("a", sr=(float("inf"), 1.0, 0.0), bicubic=(31.0, 0.9, 0.3)),
            _result("b", sr=(20.0, 0.6, 0.1), bicubic=(28.0, 0.7, 0.5)),
        ]

        self.assertEqual(_by_name(summarise(results, []))["PSNR"].counted, 1)

    def test_every_psnr_infinite_leaves_no_mean_rather_than_a_wrong_one(self):
        results = [_result("a", sr=(float("inf"), 1.0, 0.0), bicubic=(float("inf"), 1.0, 0.0))]

        psnr = _by_name(summarise(results, []))["PSNR"]

        self.assertEqual(psnr.counted, 0)
        self.assertIsNone(psnr.sr_mean)
        self.assertEqual(psnr.winner, "n/a")

    def test_the_winner_follows_each_metric_own_direction(self):
        results = [_result("a", sr=(30.0, 0.80, 0.20), bicubic=(32.0, 0.90, 0.30))]

        metrics = _by_name(summarise(results, []))

        self.assertTrue(metrics["PSNR"].higher_is_better)
        self.assertTrue(metrics["SSIM"].higher_is_better)
        self.assertFalse(metrics["LPIPS"].higher_is_better)
        self.assertEqual(metrics["PSNR"].winner, "bicubic")
        self.assertEqual(metrics["SSIM"].winner, "bicubic")
        # Lower LPIPS is better, so SR wins here even though its number is smaller.
        self.assertEqual(metrics["LPIPS"].winner, "SR")
        self.assertAlmostEqual(metrics["LPIPS"].margin, 0.10)

    def test_equal_means_are_a_tie(self):
        results = [_result("a", sr=(30.0, 0.8, 0.2), bicubic=(30.0, 0.8, 0.2))]

        self.assertEqual(_by_name(summarise(results, []))["PSNR"].winner, "tie")

    def test_no_successful_image_produces_a_summary_rather_than_an_error(self):
        summary = summarise([], [ImageFailure("a", "decode", "broken")])

        self.assertEqual(summary.included, 0)
        self.assertEqual(summary.failed, 1)
        for metric in summary.metrics:
            self.assertIsNone(metric.sr_mean)
            self.assertEqual(metric.winner, "n/a")

    def test_the_three_metrics_are_reported_in_a_fixed_order(self):
        summary = summarise([_result("a", sr=(30.0, 0.8, 0.2), bicubic=(30.0, 0.8, 0.2))], [])

        self.assertEqual([m.name for m in summary.metrics], ["PSNR", "SSIM", "LPIPS"])

    def test_means_ignore_nothing_else(self):
        results = [_result(str(i), sr=(float(i), 0.5, 0.5), bicubic=(float(i), 0.5, 0.5)) for i in range(1, 5)]

        psnr = _by_name(summarise(results, []))["PSNR"]

        self.assertEqual(psnr.counted, 4)
        self.assertEqual(psnr.sr_mean, 2.5)
        self.assertFalse(math.isnan(psnr.sr_mean))


if __name__ == "__main__":
    unittest.main()
