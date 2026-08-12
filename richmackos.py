#!/usr/bin/env python3

import os
import sys
import json
import sqlite3
import hashlib
import subprocess
import shutil
import socket
import urllib.request
from pathlib import Path
from datetime import datetime

HOME = Path.home()
BASE = HOME / ".richmackos"
DB = BASE / "richmackos.db"
SKILLS = BASE / "skills"
PLUGINS = BASE / "plugins"

OLLAMA = "http://richmack.local:11434"
DEFAULT_MODEL = "huihui_ai/granite4.1-abliterated:3b"

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
RED = "\033[31m"
GRAY = "\033[90m"


def color(text, c):
    return f"{c}{text}{RESET}"


def connect():
    con = sqlite3.connect(DB)

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
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY,
            path TEXT UNIQUE,
            name TEXT,
            language TEXT,
            remote TEXT,
            branch TEXT,
            dirty INTEGER,
            last_commit TEXT,
            indexed_at TEXT
        )
    """)

    con.commit()
    return con


def human_size(n):
    units = ["B", "K", "M", "G", "T"]
    value = float(n)

    for unit in units:
        if value < 1024:
            return f"{value:.1f}{unit}"
        value /= 1024

    return f"{value:.1f}P"


def classify(path):
    ext = path.suffix.lower()

    mapping = {
        ".pdf": "document",
        ".txt": "text",
        ".md": "text",
        ".rst": "text",
        ".doc": "document",
        ".docx": "document",
        ".xls": "spreadsheet",
        ".xlsx": "spreadsheet",
        ".csv": "data",
        ".json": "data",
        ".yaml": "config",
        ".yml": "config",
        ".toml": "config",
        ".ini": "config",
        ".conf": "config",
        ".py": "python",
        ".sh": "shell",
        ".js": "javascript",
        ".ts": "typescript",
        ".html": "web",
        ".css": "web",
        ".zip": "archive",
        ".tar": "archive",
        ".gz": "archive",
        ".7z": "archive",
        ".mp3": "audio",
        ".wav": "audio",
        ".flac": "audio",
        ".mp4": "video",
        ".mkv": "video",
        ".avi": "video",
        ".jpg": "image",
        ".jpeg": "image",
        ".png": "image",
        ".webp": "image",
        ".iso": "disk-image",
    }

    return mapping.get(ext, "other")


def git_info(path):
    try:
        root = subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=4
        ).strip()

        root = Path(root)

        branch = subprocess.check_output(
            ["git", "-C", str(root), "branch", "--show-current"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=4
        ).strip()

        try:
            remote = subprocess.check_output(
                ["git", "-C", str(root), "remote", "get-url", "origin"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=4
            ).strip()
        except Exception:
            remote = ""

        status = subprocess.check_output(
            ["git", "-C", str(root), "status", "--porcelain"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=4
        )

        try:
            last_commit = subprocess.check_output(
                ["git", "-C", str(root), "log", "-1", "--format=%ci"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=4
            ).strip()
        except Exception:
            last_commit = ""

        return {
            "root": str(root),
            "branch": branch,
            "remote": remote,
            "dirty": bool(status.strip()),
            "last_commit": last_commit
        }

    except Exception:
        return None


def detect_language(root):
    root = Path(root)

    checks = [
        ("Python", ["pyproject.toml", "requirements.txt", "setup.py"]),
        ("Node.js", ["package.json"]),
        ("Rust", ["Cargo.toml"]),
        ("Go", ["go.mod"]),
        ("Ruby", ["Gemfile"]),
        ("PHP", ["composer.json"]),
        ("Java", ["pom.xml", "build.gradle"]),
        ("Docker", ["Dockerfile", "docker-compose.yml", "compose.yaml"]),
    ]

    found = []

    for language, markers in checks:
        if any((root / marker).exists() for marker in markers):
            found.append(language)

    return ", ".join(found) if found else "Unknown"


def scan(root):
    root = Path(root).expanduser().resolve()

    if not root.exists():
        print(color(f"Path not found: {root}", RED))
        return

    con = connect()
    files = 0
    projects_seen = set()

    print(color(f"\nScanning {root}", CYAN))

    for current, dirs, names in os.walk(root):
        dirs[:] = [
            d for d in dirs
            if d not in {
                ".git",
                "node_modules",
                ".cache",
                "__pycache__",
                ".venv",
                "venv"
            }
        ]

        current_path = Path(current)

        if (current_path / ".git").exists():
            info = git_info(current_path)

            if info and info["root"] not in projects_seen:
                projects_seen.add(info["root"])

                language = detect_language(info["root"])

                con.execute("""
                    INSERT OR REPLACE INTO projects
                    (path, name, language, remote, branch, dirty,
                     last_commit, indexed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    info["root"],
                    Path(info["root"]).name,
                    language,
                    info["remote"],
                    info["branch"],
                    int(info["dirty"]),
                    info["last_commit"],
                    datetime.now().isoformat()
                ))

        for name in names:
            path = current_path / name

            try:
                st = path.stat()
            except Exception:
                continue

            category = classify(path)

            con.execute("""
                INSERT OR REPLACE INTO files
                (path, name, extension, size, mtime,
                 category, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(path),
                path.name,
                path.suffix.lower(),
                st.st_size,
                st.st_mtime,
                category,
                datetime.now().isoformat()
            ))

            files += 1

            if files % 250 == 0:
                print(
                    f"\r{GREEN}Indexed {files:,} files...{RESET}",
                    end="",
                    flush=True
                )

    con.commit()
    con.close()

    print(
        f"\r{GREEN}{BOLD}✓ Indexed {files:,} files "
        f"and {len(projects_seen)} Git repositories.{RESET}"
    )


def search(term):
    con = connect()

    rows = con.execute("""
        SELECT path, category, size
        FROM files
        WHERE path LIKE ?
           OR name LIKE ?
        ORDER BY mtime DESC
        LIMIT 100
    """, (f"%{term}%", f"%{term}%")).fetchall()

    con.close()

    if not rows:
        print(color("No matches.", YELLOW))
        return

    for path, category, size in rows:
        print(
            f"{CYAN}{category:<12}{RESET} "
            f"{GREEN}{human_size(size):>8}{RESET} "
            f"{path}"
        )


def repos():
    con = connect()

    rows = con.execute("""
        SELECT name, path, language, branch, dirty,
               remote, last_commit
        FROM projects
        ORDER BY last_commit DESC
    """).fetchall()

    con.close()

    if not rows:
        print("No repositories indexed.")
        return

    for name, path, lang, branch, dirty, remote, last in rows:
        flag = f"{RED}DIRTY{RESET}" if dirty else f"{GREEN}clean{RESET}"

        print(
            f"\n{BOLD}{CYAN}{name}{RESET}  {flag}"
        )
        print(f"  path:     {path}")
        print(f"  stack:    {lang}")
        print(f"  branch:   {branch or '-'}")
        print(f"  remote:   {remote or '-'}")
        print(f"  commit:   {last or '-'}")


def remember(text):
    con = connect()

    con.execute(
        "INSERT INTO memory(text, created_at) VALUES (?, ?)",
        (text, datetime.now().isoformat())
    )

    con.commit()
    con.close()

    print(color("✓ Remembered.", GREEN))


def memories(term=None):
    con = connect()

    if term:
        rows = con.execute("""
            SELECT id, text, created_at
            FROM memory
            WHERE text LIKE ?
            ORDER BY id DESC
        """, (f"%{term}%",)).fetchall()
    else:
        rows = con.execute("""
            SELECT id, text, created_at
            FROM memory
            ORDER BY id DESC
            LIMIT 100
        """).fetchall()

    con.close()

    for ident, text, created in rows:
        print(
            f"{MAGENTA}[{ident}]{RESET} "
            f"{text} "
            f"{GRAY}{created[:19]}{RESET}"
        )


def forget(ident):
    con = connect()

    con.execute(
        "DELETE FROM memory WHERE id = ?",
        (ident,)
    )

    con.commit()
    con.close()

    print(color(f"✓ Forgot memory {ident}.", GREEN))


def large_files(limit=20):
    con = connect()

    rows = con.execute("""
        SELECT path, size
        FROM files
        ORDER BY size DESC
        LIMIT ?
    """, (limit,)).fetchall()

    con.close()

    for path, size in rows:
        print(
            f"{YELLOW}{human_size(size):>10}{RESET} {path}"
        )


def duplicate_candidates():
    con = connect()

    rows = con.execute("""
        SELECT size, COUNT(*)
        FROM files
        WHERE size > 0
        GROUP BY size
        HAVING COUNT(*) > 1
        ORDER BY size DESC
        LIMIT 100
    """).fetchall()

    groups = 0

    for size, count in rows:
        paths = con.execute(
            "SELECT path FROM files WHERE size = ?",
            (size,)
        ).fetchall()

        hashes = {}

        for (path,) in paths:
            try:
                h = hashlib.sha256()

                with open(path, "rb") as f:
                    while True:
                        block = f.read(1024 * 1024)

                        if not block:
                            break

                        h.update(block)

                hashes.setdefault(h.hexdigest(), []).append(path)

            except Exception:
                pass

        for digest, matches in hashes.items():
            if len(matches) > 1:
                groups += 1

                print(
                    f"\n{MAGENTA}Duplicate group {groups}{RESET} "
                    f"{human_size(size)}"
                )

                for match in matches:
                    print(f"  {match}")

    con.close()

    if not groups:
        print(color("No exact duplicates found.", GREEN))


def system_status():
    print(
        f"{BOLD}{CYAN}"
        f"╭─ RICHMACK SYSTEM ─────────────────────────"
        f"{RESET}"
    )

    print(f"{BOLD}Host:{RESET} {socket.gethostname()}")

    try:
        uptime = Path("/proc/uptime").read_text().split()[0]
        hours = float(uptime) / 3600
        print(f"{BOLD}Uptime:{RESET} {hours:.1f} hours")
    except Exception:
        pass

    try:
        mem = {}

        for line in Path("/proc/meminfo").read_text().splitlines():
            key, value = line.split(":", 1)
            mem[key] = int(value.strip().split()[0])

        total = mem["MemTotal"] * 1024
        available = mem["MemAvailable"] * 1024
        used = total - available

        print(
            f"{BOLD}RAM:{RESET} "
            f"{human_size(used)} / {human_size(total)}"
        )
    except Exception:
        pass

    disk = shutil.disk_usage(HOME)

    print(
        f"{BOLD}Disk:{RESET} "
        f"{human_size(disk.used)} / {human_size(disk.total)}"
    )

    con = connect()

    file_count = con.execute(
        "SELECT COUNT(*) FROM files"
    ).fetchone()[0]

    project_count = con.execute(
        "SELECT COUNT(*) FROM projects"
    ).fetchone()[0]

    memory_count = con.execute(
        "SELECT COUNT(*) FROM memory"
    ).fetchone()[0]

    con.close()

    print(f"{BOLD}Indexed files:{RESET} {file_count:,}")
    print(f"{BOLD}Projects:{RESET} {project_count}")
    print(f"{BOLD}Memories:{RESET} {memory_count}")

    try:
        with urllib.request.urlopen(
            OLLAMA + "/api/tags",
            timeout=3
        ) as r:
            data = json.loads(r.read())

        models = data.get("models", [])

        print(
            f"{BOLD}AI server:{RESET} "
            f"{GREEN}ONLINE{RESET}"
        )

        print(
            f"{BOLD}Models:{RESET} {len(models)}"
        )

    except Exception:
        print(
            f"{BOLD}AI server:{RESET} "
            f"{RED}OFFLINE{RESET}"
        )

    ragdb = HOME / ".richmack-rag" / "rag.db"

    print(
        f"{BOLD}RAG:{RESET} "
        + (
            f"{GREEN}available{RESET}"
            if ragdb.exists()
            else f"{YELLOW}not initialized{RESET}"
        )
    )

    print(
        f"{BOLD}{CYAN}"
        f"╰────────────────────────────────────────────"
        f"{RESET}"
    )


def doctor():
    checks = {
        "python3": shutil.which("python3"),
        "git": shutil.which("git"),
        "curl": shutil.which("curl"),
        "richmackai": shutil.which("richmackai"),
        "richmackrag": shutil.which("richmackrag"),
    }

    print(color("RichmackOS Doctor\n", CYAN))

    for name, result in checks.items():
        status = (
            f"{GREEN}OK{RESET}"
            if result
            else f"{YELLOW}missing{RESET}"
        )

        print(f"{name:<15} {status}")

    try:
        urllib.request.urlopen(
            OLLAMA + "/api/tags",
            timeout=3
        )

        print(
            f"{'richmack.local':<15} "
            f"{GREEN}OK{RESET}"
        )

    except Exception as e:
        print(
            f"{'richmack.local':<15} "
            f"{RED}FAILED{RESET} {e}"
        )


def skill_add(name, command):
    path = SKILLS / f"{name}.skill"

    path.write_text(command + "\n")

    print(
        color(
            f"✓ Skill saved: {name}",
            GREEN
        )
    )


def skill_list():
    for path in sorted(SKILLS.glob("*.skill")):
        print(path.stem)


def skill_show(name):
    path = SKILLS / f"{name}.skill"

    if not path.exists():
        print(color("Skill not found.", RED))
        return

    print(path.read_text())


def skill_run(name):
    path = SKILLS / f"{name}.skill"

    if not path.exists():
        print(color("Skill not found.", RED))
        return

    command = path.read_text().strip()

    print(
        f"{YELLOW}Skill command:{RESET}\n{command}\n"
    )

    answer = input(
        f"{BOLD}Run this command? [y/N] {RESET}"
    ).strip().lower()

    if answer != "y":
        print("Cancelled.")
        return

    subprocess.run(
        command,
        shell=True,
        check=False
    )


def plugin_list():
    files = list(PLUGINS.glob("*"))

    if not files:
        print("No plugins installed.")
        return

    for path in sorted(files):
        print(path.name)


def readme_for_project(path):
    path = Path(path).expanduser().resolve()

    if not path.exists():
        print("Path not found.")
        return

    info = git_info(path)

    pieces = []

    for filename in [
        "README.md",
        "pyproject.toml",
        "requirements.txt",
        "package.json",
        "Dockerfile",
        "docker-compose.yml",
        "compose.yaml"
    ]:
        candidate = path / filename

        if candidate.exists():
            try:
                text = candidate.read_text(
                    errors="ignore"
                )[:8000]

                pieces.append(
                    f"FILE: {filename}\n{text}"
                )
            except Exception:
                pass

    prompt = f"""
Create a concise README for this project.

Project path:
{path}

Detected stack:
{detect_language(path)}

Git information:
{json.dumps(info or {}, indent=2)}

Project files:
{chr(10).join(pieces)}

Include:
- purpose
- features
- requirements
- installation
- usage
- project structure
"""

    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt,
        "stream": False
    }

    req = urllib.request.Request(
        OLLAMA + "/api/generate",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(
            req,
            timeout=180
        ) as r:
            result = json.loads(r.read())

        answer = result.get(
            "response",
            ""
        ).strip()

        output_dir = HOME / "Readme" / path.name
        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        output = output_dir / "README.md"

        output.write_text(
            answer + "\n"
        )

        print(
            color(
                f"✓ README saved: {output}",
                GREEN
            )
        )

    except Exception as e:
        print(color(str(e), RED))


def help_screen():
    print(f"""
{BOLD}{CYAN}RichmackOS{RESET}

{BOLD}System{RESET}
  richmack status
  richmack doctor

{BOLD}Index & Search{RESET}
  richmack scan PATH
  richmack search QUERY
  richmack large
  richmack duplicates

{BOLD}Projects{RESET}
  richmack repos
  richmack readme PATH

{BOLD}Memory{RESET}
  richmack remember "TEXT"
  richmack memories
  richmack recall QUERY
  richmack forget ID

{BOLD}Skills{RESET}
  richmack skill add NAME "COMMAND"
  richmack skill list
  richmack skill show NAME
  richmack skill run NAME

{BOLD}Plugins{RESET}
  richmack plugins

{BOLD}AI{RESET}
  richmack ai "QUESTION"
  richmack chat
  richmack rag "QUESTION"
""")


def main():
    BASE.mkdir(
        parents=True,
        exist_ok=True
    )

    SKILLS.mkdir(
        parents=True,
        exist_ok=True
    )

    PLUGINS.mkdir(
        parents=True,
        exist_ok=True
    )

    if len(sys.argv) < 2:
        help_screen()
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "status":
        system_status()

    elif cmd == "doctor":
        doctor()

    elif cmd == "scan":
        scan(
            args[0] if args else HOME
        )

    elif cmd == "search":
        search(
            " ".join(args)
        )

    elif cmd == "repos":
        repos()

    elif cmd == "large":
        large_files()

    elif cmd == "duplicates":
        duplicate_candidates()

    elif cmd == "remember":
        remember(
            " ".join(args)
        )

    elif cmd in {"memories", "memory"}:
        memories()

    elif cmd == "recall":
        memories(
            " ".join(args)
        )

    elif cmd == "forget":
        forget(
            int(args[0])
        )

    elif cmd == "skill":
        if not args:
            skill_list()
            return

        action = args[0]

        if action == "list":
            skill_list()

        elif action == "add":
            skill_add(
                args[1],
                " ".join(args[2:])
            )

        elif action == "show":
            skill_show(
                args[1]
            )

        elif action == "run":
            skill_run(
                args[1]
            )

    elif cmd == "plugins":
        plugin_list()

    elif cmd == "readme":
        readme_for_project(
            args[0] if args else "."
        )

    elif cmd == "ai":
        subprocess.run(
            ["richmackai"] + args
        )

    elif cmd == "chat":
        subprocess.run(
            ["richmackai", "--chat"]
        )

    elif cmd == "rag":
        subprocess.run(
            ["richmackrag", "ask"] + args
        )

    elif cmd in {"help", "-h", "--help"}:
        help_screen()

    else:
        print(
            color(
                f"Unknown command: {cmd}",
                RED
            )
        )

        help_screen()


if __name__ == "__main__":
    main()
