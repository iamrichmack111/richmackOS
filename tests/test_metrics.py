import tempfile
import unittest
from pathlib import Path

from richmack_metrics.complexity import analyze_python
from richmack_metrics.scoring import (
    calculate_scores,
    clamp,
    complexity_score,
    debt_score,
    testing_score,
    throughput_score,
)


class MetricsTests(unittest.TestCase):

    def test_clamp_low(self):
        self.assertEqual(
            clamp(-10),
            0,
        )

    def test_clamp_middle(self):
        self.assertEqual(
            clamp(5),
            5,
        )

    def test_clamp_high(self):
        self.assertEqual(
            clamp(20),
            10,
        )

    def test_complexity_analysis(self):

        with tempfile.TemporaryDirectory() as directory:

            path = (
                Path(directory)
                / "example.py"
            )

            path.write_text(
                """
def example(value):
    if value:
        for item in range(3):
            if item:
                print(item)
    return value
""",
                encoding="utf-8",
            )

            result = analyze_python(
                [path]
            )

            self.assertEqual(
                result.syntax_errors,
                0,
            )

            self.assertEqual(
                result.functions,
                1,
            )

            self.assertGreaterEqual(
                result.maximum_complexity,
                4,
            )

            self.assertEqual(
                len(result.hotspots),
                1,
            )

            self.assertEqual(
                result.hotspots[0].name,
                "example",
            )

    def test_syntax_error_detection(self):

        with tempfile.TemporaryDirectory() as directory:

            path = (
                Path(directory)
                / "broken.py"
            )

            path.write_text(
                "def broken(:\n    pass\n",
                encoding="utf-8",
            )

            result = analyze_python(
                [path]
            )

            self.assertEqual(
                result.syntax_errors,
                1,
            )

    def test_debt_perfect(self):
        self.assertEqual(
            debt_score(
                1000,
                0,
                0,
            ),
            10,
        )

    def test_debt_penalty(self):
        self.assertLess(
            debt_score(
                1000,
                10,
                10,
            ),
            10,
        )

    def test_testing_zero(self):
        self.assertEqual(
            testing_score(
                10000,
                0,
                0,
            ),
            0,
        )

    def test_testing_improves(self):
        low = testing_score(
            10000,
            100,
            1,
        )

        high = testing_score(
            10000,
            3000,
            10,
        )

        self.assertGreater(
            high,
            low,
        )

    def test_throughput_zero_hours(self):
        self.assertEqual(
            throughput_score(
                10000,
                10,
                20,
                0,
            ),
            0,
        )

    def test_throughput_bounds(self):
        value = throughput_score(
            15000,
            20,
            50,
            13,
        )

        self.assertGreaterEqual(
            value,
            0,
        )

        self.assertLessEqual(
            value,
            10,
        )

    def test_complexity_score_bounds(self):
        value = complexity_score(
            5,
            30,
            0,
            2,
        )

        self.assertGreaterEqual(
            value,
            0,
        )

        self.assertLessEqual(
            value,
            10,
        )

    def test_perfect_composite_scores(self):
        result = calculate_scores(
            complexity=10,
            testing=10,
            debt=10,
            automation=10,
            throughput=10,
        )

        self.assertEqual(
            result[
                "engineering_index"
            ],
            10,
        )

        self.assertEqual(
            result["weissman"],
            10,
        )


if __name__ == "__main__":
    unittest.main()
