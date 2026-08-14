from __future__ import annotations

import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import youtube_chat_v2 as yc


def make_video(
    video_id="video-1",
    title="Test Video",
    chunks=None,
):
    return {
        "metadata": {
            "video_id": video_id,
            "title": title,
        },
        "description": "",
        "summary": "",
        "keywords": [],
        "chunks": chunks or [
            {
                "chunk_no": 1,
                "text": "Artificial intelligence discussion.",
            }
        ],
    }


class FollowupClassificationTests(unittest.TestCase):

    def test_generic_overview(self):
        self.assertTrue(
            yc.is_overview_followup(
                "what else?"
            )
        )

    def test_explicit_context_followup(self):
        self.assertTrue(
            yc.is_context_followup(
                "tell me more"
            )
        )

    def test_pronoun_followup(self):
        self.assertTrue(
            yc.is_context_followup(
                "why did they say that?"
            )
        )

    def test_explicit_new_subject_is_not_context_followup(self):
        self.assertFalse(
            yc.is_context_followup(
                "tell me more about growth hormone"
            )
        )

    def test_channel_wide_question(self):
        self.assertTrue(
            yc.is_channel_wide_question(
                "what are the main topics across the latest videos?"
            )
        )

    def test_specific_question_not_channel_wide(self):
        self.assertFalse(
            yc.is_channel_wide_question(
                "what did Madonna say about AI?"
            )
        )


class ChatRoutingTests(unittest.TestCase):

    def test_no_current_video_routes_channel_wide(self):
        route = yc.classify_chat_route(
            "main topics across the latest videos",
            None,
        )

        self.assertEqual(
            route,
            "channel",
        )

    def test_current_video_context_followup_wins_over_channel_pattern(self):
        video = make_video()

        route = yc.classify_chat_route(
            "what else did they say about all videos?",
            video,
        )

        self.assertEqual(
            route,
            "context",
        )

    def test_current_video_overview(self):
        video = make_video()

        route = yc.classify_chat_route(
            "what else is mentioned?",
            video,
        )

        # Existing chat() checks context follow-up before overview.
        self.assertEqual(
            route,
            "context",
        )

    def test_new_specific_question_routes_video(self):
        video = make_video()

        route = yc.classify_chat_route(
            "tell me more about growth hormone",
            video,
        )

        self.assertEqual(
            route,
            "video",
        )


class RetrievalQuestionTests(unittest.TestCase):

    def test_context_retrieval_uses_previous_question(self):
        self.assertEqual(
            yc.build_context_retrieval_question(
                "what else?",
                "what did they say about AI?",
            ),
            "what did they say about AI? what else?",
        )

    def test_context_retrieval_without_previous_question(self):
        self.assertEqual(
            yc.build_context_retrieval_question(
                "what else?",
                None,
            ),
            "what else?",
        )


