#!/usr/bin/env python3

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOME = Path.home()
BASE = HOME / ".richmackos"
OUT = HOME / "Knowledge-Inbox" / "YouTube"
STATE = BASE / "youtube-state.json"
CHANNELS_FILE = BASE / "youtube-channels.json"

def load_channels():
    if not CHANNELS_FILE.exists():
        return {}

    try:
        return json.loads(
            CHANNELS_FILE.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return {}


CHANNELS = load_channels()


RESET   = "\033[0m"
BOLD    = "\033[1m"
CYAN    = "\033[36m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
MAGENTA = "\033[35m"
RED     = "\033[31m"
GRAY    = "\033[90m"


def check_ytdlp():
    local_ytdlp = Path.home() / ".local" / "bin" / "yt-dlp"

    if local_ytdlp.exists() and local_ytdlp.is_file():
        return [str(local_ytdlp)]

    found = shutil.which("yt-dlp")

    if found:
        return [found]

    try:
        subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--version"],
            capture_output=True,
            check=True,
        )

        return [
            sys.executable,
            "-m",
            "yt_dlp"
        ]

    except Exception:
        pass

    raise SystemExit(
        "yt-dlp is not available. Expected it at "
        "~/.local/bin/yt-dlp"
    )


YTDLP = None


def load_state():
    if not STATE.exists():
        return {"videos": {}}

    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {"videos": {}}


def save_state(state):
    STATE.write_text(
        json.dumps(state, indent=2, sort_keys=True)
    )


def safe_name(text):
    text = re.sub(r"[^\w.-]+", "-", text, flags=re.UNICODE)
    return text.strip("-")[:100]


def progress(label, current, total, width=26):
    if total <= 0:
        total = 1

    ratio = min(max(current / total, 0), 1)
    filled = int(width * ratio)
    bar = "█" * filled + "░" * (width - filled)

    print(
        f"\r{BOLD}{label:<14}{RESET} "
        f"{CYAN}{bar}{RESET} "
        f"{int(ratio * 100):3d}%",
        end="",
        flush=True,
    )

    if current >= total:
        print()


def list_channel_videos(channel_url, limit):
    cmd = (
        YTDLP
        + [
            "--flat-playlist",
            "--playlist-end",
            str(limit),
            "--dump-single-json",
            channel_url,
        ]
    )

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=180,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
            or "yt-dlp channel listing failed"
        )

    data = json.loads(result.stdout)

    videos = []

    for entry in data.get("entries", []):
        if not entry:
            continue

        video_id = entry.get("id")

        if not video_id:
            continue

        videos.append({
            "id": video_id,
            "title": entry.get("title") or video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
        })

    return videos


def get_metadata(video_url):
    cmd = (
        YTDLP
        + [
            "--skip-download",
            "--dump-single-json",
            video_url,
        ]
    )

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=180,
    )

    if result.returncode != 0:
        return {}

    try:
        return json.loads(result.stdout)
    except Exception:
        return {}


def download_subtitles(video_url, workdir):
    template = str(
        workdir / "%(id)s.%(ext)s"
    )

    cmd = (
        YTDLP
        + [
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs",
            "en.*,en",
            "--sub-format",
            "vtt",
            "--no-overwrites",
            "-o",
            template,
            video_url,
        ]
    )

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,
    )

    files = sorted(workdir.glob("*.vtt"))

    return files, result


def clean_vtt(path):
    lines = path.read_text(
        errors="ignore"
    ).splitlines()

    output = []
    previous = None

    for raw in lines:
        line = raw.strip()

        if not line:
            continue

        if line.startswith("WEBVTT"):
            continue

        if line.startswith("Kind:"):
            continue

        if line.startswith("Language:"):
            continue

        if "-->" in line:
            continue

        if re.fullmatch(r"\d+", line):
            continue

        line = re.sub(
            r"<[^>]+>",
            "",
            line
        )

        line = html.unescape(line)

        line = re.sub(
            r"\s+",
            " ",
            line
        ).strip()

        if not line:
            continue

        if line == previous:
            continue

        # YouTube VTT often repeats partial caption growth.
        if previous and line.startswith(previous):
            if output:
                output[-1] = line
            previous = line
            continue

        output.append(line)
        previous = line

    return "\n".join(output).strip()


