#!/usr/bin/env python3

import argparse
import json
import math
import sqlite3
import urllib.request
from pathlib import Path

HOME = Path.home()
DB = HOME / ".richmack-rag" / "rag.db"

OLLAMA = "http://richmack.local:11434"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "huihui_ai/granite4.1-abliterated:3b"

RESET   = "\033[0m"
BOLD    = "\033[1m"
CYAN    = "\033[36m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
MAGENTA = "\033[35m"
RED     = "\033[31m"
GRAY    = "\033[90m"

SCOPES = {
    "youtube": [
        str(HOME / "Knowledge-Inbox" / "YouTube") + "/%",
    ],

    "projects": [
        str(HOME / "Projects") + "/%",
        str(HOME / "RichmackOS") + "/%",
    ],

    "system": [
        str(HOME / "Readme") + "/%",
        str(HOME / "computer-specs.txt"),
    ],
}


def post(endpoint, payload):
    req = urllib.request.Request(
        OLLAMA + endpoint,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def embed(text):
    data = post(
        "/api/embed",
        {
            "model": EMBED_MODEL,
            "input": text,
        },
    )

    vectors = data.get("embeddings", [])

    if not vectors:
        raise RuntimeError("No embedding returned.")

    return vectors[0]


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))

    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))

    if not na or not nb:
        return 0.0

    return dot / (na * nb)


def load_rows(scope):
    con = sqlite3.connect(DB)

    if scope == "all":
        rows = con.execute(
            """
            SELECT path, chunk_no, text, vector
            FROM chunks
            """
        ).fetchall()

    elif scope == "docs":
        knowledge = str(HOME / "Knowledge-Inbox") + "/%"
        youtube = str(HOME / "Knowledge-Inbox" / "YouTube") + "/%"
        documents = str(HOME / "Documents") + "/%"

        rows = con.execute(
            """
            SELECT path, chunk_no, text, vector
            FROM chunks
            WHERE
                (path LIKE ? AND path NOT LIKE ?)
                OR path LIKE ?
            """,
            (
                knowledge,
                youtube,
                documents,
            ),
        ).fetchall()

    else:
        patterns = SCOPES.get(scope)

        if not patterns:
            con.close()
            raise RuntimeError(
                f"Unknown scope: {scope}"
            )

        clauses = []
        params = []

        for pattern in patterns:
            if "%" in pattern:
                clauses.append("path LIKE ?")
            else:
                clauses.append("path = ?")

            params.append(pattern)

        sql = (
            "SELECT path, chunk_no, text, vector "
            "FROM chunks WHERE "
            + " OR ".join(clauses)
        )

        rows = con.execute(
            sql,
            params,
        ).fetchall()

    con.close()
    return rows


def retrieve(scope, question, limit=8):
    qvec = embed(question)
    rows = load_rows(scope)

    scored = []

    for path, chunk_no, text, vector_json in rows:
        try:
            vector = json.loads(vector_json)
            score = cosine(qvec, vector)

            scored.append(
                (
                    score,
                    path,
                    chunk_no,
                    text,
                )
            )

        except Exception:
            continue

    scored.sort(
        reverse=True,
        key=lambda x: x[0],
    )

    return scored[:limit]


def evidence_score(matches):
    if not matches:
        return 0

    top = [
        max(0.0, min(1.0, m[0]))
        for m in matches[:3]
    ]

    if len(top) == 1:
        score = top[0]

    elif len(top) == 2:
        score = (
            top[0] * 0.70
            + top[1] * 0.30
        )

    else:
        score = (
            top[0] * 0.60
            + top[1] * 0.25
            + top[2] * 0.15
        )

    return round(score * 100)


def ask(scope, question):
    print(
        f"{GRAY}"
        f"RAG scope: {scope}"
        f"{RESET}"
    )

    print(
        f"{GRAY}"
        f"Embedding question and searching scoped knowledge..."
        f"{RESET}"
    )

    matches = retrieve(
        scope,
        question,
    )

    if not matches:
        print(
            f"{RED}"
            f"No indexed chunks found in scope '{scope}'."
            f"{RESET}"
        )
        return

    context = []

    for i, (score, path, chunk_no, text) in enumerate(matches, 1):
        context.append(
            f"""REFERENCE [{i}]
SOURCE: {path}
CHUNK: {chunk_no}
SIMILARITY: {score:.4f}

{text}"""
        )

    joined = "\n\n---\n\n".join(context)

    prompt = f"""
You are answering a question using a scoped local knowledge base.

ACTIVE SCOPE:
{scope}

Use ONLY the supplied context.

Do not use outside knowledge unless the question explicitly asks for
interpretation, and never substitute unrelated documents for relevant ones.

If the answer is present, answer directly.

Cite factual claims with reference markers such as [1], [2], or [1][3].

If the context truly does not contain enough information, say:
"The selected RAG scope does not contain enough information to answer that."

QUESTION:
{question}

CONTEXT:
{joined}
"""

    data = post(
        "/api/generate",
        {
            "model": CHAT_MODEL,
            "prompt": prompt,
            "stream": False,
        },
    )

    answer = data.get(
        "response",
        "",
    ).strip()

    score = evidence_score(matches)

    if score >= 75:
        label = "HIGH"
        color = GREEN

    elif score >= 55:
        label = "MEDIUM"
        color = YELLOW

    else:
        label = "LOW"
        color = RED

    print()

    print(
        f"{BOLD}{CYAN}"
        f"╭─ RICHMACK SCOPED RAG ─────────────────────"
        f"{RESET}"
    )

    print(
        f"{BOLD}{CYAN}"
        f"{answer}"
        f"{RESET}"
    )

    print(
        f"{BOLD}{CYAN}"
        f"╰────────────────────────────────────────────"
        f"{RESET}"
    )

    print()

    print(
        f"{BOLD}Evidence match:{RESET} "
        f"{color}{score}% ({label}){RESET}"
    )

    print(
        f"{GRAY}"
        f"Evidence match reflects retrieval relevance, "
        f"not guaranteed factual accuracy."
        f"{RESET}"
    )

    print()
    print(
        f"{BOLD}{MAGENTA}References{RESET}"
    )

    for i, (sim, path, chunk_no, text) in enumerate(matches, 1):
        print(
            f"{MAGENTA}[{i}]{RESET} "
            f"{path}"
        )

        print(
            f"    chunk {chunk_no} "
            f"similarity={sim:.4f}"
        )


def main():
    parser = argparse.ArgumentParser(
        prog="richmack rag",
        description="Query a scoped RichmackOS RAG namespace.",
    )

    parser.add_argument(
        "--scope",
        required=True,
        choices=[
            "all",
            "youtube",
            "docs",
            "projects",
            "system",
        ],
        help="Knowledge namespace to search",
    )

    parser.add_argument(
        "question",
        nargs="+",
        help="Question to ask",
    )

    args = parser.parse_args()

    ask(
        args.scope,
        " ".join(args.question),
    )


if __name__ == "__main__":
    main()
