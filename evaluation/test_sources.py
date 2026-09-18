"""Checks for source discovery and decoding under the fixed degradation contract."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from sources import UnsupportedSource, decode_source, discover_sources


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def _touch(self, name):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")
        return path

    def test_lists_only_direct_png_and_jpeg_children(self):
        for name in ("a.png", "b.JPG", "c.jpeg", "d.txt", "e.json", "sub/f.png"):
            self._touch(name)

        found = discover_sources(self.root)

        self.assertEqual([path.name for path in found], ["a.png", "b.JPG", "c.jpeg"])

    def test_order_is_stable_and_independent_of_filesystem_order(self):
        for name in ("z.png", "m.JPEG", "a.jpg"):
            self._touch(name)

        self.assertEqual(
            [path.name for path in discover_sources(self.root)],
            [path.name for path in discover_sources(self.root)],
        )
        self.assertEqual([path.name for path in discover_sources(self.root)], ["a.jpg", "m.JPEG", "z.png"])

    def test_empty_directory_yields_nothing(self):
        self.assertEqual(discover_sources(self.root), [])


class DecodeTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def test_multi_frame_source_decodes_to_the_first_frame(self):
        # Mirrors the real DJI MPO files: frame 0 is the full-resolution main
        # image and frame 1 is a smaller thumbnail.
        path = self.root / "multi.jpg"
        main = Image.new("RGB", (40, 30), (200, 40, 40))
        thumbnail = Image.new("RGB", (20, 15), (40, 40, 200))
        main.save(path, format="MPO", append_images=[thumbnail])

        with Image.open(path) as probe:
            self.assertEqual(getattr(probe, "n_frames", 1), 2)

        decoded = decode_source(path)

        self.assertEqual(decoded.size, (40, 30))
        self.assertEqual(decoded.mode, "RGB")

    def test_exif_orientation_is_applied(self):
        path = self.root / "rotated.jpg"
        image = Image.new("RGB", (40, 20), (10, 120, 10))
        exif = image.getexif()
        exif[274] = 6  # Rotate 90 degrees: the decoded image must be 20x40.
        image.save(path, format="JPEG", exif=exif)

        self.assertEqual(decode_source(path).size, (20, 40))

    def test_more_than_eight_bits_per_sample_is_refused_with_a_reason(self):
        path = self.root / "deep.png"
        Image.new("I;16", (16, 16), 1000).save(path, format="PNG")

        with self.assertRaises(UnsupportedSource) as raised:
            decode_source(path)

        self.assertIn("16", str(raised.exception))

    def test_eight_bit_png_is_accepted(self):
        path = self.root / "plain.png"
        Image.new("RGB", (12, 9), (1, 2, 3)).save(path, format="PNG")

        decoded = decode_source(path)

        self.assertEqual(decoded.size, (12, 9))
        self.assertEqual(decoded.mode, "RGB")

    def test_decoding_leaves_the_source_file_untouched(self):
        path = self.root / "plain.png"
        Image.new("RGB", (12, 9), (7, 8, 9)).save(path, format="PNG")
        before = hashlib.sha256(path.read_bytes()).hexdigest()

        decode_source(path)

        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)


if __name__ == "__main__":
    unittest.main()