def choose_best_vtt(files):
    if not files:
        return None

    priorities = [
        ".en.vtt",
        ".en-orig.vtt",
    ]

    for suffix in priorities:
        for path in files:
            if path.name.endswith(suffix):
                return path

    return files[0]


def write_transcript(channel_key, channel_name, video, metadata, transcript):
    directory = OUT / safe_name(channel_name)
    directory.mkdir(
        parents=True,
        exist_ok=True
    )

    video_id = video["id"]
    output = directory / f"{video_id}.txt"

    title = (
        metadata.get("title")
        or video.get("title")
        or video_id
    )

    uploader = (
        metadata.get("channel")
        or metadata.get("uploader")
        or channel_name
    )

    upload_date = metadata.get("upload_date") or ""
    duration = metadata.get("duration_string") or metadata.get("duration") or ""
    description = metadata.get("description") or ""

    text = f"""TITLE: {title}
CHANNEL: {uploader}
CHANNEL_KEY: {channel_key}
VIDEO_ID: {video_id}
URL: https://www.youtube.com/watch?v={video_id}
UPLOAD_DATE: {upload_date}
DURATION: {duration}

DESCRIPTION:
{description[:4000]}

TRANSCRIPT:
{transcript}
"""

    output.write_text(
        text,
        encoding="utf-8"
    )

    return output


def sync_channel(key, limit, force=False):
    channel = CHANNELS[key]
    state = load_state()
    videos_state = state.setdefault("videos", {})

    print()
    print(
        f"{BOLD}{MAGENTA}"
        f"{channel['name']}"
        f"{RESET}"
    )

    try:
        videos = list_channel_videos(
            channel["url"],
            limit
        )
    except Exception as e:
        print(
            f"{RED}Channel error:{RESET} {e}"
        )
        return 0, 0

    added = 0
    skipped = 0

    for i, video in enumerate(videos, 1):
        progress(
            "Videos",
            i - 1,
            len(videos)
        )

        video_id = video["id"]

        existing = videos_state.get(video_id)

        if existing and existing.get("status") == "indexed" and not force:
            skipped += 1
            progress(
                "Videos",
                i,
                len(videos)
            )
            continue

        metadata = get_metadata(
            video["url"]
        )

        with tempfile.TemporaryDirectory(
            prefix="richmack-youtube-"
        ) as tmp:
            workdir = Path(tmp)

            vtts, result = download_subtitles(
                video["url"],
                workdir
            )

            best = choose_best_vtt(vtts)

            if not best:
                videos_state[video_id] = {
                    "channel": channel["name"],
                    "title": video["title"],
                    "status": "no-subtitles",
                }

                save_state(state)

                print()
                print(
                    f"{YELLOW}NO SUBS{RESET} "
                    f"{video['title']}"
                )

                progress(
                    "Videos",
                    i,
                    len(videos)
                )
                continue

            transcript = clean_vtt(best)

            if not transcript:
                videos_state[video_id] = {
                    "channel": channel["name"],
                    "title": video["title"],
                    "status": "empty-transcript",
                }

                save_state(state)

                print()
                print(
                    f"{YELLOW}EMPTY{RESET} "
                    f"{video['title']}"
                )

                progress(
                    "Videos",
                    i,
                    len(videos)
                )
                continue

            output = write_transcript(
                key,
                channel["name"],
                video,
                metadata,
                transcript
            )

            videos_state[video_id] = {
                "channel": channel["name"],
                "title": metadata.get("title") or video["title"],
                "status": "indexed",
                "path": str(output),
                "url": video["url"],
            }

            save_state(state)

            added += 1

            print()
            print(
                f"{GREEN}✓{RESET} "
                f"{output}"
            )

        progress(
            "Videos",
            i,
            len(videos)
        )

    return added, skipped


