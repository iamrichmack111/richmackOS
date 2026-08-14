#!/usr/bin/env python3

import argparse
import datetime
import json
import re
import shutil
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

HOME = Path.home()

BASE = HOME / ".richmackos"
CHANNELS_FILE = BASE / "youtube-channels.json"
YT_ROOT = HOME / "Knowledge-Inbox" / "YouTube"
RESEARCH_ROOT = HOME / "Knowledge" / "Research" / "youtube"

OLLAMA = "http://richmack.local:11434"
DEFAULT_MODEL = "gemma3:4b"

RESET   = "\033[0m"
BOLD    = "\033[1m"
CYAN    = "\033[36m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
MAGENTA = "\033[35m"
BLUE    = "\033[34m"
RED     = "\033[31m"
GRAY    = "\033[90m"


###############################################################################
# TERMINAL UI
###############################################################################

def bar(label, percent, color=CYAN, width=30):
    percent = max(0, min(100, int(percent)))

    filled = int(
        width * percent / 100
    )

    graph = (
        "█" * filled
        + "░" * (width - filled)
    )

    print(
        f"\r{BOLD}{label:<22}{RESET} "
        f"{color}{graph}{RESET} "
        f"{BOLD}{percent:3d}%{RESET}",
        end="",
        flush=True
    )

    if percent >= 100:
        print()


def wait_bar(label, start, end, thread, color=MAGENTA):
    value = start

    while thread.is_alive():
        bar(
            label,
            value,
            color
        )

        if value < end - 1:
            value += 1

        time.sleep(0.25)

    thread.join()

    bar(
        label,
        end,
        GREEN
    )


###############################################################################
# CHANNELS
###############################################################################

def load_channels():
    return json.loads(
        CHANNELS_FILE.read_text(
            encoding="utf-8"
        )
    )


def normalize(value):
    return re.sub(
        r"[^a-z0-9]+",
        "-",
        value.lower()
    ).strip("-")


def find_channel_dir(name):
    wanted = normalize(name)

    if not YT_ROOT.exists():
        return None

    for path in YT_ROOT.iterdir():
        if (
            path.is_dir()
            and normalize(path.name) == wanted
        ):
            return path

    return None


###############################################################################
# TRANSCRIPT METADATA
###############################################################################

def transcript_metadata(path):
    meta = {}

    try:
        text = path.read_text(
            errors="ignore"
        )[:12000]
    except Exception:
        return meta

    for line in text.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(
            ":",
            1
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


def upload_date(path):
    meta = transcript_metadata(path)
    value = meta.get(
        "UPLOAD_DATE",
        ""
    )

    if re.fullmatch(
        r"\d{8}",
        value
    ):
        try:
            return datetime.datetime.strptime(
                value,
                "%Y%m%d"
            ).date()
        except Exception:
            pass

    return datetime.datetime.fromtimestamp(
        path.stat().st_mtime
    ).date()


def select_transcripts(
    directory,
    limit=None,
    days=None
):
    files = list(
        directory.glob("*.txt")
    )

    files.sort(
        key=upload_date,
        reverse=True
    )

    if days is not None:
        cutoff = (
            datetime.date.today()
            - datetime.timedelta(
                days=days
            )
        )

        files = [
            path
            for path in files
            if upload_date(path) >= cutoff
        ]

    if limit is not None:
        files = files[:limit]

    return files


###############################################################################
# CORPUS
###############################################################################

def build_corpus(
    files,
    max_chars=80000
):
    pieces = []
    used = 0

    for path in files:
        try:
            content = path.read_text(
                errors="ignore"
            )
        except Exception:
            continue

        remaining = (
            max_chars - used
        )

        if remaining <= 0:
            break

        content = content[:remaining]

        pieces.append(
            f"""
==================================================
SOURCE FILE: {path.name}
==================================================

{content}
"""
        )

        used += len(content)

    return "\n".join(pieces)


###############################################################################
# OLLAMA
###############################################################################

def ollama_generate(
    model,
    prompt,
    output_holder,
    error_holder
):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1
        }
    }

    req = urllib.request.Request(
        OLLAMA + "/api/generate",
        data=json.dumps(
            payload
        ).encode(),
        headers={
            "Content-Type":
            "application/json"
        }
    )

    try:
        with urllib.request.urlopen(
            req,
            timeout=900
        ) as response:
            output_holder["response"] = (
                json.loads(
                    response.read()
                )
            )

    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode(
                errors="ignore"
            )
        except Exception:
            body = ""

        error_holder["error"] = (
            f"HTTP {e.code}: {body}"
        )

    except Exception as e:
        error_holder["error"] = str(e)


