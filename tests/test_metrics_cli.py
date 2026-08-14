from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class MetricsCLITests(unittest.TestCase):

    def run_command(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "richmack-metrics"),
                *args,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )

    def test_summary_runs(self):
        result = self.run_command("summary")

        self.assertEqual(
            result.returncode,
            0,
            msg=result.stderr,
        )

        self.assertIn(
            "RichmackOS Engineering Metrics",
            result.stdout,
        )

        self.assertIn(
            "RICHMACK WEISSMAN",
            result.stdout,
        )

    def test_hotspots_runs(self):
        result = self.run_command("hotspots")

        self.assertEqual(
            result.returncode,
            0,
            msg=result.stderr,
        )

        self.assertIn(
            "RichmackOS Complexity Hotspots",
            result.stdout,
        )

        self.assertIn(
            "FUNCTION",
            result.stdout,
        )

    def test_json_is_valid(self):
        result = self.run_command("--json")

        self.assertEqual(
            result.returncode,
            0,
            msg=result.stderr,
        )

        payload = json.loads(result.stdout)

        self.assertIn(
            "source",
            payload,
        )

        self.assertIn(
            "tests",
            payload,
        )

        self.assertIn(
            "complexity",
            payload,
        )

        self.assertIn(
            "scores",
            payload,
        )

        self.assertIn(
            "weissman",
            payload["scores"],
        )

    def test_invalid_hours_fail(self):
        result = self.run_command(
            "--hours",
            "0",
        )

        self.assertNotEqual(
            result.returncode,
            0,
        )


if __name__ == "__main__":
    unittest.main()
