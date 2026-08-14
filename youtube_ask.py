#!/usr/bin/env python3

import argparse
import datetime
import json
import math
import re
import sqlite3
import urllib.request
from pathlib import Path

HOME = Path.home()

RAG_DB = HOME / ".richmack-rag" / "rag.db"
YT_ROOT = HOME / "Knowledge-Inbox" / "YouTube"

OLLAMA = "http://richmack.local:11434"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "huihui_ai/granite4.1-abliterated:3b"

CHANNELS = {
    "danny-jones": "Danny Jones",
    "tim-ferriss": "Tim Ferriss",
    "poetik-flakko": "Poetik Flakko",
    "vladtv": "VladTV",
    "fireship": "Fireship",
    "esoterica": "ESOTERICA",
    "chill-dude-explains": "Chill Dude Explains",
}

RESET   = "\033[0m"
BOLD    = "\033[1m"
CYAN    = "\033[36m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
MAGENTA = "\033[35m"
RED     = "\033[31m"
GRAY    = "\033[90m"


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


def normalize_name(text):
    return re.sub(
        r"[^a-z0-9]+",
        "-",
        text.lower(),
    ).strip("-")


def find_channel_dir(key):
    if key not in CHANNELS:
        raise SystemExit(
            "Unknown channel.\n"
            "Use: richmack youtube channels"
        )

    wanted = normalize_name(
        CHANNELS[key]
    )

    if not YT_ROOT.exists():
        raise SystemExit(
            "YouTube transcript root does not exist."
        )

    for path in YT_ROOT.iterdir():
        if not path.is_dir():
            continue

        if normalize_name(path.name) == wanted:
            return path

    raise SystemExit(
        f"No transcript directory found for {CHANNELS[key]}.\n"
        f"Run: richmack youtube sync --channel {key} --limit 1"
    )


def transcript_metadata(path):
    try:
        text = path.read_text(
            errors="ignore"
        )[:12000]

    except Exception:
        return {}

    meta = {}

    for line in text.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(
            ":",
            1,
        )

        key = key.strip().upper()

        if key in {
            "TITLE",
            "CHANNEL",
            "CHANNEL_KEY",
            "VIDEO_ID",
            "URL",
            "UPLOAD_DATE",
            "DURATION",
        }:
            meta[key] = value.strip()

    return meta


def parse_upload_date(path):
    meta = transcript_metadata(path)
    value = meta.get("UPLOAD_DATE", "")

    if re.fullmatch(r"\d{8}", value):
        try:
            return datetime.datetime.strptime(
                value,
                "%Y%m%d",
            ).date()
        except Exception:
            pass

    try:
        return datetime.datetime.fromtimestamp(
            path.stat().st_mtime
        ).date()

    except Exception:
        return datetime.date.min


def _filter_files_by_video(
    files,
    video
):
    if not video:
        return files

    return [
        path
        for path in files
        if (
            path.stem == video
            or transcript_metadata(
                path
            ).get(
                "VIDEO_ID"
            ) == video
        )
    ]


def _filter_files_since(
    files,
    since
):
    if not since:
        return files

    since_date = (
        datetime.datetime.strptime(
            since,
            "%Y-%m-%d",
        ).date()
    )

    return [
        path
        for path in files
        if parse_upload_date(
            path
        ) >= since_date
    ]


def _filter_files_by_days(
    files,
    days
):
    if days is None:
        return files

    cutoff = (
        datetime.date.today()
        - datetime.timedelta(
            days=days
        )
    )

    return [
        path
        for path in files
        if parse_upload_date(
            path
        ) >= cutoff
    ]


def _sort_candidate_files(
    files
):
    return sorted(
        files,
        key=parse_upload_date,
        reverse=True,
    )


def candidate_files(
    channel_dir,
    latest=False,
    days=None,
    since=None,
    video=None,
):
    files = list(
        channel_dir.glob(
            "*.txt"
        )
    )

    if not files:
        return []

    files = _filter_files_by_video(
        files,
        video
    )

    files = _filter_files_since(
        files,
        since
    )

    files = _filter_files_by_days(
        files,
        days
    )

    files = _sort_candidate_files(
        files
    )

    if latest and files:
        return [
            files[0]
        ]

    return files