def parse_json_response(data):
    raw = data.get(
        "response",
        ""
    ).strip()

    try:
        return json.loads(raw)
    except Exception:
        pass

    # Fallback in case model wraps JSON.
    match = re.search(
        r"\{.*\}",
        raw,
        flags=re.DOTALL
    )

    if match:
        try:
            return json.loads(
                match.group(0)
            )
        except Exception:
            pass

    raise RuntimeError(
        "Model did not return valid JSON."
    )


def run_pass(
    model,
    prompt,
    label,
    start,
    end
):
    output = {}
    errors = {}

    thread = threading.Thread(
        target=ollama_generate,
        args=(
            model,
            prompt,
            output,
            errors
        ),
        daemon=True
    )

    thread.start()

    wait_bar(
        label,
        start,
        end,
        thread
    )

    if errors:
        raise RuntimeError(
            errors["error"]
        )

    return parse_json_response(
        output["response"]
    )


###############################################################################
# RESEARCH PASSES
###############################################################################

def summary_pass(
    model,
    channel,
    corpus
):
    prompt = f"""
You are analyzing YouTube transcripts from:

CHANNEL: {channel}

Return ONLY valid JSON.

Schema:

{{
  "channel_overview": "detailed multi-paragraph overview",
  "detailed_summary": "detailed multi-paragraph synthesis",
  "key_themes": [
    {{
      "theme": "name",
      "explanation": "detailed explanation"
    }}
  ],
  "practical_takeaways": [
    "specific takeaway"
  ]
}}

Requirements:

- use only supplied transcript material
- synthesize across videos
- preserve important details
- identify procedures, warnings, advice, arguments and examples
- do not ask the user follow-up questions
- do not invent information

TRANSCRIPTS:

{corpus}
"""

    return run_pass(
        model,
        prompt,
        "Pass 1: Summary",
        15,
        40
    )


def extraction_pass(
    model,
    channel,
    corpus
):
    prompt = f"""
You are performing structured knowledge extraction
from YouTube transcripts.

CHANNEL: {channel}

Return ONLY valid JSON.

Schema:

{{
  "keywords": [],
  "tags": [],
  "people": [
    {{
      "name": "",
      "context": ""
    }}
  ],
  "organizations": [
    {{
      "name": "",
      "context": ""
    }}
  ],
  "resources": [
    {{
      "name": "",
      "type": "",
      "why_mentioned": "",
      "url": "",
      "search_term": ""
    }}
  ],
  "books": [],
  "websites": [],
  "tools": [],
  "medical_terms": [],
  "legal_terms": [],
  "psychology_terms": [],
  "technologies": []
}}

RESOURCE EXTRACTION IS IMPORTANT.

Look in BOTH:
- video descriptions
- transcript speech

Resources can include:

- websites
- books
- articles
- papers
- studies
- apps
- software
- organizations
- agencies
- creators
- courses
- training programs
- products
- named procedures
- medical techniques
- legal doctrines
- psychological techniques
- research institutions
- tools
- URLs

Never invent a URL.

If a URL is not provided, use an empty string.

Provide approximately 20-40 useful keywords.

Provide approximately 10-20 tags.

TRANSCRIPTS:

{corpus}
"""

    return run_pass(
        model,
        prompt,
        "Pass 2: Extraction",
        40,
        68
    )


def research_pass(
    model,
    channel,
    corpus
):
    prompt = f"""
You are building a research roadmap from YouTube
transcripts.

CHANNEL: {channel}

Return ONLY valid JSON.

Schema:

{{
  "research_queries": [
    "specific search query"
  ],
  "notable_claims": [
    {{
      "claim": "",
      "context": "",
      "verification_needed": true
    }}
  ],
  "questions_raised": [
    "specific unresolved question"
  ],
  "topics_to_verify": [
    "specific item requiring independent verification"
  ],
  "connections": [
    {{
      "concept_a": "",
      "concept_b": "",
      "relationship": ""
    }}
  ]
}}

Generate 10-25 concrete research queries.

Good research queries are specific, such as:

"mammalian dive reflex anxiety clinical research"

"Stop the Bleed tourniquet training"

"crowd crush density engineering research"

Do not output vague phrases like:

"research safety"

Separate claims made by the creator from verified facts.

Use only the supplied material.

TRANSCRIPTS:

{corpus}
"""

    return run_pass(
        model,
        prompt,
        "Pass 3: Research",
        68,
        90
    )


