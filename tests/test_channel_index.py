from __future__ import annotations

import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import youtube_knowledge as yk


def legacy_build_channel_index(
    channel_key,
    channel_name,
):
    channel_root = (
        yk.KNOWLEDGE_ROOT
        / channel_key
    )

    videos_root = (
        channel_root
        / "videos"
    )

    entries = []

    if videos_root.exists():
        for video_dir in videos_root.iterdir():
            if not video_dir.is_dir():
                continue

            metadata_path = (
                video_dir
                / "metadata.json"
            )

            if not metadata_path.exists():
                continue

            try:
                meta = json.loads(
                    metadata_path.read_text(
                        encoding="utf-8"
                    )
                )
            except Exception:
                continue

            keywords = []

            keyword_path = (
                video_dir
                / "keywords.json"
            )

            if keyword_path.exists():
                try:
                    keywords = json.loads(
                        keyword_path.read_text(
                            encoding="utf-8"
                        )
                    )
                except Exception:
                    pass

            summary = ""

            summary_path = (
                video_dir
                / "summary.md"
            )

            if summary_path.exists():
                summary = (
                    summary_path
                    .read_text(
                        encoding="utf-8",
                        errors="ignore",
                    )
                    [:3000]
                )

            entries.append({
                "video_id":
                    meta.get("video_id"),

                "title":
                    meta.get("title"),

                "upload_date":
                    meta.get("upload_date"),

                "url":
                    meta.get("url"),

                "keywords":
                    keywords,

                "summary_preview":
                    summary,
            })

    entries.sort(
        key=lambda item:
            item.get(
                "upload_date",
                ""
            ),
        reverse=True,
    )

    index = {
        "channel_key":
            channel_key,

        "channel":
            channel_name,

        "videos":
            entries,
    }

    channel_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    yk.write_json(
        channel_root
        / "index.json",
        index,
    )

    topic_scores = Counter()
    topic_videos = {}

    for item in entries:
        video_id = item.get(
            "video_id",
            ""
        )

        for position, topic in enumerate(
            item.get(
                "keywords",
                []
            )
        ):
            if not topic:
                continue

            key = topic.lower()

            weight = max(
                1,
                40 - position,
            )

            words = topic.split()

            if len(words) >= 2:
                weight += 15

            topic_scores[
                topic
            ] += weight

            topic_videos.setdefault(
                key,
                set()
            ).add(
                video_id
            )

    ranked_topics = sorted(
        topic_scores.items(),
        key=lambda item: (
            item[1],
            len(item[0].split()),
            len(item[0]),
        ),
        reverse=True,
    )

    topics = []
    seen = set()

    for topic, score in ranked_topics:
        key = topic.lower()

        if key in seen:
            continue

        seen.add(key)

        topics.append({
            "topic": topic,
            "video_count": len(
                topic_videos.get(
                    key,
                    set(),
                )
            ),
            "score": score,
        })

        if len(topics) >= 100:
            break

    yk.write_json(
        channel_root
        / "topics.json",
        topics,
    )


def build_fixture(root: Path) -> None:
    videos = (
        root
        / "test-channel"
        / "videos"
    )

    videos.mkdir(
        parents=True,
        exist_ok=True,
    )

    first = videos / "video-one"
    first.mkdir()

    (first / "metadata.json").write_text(
        json.dumps({
            "video_id": "v1",
            "title": "First Video",
            "upload_date": "20260814",
            "url": "https://example.test/v1",
        }),
        encoding="utf-8",
    )

    (first / "keywords.json").write_text(
        json.dumps([
            "Artificial Intelligence",
            "Linux",
            "Machine Learning",
        ]),
        encoding="utf-8",
    )

    (first / "summary.md").write_text(
        "First video summary.",
        encoding="utf-8",
    )

    second = videos / "video-two"
    second.mkdir()

    (second / "metadata.json").write_text(
        json.dumps({
            "video_id": "v2",
            "title": "Second Video",
            "upload_date": "20260810",
            "url": "https://example.test/v2",
        }),
        encoding="utf-8",
    )

    (second / "keywords.json").write_text(
        json.dumps([
            "artificial intelligence",
            "Docker",
            "Linux",
        ]),
        encoding="utf-8",
    )

    (second / "summary.md").write_text(
        "Second video summary.",
        encoding="utf-8",
    )

    # Invalid metadata should be ignored.
    invalid = videos / "broken-video"
    invalid.mkdir()

    (invalid / "metadata.json").write_text(
        "{broken json",
        encoding="utf-8",
    )

    # Directory without metadata should be ignored.
    (videos / "no-metadata").mkdir()

    # Non-directory entry should be ignored.
    (videos / "random.txt").write_text(
        "ignore",
        encoding="utf-8",
    )


class ChannelIndexCharacterizationTests(unittest.TestCase):

    def run_builder(
        self,
        builder,
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            build_fixture(root)

            with patch.object(
                yk,
                "KNOWLEDGE_ROOT",
                root,
            ):
                builder(
                    "test-channel",
                    "Test Channel",
                )

                index = json.loads(
                    (
                        root
                        / "test-channel"
                        / "index.json"
                    ).read_text(
                        encoding="utf-8"
                    )
                )

                topics = json.loads(
                    (
                        root
                        / "test-channel"
                        / "topics.json"
                    ).read_text(
                        encoding="utf-8"
                    )
                )

            return index, topics

    def test_current_matches_legacy(self):
        expected = self.run_builder(
            legacy_build_channel_index
        )

        actual = self.run_builder(
            yk.build_channel_index
        )

        self.assertEqual(
            actual,
            expected,
        )

    def test_video_sort_order(self):
        index, _ = self.run_builder(
            yk.build_channel_index
        )

        self.assertEqual(
            [
                video["video_id"]
                for video in index["videos"]
            ],
            [
                "v1",
                "v2",
            ],
        )

    def test_case_insensitive_topic_video_count(self):
        _, topics = self.run_builder(
            yk.build_channel_index
        )

        ai_topics = [
            item
            for item in topics
            if (
                item["topic"].lower()
                == "artificial intelligence"
            )
        ]

        self.assertEqual(
            len(ai_topics),
            1,
        )

        self.assertEqual(
            ai_topics[0]["video_count"],
            2,
        )

    def test_missing_video_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            with patch.object(
                yk,
                "KNOWLEDGE_ROOT",
                root,
            ):
                yk.build_channel_index(
                    "empty-channel",
                    "Empty Channel",
                )

                index = json.loads(
                    (
                        root
                        / "empty-channel"
                        / "index.json"
                    ).read_text(
                        encoding="utf-8"
                    )
                )

                topics = json.loads(
                    (
                        root
                        / "empty-channel"
                        / "topics.json"
                    ).read_text(
                        encoding="utf-8"
                    )
                )

        self.assertEqual(
            index["videos"],
            [],
        )

        self.assertEqual(
            topics,
            [],
        )


if __name__ == "__main__":
    unittest.main()
