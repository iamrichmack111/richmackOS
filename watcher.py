#!/usr/bin/env python3

import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HOME = Path.home()
BASE = HOME / ".richmackos"
DB = BASE / "richmackos.db"

RESET   = "\033[0m"
BOLD    = "\033[1m"
CYAN    = "\033[36m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
RED     = "\033[31m"
GRAY    = "\033[90m"

SKIP_PARTS = {
    ".git",
    ".cache",
    ".config",
    ".local",
    ".ssh",
    ".gnupg",
    ".richmackos",
    ".richmack-rag",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
}

RAG_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".rst",
    ".csv",
    ".json",
    ".yaml",
    ".yml",
    ".html",
}

CATEGORY_MAP = {
    ".pdf": "document",

    ".txt": "text",
    ".md": "text",
    ".markdown": "text",
    ".rst": "text",

    ".doc": "document",
    ".docx": "document",
    ".odt": "document",

    ".csv": "data",
    ".tsv": "data",
    ".json": "data",
    ".xml": "data",
    ".sql": "data",
    ".db": "data",
    ".sqlite": "data",
    ".sqlite3": "data",

    ".yaml": "config",
    ".yml": "config",
    ".toml": "config",
    ".ini": "config",
    ".conf": "config",

    ".py": "python",
    ".sh": "shell",
    ".bash": "shell",

    ".js": "javascript",
    ".ts": "typescript",

    ".html": "web",
    ".css": "web",

    ".zip": "archive",
    ".tar": "archive",
    ".gz": "archive",
    ".bz2": "archive",
    ".xz": "archive",
    ".7z": "archive",
    ".rar": "archive",

    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".webp": "image",

    ".mp3": "audio",
    ".wav": "audio",
    ".flac": "audio",
    ".ogg": "audio",
    ".m4a": "audio",

    ".mp4": "video",
    ".mkv": "video",
    ".avi": "video",
    ".mov": "video",
    ".webm": "video",

    ".iso": "disk-image",
    ".img": "disk-image",
}


def db():
    con = sqlite3.connect(DB, timeout=15)

    con.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            path TEXT UNIQUE,
            name TEXT,
            extension TEXT,
            size INTEGER,
            mtime REAL,
            category TEXT,
            is_git_repo INTEGER DEFAULT 0,
            git_remote TEXT,
            indexed_at TEXT
        )
    """)

    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_files_path
        ON files(path)
    """)

    con.commit()
    return con


def skipped(path):
    path = Path(path)

    for part in path.parts:
        if part in SKIP_PARTS:
            return True

    return False