###############################################################################
# SOURCE VIDEO DATA
###############################################################################

def source_videos(files):
    results = []

    for path in files:
        meta = transcript_metadata(
            path
        )

        results.append({
            "title": meta.get(
                "TITLE",
                path.stem
            ),
            "video_id": meta.get(
                "VIDEO_ID",
                path.stem
            ),
            "upload_date": meta.get(
                "UPLOAD_DATE",
                ""
            ),
            "url": meta.get(
                "URL",
                ""
            ),
            "file": str(path)
        })

    return results


###############################################################################
# MARKDOWN RENDERER
###############################################################################

def heading(title):
    return (
        "\n"
        + "=" * 72
        + "\n"
        + title
        + "\n"
        + "=" * 72
        + "\n"
    )


def _append_named_items(
    lines,
    title,
    items
):
    lines.append(
        f"\n## {title}\n"
    )

    for item in items:
        if isinstance(
            item,
            dict
        ):
            lines.append(
                f"- **{item.get('name', '')}** — "
                f"{item.get('context', '')}"
            )
        else:
            lines.append(
                f"- {item}"
            )


def _append_simple_list(
    lines,
    title,
    items,
    code=False
):
    lines.append(
        f"\n## {title}\n"
    )

    for item in items:
        if code:
            lines.append(
                f"- `{item}`"
            )
        else:
            lines.append(
                f"- {item}"
            )


def _append_key_themes(
    lines,
    summary
):
    lines.append(
        "\n## Key Themes\n"
    )

    for item in summary.get(
        "key_themes",
        []
    ):
        if isinstance(
            item,
            dict
        ):
            lines.append(
                f"- **{item.get('theme', '')}** — "
                f"{item.get('explanation', '')}"
            )
        else:
            lines.append(
                f"- {item}"
            )


def _format_tags(tags):
    return " ".join(
        tag
        if str(tag).startswith("#")
        else "#" + str(tag).replace(
            " ",
            "-"
        )
        for tag in tags
    )


def _append_resources(
    lines,
    resources
):
    lines.append(
        "\n## Resources Mentioned\n"
    )

    if not resources:
        lines.append(
            "No explicit resources extracted."
        )

    for item in resources:
        if not isinstance(
            item,
            dict
        ):
            lines.append(
                f"- {item}"
            )
            continue

        lines.append(
            f"\n### "
            f"{item.get('name', 'Unnamed resource')}"
        )

        lines.append(
            f"- **Type:** "
            f"{item.get('type', '')}"
        )

        lines.append(
            f"- **Why mentioned:** "
            f"{item.get('why_mentioned', '')}"
        )

        url = item.get(
            "url",
            ""
        )

        lines.append(
            f"- **URL:** "
            f"{url if url else 'not supplied'}"
        )

        lines.append(
            f"- **Search term:** "
            f"{item.get('search_term', '')}"
        )


def _append_category_sections(
    lines,
    extraction
):
    sections = (
        (
            "Books",
            "books"
        ),
        (
            "Websites",
            "websites"
        ),
        (
            "Tools",
            "tools"
        ),
        (
            "Medical Terms",
            "medical_terms"
        ),
        (
            "Legal Terms",
            "legal_terms"
        ),
        (
            "Psychology Terms",
            "psychology_terms"
        ),
        (
            "Technologies",
            "technologies"
        ),
    )

    for title, key in sections:
        values = extraction.get(
            key,
            []
        )

        if not values:
            continue

        _append_simple_list(
            lines,
            title,
            values
        )


def _append_notable_claims(
    lines,
    research
):
    lines.append(
        "\n## Notable Claims\n"
    )

    for item in research.get(
        "notable_claims",
        []
    ):
        if not isinstance(
            item,
            dict
        ):
            lines.append(
                f"- {item}"
            )
            continue

        lines.append(
            f"- **Claim:** "
            f"{item.get('claim', '')}"
        )

        if item.get(
            "context"
        ):
            lines.append(
                f"  - Context: "
                f"{item.get('context')}"
            )

        if item.get(
            "verification_needed"
        ):
            lines.append(
                "  - Verification: independent verification recommended"
            )


def _append_connections(
    lines,
    research
):
    lines.append(
        "\n## Concept Connections\n"
    )

    for item in research.get(
        "connections",
        []
    ):
        if not isinstance(
            item,
            dict
        ):
            continue

        lines.append(
            f"- **{item.get('concept_a', '')} ↔ "
            f"{item.get('concept_b', '')}** — "
            f"{item.get('relationship', '')}"
        )


