from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .repository import run_git


@dataclass
class GitMetrics:
    commits: int = 0
    contributors: int = 0
    tags: int = 0
    changed_files_30d: int = 0


def _integer(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def collect_git_metrics(root: Path) -> GitMetrics:
    commits = _integer(
        run_git(
            root,
            "rev-list",
            "--count",
            "HEAD",
        )
    )

    contributors_output = run_git(
        root,
        "shortlog",
        "-sne",
        "HEAD",
    )

    contributors = len(
        [
            line
            for line in contributors_output.splitlines()
            if line.strip()
        ]
    )

    tags_output = run_git(
        root,
        "tag",
        "--list",
    )

    tags = len(
        [
            line
            for line in tags_output.splitlines()
            if line.strip()
        ]
    )

    changed_output = run_git(
        root,
        "log",
        "--since=30 days ago",
        "--name-only",
        "--pretty=format:",
    )

    changed_files = len(
        {
            line.strip()
            for line in changed_output.splitlines()
            if line.strip()
        }
    )

    return GitMetrics(
        commits=commits,
        contributors=contributors,
        tags=tags,
        changed_files_30d=changed_files,
    )
