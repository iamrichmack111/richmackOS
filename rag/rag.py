#!/usr/bin/env python3

import sys
import json
import math
import re
import sqlite3
import urllib.request
from pathlib import Path

DB = Path.home() / ".richmack-rag" / "rag.db"

OLLAMA = "http://richmack.local:11434"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "huihui_ai/granite4.1-abliterated:3b"

CHUNK_SIZE = 4000
OVERLAP = 500
RETRIEVE_LIMIT = 8

# ANSI colors
RESET   = "\033[0m"
BOLD    = "\033[1m"
CYAN    = "\033[36m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
MAGENTA = "\033[35m"
BLUE    = "\033[34m"
RED     = "\033[31m"
GRAY    = "\033[90m"


def progress(label, current, total, width=30, color=GREEN):
    if total <= 0:
        total = 1

    ratio = min(max(current / total, 0), 1)
    filled = int(width * ratio)

    bar = "█" * filled + "░" * (width - filled)
    percent = int(ratio * 100)

    print(
        f"\r{BOLD}{label:<18}{RESET} "
        f"{color}{bar}{RESET} "
        f"{BOLD}{percent:3d}%{RESET}",
        end="",
        flush=True
    )

    if current >= total:
        print()


def db():
    con = sqlite3.connect(DB)

    con.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY,
            path TEXT NOT NULL,
            chunk_no INTEGER NOT NULL,
            text TEXT NOT NULL,
            vector TEXT NOT NULL,
            UNIQUE(path, chunk_no)
        )
    """)

    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunks_path
        ON chunks(path)
    """)

    return con


def post(endpoint, payload):
    req = urllib.request.Request(
        OLLAMA + endpoint,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def embed(text):
    data = post(
        "/api/embed",
        {
            "model": EMBED_MODEL,
            "input": text
        }
    )

    vectors = data.get("embeddings", [])

    if not vectors:
        raise RuntimeError(
            "Embedding API returned no vector: " + repr(data)
        )

    return vectors[0]


def split_chunks(text):
    text = text.strip()

    start = 0
    number = 0

    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunk = text[start:end].strip()

        if chunk:
            yield number, chunk

        number += 1

        if end >= len(text):
            break

        start = max(0, end - OVERLAP)


def index_file(path):
    path = Path(path).expanduser().resolve()

    try:
        text = path.read_text(errors="ignore")
    except Exception as e:
        print(f"{RED}SKIP:{RESET} {path} {e}")
        return

    pieces = list(split_chunks(text))

    if not pieces:
        print(f"{YELLOW}EMPTY:{RESET} {path}")
        return

    con = db()

    con.execute(
        "DELETE FROM chunks WHERE path = ?",
        (str(path),)
    )

    print(
        f"\n{BOLD}{BLUE}Indexing:{RESET} {path}"
    )

    for i, (number, chunk) in enumerate(pieces, 1):
        progress(
            "Embedding",
            i - 1,
            len(pieces),
            color=GREEN
        )

        vector = embed(chunk)

        con.execute(
            """
            INSERT OR REPLACE INTO chunks
            (path, chunk_no, text, vector)
            VALUES (?, ?, ?, ?)
            """,
            (
                str(path),
                number,
                chunk,
                json.dumps(vector)
            )
        )

        progress(
            "Embedding",
            i,
            len(pieces),
            color=GREEN
        )

    con.commit()
    con.close()

    print(
        f"{GREEN}{BOLD}✓ Indexed{RESET} "
        f"{len(pieces)} chunks"
    )


def index_path(root):
    root = Path(root).expanduser().resolve()

    allowed = {
        ".txt",
        ".md",
        ".markdown",
        ".rst",
        ".log",
        ".csv",
        ".json",
        ".yaml",
        ".yml",
        ".html"
    }

    if root.is_file():
        index_file(root)
        return

    files = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in allowed:
            continue

        if ".git" in path.parts:
            continue

        files.append(path)

    print(
        f"{BOLD}Found {len(files)} indexable files.{RESET}"
    )

    for i, path in enumerate(files, 1):
        print(
            f"\n{MAGENTA}[{i}/{len(files)}]{RESET}"
        )
        index_file(path)


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))

    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))

    if not na or not nb:
        return 0.0

    return dot / (na * nb)