def _append_source_videos(
    lines,
    videos
):
    lines.append(
        "\n## Source Videos\n"
    )

    for video in videos:
        lines.append(
            f"\n### {video['title']}"
        )

        lines.append(
            f"- Video ID: "
            f"`{video['video_id']}`"
        )

        lines.append(
            f"- Upload date: "
            f"{video['upload_date'] or 'unknown'}"
        )

        lines.append(
            f"- URL: "
            f"{video['url'] or 'not supplied'}"
        )


def _append_research_sections(
    lines,
    summary,
    research
):
    _append_simple_list(
        lines,
        "Things To Look Up",
        research.get(
            "research_queries",
            []
        ),
        code=True
    )

    _append_notable_claims(
        lines,
        research
    )

    _append_simple_list(
        lines,
        "Practical Takeaways",
        summary.get(
            "practical_takeaways",
            []
        )
    )

    _append_simple_list(
        lines,
        "Questions Raised",
        research.get(
            "questions_raised",
            []
        )
    )

    _append_simple_list(
        lines,
        "Topics To Verify",
        research.get(
            "topics_to_verify",
            []
        )
    )

    _append_connections(
        lines,
        research
    )


def render_markdown(data):
    """
    Render a complete channel research brief as Markdown.

    Individual section renderers keep formatting behavior
    isolated and independently testable.
    """

    lines = [
        f"# {data['channel']} Research Brief",
        f"\nGenerated: {data['generated_at']}",
        f"\nModel: `{data['model']}`",
        (
            f"\nTranscripts analyzed: "
            f"{len(data['source_videos'])}"
        ),
    ]

    summary = data["summary"]
    extraction = data["extraction"]
    research = data["research"]

    lines.append(
        "\n## Channel Overview\n"
    )

    lines.append(
        summary.get(
            "channel_overview",
            ""
        )
    )

    lines.append(
        "\n## Detailed Summary\n"
    )

    lines.append(
        summary.get(
            "detailed_summary",
            ""
        )
    )

    _append_key_themes(
        lines,
        summary
    )

    _append_simple_list(
        lines,
        "Keywords",
        extraction.get(
            "keywords",
            []
        )
    )

    lines.append(
        "\n## Tags\n"
    )

    lines.append(
        _format_tags(
            extraction.get(
                "tags",
                []
            )
        )
    )

    _append_resources(
        lines,
        extraction.get(
            "resources",
            []
        )
    )

    _append_named_items(
        lines,
        "People",
        extraction.get(
            "people",
            []
        )
    )

    _append_named_items(
        lines,
        "Organizations",
        extraction.get(
            "organizations",
            []
        )
    )

    _append_category_sections(
        lines,
        extraction
    )

    _append_research_sections(
        lines,
        summary,
        research
    )

    _append_source_videos(
        lines,
        data["source_videos"]
    )

    return "\n".join(
        lines
    ) + "\n"


###############################################################################
# SAVE
###############################################################################

def save_research(
    channel_key,
    data
):
    directory = (
        RESEARCH_ROOT
        / channel_key
    )

    directory.mkdir(
        parents=True,
        exist_ok=True
    )

    stamp = datetime.datetime.now().strftime(
        "%Y-%m-%d_%H%M%S"
    )

    json_path = (
        directory
        / f"{stamp}.json"
    )

    md_path = (
        directory
        / f"{stamp}.md"
    )

    json_path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        )
        + "\n",
        encoding="utf-8"
    )

    md_text = render_markdown(
        data
    )

    md_path.write_text(
        md_text,
        encoding="utf-8"
    )

    latest_json = (
        directory
        / "latest.json"
    )

    latest_md = (
        directory
        / "latest.md"
    )

    shutil.copy2(
        json_path,
        latest_json
    )

    shutil.copy2(
        md_path,
        latest_md
    )

    return (
        md_path,
        json_path,
        latest_md,
        latest_json
    )


###############################################################################
# RUN CHANNEL
###############################################################################

