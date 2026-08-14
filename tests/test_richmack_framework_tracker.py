from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from richmack_framework.database import (
    add_session,
    add_topic,
    get_topic,
    initialize,
    list_topics,
    topic_sessions,
)

from richmack_framework.tracker import (
    topic_summary,
)


class FrameworkTrackerTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()

        self.db = (
            Path(self.temp.name)
            / "framework.db"
        )

        initialize(
            self.db
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_add_topic(self):
        add_topic(
            "Hebrew",
            "Language study",
            self.db,
        )

        topic = get_topic(
            "Hebrew",
            self.db,
        )

        self.assertEqual(
            topic["name"],
            "Hebrew",
        )

    def test_duplicate_topic_rejected(self):
        add_topic(
            "Hebrew",
            db_path=self.db,
        )

        with self.assertRaises(
            ValueError
        ):
            add_topic(
                "hebrew",
                db_path=self.db,
            )

    def test_list_topics(self):
        add_topic(
            "Hebrew",
            db_path=self.db,
        )

        add_topic(
            "Python",
            db_path=self.db,
        )

        rows = list_topics(
            self.db
        )

        self.assertEqual(
            len(rows),
            2,
        )

    def test_add_session(self):
        add_topic(
            "Hebrew",
            db_path=self.db,
        )

        add_session(
            "Hebrew",
            raw_reps=10,
            stable_reps=7,
            learning_units=2,
            refresh_units=1,
            connections=3,
            db_path=self.db,
        )

        rows = topic_sessions(
            "Hebrew",
            self.db,
        )

        self.assertEqual(
            len(rows),
            1,
        )

        self.assertEqual(
            rows[0]["stable_reps"],
            7,
        )

    def test_unknown_topic_rejected(self):
        with self.assertRaises(
            ValueError
        ):
            add_session(
                "Unknown",
                db_path=self.db,
            )

    def test_stable_reps_cannot_exceed_raw(self):
        add_topic(
            "Hebrew",
            db_path=self.db,
        )

        with self.assertRaises(
            ValueError
        ):
            add_session(
                "Hebrew",
                raw_reps=5,
                stable_reps=6,
                db_path=self.db,
            )

    def test_topic_summary(self):
        add_topic(
            "Hebrew",
            db_path=self.db,
        )

        add_session(
            "Hebrew",
            raw_reps=10,
            stable_reps=7,
            learning_units=2,
            refresh_units=1,
            connections=3,
            capability=0.5,
            db_path=self.db,
        )

        add_session(
            "Hebrew",
            raw_reps=10,
            stable_reps=8,
            learning_units=1,
            refresh_units=1 / 3,
            connections=2,
            capability=0.7,
            db_path=self.db,
        )

        result = topic_summary(
            "Hebrew",
            self.db,
        )

        self.assertEqual(
            result["sessions"],
            2,
        )

        self.assertEqual(
            result["raw_reps"],
            20,
        )

        self.assertEqual(
            result["stable_reps"],
            15,
        )

        self.assertAlmostEqual(
            result["retention"],
            0.75,
        )

        self.assertAlmostEqual(
            result["latest_capability"],
            0.7,
        )


if __name__ == "__main__":
    unittest.main()
