from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from richmack_framework.ai import (
    DEFAULT_MODEL,
    ask_framework,
    build_framework_context_text,
    build_system_prompt,
    build_user_prompt,
    load_framework_context,
    ollama_chat,
)
from richmack_framework.database import (
    add_session,
    add_topic,
    initialize,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        return False

    def read(self):
        return json.dumps(
            self.payload
        ).encode("utf-8")


class FrameworkAIContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "framework.db"

        initialize(self.db)

        add_topic(
            "Hebrew",
            description="Hebrew language study",
            db_path=self.db,
        )

        add_session(
            "Hebrew",
            raw_reps=10,
            stable_reps=7,
            learning_units=2,
            refresh_units=2 / 3,
            connections=3,
            capability=0.4,
            notes="Vocabulary and root review",
            db_path=self.db,
        )

        add_session(
            "Hebrew",
            raw_reps=10,
            stable_reps=8,
            learning_units=1,
            refresh_units=1 / 3,
            connections=2,
            capability=0.55,
            notes="Reading and recall practice",
            db_path=self.db,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_load_context(self):
        context = load_framework_context(
            "Hebrew",
            self.db,
        )

        self.assertEqual(context.topic, "Hebrew")
        self.assertEqual(len(context.sessions), 2)
        self.assertAlmostEqual(
            context.summary["retention"],
            0.75,
        )

    def test_unknown_topic_fails(self):
        with self.assertRaises(ValueError):
            load_framework_context(
                "Unknown",
                self.db,
            )

    def test_history_limit(self):
        context = load_framework_context(
            "Hebrew",
            self.db,
            history_limit=1,
        )

        self.assertEqual(len(context.sessions), 1)
        self.assertIn(
            "Reading and recall",
            context.sessions[0]["notes"],
        )

    def test_context_text_contains_metrics(self):
        context = load_framework_context(
            "Hebrew",
            self.db,
        )

        text = build_framework_context_text(
            context
        )

        self.assertIn("Retention: 75.00%", text)
        self.assertIn(
            "Stable repetitions: 15.00",
            text,
        )
        self.assertIn(
            "Vocabulary and root review",
            text,
        )

    def test_user_prompt_contains_question(self):
        context = load_framework_context(
            "Hebrew",
            self.db,
        )

        prompt = build_user_prompt(
            context,
            "What should I study next?",
        )

        self.assertIn(
            "What should I study next?",
            prompt,
        )

    def test_empty_question_fails(self):
        context = load_framework_context(
            "Hebrew",
            self.db,
        )

        with self.assertRaises(ValueError):
            build_user_prompt(
                context,
                "   ",
            )

    def test_system_prompt_marks_model_as_planning(self):
        text = build_system_prompt()
        self.assertIn("planning models", text)
        self.assertIn("Do not invent", text)

    def test_system_prompt_forbids_invented_future_dates(self):
        text = build_system_prompt()

        self.assertIn(
            "Never invent future dates",
            text,
        )

        self.assertIn(
            'your next session',
            text,
        )

    def test_system_prompt_limits_invented_numeric_targets(self):
        text = build_system_prompt()

        self.assertIn(
            "Do not invent numeric targets",
            text,
        )


class FrameworkOllamaTests(unittest.TestCase):
    @patch(
        "richmack_framework.ai."
        "urllib.request.urlopen"
    )
    def test_ollama_chat(
        self,
        mock_urlopen,
    ):
        mock_urlopen.return_value = FakeResponse({
            "message": {
                "role": "assistant",
                "content": "Review Hebrew roots.",
            }
        })

        answer = ollama_chat(
            model=DEFAULT_MODEL,
            system_prompt="system",
            user_prompt="question",
        )

        self.assertEqual(
            answer,
            "Review Hebrew roots.",
        )

        request = (
            mock_urlopen
            .call_args
            .args[0]
        )

        payload = json.loads(
            request.data.decode("utf-8")
        )

        self.assertEqual(
            payload["model"],
            DEFAULT_MODEL,
        )

        self.assertFalse(payload["stream"])


class FrameworkAskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "framework.db"

        initialize(self.db)

        add_topic(
            "Linux",
            db_path=self.db,
        )

        add_session(
            "Linux",
            raw_reps=7,
            stable_reps=7,
            learning_units=1,
            refresh_units=1 / 3,
            connections=2,
            notes="SSH practice",
            db_path=self.db,
        )

    def tearDown(self):
        self.temp.cleanup()

    @patch(
        "richmack_framework.ai."
        "ollama_chat"
    )
    def test_ask_framework(
        self,
        mock_chat,
    ):
        mock_chat.return_value = "Practice SSH again."

        answer, context = ask_framework(
            "Linux",
            "What next?",
            db_path=self.db,
        )

        self.assertEqual(
            answer,
            "Practice SSH again.",
        )

        self.assertEqual(
            context.topic,
            "Linux",
        )

        user_prompt = (
            mock_chat
            .call_args
            .kwargs["user_prompt"]
        )

        self.assertIn("SSH practice", user_prompt)
        self.assertIn("What next?", user_prompt)


class FrameworkKnowledgeGroundingTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()

        self.db = (
            Path(self.temp.name)
            / "framework.db"
        )

        from richmack_framework.database import (
            add_topic,
            initialize,
        )

        from richmack_framework.knowledge import (
            add_concept,
            add_mistake,
            add_note,
            add_question,
            add_relation,
            set_confidence,
        )

        initialize(
            self.db
        )

        add_topic(
            "Hebrew",
            db_path=self.db,
        )

        add_concept(
            "Hebrew",
            "Triliteral roots",
            db_path=self.db,
        )

        add_concept(
            "Hebrew",
            "Vocabulary",
            db_path=self.db,
        )

        set_confidence(
            "Hebrew",
            "Triliteral roots",
            0.60,
            db_path=self.db,
        )

        add_note(
            "Hebrew",
            "Reviewed root patterns.",
            concept_name="Triliteral roots",
            db_path=self.db,
        )

        add_mistake(
            "Hebrew",
            "Confused two verb patterns.",
            concept_name="Triliteral roots",
            db_path=self.db,
        )

        add_question(
            "Hebrew",
            "How does the root change across stems?",
            concept_name="Triliteral roots",
            db_path=self.db,
        )

        add_relation(
            "Hebrew",
            "Triliteral roots",
            "Vocabulary",
            relation="supports",
            strength=0.9,
            db_path=self.db,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_context_includes_knowledge_graph(self):
        context = load_framework_context(
            "Hebrew",
            self.db,
        )

        output = build_framework_context_text(
            context
        )

        self.assertIn(
            "KNOWLEDGE GRAPH",
            output,
        )

        self.assertIn(
            "Triliteral roots",
            output,
        )

        self.assertIn(
            "confidence 60.0%",
            output,
        )

        self.assertIn(
            "Confused two verb patterns.",
            output,
        )

        self.assertIn(
            "How does the root change across stems?",
            output,
        )

        self.assertIn(
            "--supports-->",
            output,
        )


if __name__ == "__main__":
    unittest.main()