def query_terms(question):
    words = set(
        re.findall(
            r"[a-z0-9][a-z0-9._+-]*",
            question.lower()
        )
    )

    aliases = {
        "ram": {
            "ram", "memory", "mem", "gib", "mib",
            "gb", "mb", "total"
        },
        "memory": {
            "ram", "memory", "mem", "gib", "mib",
            "gb", "mb", "total"
        },
        "cpu": {
            "cpu", "processor", "model", "mhz",
            "ghz", "core", "cores", "athlon"
        },
        "processor": {
            "cpu", "processor", "model", "mhz",
            "ghz", "core", "cores", "athlon"
        }
    }

    expanded = set(words)

    for word in list(words):
        expanded.update(aliases.get(word, set()))

    return expanded


def lexical_score(question, text):
    terms = query_terms(question)

    if not terms:
        return 0.0

    lower = text.lower()

    hits = sum(
        1 for term in terms
        if term in lower
    )

    return min(
        1.0,
        hits / max(3, min(len(terms), 8))
    )


def retrieve(question, limit=RETRIEVE_LIMIT):
    print()

    progress(
        "Query embedding",
        0,
        1,
        color=BLUE
    )

    qvec = embed(question)

    progress(
        "Query embedding",
        1,
        1,
        color=BLUE
    )

    con = db()

    rows = con.execute(
        "SELECT path, chunk_no, text, vector FROM chunks"
    ).fetchall()

    con.close()

    if not rows:
        return []

    scored = []
    total = len(rows)

    for i, (path, number, text, vector) in enumerate(rows, 1):
        try:
            vec = json.loads(vector)

            semantic = cosine(qvec, vec)
            lexical = lexical_score(question, text)

            # Hybrid retrieval:
            # semantic understanding + exact technical keyword matching.
            score = (
                0.65 * semantic +
                0.35 * lexical
            )

            scored.append(
                (score, path, number, text)
            )

        except Exception:
            pass

        if (
            i == total
            or i == 1
            or i % max(1, total // 30) == 0
        ):
            progress(
                "Searching",
                i,
                total,
                color=GREEN
            )

    scored.sort(
        reverse=True,
        key=lambda x: x[0]
    )

    return scored[:limit]

def confidence_score(matches):
    """
    Retrieval confidence, not factual certainty.

    Weighted from the strongest three cosine similarities.
    """

    if not matches:
        return 0

    scores = [
        max(0.0, min(1.0, m[0]))
        for m in matches[:3]
    ]

    weights = [0.60, 0.25, 0.15]

    weighted = 0.0
    used = 0.0

    for score, weight in zip(scores, weights):
        weighted += score * weight
        used += weight

    if not used:
        return 0

    return round((weighted / used) * 100)


def confidence_label(score):
    if score >= 80:
        return "HIGH", GREEN

    if score >= 60:
        return "MEDIUM", YELLOW

    return "LOW", RED


def ask(question):
    matches = retrieve(question)

    if not matches:
        print(
            f"{RED}No indexed documents found.{RESET}"
        )
        return

    print()
    progress(
        "Preparing context",
        1,
        1,
        color=MAGENTA
    )

    context_parts = []

    for ref, (score, path, number, text) in enumerate(
        matches,
        1
    ):
        context_parts.append(
            f"""
REFERENCE [{ref}]
FILE: {path}
CHUNK: {number}
SIMILARITY: {score:.4f}

{text}
""".strip()
        )

    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""
You are answering questions about the user's indexed documents.

Use the supplied document context as the source of truth.

IMPORTANT:
System reports, command output, tables, labels, and key/value lines are
explicit factual evidence.

For example:
"Model name: AMD Athlon Processor LE-1640" explicitly identifies the CPU.
"Mem: 2.8Gi" explicitly states approximately 2.8 GiB of installed/visible RAM.

Read technical output literally. Do not claim information is absent when
a labeled field or table row contains the requested value.

If the requested information appears anywhere in the context,
answer directly and naturally.

You may combine facts from multiple references.

Cite supporting information inline using reference markers such as:
[1]
[2]
[1][3]

Only cite references actually supplied below.

Do not claim information is missing if the relevant facts are
present in the supplied context.

If the context truly does not contain enough information, say:
"The indexed documents do not contain enough information to answer that."

Keep the answer concise and factual.

QUESTION:
{question}

DOCUMENT CONTEXT:
{context}
"""

    print()
    progress(
        "Generating answer",
        0,
        1,
        color=CYAN
    )

    data = post(
        "/api/generate",
        {
            "model": CHAT_MODEL,
            "prompt": prompt,
            "stream": False
        }
    )

    progress(
        "Generating answer",
        1,
        1,
        color=CYAN
    )

    answer = data.get(
        "response",
        ""
    ).strip()

    confidence = confidence_score(matches)
    label, label_color = confidence_label(confidence)

    print()
    print(
        f"{BOLD}{CYAN}"
        f"╭─ RICHMACK AI ─────────────────────────────"
        f"{RESET}"
    )

    print(
        f"{BOLD}{CYAN}{answer}{RESET}"
    )

    print(
        f"{BOLD}{CYAN}"
        f"╰────────────────────────────────────────────"
        f"{RESET}"
    )

    print()

    print(
        f"{BOLD}Evidence match:{RESET} "
        f"{label_color}{BOLD}"
        f"{confidence}% ({label})"
        f"{RESET}"
    )

    print(
        f"{GRAY}"
        f"Confidence reflects document similarity, "
        f"not guaranteed factual accuracy."
        f"{RESET}"
    )

    print()
    print(
        f"{BOLD}{MAGENTA}References{RESET}"
    )

    for ref, (score, path, number, text) in enumerate(
        matches,
        1
    ):
        print(
            f"{MAGENTA}[{ref}]{RESET} "
            f"{BOLD}{path}{RESET}"
        )

        print(
            f"    chunk {number}  "
            f"similarity={score:.4f}"
        )


def search(question):
    matches = retrieve(question)

    if not matches:
        print("No matching chunks found.")
        return

    print()

    for rank, (score, path, number, text) in enumerate(
        matches,
        1
    ):
        print(
            f"{BOLD}{MAGENTA}"
            f"=== MATCH {rank} ==="
            f"{RESET}"
        )

        print(
            f"{YELLOW}similarity:{RESET} "
            f"{score:.4f}"
        )

        print(
            f"{CYAN}path:{RESET} "
            f"{path}"
        )

        print(
            f"{BLUE}chunk:{RESET} "
            f"{number}"
        )

        print()

        print(
            text[:1500]
        )

        print()


def stats():
    con = db()

    chunks_count = con.execute(
        "SELECT COUNT(*) FROM chunks"
    ).fetchone()[0]

    files_count = con.execute(
        "SELECT COUNT(DISTINCT path) FROM chunks"
    ).fetchone()[0]

    con.close()

    print(
        f"{BOLD}{CYAN}Richmack RAG Index{RESET}"
    )

    print(
        f"Files:    {GREEN}{files_count}{RESET}"
    )

    print(
        f"Chunks:   {GREEN}{chunks_count}{RESET}"
    )

    print(
        f"Database: {MAGENTA}{DB}{RESET}"
    )

    print(
        f"Embedder: {BLUE}{EMBED_MODEL}{RESET}"
    )

    print(
        f"LLM:      {BLUE}{CHAT_MODEL}{RESET}"
    )


def main():
    if len(sys.argv) < 2:
        print(
f"""{BOLD}{CYAN}Richmack RAG{RESET}

Usage:
  richmackrag index PATH
  richmackrag ask QUESTION
  richmackrag search QUESTION
  richmackrag stats
"""
        )
        return

    command = sys.argv[1]

    if command == "index":
        if len(sys.argv) < 3:
            raise SystemExit(
                "Usage: richmackrag index PATH"
            )

        index_path(sys.argv[2])

    elif command == "ask":
        if len(sys.argv) < 3:
            raise SystemExit(
                "Usage: richmackrag ask QUESTION"
            )

        ask(
            " ".join(sys.argv[2:])
        )

    elif command == "search":
        if len(sys.argv) < 3:
            raise SystemExit(
                "Usage: richmackrag search QUESTION"
            )

        search(
            " ".join(sys.argv[2:])
        )

    elif command == "stats":
        stats()

    else:
        raise SystemExit(
            "Unknown command: " + command
        )


if __name__ == "__main__":
    main()
