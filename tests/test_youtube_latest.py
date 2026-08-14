#!/usr/bin/env python3
import json
import os
import tempfile
import time
import unittest
from pathlib import Path

import youtube_knowledge
import youtube_summarize
import youtube_chat


def write_transcript(path: Path, video_id: str, upload_date: str):
    path.write_text(
        f"TITLE: Test {video_id}\n"
        f"VIDEO_ID: {video_id}\n"
        f"UPLOAD_DATE: {upload_date}\n"
        "\nTRANSCRIPT:\nhello\n",
        encoding="utf-8",
    )


class LatestVideoOrderingTests(unittest.TestCase):
    def test_knowledge_build_sort_uses_upload_date_not_mtime(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old = root / "old.txt"
            new = root / "new.txt"
            write_transcript(old, "old", "20240101")
            write_transcript(new, "new", "20260814")

            now = time.time()
            os.utime(old, (now + 1000, now + 1000))
            os.utime(new, (now, now))

            files = sorted(
                [old, new],
                key=youtube_knowledge.source_upload_sort_key,
                reverse=True,
            )
            self.assertEqual(files[0].name, "new.txt")

    def test_summarize_prefers_knowledge_index_order(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            channel_dir = root / "transcripts"
            channel_dir.mkdir()
            knowledge_root = root / "knowledge"
            index_dir = knowledge_root / "test-channel"
            index_dir.mkdir(parents=True)

            old = channel_dir / "old.txt"
            new = channel_dir / "new.txt"
            write_transcript(old, "old", "20240101")
            write_transcript(new, "new", "20260814")

            # Knowledge index is authoritative and newest-first.
            (index_dir / "index.json").write_text(
                json.dumps({"videos": [
                    {"video_id": "new", "upload_date": "20260814"},
                    {"video_id": "old", "upload_date": "20240101"},
                ]}),
                encoding="utf-8",
            )

            previous = youtube_summarize.KNOWLEDGE_ROOT
            youtube_summarize.KNOWLEDGE_ROOT = knowledge_root
            try:
                selected = youtube_summarize.select_files(
                    channel_dir,
                    channel_key="test-channel",
                    limit=1,
                )
            finally:
                youtube_summarize.KNOWLEDGE_ROOT = previous

            self.assertEqual([p.name for p in selected], ["new.txt"])

    def test_chat_limit_uses_upload_date_not_mtime(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old = root / "old.txt"
            new = root / "new.txt"
            write_transcript(old, "old", "20240101")
            write_transcript(new, "new", "20260814")
            now = time.time()
            os.utime(old, (now + 1000, now + 1000))
            os.utime(new, (now, now))
            files = sorted(
                [old, new],
                key=youtube_chat.transcript_upload_sort_key,
                reverse=True,
            )
            self.assertEqual(files[0].name, "new.txt")


if __name__ == "__main__":
    unittest.main()
