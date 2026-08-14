from __future__ import annotations

import unittest
from pathlib import Path

from richmack_metrics.collector import collect_metrics


ROOT = Path(__file__).resolve().parent.parent


class CollectorTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.result = collect_metrics(
            ROOT,
            active_hours=13.0,
        )

    def test_source_data_exists(self):
        self.assertGreater(
            self.result["source"]["files"],
            0,
        )

        self.assertGreater(
            self.result["source"]["lines"],
            0,
        )

    def test_complexity_data_exists(self):
        complexity = self.result["complexity"]

        self.assertGreater(
            complexity["functions"],
            0,
        )

        self.assertGreaterEqual(
            complexity["average_complexity"],
            0,
        )

    def test_score_range(self):
        for name, value in self.result["scores"].items():
            self.assertGreaterEqual(
                value,
                0,
                msg=name,
            )

            self.assertLessEqual(
                value,
                10,
                msg=name,
            )

    def test_no_python_syntax_errors(self):
        self.assertEqual(
            self.result["complexity"]["syntax_errors"],
            0,
        )

    def test_hotspots_are_sorted(self):
        hotspots = self.result["complexity"]["hotspots"]

        complexities = [
            item["complexity"]
            for item in hotspots
        ]

        self.assertEqual(
            complexities,
            sorted(
                complexities,
                reverse=True,
            ),
        )


if __name__ == "__main__":
    unittest.main()
