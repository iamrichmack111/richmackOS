from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class YouTubeChatRoutingTests(unittest.TestCase):

    def test_youtube_cmd_routes_to_v2(self):
        text = (
            ROOT
            / "youtube_cmd"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "youtube_chat_v2.py",
            text,
        )

    def test_legacy_chat_module_removed(self):
        self.assertFalse(
            (
                ROOT
                / "youtube_chat.py"
            ).exists()
        )

    def test_v2_module_exists(self):
        self.assertTrue(
            (
                ROOT
                / "youtube_chat_v2.py"
            ).exists()
        )

    def test_v2_contains_chat_entrypoint(self):
        text = (
            ROOT
            / "youtube_chat_v2.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "def chat(",
            text,
        )

        self.assertIn(
            'if __name__ == "__main__":',
            text,
        )


if __name__ == "__main__":
    unittest.main()
