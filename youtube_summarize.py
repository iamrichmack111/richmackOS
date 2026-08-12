#!/usr/bin/env python3

import argparse
import datetime
import json
import urllib.request
from pathlib import Path

HOME = Path.home()
BASE = HOME / ".richmackos"
CHANNELS_FILE = BASE / "youtube-channels.json"
YT_ROOT = HOME / "Knowledge-Inbox" / "YouTube"

OLLAMA = "http://richmack.local:11434"
MODEL = "gemma3:4b"

RESET   = "\033[0m"
BOLD    = "\033[1m"
CYAN    = "\033[36m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
MAGENTA = "\033[35m"
GRAY    = "\033[90m"
RED     = "\033[31m"


def load_channels():
    return json.loads(
        CHANNELS_FILE.read_text(
            encoding="utf-8"
        )
    )


def post(payload):
    req = urllib.request.Request(
        OLLAMA + "/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


def normalize(text):
    return "".join(
        ch.lower() if ch.isalnum() else "-"
        for ch in text
    ).strip("-")


def find_channel_dir(name):
    wanted = normalize(name)

    for path in YT_ROOT.iterdir():
        if path.is_dir() and normalize(path.name) == wanted:
            return path

    return None


def parse_date(path):
    try:
        text = path.read_text(
            errors="ignore"
        )[:5000]

        for line in text.splitlines():
            if line.startswith("UPLOAD_DATE:"):
                value = line.split(":", 1)[1].strip()

                if len(value) == 8 and value.isdigit():
                    return datetime.datetime.strptime(
                        value,
                        "%Y%m%d"
                    ).date()

    except Exception:
        pass

    return datetime.datetime.fromtimestamp(
        path.stat().st_mtime
    ).date()


def select_files(channel_dir, days=None, limit=None):
    files = list(
        channel_dir.glob("*.txt")
    )

    files.sort(
        key=parse_date,
        reverse=True
    )

    if days is not None:
        cutoff = (
            datetime.date.today()
            - datetime.timedelta(days=days)
        )

        files = [
            f for f in files
            if parse_date(f) >= cutoff
        ]

    if limit is not None:
        files = files[:limit]

    return files


def read_transcripts(files, max_chars=50000):
    parts = []
    used = 0

    for path in files:
        try:
            text = path.read_text(
                errors="ignore"
            )
        except Exception:
            continue

        remaining = max_chars - used

        if remaining <= 0:
            break

        text = text[:remaining]

        parts.append(
            f"\n=== SOURCE: {path.name} ===\n{text}\n"
        )

        used += len(text)

    return "\n".join(parts)


def summarize_channel(key, config, days=None, limit=None):
    channel_dir = find_channel_dir(
        config["name"]
    )

    if not channel_dir:
        print(
            f"{RED}No transcript directory found for "
            f"{config['name']}.{RESET}"
        )
        return

    files = select_files(
        channel_dir,
        days=days,
        limit=limit
    )

    if not files:
        print(
            f"{YELLOW}No transcripts match filters for "
            f"{config['name']}.{RESET}"
        )
        return

    corpus = read_transcripts(files)

    prompt = f"""
You are creating a detailed research brief from YouTube transcripts.

CHANNEL:
{config["name"]}

TRANSCRIPTS ANALYZED:
{len(files)}

IMPORTANT OUTPUT RULES:

You MUST use every section below.
Do not collapse the answer into one paragraph.
Use clear headings exactly as written.
Use bullet points where appropriate.
Be detailed.
Use only the supplied transcripts and transcript metadata.
Do not invent resources, links, names, claims, or references.

CHANNEL OVERVIEW
Write 2-4 substantial paragraphs explaining the overall subject matter,
style, recurring concerns, and what the selected videos are trying to teach.

DETAILED SUMMARY
Write a detailed multi-paragraph synthesis of the selected videos.
Explain major arguments, examples, procedures, stories, advice,
warnings, distinctions, and recurring ideas.

KEY THEMES
Provide 6-15 major themes.
For each theme, give a 1-3 sentence explanation.

KEYWORDS
Provide 20-40 useful keywords, phrases, named concepts, technical terms,
legal terms, medical terms, books, organizations, technologies, or people
that appear in or are clearly supported by the transcripts.

TAGS
Provide 10-20 concise hashtag-style tags.

RESOURCES MENTIONED
Extract specific resources explicitly mentioned in the transcripts or
video metadata.

Include, when present:
- websites
- URLs
- books
- articles
- studies
- apps
- software
- tools
- organizations
- agencies
- creators
- channels
- products
- courses
- hotlines
- legal phrases
- medical techniques
- named frameworks
- named procedures
- research institutions

For every resource, provide:
- resource name
- what it is
- why it was mentioned
- any URL or exact identifying information present in the transcript

If a URL is not present, DO NOT invent one.

THINGS TO LOOK UP
Provide 10-25 concrete follow-up research items.

These should be specific enough to search for directly.
Prefer named concepts, organizations, books, studies, procedures,
legal doctrines, medical techniques, or technologies actually mentioned
or strongly implied by the transcript.

NOTABLE CLAIMS
List the strongest or most interesting claims made in the videos.
Label them as claims from the transcript rather than verified facts.

PRACTICAL TAKEAWAYS
Provide actionable lessons or procedures from the videos.

QUESTIONS RAISED
List unresolved questions, uncertainties, debates, risks, or limitations.

SOURCE VIDEOS
For each transcript analyzed, list:
- title
- video ID
- upload date
- URL
when available from the transcript header.

TRANSCRIPTS:
{corpus}
"""

    data = post({
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    })

    answer = data.get(
        "response",
        ""
    ).strip()

    print()
    print(
        f"{BOLD}{CYAN}"
        f"╭─ {config['name']} RESEARCH BRIEF ─"
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

    print(
        f"{GRAY}"
        f"Transcripts analyzed: {len(files)}"
        f"{RESET}"
    )


def main():
    parser = argparse.ArgumentParser(
        prog="richmack youtube summarize",
        description="Create detailed research briefs from YouTube transcripts."
    )

    parser.add_argument(
        "channel",
        nargs="?",
        help="Channel key"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Summarize every configured channel"
    )

    parser.add_argument(
        "--days",
        type=int,
        help="Only include transcripts from the last N days"
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum transcripts per channel"
    )

    args = parser.parse_args()

    channels = load_channels()

    if args.all:
        for key, config in channels.items():
            summarize_channel(
                key,
                config,
                days=args.days,
                limit=args.limit
            )
        return

    if not args.channel:
        raise SystemExit(
            "Provide a channel key or use --all"
        )

    if args.channel not in channels:
        raise SystemExit(
            "Unknown channel. Use: richmack youtube channels"
        )

    summarize_channel(
        args.channel,
        channels[args.channel],
        days=args.days,
        limit=args.limit
    )


if __name__ == "__main__":
    main()