def mime_type(path):
    try:
        result = subprocess.run(
            [
                "file",
                "--brief",
                "--mime-type",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            return result.stdout.strip().lower()

    except Exception:
        pass

    return ""


def category(path):
    ext = path.suffix.lower()

    if ext in CATEGORY_MAP:
        return CATEGORY_MAP[ext]

    mime = mime_type(path)

    if mime.startswith("text/"):
        return "text"

    if mime.startswith("image/"):
        return "image"

    if mime.startswith("audio/"):
        return "audio"

    if mime.startswith("video/"):
        return "video"

    if mime == "application/pdf":
        return "document"

    if mime in {
        "application/zip",
        "application/x-tar",
        "application/gzip",
        "application/x-7z-compressed",
        "application/vnd.rar",
    }:
        return "archive"

    return "other"


def rag_index(path):
    path = Path(path)

    if path.suffix.lower() not in RAG_EXTENSIONS:
        return

    if skipped(path):
        return

    if not path.exists() or not path.is_file():
        return

    try:
        result = subprocess.run(
            [
                "richmackrag",
                "index",
                str(path)
            ],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            print(
                f"{CYAN}RAG{RESET} "
                f"{path}",
                flush=True
            )
        else:
            message = (
                result.stderr.strip()
                or result.stdout.strip()
                or "unknown RAG indexing error"
            )

            print(
                f"{RED}RAG ERROR{RESET} "
                f"{path}: {message}",
                flush=True
            )

    except subprocess.TimeoutExpired:
        print(
            f"{RED}RAG TIMEOUT{RESET} "
            f"{path}",
            flush=True
        )

    except Exception as e:
        print(
            f"{RED}RAG ERROR{RESET} "
            f"{path}: {e}",
            flush=True
        )


def upsert(path):
    path = Path(path)

    if skipped(path):
        return

    if not path.exists():
        remove(path)
        return

    if not path.is_file():
        return

    if path.is_symlink():
        return

    try:
        st = path.stat()
    except Exception:
        return

    con = db()

    con.execute("""
        INSERT INTO files
        (
            path,
            name,
            extension,
            size,
            mtime,
            category,
            indexed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(path) DO UPDATE SET
            name=excluded.name,
            extension=excluded.extension,
            size=excluded.size,
            mtime=excluded.mtime,
            category=excluded.category,
            indexed_at=excluded.indexed_at
    """, (
        str(path.resolve()),
        path.name,
        path.suffix.lower(),
        st.st_size,
        st.st_mtime,
        category(path),
        datetime.now().isoformat(),
    ))

    con.commit()
    con.close()

    print(
        f"{GREEN}INDEX{RESET} "
        f"{path}",
        flush=True
    )

    rag_index(path)


def remove(path):
    path = Path(path)

    con = db()

    # Remove both the literal path and any children if a directory vanished.
    literal = str(path)

    con.execute(
        "DELETE FROM files WHERE path = ?",
        (literal,)
    )

    con.execute(
        "DELETE FROM files WHERE path LIKE ?",
        (literal.rstrip("/") + "/%",)
    )

    con.commit()
    con.close()

    print(
        f"{YELLOW}REMOVE{RESET} "
        f"{path}",
        flush=True
    )


def initial_status():
    con = db()

    count = con.execute(
        "SELECT COUNT(*) FROM files"
    ).fetchone()[0]

    con.close()

    print(
        f"{BOLD}{CYAN}"
        f"RichmackOS incremental watcher"
        f"{RESET}",
        flush=True
    )

    print(
        f"{GRAY}"
        f"Watching: {HOME}"
        f"{RESET}",
        flush=True
    )

    print(
        f"{GRAY}"
        f"Existing indexed files: {count}"
        f"{RESET}",
        flush=True
    )


def main():
    initial_status()

    exclude = (
        r"(^|/)(\.git|\.cache|\.config|\.local|\.ssh|\.gnupg|"
        r"\.richmackos|\.richmack-rag|node_modules|__pycache__|"
        r"\.venv|venv)(/|$)"
    )

    command = [
        "inotifywait",
        "--monitor",
        "--recursive",
        "--quiet",
        "--event",
        "close_write",
        "--event",
        "moved_to",
        "--event",
        "moved_from",
        "--event",
        "delete",
        "--event",
        "create",
        "--format",
        "%w|%e|%f",
        "--exclude",
        exclude,
        str(HOME),
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    if process.stdout is None:
        raise SystemExit("Unable to read inotifywait output")

    for line in process.stdout:
        line = line.rstrip("\n")

        if not line:
            continue

        try:
            directory, events, filename = line.split("|", 2)
        except ValueError:
            print(
                f"{RED}BAD EVENT{RESET} {line}",
                flush=True
            )
            continue

        path = Path(directory) / filename

        event_set = {
            event.strip()
            for event in events.split(",")
        }

        # Ignore directories themselves.
        if "ISDIR" in event_set:
            continue

        if (
            "DELETE" in event_set
            or "MOVED_FROM" in event_set
        ):
            remove(path)
            continue

        if (
            "CLOSE_WRITE" in event_set
            or "MOVED_TO" in event_set
            or "CREATE" in event_set
        ):
            # A CREATE event can arrive before writing is finished.
            # CLOSE_WRITE will update it again with final metadata.
            time.sleep(0.05)
            upsert(path)


if __name__ == "__main__":
    main()
