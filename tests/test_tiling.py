import unittest

import torch

from drone_sr.tiling import upscale_tiled
from drone_sr.inference import _upscale_direct
from test_inference import synthetic_descriptor


def coordinate_ramp(width, height):
    y, x = torch.meshgrid(torch.arange(height), torch.arange(width), indexing="ij")
    return torch.stack((y, x, y * width + x)).unsqueeze(0).float()


def repeat_pixels(image, scale):
    return image.repeat_interleave(scale, -2).repeat_interleave(scale, -1)


class TilingTests(unittest.TestCase):
    def test_coordinates_and_outer_edges_at_two_scales(self):
        cases = ((16, 16, 4), (19, 13, 6), (7, 5, 1), (17, 15, 6))
        for width, height, tile_count in cases:
            for scale in (2, 3):
                with self.subTest(width=width, height=height, scale=scale):
                    source = coordinate_ramp(width, height)
                    calls = []

                    def predict(tile):
                        self.assertEqual(tile.device.type, "cpu")
                        x = int(tile[0, 1, 0, 0])
                        y = int(tile[0, 0, 0, 0])
                        calls.append((x, y, tile.shape[-1], tile.shape[-2]))
                        return repeat_pixels(tile, scale)

                    output = upscale_tiled(source, scale, predict, tile_size=8, overlap=2)
                    self.assertEqual(output.device.type, "cpu")
                    self.assertEqual(output.shape, (1, 3, height * scale, width * scale))
                    torch.testing.assert_close(output, repeat_pixels(source, scale), rtol=0, atol=0)
                    self.assertEqual(len(calls), tile_count)
                    if (width, height) == (19, 13):
                        self.assertCountEqual(
                            calls,
                            [(0, 0, 10, 10), (6, 0, 12, 10), (14, 0, 5, 10),
                             (0, 6, 10, 7), (6, 6, 12, 7), (14, 6, 5, 7)],
                        )

    def test_descriptor_padding_is_removed_before_tile_coordinates_are_used(self):
        source = coordinate_ramp(11, 1) / 10
        descriptor = synthetic_descriptor(scale=3)
        output = upscale_tiled(
            source, descriptor.scale, lambda tile: _upscale_direct(tile, descriptor),
            tile_size=8, overlap=2,
        )
        self.assertEqual(output.shape, (1, 3, 3, 33))
        torch.testing.assert_close(output, repeat_pixels(source, 3), rtol=0, atol=0)

    def test_wrong_tile_output_shape_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "output shape"):
            upscale_tiled(
                coordinate_ramp(9, 5), 2, lambda tile: repeat_pixels(tile, 2)[..., :-1, :],
                tile_size=8, overlap=2,
            )

    def test_tile_failure_propagates_without_a_partial_result(self):
        calls = 0
        failure = RuntimeError("second tile failed")

        def predict(tile):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise failure
            return repeat_pixels(tile, 2)

        with self.assertRaises(RuntimeError) as raised:
            upscale_tiled(coordinate_ramp(19, 13), 2, predict, tile_size=8, overlap=2)
        self.assertIs(raised.exception, failure)
        self.assertEqual(calls, 2)


if __name__ == "__main__":
    unittest.main()
