#!/usr/bin/env python3

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

HOME = Path.home()
LOGDIR = HOME / ".richmackos" / "organize-logs"

RESET   = "\033[0m"
BOLD    = "\033[1m"
CYAN    = "\033[36m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
MAGENTA = "\033[35m"
RED     = "\033[31m"
GRAY    = "\033[90m"

DESTINATIONS = {
    "pdf": HOME / "Documents" / "PDF",
    "text": HOME / "Documents" / "Text",
    "markdown": HOME / "Documents" / "Markdown",
    "document": HOME / "Documents",
    "data": HOME / "Data",
    "config": HOME / "Config",
    "script": HOME / "Scripts",
    "archive": HOME / "Archives",
    "image": HOME / "Pictures",
    "audio": HOME / "Music",
    "video": HOME / "Videos",
    "iso": HOME / "ISOs",
}

RULES = {
    ".pdf": "pdf",

    ".txt": "text",
    ".rst": "text",

    ".md": "markdown",
    ".markdown": "markdown",

    ".doc": "document",
    ".docx": "document",
    ".odt": "document",
    ".rtf": "document",

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

    ".sh": "script",
    ".bash": "script",
    ".py": "script",
    ".pl": "script",
    ".rb": "script",

    ".zip": "archive",
    ".tar": "archive",
    ".gz": "archive",
    ".bz2": "archive",
    ".xz": "archive",
    ".tgz": "archive",
    ".7z": "archive",
    ".rar": "archive",

    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".webp": "image",
    ".svg": "image",

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

    ".iso": "iso",
    ".img": "iso",
}


MIME_RULES = {
    "application/pdf": "pdf",

    "text/plain": "text",
    "text/markdown": "markdown",
    "text/x-markdown": "markdown",

    "application/json": "data",
    "text/csv": "data",
    "application/xml": "data",
    "text/xml": "data",
    "application/sql": "data",

    "application/zip": "archive",
    "application/x-7z-compressed": "archive",
    "application/x-rar": "archive",
    "application/vnd.rar": "archive",
    "application/x-tar": "archive",
    "application/gzip": "archive",
    "application/x-gzip": "archive",
    "application/x-bzip2": "archive",
    "application/x-xz": "archive",

    "image/png": "image",
    "image/jpeg": "image",
    "image/gif": "image",
    "image/webp": "image",
    "image/svg+xml": "image",

    "audio/mpeg": "audio",
    "audio/wav": "audio",
    "audio/x-wav": "audio",
    "audio/flac": "audio",
    "audio/ogg": "audio",
    "audio/mp4": "audio",

    "video/mp4": "video",
    "video/x-matroska": "video",
    "video/x-msvideo": "video",
    "video/quicktime": "video",
    "video/webm": "video",

    "application/x-iso9660-image": "iso",
}

SKIP_DIR_NAMES = {
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

# These are destinations that recursive mode should not walk back through.
DESTINATION_ROOTS = {
    p.resolve()
    for p in DESTINATIONS.values()
}


def human_size(size):
    value = float(size)

    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024

    return f"{value:.1f} PiB"


def should_skip_dir(path):
    try:
        resolved = path.resolve()
    except Exception:
        resolved = path

    if path.name in SKIP_DIR_NAMES:
        return True

    if path.name.startswith("."):
        return True

    for dest in DESTINATION_ROOTS:
        if resolved == dest:
            return True

        try:
            resolved.relative_to(dest)
            return True
        except ValueError:
            pass

    return False


def ai_classify(path):
    try:
        size = path.stat().st_size
    except Exception:
        size = 0

    prompt = (
        "Classify this real filesystem item into exactly ONE category. "
        "Output only one lowercase word from this list: "
        "pdf,text,markdown,document,data,config,script,archive,image,"
        "audio,video,iso,unknown. "
        "Do not invent information. "
        f"Filename: {path.name}. "
        f"Extension: {path.suffix.lower() or '(none)'}. "
        f"Size: {size} bytes."
    )

    try:
        result = subprocess.run(
            ["richmackai", prompt],
            capture_output=True,
            text=True,
            timeout=90
        )

        raw = result.stdout

        # Remove ANSI terminal escape sequences.
        raw = re.sub(
            r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])",
            "",
            raw
        )

        answer = raw.strip().lower()

        # Extract the first valid category word.
        allowed = set(DESTINATIONS) | {"unknown"}

        for word in re.findall(r"[a-z]+", answer):
            if word in allowed:
                return word

    except Exception:
        pass

    return "unknown"


