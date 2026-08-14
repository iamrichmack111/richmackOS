from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from richmack_metrics.repository import (
    find_repository,
    iter_source_files,
    line_count,
    read_text,
)


class RepositoryTests(unittest.TestCase):

    def test_find_repository(self):
        root = find_repository()

        self.assertTrue(
            (root / ".git").exists()
        )

    def test_line_count(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"

            path.write_text(
                "one\ntwo\nthree\n",
                encoding="utf-8",
            )

            self.assertEqual(
                line_count(path),
                3,
            )

    def test_read_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.txt"

            path.write_text(
                "RichmackOS",
                encoding="utf-8",
            )

            self.assertEqual(
                read_text(path),
                "RichmackOS",
            )

    def test_source_discovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            (root / "good.py").write_text(
                "print('ok')\n",
                encoding="utf-8",
            )

            (root / "ignore.txt").write_text(
                "not source\n",
                encoding="utf-8",
            )

            files = list(
                iter_source_files(root)
            )

            names = {
                path.name
                for path in files
            }

            self.assertIn(
                "good.py",
                names,
            )

            self.assertNotIn(
                "ignore.txt",
                names,
            )


if __name__ == "__main__":
    unittest.main()


class RepositoryResourceTests(unittest.TestCase):

    def test_bin_script_discovery_closes_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            bin_dir = root / "bin"
            bin_dir.mkdir()

            script = bin_dir / "example"

            script.write_text(
                "#!/usr/bin/env bash\n"
                "echo test\n",
                encoding="utf-8",
            )

            files = list(
                iter_source_files(root)
            )

            self.assertIn(
                script,
                files,
            )
