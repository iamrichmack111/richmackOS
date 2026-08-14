from __future__ import annotations

import datetime
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import youtube_ask as ya


def legacy_candidate_files(
    channel_dir,
    latest=False,
    days=None,
    since=None,
    video=None,
):
    files = list(
        channel_dir.glob("*.txt")
    )

    if not files:
        return []

    if video:
        files = [
            path
            for path in files
            if (
                path.stem == video
                or ya.transcript_metadata(path).get("VIDEO_ID") == video
            )
        ]

    if since:
        since_date = datetime.datetime.strptime(
            since,
            "%Y-%m-%d",
        ).date()

        files = [
            path
            for path in files
            if ya.parse_upload_date(path) >= since_date
        ]

    if days is not None:
        cutoff = (
            datetime.date.today()
            - datetime.timedelta(days=days)
        )

        files = [
            path
            for path in files
            if ya.parse_upload_date(path) >= cutoff
        ]

    files.sort(
        key=ya.parse_upload_date,
        reverse=True,
    )

    if latest and files:
        return [files[0]]

    return files


class CandidateFilesCharacterizationTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

        self.files = {
            "one": self.root / "one.txt",
            "two": self.root / "two.txt",
            "three": self.root / "three.txt",
        }

        for path in self.files.values():
            path.write_text(
                "test transcript\n",
                encoding="utf-8",
            )

        self.upload_dates = {
            self.files["one"]: datetime.date(2026, 8, 14),
            self.files["two"]: datetime.date(2026, 8, 10),
            self.files["three"]: datetime.date(2026, 7, 20),
        }

        self.metadata = {
            self.files["one"]: {
                "VIDEO_ID": "video-a",
            },
            self.files["two"]: {
                "VIDEO_ID": "video-b",
            },
            self.files["three"]: {
                "VIDEO_ID": "video-c",
            },
        }

    def tearDown(self):
        self.temp.cleanup()

    def run_both(self, **kwargs):
        with (
            patch.object(
                ya,
                "parse_upload_date",
                side_effect=lambda path: self.upload_dates[path],
            ),
            patch.object(
                ya,
                "transcript_metadata",
                side_effect=lambda path: self.metadata[path],
            ),
        ):
            expected = legacy_candidate_files(
                self.root,
                **kwargs,
            )

            actual = ya.candidate_files(
                self.root,
                **kwargs,
            )

        self.assertEqual(
            actual,
            expected,
        )

        return actual

    def test_no_filters(self):
        result = self.run_both()

        self.assertEqual(
            [path.name for path in result],
            [
                "one.txt",
                "two.txt",
                "three.txt",
            ],
        )

    def test_latest(self):
        result = self.run_both(
            latest=True,
        )

        self.assertEqual(
            [path.name for path in result],
            ["one.txt"],
        )

    def test_video_by_metadata_id(self):
        result = self.run_both(
            video="video-b",
        )

        self.assertEqual(
            [path.name for path in result],
            ["two.txt"],
        )

    def test_video_by_filename_stem(self):
        result = self.run_both(
            video="three",
        )

        self.assertEqual(
            [path.name for path in result],
            ["three.txt"],
        )

    def test_since_filter(self):
        result = self.run_both(
            since="2026-08-01",
        )

        self.assertEqual(
            [path.name for path in result],
            [
                "one.txt",
                "two.txt",
            ],
        )

    def test_days_filter_matches_legacy(self):
        with patch.object(
            ya.datetime,
            "date",
            wraps=datetime.date,
        ) as mock_date:
            mock_date.today.return_value = datetime.date(
                2026,
                8,
                14,
            )

            # Avoid relying on the patched date constructor for the
            # fixture values by using the legacy/new comparison only.
            self.run_both(
                days=10,
            )

    def test_combined_filters(self):
        result = self.run_both(
            video="video-a",
            since="2026-08-01",
            latest=True,
        )

        self.assertEqual(
            [path.name for path in result],
            ["one.txt"],
        )

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            self.assertEqual(
                ya.candidate_files(root),
                [],
            )

    def test_invalid_since_still_raises(self):
        with self.assertRaises(ValueError):
            ya.candidate_files(
                self.root,
                since="not-a-date",
            )


if __name__ == "__main__":
    unittest.main()