def retrieve(question, files, limit=8):
    if not files:
        return []

    qvec = embed(question)

    con = sqlite3.connect(RAG_DB)

    rows = []

    for path in files:
        rows.extend(
            con.execute(
                """
                SELECT path, chunk_no, text, vector
                FROM chunks
                WHERE path = ?
                """,
                (str(path.resolve()),),
            ).fetchall()
        )

    con.close()

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


def ask(args):
    channel_dir = find_channel_dir(
        args.channel
    )

    files = candidate_files(
        channel_dir,
        latest=args.latest,
        days=args.days,
        since=args.since,
        video=args.video,
    )

    if not files:
        print(
            f"{RED}"
            f"No transcript files match the requested filter."
            f"{RESET}"
        )
        return

    print(
        f"{GRAY}"
        f"Channel: {CHANNELS[args.channel]}"
        f"{RESET}"
    )

    print(
        f"{GRAY}"
        f"Transcript scope: {len(files)} video(s)"
        f"{RESET}"
    )

    if args.latest:
        print(
            f"{GRAY}"
            f"Filter: latest"
            f"{RESET}"
        )

    if args.days is not None:
        print(
            f"{GRAY}"
            f"Filter: last {args.days} day(s)"
            f"{RESET}"
        )

    if args.since:
        print(
            f"{GRAY}"
            f"Filter: since {args.since}"
            f"{RESET}"
        )

    if args.video:
        print(
            f"{GRAY}"
            f"Filter: video {args.video}"
            f"{RESET}"
        )

    print(
        f"{GRAY}"
        f"Embedding question and searching selected transcripts..."
        f"{RESET}"
    )

    question = " ".join(
        args.question
    )

    matches = retrieve(
        question,
        files,
    )

    if not matches:
        print(
            f"{RED}"
            f"No indexed RAG chunks found for the selected transcripts."
            f"{RESET}"
        )

        print(
            f"{GRAY}"
            f"Try indexing the channel directory manually:"
            f"{RESET}"
        )

        print(
            f"richmackrag index \"{channel_dir}\""
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
You are answering a question using selected YouTube transcripts.

CHANNEL:
{CHANNELS[args.channel]}

Use ONLY the supplied YouTube transcript context.

Do not use RichmackOS documentation or unrelated documents.

Read transcript metadata such as TITLE, CHANNEL, VIDEO_ID, URL,
UPLOAD_DATE, DURATION, DESCRIPTION, and TRANSCRIPT.

When multiple videos are supplied, synthesize across them when useful.

Cite factual statements using [1], [2], etc.

QUESTION:
{question}

YOUTUBE TRANSCRIPT CONTEXT:
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

    score = evidence_score(
        matches
    )

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
        f"╭─ RICHMACK YOUTUBE AI ─────────────────────"
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

    print()

    print(
        f"{BOLD}{MAGENTA}"
        f"References"
        f"{RESET}"
    )

    for i, (sim, path, chunk_no, text) in enumerate(matches, 1):
        meta = transcript_metadata(
            Path(path)
        )

        title = meta.get(
            "TITLE",
            Path(path).stem,
        )

        date = meta.get(
            "UPLOAD_DATE",
            "",
        )

        print(
            f"{MAGENTA}[{i}]{RESET} "
            f"{title}"
        )

        print(
            f"    {path}"
        )

        if date:
            print(
                f"    upload={date}"
            )

        print(
            f"    chunk={chunk_no} "
            f"similarity={sim:.4f}"
        )


def main():
    parser = argparse.ArgumentParser(
        prog="richmack youtube ask",
        description="Ask questions over filtered YouTube transcripts.",
    )

    parser.add_argument(
        "channel",
        choices=sorted(CHANNELS),
    )

    parser.add_argument(
        "--latest",
        action="store_true",
        help="Use only the newest matching transcript",
    )

    parser.add_argument(
        "--days",
        type=int,
        help="Use videos uploaded within the last N days",
    )

    parser.add_argument(
        "--since",
        metavar="YYYY-MM-DD",
        help="Use videos uploaded on or after a date",
    )

    parser.add_argument(
        "--video",
        help="Use one YouTube video ID",
    )

    parser.add_argument(
        "question",
        nargs="+",
    )

    args = parser.parse_args()

    ask(args)


if __name__ == "__main__":
    main()
