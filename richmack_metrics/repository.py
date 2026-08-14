from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Iterable


SOURCE_SUFFIXES = {
    ".py",
    ".sh",
    ".bash",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".java",
    ".rb",
}

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
    "metrics-data",
}


def run_git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return ""

    if result.returncode != 0:
        return ""

    return result.stdout.strip()


def find_repository(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()

    output = run_git(start, "rev-parse", "--show-toplevel")

    if output:
        return Path(output).resolve()

    raise RuntimeError(
        f"Could not locate a Git repository from {start}"
    )


def iter_source_files(root: Path) -> Iterable[Path]:
    for current, directories, filenames in os.walk(root):
        directories[:] = [
            name
            for name in directories
            if name not in IGNORED_DIRECTORIES
            and not name.startswith(".richmack-backup-")
        ]

        directory = Path(current)

        for filename in filenames:
            path = directory / filename

            if path.suffix.lower() in SOURCE_SUFFIXES:
                yield path

            elif path.parent.name == "bin":
                try:
                    with path.open(
                        "r",
                        encoding="utf-8",
                        errors="ignore",
                    ) as handle:
                        first_line = handle.readline()
                except OSError:
                    continue

                if first_line.startswith("#!"):
                    yield path


def line_count(path: Path) -> int:
    try:
        with path.open(
            "r",
            encoding="utf-8",
            errors="ignore",
        ) as handle:
            return sum(1 for _ in handle)
    except OSError:
        return 0


def read_text(path: Path) -> str:
    try:
        return path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except OSError:
        return ""
