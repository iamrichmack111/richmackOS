from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parent.parent

CLI = (
    ROOT
    / "scripts"
    / "richmack-framework"
)


class FrameworkCLITests(unittest.TestCase):

    def run_cli(
        self,
        *args,
    ):
        return subprocess.run(
            [
                sys.executable,
                str(CLI),
                *args,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

    def test_reference(self):
        result = self.run_cli(
            "reference"
        )

        self.assertEqual(
            result.returncode,
            0,
        )

        self.assertIn(
            "Seven-rep growth",
            result.stdout,
        )

    def test_default_command_is_reference(self):
        result = self.run_cli()

        self.assertEqual(
            result.returncode,
            0,
        )

        self.assertIn(
            "Formula Reference",
            result.stdout,
        )

    def test_growth(self):
        result = self.run_cli(
            "growth",
            "--baseline",
            "1",
            "--reps",
            "14",
            "--topic",
            "Python",
        )

        self.assertEqual(
            result.returncode,
            0,
        )

        self.assertIn(
            "4.0000x",
            result.stdout,
        )

        self.assertIn(
            "Topic: Python",
            result.stdout,
        )

    def test_target(self):
        result = self.run_cli(
            "target",
            "--growth",
            "100",
        )

        self.assertEqual(
            result.returncode,
            0,
        )

        self.assertIn(
            "46.51",
            result.stdout,
        )

    def test_retention(self):
        result = self.run_cli(
            "retention",
            "--reps",
            "40",
            "--rate",
            "0.45",
        )

        self.assertEqual(
            result.returncode,
            0,
        )

        self.assertIn(
            "18.00",
            result.stdout,
        )

        self.assertIn(
            "22.00",
            result.stdout,
        )

    def test_approach(self):
        result = self.run_cli(
            "approach",
            "--clarity",
            ".9",
            "--relevance",
            ".8",
            "--integration",
            ".7",
            "--stability",
            ".6",
        )

        self.assertEqual(
            result.returncode,
            0,
        )

        self.assertIn(
            "0.3024",
            result.stdout,
        )

    def test_learning(self):
        result = self.run_cli(
            "learning"
        )

        self.assertEqual(
            result.returncode,
            0,
        )

        self.assertIn(
            "Strict Learning Unit:   1",
            result.stdout,
        )

    def test_mass(self):
        result = self.run_cli(
            "mass",
            "--bits",
            "10",
            "--relationships",
            "3",
        )

        self.assertEqual(
            result.returncode,
            0,
        )

        self.assertIn(
            "Gross mass:",
            result.stdout,
        )

    def test_capability(self):
        result = self.run_cli(
            "capability",
            "--baseline",
            "25",
            "--target",
            "100",
            "--solo",
            "60",
            "--assisted",
            "100",
            "--capability",
            ".8",
            "--stability",
            ".9",
        )

        self.assertEqual(
            result.returncode,
            0,
        )

        self.assertIn(
            "4.0000x",
            result.stdout,
        )

        self.assertIn(
            "0.6000",
            result.stdout,
        )

    def test_focus(self):
        result = self.run_cli(
            "focus",
            "--active",
            "6",
            "--progress",
            "10",
        )

        self.assertEqual(
            result.returncode,
            0,
        )

        self.assertIn(
            "Entropy cost:           3.00",
            result.stdout,
        )

        self.assertIn(
            "Effective progress:     7.00",
            result.stdout,
        )

    def test_invalid_retention_fails(self):
        result = self.run_cli(
            "retention",
            "--reps",
            "10",
            "--rate",
            "1.5",
        )

        self.assertNotEqual(
            result.returncode,
            0,
        )


if __name__ == "__main__":
    unittest.main()