def sync(args):
    global YTDLP
    YTDLP = check_ytdlp()

    OUT.mkdir(
        parents=True,
        exist_ok=True
    )

    if args.channel:
        if args.channel not in CHANNELS:
            raise SystemExit(
                "Unknown channel. Use: richmack youtube channels"
            )

        keys = [args.channel]
    else:
        keys = list(CHANNELS)

    total_added = 0
    total_skipped = 0

    for key in keys:
        added, skipped = sync_channel(
            key,
            args.limit,
            force=args.force
        )

        total_added += added
        total_skipped += skipped

    print()
    print(
        f"{BOLD}{CYAN}"
        f"Richmack YouTube Sync Complete"
        f"{RESET}"
    )

    print(
        f"New transcripts: {GREEN}{total_added}{RESET}"
    )

    print(
        f"Already indexed: {YELLOW}{total_skipped}{RESET}"
    )

    print(
        f"Transcript root: {OUT}"
    )

    print()
    print(
        f"{GRAY}"
        f"The filesystem watcher will automatically "
        f"send new .txt transcripts to RichmackRAG."
        f"{RESET}"
    )


def channels():
    print(
        f"{BOLD}{CYAN}"
        f"Richmack YouTube Channels"
        f"{RESET}"
    )

    print()

    for key, item in CHANNELS.items():
        print(
            f"{GREEN}{key:<22}{RESET} "
            f"{item['name']}"
        )

        print(
            f"  {item['url']}"
        )


def status():
    state = load_state()
    videos = state.get("videos", {})

    print(
        f"{BOLD}{CYAN}"
        f"Richmack YouTube Status"
        f"{RESET}"
    )

    print(
        f"Known videos: {len(videos)}"
    )

    counts = {}

    for item in videos.values():
        status = item.get(
            "status",
            "unknown"
        )

        counts[status] = (
            counts.get(status, 0) + 1
        )

    for key in sorted(counts):
        print(
            f"{key:<20} {counts[key]}"
        )

    print(
        f"Transcript root: {OUT}"
    )

    print(
        f"State file: {STATE}"
    )


def search(query):
    query = query.lower()
    matches = []

    for path in OUT.rglob("*.txt"):
        try:
            text = path.read_text(
                errors="ignore"
            )
        except Exception:
            continue

        if query in text.lower():
            matches.append(path)

    if not matches:
        print(
            f"{YELLOW}No transcript matches.{RESET}"
        )
        return

    for path in matches[:100]:
        print(path)


def main():
    parser = argparse.ArgumentParser(
        prog="richmack youtube",
        description=(
            "Fetch YouTube subtitles, clean transcripts, "
            "and feed them into the RichmackOS knowledge pipeline."
        )
    )

    subs = parser.add_subparsers(
        dest="command"
    )

    sync_p = subs.add_parser(
        "sync",
        help="Sync recent videos"
    )

    sync_p.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Recent videos per channel (default: 10)"
    )

    sync_p.add_argument(
        "--channel",
        help="Sync one configured channel"
    )

    sync_p.add_argument(
        "--force",
        action="store_true",
        help="Retry already indexed videos"
    )

    subs.add_parser(
        "channels",
        help="List configured channels"
    )

    subs.add_parser(
        "status",
        help="Show ingestion status"
    )

    search_p = subs.add_parser(
        "search",
        help="Search cleaned transcript files"
    )

    search_p.add_argument(
        "query",
        nargs="+"
    )

    ask_p = subs.add_parser(
        "ask",
        help="Ask RAG questions scoped to one YouTube channel"
    )

    ask_p.add_argument(
        "channel",
        help="Configured channel key"
    )

    ask_p.add_argument(
        "question",
        nargs="+",
        help="Question about the channel transcripts"
    )

    ask_p.add_argument(
        "--latest",
        action="store_true",
        help="Restrict retrieval to the newest transcript"
    )

    args = parser.parse_args()

    if args.command == "sync":
        sync(args)

    elif args.command == "channels":
        channels()

    elif args.command == "status":
        status()

    elif args.command == "search":
        search(
            " ".join(args.query)
        )

    elif args.command == "ask":
        command = [
            sys.executable,
            str(Path.home() / ".richmackos" / "youtube_ask.py"),
            args.channel,
        ]

        if args.latest:
            command.append("--latest")

        command.extend(args.question)

        subprocess.run(
            command,
            check=False
        )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
