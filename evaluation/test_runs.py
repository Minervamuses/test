"""Checks for creating a fresh evaluation run directory."""

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from runs import RUN_SUBDIRECTORIES, create_run_directory


class RunDirectoryTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name) / "runs"
        self.moment = datetime(2026, 9, 19, 1, 23, 45, tzinfo=timezone.utc)

    def test_creates_a_timestamped_directory_with_the_expected_layout(self):
        run = create_run_directory(self.root, moment=self.moment)

        self.assertEqual(run.parent, self.root)
        self.assertEqual(run.name, "20260919T012345Z")
        for name in RUN_SUBDIRECTORIES:
            self.assertTrue((run / name).is_dir(), name)

    def test_refuses_to_reuse_an_existing_directory(self):
        create_run_directory(self.root, moment=self.moment)

        with self.assertRaises(FileExistsError):
            create_run_directory(self.root, moment=self.moment)

    def test_two_moments_produce_two_independent_directories(self):
        first = create_run_directory(self.root, moment=self.moment)
        (first / "marker.txt").write_text("kept", encoding="utf-8")

        second = create_run_directory(self.root, moment=self.moment.replace(second=46))

        self.assertNotEqual(first, second)
        self.assertEqual((first / "marker.txt").read_text(encoding="utf-8"), "kept")


if __name__ == "__main__":
    unittest.main()