def detect_mime(path):
    try:
        result = subprocess.run(
            [
                "file",
                "--brief",
                "--mime-type",
                str(path)
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return None

        mime = result.stdout.strip().lower()

        return mime or None

    except Exception:
        return None


def classify_file(path, use_ai=False):
    ext = path.suffix.lower()

    # 1. Deterministic extension rule.
    if ext in RULES:
        return RULES[ext], f"extension {ext}"

    # 2. Ask Linux what the file actually is.
    mime = detect_mime(path)

    if mime:
        if mime in MIME_RULES:
            return MIME_RULES[mime], f"MIME type {mime}"

        # Useful generic MIME families.
        if mime.startswith("image/"):
            return "image", f"MIME type {mime}"

        if mime.startswith("audio/"):
            return "audio", f"MIME type {mime}"

        if mime.startswith("video/"):
            return "video", f"MIME type {mime}"

        if mime.startswith("text/"):
            return "text", f"MIME type {mime}"

    # 3. AI is only the fallback after rules + MIME.
    if use_ai:
        category = ai_classify(path)

        if category in DESTINATIONS:
            if mime:
                reason = (
                    f"AI metadata classification "
                    f"after inconclusive MIME {mime}"
                )
            else:
                reason = "AI metadata classification"

            return category, reason

    # 4. Leave it alone.
    return None, None


def iter_files(root, recursive=False):
    root = Path(root).expanduser().resolve()

    if recursive:
        for current, dirs, files in os.walk(root):
            current_path = Path(current)

            dirs[:] = [
                d for d in dirs
                if not should_skip_dir(current_path / d)
            ]

            for filename in files:
                path = current_path / filename

                if path.name.startswith("."):
                    continue

                if path.is_symlink():
                    continue

                if path.is_file():
                    yield path

    else:
        for path in sorted(root.iterdir()):
            if path.name.startswith("."):
                continue

            if path.is_symlink():
                continue

            if path.is_file():
                yield path


def build_plan(root, recursive=False, use_ai=False):
    root = Path(root).expanduser().resolve()

    if not root.exists():
        raise SystemExit(f"Path does not exist: {root}")

    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    plan = []
    unknown = []

    files = list(
        iter_files(
            root,
            recursive=recursive
        )
    )

    total = len(files)

    print()
    print(
        f"{BOLD}{CYAN}"
        f"RichmackOS Organization Plan"
        f"{RESET}"
    )
    print(
        f"{GRAY}"
        f"Source: {root}"
        f"{RESET}"
    )
    print(
        f"{GRAY}"
        f"Mode: {'recursive' if recursive else 'top-level'}"
        f"{RESET}"
    )
    print(
        f"{GRAY}"
        f"AI fallback: {'enabled' if use_ai else 'disabled'}"
        f"{RESET}"
    )
    print()

    for i, path in enumerate(files, 1):
        if total:
            ratio = i / total
            width = 28
            filled = int(width * ratio)
            bar = "█" * filled + "░" * (width - filled)

            print(
                f"\r{CYAN}{bar}{RESET} "
                f"{int(ratio * 100):3d}% "
                f"{GRAY}{path.name[:35]:<35}{RESET}",
                end="",
                flush=True
            )

        category, reason = classify_file(
            path,
            use_ai=use_ai
        )

        if not category:
            unknown.append(path)
            continue

        destination_dir = DESTINATIONS[category]

        # In recursive mode preserve the relative parent path,
        # preventing same-name collisions such as multiple README.md files.
        if recursive:
            relative = path.relative_to(root)

            if relative.parent == Path("."):
                destination = destination_dir / path.name
            else:
                destination = (
                    destination_dir /
                    relative.parent /
                    path.name
                )
        else:
            destination = destination_dir / path.name

        try:
            if path.resolve() == destination.resolve():
                continue
        except Exception:
            pass

        plan.append({
            "source": path,
            "destination": destination,
            "category": category,
            "reason": reason,
        })

    if total:
        print()

    return plan, unknown


def show_plan(plan, unknown):
    print()

    if not plan:
        print(
            f"{GREEN}"
            f"No moves proposed."
            f"{RESET}"
        )

    else:
        print(
            f"{BOLD}{MAGENTA}"
            f"PROPOSED MOVES"
            f"{RESET}"
        )
        print()

        for i, item in enumerate(plan, 1):
            src = item["source"]
            dst = item["destination"]

            try:
                size = human_size(
                    src.stat().st_size
                )
            except Exception:
                size = "?"

            print(
                f"{BOLD}{i:>3}.{RESET} "
                f"{CYAN}{item['category']}{RESET} "
                f"{YELLOW}{src}{RESET}"
            )

            print(
                f"     {CYAN}→{RESET} "
                f"{GREEN}{dst}{RESET} "
                f"{GRAY}({size}){RESET}"
            )

            print(
                f"     {GRAY}{item['reason']}{RESET}"
            )

    if unknown:
        print()
        print(
            f"{BOLD}{YELLOW}"
            f"UNCLASSIFIED ({len(unknown)})"
            f"{RESET}"
        )

        for path in unknown[:50]:
            print(f"  {path}")

        if len(unknown) > 50:
            print(
                f"  ... and {len(unknown) - 50} more"
            )

    print()

    print(
        f"{BOLD}Summary:{RESET} "
        f"{len(plan)} proposed moves, "
        f"{len(unknown)} unclassified."
    )


def apply_plan(plan):
    if not plan:
        print(
            f"{YELLOW}"
            f"Nothing to apply."
            f"{RESET}"
        )
        return

    conflicts = [
        item
        for item in plan
        if item["destination"].exists()
    ]

    if conflicts:
        print()
        print(
            f"{RED}{BOLD}"
            f"Destination conflicts detected."
            f"{RESET}"
        )

        for item in conflicts:
            print(
                f"{item['source']}"
            )
            print(
                f"  destination exists: "
                f"{item['destination']}"
            )

        print()
        print(
            f"{RED}"
            f"No files were moved."
            f"{RESET}"
        )
        return

    print()

    confirm = input(
        f"{BOLD}"
        f"Type APPLY to move {len(plan)} file(s): "
        f"{RESET}"
    ).strip()

    if confirm != "APPLY":
        print(
            f"{YELLOW}"
            f"Cancelled. Nothing moved."
            f"{RESET}"
        )
        return

    LOGDIR.mkdir(
        parents=True,
        exist_ok=True
    )

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    logfile = LOGDIR / f"moves-{stamp}.jsonl"

    moved = 0

    for item in plan:
        src = item["source"]
        dst = item["destination"]

        dst.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        shutil.move(
            str(src),
            str(dst)
        )

        record = {
            "timestamp": datetime.now().isoformat(),
            "source": str(src),
            "destination": str(dst),
            "category": item["category"],
            "reason": item["reason"],
        }

        with logfile.open(
            "a",
            encoding="utf-8"
        ) as f:
            f.write(
                json.dumps(record) + "\n"
            )

        moved += 1

        print(
            f"{GREEN}✓{RESET} "
            f"{src.name} "
            f"{CYAN}→{RESET} "
            f"{dst.parent}"
        )

    print()
    print(
        f"{GREEN}{BOLD}"
        f"Moved {moved} file(s)."
        f"{RESET}"
    )
    print(
        f"{GRAY}"
        f"Move log: {logfile}"
        f"{RESET}"
    )


def list_logs():
    LOGDIR.mkdir(
        parents=True,
        exist_ok=True
    )

    logs = sorted(
        list(LOGDIR.glob("moves-*.jsonl")) +
        list(LOGDIR.glob("moves-*.undone")),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not logs:
        print(
            f"{YELLOW}"
            f"No organization logs found."
            f"{RESET}"
        )
        return

    print(
        f"{BOLD}{CYAN}"
        f"RichmackOS Organization Logs"
        f"{RESET}"
    )
    print()

    for path in logs:
        try:
            count = sum(
                1
                for line in path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            )
        except Exception:
            count = 0

        state = (
            "UNDONE"
            if path.suffix == ".undone"
            else "ACTIVE"
        )

        print(
            f"{MAGENTA}{path.name}{RESET} "
            f"{GRAY}({count} move(s), {state}){RESET}"
        )


def undo_last():
    LOGDIR.mkdir(
        parents=True,
        exist_ok=True
    )

    logs = sorted(
        LOGDIR.glob("moves-*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not logs:
        print(
            f"{YELLOW}"
            f"No active move logs found."
            f"{RESET}"
        )
        return

    logfile = logs[0]

    records = [
        json.loads(line)
        for line in logfile.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    if not records:
        print(
            f"{YELLOW}"
            f"Latest move log is empty."
            f"{RESET}"
        )
        return

    print(
        f"{BOLD}{MAGENTA}"
        f"UNDO PLAN"
        f"{RESET}"
    )
    print(
        f"{GRAY}"
        f"Log: {logfile}"
        f"{RESET}"
    )
    print()

    conflicts = []

    for record in reversed(records):
        current = Path(
            record["destination"]
        )

        original = Path(
            record["source"]
        )

        print(
            f"{YELLOW}{current}{RESET}"
        )

        print(
            f"  {CYAN}→{RESET} "
            f"{GREEN}{original}{RESET}"
        )

        if not current.exists():
            conflicts.append(
                (
                    current,
                    original,
                    "current file is missing"
                )
            )

        elif original.exists():
            conflicts.append(
                (
                    current,
                    original,
                    "original path already exists"
                )
            )

    if conflicts:
        print()
        print(
            f"{RED}{BOLD}"
            f"Undo cannot proceed safely."
            f"{RESET}"
        )

        for current, original, reason in conflicts:
            print()
            print(
                f"{RED}{reason}{RESET}"
            )
            print(
                f"  current:  {current}"
            )
            print(
                f"  original: {original}"
            )

        print()
        print(
            f"{RED}"
            f"No files were restored."
            f"{RESET}"
        )
        return

    print()

    confirm = input(
        f"{BOLD}"
        f"Type UNDO to restore "
        f"{len(records)} file(s): "
        f"{RESET}"
    ).strip()

    if confirm != "UNDO":
        print(
            f"{YELLOW}"
            f"Cancelled. Nothing restored."
            f"{RESET}"
        )
        return

    restored = 0

    for record in reversed(records):
        current = Path(
            record["destination"]
        )

        original = Path(
            record["source"]
        )

        original.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        shutil.move(
            str(current),
            str(original)
        )

        restored += 1

        print(
            f"{GREEN}✓{RESET} "
            f"{current.name} "
            f"{CYAN}→{RESET} "
            f"{original.parent}"
        )

    undone = logfile.with_suffix(
        ".undone"
    )

    logfile.rename(
        undone
    )

    print()
    print(
        f"{GREEN}{BOLD}"
        f"Restored {restored} file(s)."
        f"{RESET}"
    )


def main():
    parser = argparse.ArgumentParser(
        prog="richmack organize",
        description=(
            "Plan, apply, log, recursively organize, "
            "AI-classify unknown files, and undo moves."
        )
    )

    parser.add_argument(
        "path",
        nargs="?",
        default=str(HOME),
        help="Directory to organize"
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply plan after explicit confirmation"
    )

    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Inspect subdirectories recursively"
    )

    parser.add_argument(
        "--ai",
        action="store_true",
        help=(
            "Use RichmackAI only for otherwise "
            "unclassified filenames"
        )
    )

    parser.add_argument(
        "--logs",
        action="store_true",
        help="List organization logs"
    )

    parser.add_argument(
        "--undo-last",
        action="store_true",
        help="Undo latest active organization run"
    )

    args = parser.parse_args()

    if args.logs:
        list_logs()
        return

    if args.undo_last:
        undo_last()
        return

    root = Path(
        args.path
    ).expanduser().resolve()

    plan, unknown = build_plan(
        root,
        recursive=args.recursive,
        use_ai=args.ai
    )

    show_plan(
        plan,
        unknown
    )

    if args.apply:
        apply_plan(plan)
    else:
        print()
        print(
            f"{GRAY}"
            f"Dry run only. No files were moved."
            f"{RESET}"
        )


if __name__ == "__main__":
    main()
