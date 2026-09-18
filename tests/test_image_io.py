import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import torch
from PIL import Image, ImageOps

from drone_sr.image_io import read_image, write_png


class ImageIOTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "source.png"
        self.destination = self.root / "output" / "source.png"

    def _oriented_source(self, path, orientation, image_format):
        # Non-square with four distinguishable corners: every orientation maps to
        # a different pixel layout, so rotations and mirrors cannot be confused.
        image = Image.new("RGB", (40, 20), (10, 10, 10))
        for corner, color in (
            ((0, 0), (255, 0, 0)),
            ((39, 0), (0, 255, 0)),
            ((0, 19), (0, 0, 255)),
            ((39, 19), (255, 255, 0)),
        ):
            image.putpixel(corner, color)
        exif = Image.Exif()
        exif[274] = orientation
        image.save(path, format=image_format, exif=exif)

    def test_rgb_channels_range_shape_and_png_round_trip(self):
        source = Image.new("RGB", (2, 1))
        source.putdata([(255, 0, 128), (0, 64, 255)])
        source.save(self.source)
        original = self.source.read_bytes()

        tensor = read_image(self.source)

        self.assertEqual(tensor.shape, (1, 3, 1, 2))
        self.assertEqual(tensor.dtype, torch.float32)
        torch.testing.assert_close(
            tensor,
            torch.tensor([[[[255, 0]], [[0, 64]], [[128, 255]]]]) / 255,
        )
        write_png(tensor, self.destination, self.source)
        with Image.open(self.destination) as output:
            self.assertEqual(output.format, "PNG")
            self.assertEqual(output.mode, "RGB")
            self.assertEqual(output.size, (2, 1))
            self.assertEqual(output.tobytes(), source.tobytes())
        self.assertEqual(self.source.read_bytes(), original)

    def test_grayscale_becomes_rgb_and_bad_image_raises(self):
        Image.new("L", (1, 1), 64).save(self.source)
        torch.testing.assert_close(read_image(self.source), torch.full((1, 3, 1, 1), 64 / 255))
        self.source.write_bytes(b"not an image")
        with self.assertRaises(OSError):
            read_image(self.source)

    def test_high_bit_depth_is_rejected_explicitly(self):
        Image.new("I;16", (2, 2)).save(self.source)
        with self.assertRaisesRegex(ValueError, "Unsupported image mode"):
            read_image(self.source)

    def test_exif_orientation_is_applied_to_pixels(self):
        for image_format, suffix in (("JPEG", ".jpg"), ("PNG", ".png")):
            for orientation in range(1, 9):
                with self.subTest(format=image_format, orientation=orientation):
                    source = self.root / f"oriented_{orientation}{suffix}"
                    self._oriented_source(source, orientation, image_format)
                    before = hashlib.sha256(source.read_bytes()).hexdigest()
                    with Image.open(source) as opened:
                        stored = opened.convert("RGB").tobytes()
                        expected = ImageOps.exif_transpose(opened).convert("RGB")
                    if orientation != 1:
                        # Guard the fixture: orientations 2-4 keep the size, so a
                        # size-only comparison would pass without any correction.
                        self.assertNotEqual(expected.tobytes(), stored)

                    destination = self.root / "output" / f"oriented_{orientation}.png"
                    write_png(read_image(source), destination, source)

                    with Image.open(destination) as output:
                        self.assertEqual(output.size, expected.size)
                        self.assertEqual(output.tobytes(), expected.tobytes())
                    self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)

    def test_oriented_tiff_is_not_transposed_twice(self):
        source = self.root / "oriented.tif"
        self._oriented_source(source, 6, "TIFF")
        with Image.open(source) as opened:
            # Pillow applies the tag itself while loading a TIFF.
            expected = opened.convert("RGB")

        tensor = read_image(source)

        self.assertEqual(expected.size, (20, 40))
        write_png(tensor, self.destination, source)
        with Image.open(self.destination) as output:
            self.assertEqual(output.size, expected.size)
            self.assertEqual(output.tobytes(), expected.tobytes())

    def test_multi_frame_images_stay_rejected(self):
        first = Image.new("RGB", (4, 2), (10, 20, 30))
        second = Image.new("RGB", (4, 2), (40, 50, 60))
        pages = self.root / "pages.tif"
        first.save(pages, save_all=True, append_images=[second])
        animated = self.root / "animated.png"
        first.save(animated, save_all=True, append_images=[second])
        for source in (pages, animated):
            with self.subTest(source=source.name):
                with self.assertRaisesRegex(ValueError, "Only single-frame images are supported"):
                    read_image(source)

    def test_clamp_and_round_before_png_encoding(self):
        Image.new("RGB", (1, 1)).save(self.source)
        tensor = torch.tensor([[[[-0.5]], [[0.5]], [[1.5]]]])
        write_png(tensor, self.destination, self.source)
        with Image.open(self.destination) as output:
            self.assertEqual(output.getpixel((0, 0)), (0, 128, 255))

    def test_nonfinite_output_does_not_replace_existing_result(self):
        Image.new("RGB", (1, 1)).save(self.source)
        self.destination.parent.mkdir()
        self.destination.write_bytes(b"previous result")
        with self.assertRaisesRegex(ValueError, "non-finite"):
            write_png(torch.full((1, 3, 1, 1), float("nan")), self.destination, self.source)
        self.assertEqual(self.destination.read_bytes(), b"previous result")

    def test_encoding_failure_keeps_previous_result_and_cleans_temporary_file(self):
        Image.new("RGB", (1, 1)).save(self.source)
        self.destination.parent.mkdir()
        self.destination.write_bytes(b"previous result")
        with patch.object(Image.Image, "save", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(OSError, "disk full"):
                write_png(torch.zeros(1, 3, 1, 1), self.destination, self.source)
        self.assertEqual(self.destination.read_bytes(), b"previous result")
        self.assertEqual(list(self.destination.parent.iterdir()), [self.destination])

    def test_source_and_its_file_aliases_cannot_be_overwritten(self):
        Image.new("RGB", (1, 1), (12, 34, 56)).save(self.source)
        original = self.source.read_bytes()
        symbolic = self.root / "symbolic.png"
        symbolic.symlink_to(self.source)
        hard = self.root / "hard.png"
        hard.hardlink_to(self.source)
        for destination in (self.source, symbolic, hard):
            with self.subTest(destination=destination.name):
                with self.assertRaisesRegex(ValueError, "overwrite input"):
                    write_png(torch.zeros(1, 3, 1, 1), destination, self.source)
        self.assertEqual(self.source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
