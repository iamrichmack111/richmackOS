from __future__ import annotations

import unittest

import youtube_knowledge as yk


def legacy_is_good_topic(value):
    value = yk.clean_topic(value)

    if not value:
        return False

    words = yk.normalized_topic_words(
        value
    )

    if not words:
        return False

    if all(
        (
            word.replace("'", "")
            in yk.TOPIC_FILLER
            or word.replace("'", "")
            in yk.STOPWORDS
        )
        for word in words
    ):
        return False

    first = words[0].replace(
        "'",
        ""
    )

    if (
        first in yk.TOPIC_FILLER
        and len(words) <= 3
    ):
        return False

    meaningful = [
        word
        for word in words
        if (
            word.replace("'", "")
            not in yk.TOPIC_FILLER
            and word.replace("'", "")
            not in yk.STOPWORDS
            and len(
                word.replace("'", "")
            ) >= 3
        )
    ]

    if not meaningful:
        return False

    low = value.lower()

    artifacts = (
        "mhm.",
        "yeah.",
        "uh.",
        "um.",
        "[laughter]",
        "[music]",
        "[applause]",
    )

    if any(
        low.startswith(item)
        for item in artifacts
    ):
        return False

    return True


CASES = [
    "",
    " ",
    "the and this",
    "yeah",
    "Yeah. And",
    "mhm.",
    "uh.",
    "um.",
    "[laughter]",
    "[music]",
    "[applause]",
    "Artificial Intelligence",
    "machine learning",
    "growth hormone",
    "Linux servers",
    "Docker",
    "the Linux kernel",
    "AI research",
    "psychology and cognition",
    "Yeah artificial intelligence",
    "Well machine learning systems",
    "and the",
    "this is",
    "quantum computing",
    "neural networks",
]


class GoodTopicCharacterizationTests(unittest.TestCase):

    def test_matches_legacy_reference(self):
        for value in CASES:
            with self.subTest(value=value):
                self.assertEqual(
                    yk.is_good_topic(value),
                    legacy_is_good_topic(value),
                )

    def test_known_good_topics(self):
        good = (
            "Artificial Intelligence",
            "machine learning",
            "growth hormone",
            "Linux servers",
            "quantum computing",
            "neural networks",
        )

        for value in good:
            with self.subTest(value=value):
                self.assertTrue(
                    yk.is_good_topic(value)
                )

    def test_known_bad_topics(self):
        bad = (
            "",
            "the and this",
            "yeah",
            "Yeah. And",
            "mhm.",
            "uh.",
            "[music]",
            "[applause]",
        )

        for value in bad:
            with self.subTest(value=value):
                self.assertFalse(
                    yk.is_good_topic(value)
                )


if __name__ == "__main__":
    unittest.main()
