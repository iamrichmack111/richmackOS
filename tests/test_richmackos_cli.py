from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class RichmackOSCLITests(unittest.TestCase):

    def run_cli(self, *args: str):
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "richmackos.py"),
                *args,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )

    def test_help(self):
        result = self.run_cli(
            "--help"
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=result.stderr,
        )

        self.assertIn(
            "RichmackOS",
            result.stdout,
        )

    def test_unknown_command(self):
        result = self.run_cli(
            "definitely-not-a-command"
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=result.stderr,
        )

        self.assertIn(
            "Unknown command",
            result.stdout,
        )

    def test_skill_without_args(self):
        result = self.run_cli(
            "skill"
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=result.stderr,
        )

    def test_skill_add_missing_args_does_not_crash(self):
        result = self.run_cli(
            "skill",
            "add",
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=result.stderr,
        )

        self.assertIn(
            "Usage:",
            result.stdout,
        )

    def test_forget_missing_id_does_not_crash(self):
        result = self.run_cli(
            "forget"
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=result.stderr,
        )

        self.assertIn(
            "memory ID",
            result.stdout,
        )

    def test_forget_invalid_id_does_not_crash(self):
        result = self.run_cli(
            "forget",
            "abc"
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=result.stderr,
        )

        self.assertIn(
            "Invalid memory ID",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
