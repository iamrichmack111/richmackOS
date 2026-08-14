from __future__ import annotations

import unittest
from collections import Counter

import youtube_knowledge as yk


def _legacy_extract_keywords(
    title,
    transcript,
    limit=40,
):
    scores = Counter()

    title_words = [
        word
        for word in yk.topic_tokens(title)
        if len(
            word.replace("'", "")
        ) >= 3
    ]

    for size in (4, 3, 2):
        for i in range(
            len(title_words) - size + 1
        ):
            phrase = yk.clean_topic(
                " ".join(
                    title_words[
                        i:i + size
                    ]
                )
            )

            low_words = [
                word.lower().replace("'", "")
                for word in phrase.split()
            ]

            useful = [
                word
                for word in low_words
                if word not in yk.STOPWORDS
            ]

            if len(useful) >= 1:
                scores[phrase] += 8

    for word in title_words:
        low = (
            word.lower()
            .replace("'", "")
        )

        if (
            low not in yk.STOPWORDS
            and len(low) >= 4
        ):
            scores[word] += 6

    for phrase in yk.extract_named_phrases(
        title + "\n" + transcript
    ):
        low = phrase.lower()

        if low in {
            "the",
            "this",
            "that",
            "and",
        }:
            continue

        scores[phrase] += 5

    phrase_counts = Counter(
        yk.extract_ngram_phrases(
            transcript
        )
    )

    for phrase, count in phrase_counts.items():
        score = min(
            10,
            2 + count
        )

        scores[phrase] += score

    important_single = Counter()

    for word in yk.topic_tokens(
        transcript
    ):
        low = (
            word.lower()
            .replace("'", "")
        )

        if (
            len(low) < 5
            or low in yk.STOPWORDS
        ):
            continue

        important_single[word] += 1

    for word, count in important_single.items():
        if count >= 2:
            scores[word] += min(
                5,
                count
            )

    ranked = sorted(
        scores.items(),
        key=lambda item: (
            item[1],
            len(item[0].split()),
            len(item[0]),
        ),
        reverse=True,
    )

    output = []
    seen = set()

    for phrase, score in ranked:
        phrase = yk.clean_topic(
            phrase
        )

        key = phrase.lower()

        if not phrase:
            continue

        if not yk.is_good_topic(
            phrase
        ):
            continue

        if key in seen:
            continue

        words = [
            word.lower().replace("'", "")
            for word in phrase.split()
        ]

        if (
            words
            and all(
                word in yk.STOPWORDS
                for word in words
            )
        ):
            continue

        seen.add(key)
        output.append(phrase)

        if len(output) >= limit:
            break

    return output


CASES = [
    (
        "Artificial Intelligence Predictions and Machine Learning",
        """
        Artificial intelligence is changing software development.
        Machine learning systems use neural networks.
        Artificial intelligence models continue improving.
        Machine learning performance continues increasing.
        Neural networks are important for modern AI research.
        """,
    ),
    (
        "Growth Hormone, Sleep and Human Performance",
        """
        Growth hormone secretion increases during deep sleep.
        Sleep quality affects growth hormone production.
        Human performance depends on recovery and sleep.
        Growth hormone is discussed repeatedly in this episode.
        """,
    ),
    (
        "Linux Servers, Docker and Kubernetes",
        """
        Linux servers can run Docker containers.
        Kubernetes manages Docker workloads across servers.
        Linux administrators use containers for deployment.
        Kubernetes orchestration helps distributed applications.
        """,
    ),
    (
        "The Future of Robotics",
        """
        Robotics research is accelerating.
        Robots are becoming more capable.
        Robotics systems increasingly use artificial intelligence.
        Robotics research affects manufacturing and automation.
        """,
    ),
    (
        "",
        "",
    ),
]


class KeywordCharacterizationTests(unittest.TestCase):

    def test_current_algorithm_matches_legacy_reference(self):
        for title, transcript in CASES:
            with self.subTest(title=title):
                expected = _legacy_extract_keywords(
                    title,
                    transcript,
                )

                actual = yk.extract_keywords(
                    title,
                    transcript,
                )

                self.assertEqual(
                    actual,
                    expected,
                )

    def test_limit_matches_legacy_reference(self):
        title, transcript = CASES[0]

        for limit in (
            1,
            3,
            5,
            10,
            40,
        ):
            with self.subTest(limit=limit):
                self.assertEqual(
                    yk.extract_keywords(
                        title,
                        transcript,
                        limit=limit,
                    ),
                    _legacy_extract_keywords(
                        title,
                        transcript,
                        limit=limit,
                    ),
                )

    def test_empty_input(self):
        self.assertEqual(
            yk.extract_keywords(
                "",
                "",
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
