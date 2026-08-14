from __future__ import annotations

import unittest
from unittest.mock import patch

from richmack_ui.terminal import (
    color,
    metric_bar,
    panel,
)


class RichmackUITests(unittest.TestCase):

    def test_metric_bar_empty(self):
        self.assertEqual(
            metric_bar(
                0,
                maximum=1,
                width=10,
            ),
            "░" * 10,
        )

    def test_metric_bar_full(self):
        self.assertEqual(
            metric_bar(
                1,
                maximum=1,
                width=10,
            ),
            "█" * 10,
        )

    def test_metric_bar_half(self):
        self.assertEqual(
            metric_bar(
                0.5,
                maximum=1,
                width=10,
            ),
            "█████░░░░░",
        )

    def test_metric_bar_clamps_high(self):
        self.assertEqual(
            metric_bar(
                2,
                maximum=1,
                width=10,
            ),
            "█" * 10,
        )

    def test_metric_bar_clamps_low(self):
        self.assertEqual(
            metric_bar(
                -1,
                maximum=1,
                width=10,
            ),
            "░" * 10,
        )

    def test_panel_contains_title(self):
        output = panel(
            "Richmack Framework",
            width=40,
        )

        self.assertIn(
            "Richmack Framework",
            output,
        )

    @patch(
        "richmack_ui.terminal.supports_color",
        return_value=False,
    )
    def test_color_disabled(
        self,
        _mock,
    ):
        self.assertEqual(
            color(
                "hello",
                "\033[31m",
            ),
            "hello",
        )


if __name__ == "__main__":
    unittest.main()