class EvidenceSelectionTests(unittest.TestCase):

    def test_context_followup_uses_current_video(self):
        current = make_video(
            video_id="current"
        )

        with patch.object(
            yc,
            "retrieve_transcript",
            return_value=[("score", "chunk")],
        ) as retrieve:
            video, evidence = yc.select_chat_evidence(
                route="context",
                question="what else?",
                last_question="what did they say about AI?",
                current_video=current,
                videos=[current],
                top_k=6,
            )

        self.assertIs(
            video,
            current,
        )

        self.assertEqual(
            evidence,
            [("score", "chunk")],
        )

        retrieve.assert_called_once_with(
            "what did they say about AI? what else?",
            current,
            top_k=6,
        )

    def test_context_followup_falls_back_to_whole_video(self):
        current = make_video()

        with (
            patch.object(
                yc,
                "retrieve_transcript",
                return_value=[],
            ),
            patch.object(
                yc,
                "whole_video_sample",
                return_value=[("fallback", "chunk")],
            ) as whole,
        ):
            video, evidence = yc.select_chat_evidence(
                route="context",
                question="go deeper",
                last_question="AI claims",
                current_video=current,
                videos=[current],
                top_k=5,
            )

        self.assertIs(
            video,
            current,
        )

        self.assertEqual(
            evidence,
            [("fallback", "chunk")],
        )

        whole.assert_called_once_with(
            current,
            top_k=5,
        )

    def test_overview_uses_whole_video_sample(self):
        current = make_video()

        with patch.object(
            yc,
            "whole_video_sample",
            return_value=[("overview", "chunk")],
        ) as whole:
            video, evidence = yc.select_chat_evidence(
                route="overview",
                question="overview",
                last_question=None,
                current_video=current,
                videos=[current],
                top_k=7,
            )

        self.assertIs(
            video,
            current,
        )

        self.assertEqual(
            evidence,
            [("overview", "chunk")],
        )

        whole.assert_called_once_with(
            current,
            top_k=7,
        )

    def test_new_video_question_selects_video(self):
        chosen = make_video(
            video_id="selected"
        )

        with (
            patch.object(
                yc,
                "select_video",
                return_value=chosen,
            ) as select,
            patch.object(
                yc,
                "retrieve_transcript",
                return_value=[("selected", "chunk")],
            ) as retrieve,
        ):
            video, evidence = yc.select_chat_evidence(
                route="video",
                question="growth hormone",
                last_question=None,
                current_video=None,
                videos=[chosen],
                top_k=4,
            )

        self.assertIs(
            video,
            chosen,
        )

        self.assertEqual(
            evidence,
            [("selected", "chunk")],
        )

        select.assert_called_once_with(
            "growth hormone",
            [chosen],
        )

        retrieve.assert_called_once_with(
            "growth hormone",
            chosen,
            top_k=4,
        )


if __name__ == "__main__":
    unittest.main()


class ChatCommandTests(unittest.TestCase):

    def test_quit_command(self):
        self.assertEqual(
            yc.chat_command_type("/quit"),
            "quit",
        )

    def test_exit_command(self):
        self.assertEqual(
            yc.chat_command_type("exit"),
            "quit",
        )

    def test_help_command(self):
        self.assertEqual(
            yc.chat_command_type("/help"),
            "help",
        )

    def test_clear_command(self):
        self.assertEqual(
            yc.chat_command_type("/clear"),
            "clear",
        )

    def test_video_command(self):
        self.assertEqual(
            yc.chat_command_type("/video"),
            "video",
        )

    def test_sources_command(self):
        self.assertEqual(
            yc.chat_command_type("/sources"),
            "sources",
        )

    def test_regular_question(self):
        self.assertIsNone(
            yc.chat_command_type(
                "what did they say about AI?"
            )
        )


class ChatRenderingTests(unittest.TestCase):

    def test_video_title(self):
        video = make_video(
            title="Example Title"
        )

        self.assertEqual(
            yc.current_video_title(video),
            "Example Title",
        )

    def test_no_current_video_title(self):
        self.assertEqual(
            yc.current_video_title(None),
            "",
        )

    def test_transcript_source_line(self):
        item = {
            "number": 1,
            "type": "TRANSCRIPT",
            "chunk": 4,
        }

        self.assertEqual(
            yc.format_source_line(
                item,
                title="Example",
            ),
            "  [1] Example — TRANSCRIPT chunk 4",
        )

    def test_description_source_line(self):
        item = {
            "number": 2,
            "type": "DESCRIPTION",
        }

        self.assertEqual(
            yc.format_source_line(
                item,
                title="Example",
            ),
            "  [2] Example — DESCRIPTION",
        )