def research_channel(
    key,
    config,
    model,
    limit,
    days
):
    print()

    print(
        f"{BOLD}{CYAN}"
        f"╭─ RICHMACK YOUTUBE RESEARCH ────────────────"
        f"{RESET}"
    )

    print(
        f"{BOLD}Channel:{RESET} "
        f"{config['name']}"
    )

    print(
        f"{BOLD}Model:{RESET} "
        f"{model}"
    )

    print(
        f"{BOLD}{CYAN}"
        f"╰────────────────────────────────────────────"
        f"{RESET}"
    )

    bar(
        "Finding transcripts",
        5,
        CYAN
    )

    directory = find_channel_dir(
        config["name"]
    )

    if not directory:
        print()

        print(
            f"{RED}"
            f"No transcript directory found."
            f"{RESET}"
        )

        return False

    files = select_transcripts(
        directory,
        limit=limit,
        days=days
    )

    bar(
        "Finding transcripts",
        10,
        CYAN
    )

    if not files:
        print()

        print(
            f"{YELLOW}"
            f"No matching transcripts."
            f"{RESET}"
        )

        return False

    bar(
        "Building corpus",
        12,
        BLUE
    )

    corpus = build_corpus(
        files
    )

    bar(
        "Building corpus",
        15,
        BLUE
    )

    try:
        summary = summary_pass(
            model,
            config["name"],
            corpus
        )

        extraction = extraction_pass(
            model,
            config["name"],
            corpus
        )

        research = research_pass(
            model,
            config["name"],
            corpus
        )

    except Exception as e:
        print()

        print(
            f"{RED}"
            f"Research failed: {e}"
            f"{RESET}"
        )

        return False

    bar(
        "Rendering report",
        94,
        YELLOW
    )

    data = {
        "channel": config[
            "name"
        ],
        "channel_key": key,
        "generated_at": (
            datetime.datetime.now()
            .isoformat()
        ),
        "model": model,
        "transcripts_analyzed": (
            len(files)
        ),
        "source_videos": (
            source_videos(
                files
            )
        ),
        "summary": summary,
        "extraction": extraction,
        "research": research
    }

    bar(
        "Saving JSON",
        96,
        YELLOW
    )

    (
        md_path,
        json_path,
        latest_md,
        latest_json
    ) = save_research(
        key,
        data
    )

    bar(
        "Saving Markdown",
        98,
        YELLOW
    )

    bar(
        "Research complete",
        100,
        GREEN
    )

    print()

    print(
        f"{GREEN}{BOLD}"
        f"Research brief created."
        f"{RESET}"
    )

    print()

    print(
        f"{BOLD}Markdown:{RESET}"
    )

    print(
        f"  {md_path}"
    )

    print(
        f"{BOLD}JSON:{RESET}"
    )

    print(
        f"  {json_path}"
    )

    print(
        f"{BOLD}Latest:{RESET}"
    )

    print(
        f"  {latest_md}"
    )

    print(
        f"  {latest_json}"
    )

    return True


###############################################################################
# MAIN
###############################################################################

def main():
    parser = argparse.ArgumentParser(
        prog=(
            "richmack youtube research"
        ),
        description=(
            "Create structured multi-pass "
            "YouTube research briefs."
        )
    )

    parser.add_argument(
        "channel",
        nargs="?",
        help="Channel key"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help=(
            "Research every configured channel"
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help=(
            "Maximum transcripts per channel "
            "(default: 3)"
        )
    )

    parser.add_argument(
        "--days",
        type=int,
        help=(
            "Only include videos from "
            "the last N days"
        )
    )

    parser.add_argument(
        "-m",
        "--model",
        default=DEFAULT_MODEL,
        help=(
            "Ollama model "
            f"(default: {DEFAULT_MODEL})"
        )
    )

    args = parser.parse_args()

    channels = load_channels()

    RESEARCH_ROOT.mkdir(
        parents=True,
        exist_ok=True
    )

    if args.all:
        total = len(
            channels
        )

        success = 0

        for i, (
            key,
            config
        ) in enumerate(
            channels.items(),
            1
        ):
            print()

            print(
                f"{BOLD}{MAGENTA}"
                f"CHANNEL {i}/{total}"
                f"{RESET}"
            )

            if research_channel(
                key,
                config,
                args.model,
                args.limit,
                args.days
            ):
                success += 1

        print()

        print(
            f"{GREEN}{BOLD}"
            f"Completed {success}/{total} channels."
            f"{RESET}"
        )

        return

    if not args.channel:
        raise SystemExit(
            "Provide a channel key or use --all"
        )

    if args.channel not in channels:
        raise SystemExit(
            "Unknown channel. "
            "Use: richmack youtube channels"
        )

    research_channel(
        args.channel,
        channels[
            args.channel
        ],
        args.model,
        args.limit,
        args.days
    )


if __name__ == "__main__":
    main()
