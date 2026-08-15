from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from richmack_framework.database import add_topic
from richmack_framework.knowledge import (
    add_concept,
    add_mistake,
    add_note,
    add_question,
    add_relation,
    initialize_knowledge,
    knowledge_summary,
    list_concepts,
    set_confidence,
)


class FrameworkKnowledgeTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()

        self.db = (
            Path(self.temp.name)
            / "framework.db"
        )

        initialize_knowledge(
            self.db
        )

        add_topic(
            "Hebrew",
            db_path=self.db,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_concept(self):
        add_concept(
            "Hebrew",
            "Triliteral roots",
            db_path=self.db,
        )

        rows = list_concepts(
            "Hebrew",
            self.db,
        )

        self.assertEqual(
            rows[0]["name"],
            "Triliteral roots",
        )

    def test_duplicate_concept(self):
        add_concept(
            "Hebrew",
            "Qal",
            db_path=self.db,
        )

        with self.assertRaises(
            ValueError
        ):
            add_concept(
                "Hebrew",
                "qal",
                db_path=self.db,
            )

    def test_note_mistake_question(self):
        add_concept(
            "Hebrew",
            "Qal",
            db_path=self.db,
        )

        add_note(
            "Hebrew",
            "Basic verbal stem.",
            concept_name="Qal",
            db_path=self.db,
        )

        add_mistake(
            "Hebrew",
            "Confused Qal with Piel.",
            concept_name="Qal",
            db_path=self.db,
        )

        add_question(
            "Hebrew",
            "How does Qal differ from Niphal?",
            concept_name="Qal",
            db_path=self.db,
        )

        result = knowledge_summary(
            "Hebrew",
            self.db,
        )

        self.assertEqual(
            len(result["notes"]),
            1,
        )

        self.assertEqual(
            len(result["mistakes"]),
            1,
        )

        self.assertEqual(
            len(result["questions"]),
            1,
        )

    def test_confidence(self):
        add_concept(
            "Hebrew",
            "Roots",
            db_path=self.db,
        )

        set_confidence(
            "Hebrew",
            "Roots",
            0.75,
            db_path=self.db,
        )

        rows = list_concepts(
            "Hebrew",
            self.db,
        )

        self.assertAlmostEqual(
            rows[0]["confidence"],
            0.75,
        )

    def test_relation(self):
        add_concept(
            "Hebrew",
            "Roots",
            db_path=self.db,
        )

        add_concept(
            "Hebrew",
            "Vocabulary",
            db_path=self.db,
        )

        add_relation(
            "Hebrew",
            "Roots",
            "Vocabulary",
            relation="supports",
            strength=0.9,
            db_path=self.db,
        )

        result = knowledge_summary(
            "Hebrew",
            self.db,
        )

        self.assertEqual(
            result["relations"][0]["relation"],
            "supports",
        )


    def test_summary_contains_all_knowledge_types(self):
        add_concept(
            "Hebrew",
            "Roots",
            db_path=self.db,
        )

        add_concept(
            "Hebrew",
            "Vocabulary",
            db_path=self.db,
        )

        set_confidence(
            "Hebrew",
            "Roots",
            0.8,
            db_path=self.db,
        )

        add_note(
            "Hebrew",
            "Root note",
            concept_name="Roots",
            db_path=self.db,
        )

        add_mistake(
            "Hebrew",
            "Root mistake",
            concept_name="Roots",
            db_path=self.db,
        )

        add_question(
            "Hebrew",
            "Root question",
            concept_name="Roots",
            db_path=self.db,
        )

        add_relation(
            "Hebrew",
            "Roots",
            "Vocabulary",
            relation="supports",
            strength=0.9,
            db_path=self.db,
        )

        result = knowledge_summary(
            "Hebrew",
            self.db,
        )

        self.assertEqual(
            len(result["concepts"]),
            2,
        )

        self.assertEqual(
            len(result["notes"]),
            1,
        )

        self.assertEqual(
            len(result["mistakes"]),
            1,
        )

        self.assertEqual(
            len(result["questions"]),
            1,
        )

        self.assertEqual(
            len(result["relations"]),
            1,
        )


if __name__ == "__main__":
    unittest.main()