class ChannelQuestionExecutionTests(unittest.TestCase):

    def test_channel_question_returns_lock_and_evidence(self):
        videos = [
            make_video(
                video_id="winner",
                title="Winner Video",
            )
        ]

        evidence = [
            {
                "number": 1,
                "title": "Winner Video",
                "video_id": "winner",
            }
        ]

        with (
            patch.object(
                yc,
                "generate_channel_answer",
                return_value=(
                    "answer",
                    evidence,
                    "winner",
                ),
            ),
            patch.object(
                yc,
                "find_video_by_id",
                return_value=videos[0],
            ),
            patch.object(
                yc,
                "print_answer_panel",
            ),
            patch.object(
                yc,
                "print_channel_evidence",
            ),
            patch.object(
                yc,
                "progress",
            ),
        ):
            with redirect_stdout(StringIO()):
                result = yc.run_channel_question(
                    model="model",
                    question="most unusual claim",
                    videos=videos,
                )

        self.assertEqual(
            result["answer"],
            "answer",
        )

        self.assertEqual(
            result["evidence"],
            evidence,
        )

        self.assertIs(
            result["current_video"],
            videos[0],
        )

    def test_channel_question_without_selected_video_clears_lock(self):
        with (
            patch.object(
                yc,
                "generate_channel_answer",
                return_value=(
                    "answer",
                    [],
                    None,
                ),
            ),
            patch.object(
                yc,
                "print_answer_panel",
            ),
            patch.object(
                yc,
                "print_channel_evidence",
            ),
            patch.object(
                yc,
                "progress",
            ),
        ):
            with redirect_stdout(StringIO()):
                result = yc.run_channel_question(
                    model="model",
                    question="main topics",
                    videos=[],
                )

        self.assertIsNone(
            result["current_video"]
        )

        self.assertEqual(
            result["evidence"],
            [],
        )


class VideoQuestionExecutionTests(unittest.TestCase):

    def test_video_question_uses_transcript_evidence(self):
        video = make_video(
            title="Test Video"
        )

        raw_evidence = [
            (
                1.0,
                {
                    "chunk_no": 1,
                    "text": "AI evidence",
                },
            )
        ]

        display = [
            {
                "number": 1,
                "type": "TRANSCRIPT",
                "chunk": 1,
            }
        ]

        with (
            patch.object(
                yc,
                "select_chat_evidence",
                return_value=(
                    video,
                    raw_evidence,
                ),
            ),
            patch.object(
                yc,
                "generate",
                return_value=(
                    "answer",
                    display,
                ),
            ) as generate,
            patch.object(
                yc,
                "print_answer_panel",
            ),
            patch.object(
                yc,
                "print_single_video_evidence",
            ),
            patch.object(
                yc,
                "progress",
            ),
        ):
            with redirect_stdout(StringIO()):
                result = yc.run_video_question(
                    route="video",
                    model="model",
                    question="AI",
                    last_question=None,
                    current_video=None,
                    videos=[video],
                    top_k=6,
                )

        self.assertIs(
            result["current_video"],
            video,
        )

        self.assertEqual(
            result["evidence"],
            display,
        )

        generate.assert_called_once_with(
            "model",
            "AI",
            video,
            raw_evidence,
            description_fallback=False,
        )

    def test_video_question_uses_description_only_after_no_transcript(self):
        video = make_video()

        with (
            patch.object(
                yc,
                "select_chat_evidence",
                return_value=(
                    video,
                    [],
                ),
            ),
            patch.object(
                yc,
                "whole_video_sample",
                return_value=[],
            ),
            patch.object(
                yc,
                "generate",
                return_value=(
                    "answer",
                    [],
                ),
            ) as generate,
            patch.object(
                yc,
                "print_answer_panel",
            ),
            patch.object(
                yc,
                "print_single_video_evidence",
            ),
            patch.object(
                yc,
                "progress",
            ),
        ):
            with redirect_stdout(StringIO()):
                yc.run_video_question(
                    route="video",
                    model="model",
                    question="question",
                    last_question=None,
                    current_video=None,
                    videos=[video],
                    top_k=6,
                )

        generate.assert_called_once_with(
            "model",
            "question",
            video,
            [],
            description_fallback=True,
        )

    def test_context_route_preserves_current_video(self):
        current = make_video(
            video_id="locked"
        )

        with (
            patch.object(
                yc,
                "select_chat_evidence",
                return_value=(
                    current,
                    [("score", "chunk")],
                ),
            ),
            patch.object(
                yc,
                "generate",
                return_value=(
                    "answer",
                    [],
                ),
            ),
            patch.object(
                yc,
                "print_answer_panel",
            ),
            patch.object(
                yc,
                "print_single_video_evidence",
            ),
            patch.object(
                yc,
                "progress",
            ),
        ):
            with redirect_stdout(StringIO()):
                result = yc.run_video_question(
                    route="context",
                    model="model",
                    question="what else?",
                    last_question="AI",
                    current_video=current,
                    videos=[current],
                    top_k=6,
                )

        self.assertIs(
            result["current_video"],
            current,
        )
