#!/usr/bin/env python3

import json
import sys
from pathlib import Path

HOME = Path.home()

sys.path.insert(
    0,
    str(HOME / ".richmackos")
)

from youtube_research import render_markdown

ROOT = (
    HOME
    / "Knowledge"
    / "Research"
    / "youtube"
)


def rebuild(json_path):
    try:
        data = json.loads(
            json_path.read_text(
                encoding="utf-8"
            )
        )
    except Exception as e:
        print(
            f"ERROR reading {json_path}: {e}"
        )
        return False

    md_path = json_path.with_suffix(
        ".md"
    )

    try:
        markdown = render_markdown(
            data
        )
    except Exception as e:
        print(
            f"ERROR rendering {json_path}: {e}"
        )
        return False

    if not markdown.strip():
        print(
            f"ERROR renderer returned empty output: "
            f"{json_path}"
        )
        return False

    tmp = md_path.with_name(
        "." + md_path.name + ".tmp"
    )

    tmp.write_text(
        markdown,
        encoding="utf-8"
    )

    tmp.replace(
        md_path
    )

    print(
        f"REBUILT {md_path} "
        f"({md_path.stat().st_size} bytes)"
    )

    return True


def main():
    if not ROOT.exists():
        raise SystemExit(
            f"Research directory missing: {ROOT}"
        )

    rebuilt = 0
    skipped = 0

    # Historical timestamp JSONs first.
    files = sorted(
        p
        for p in ROOT.rglob("*.json")
        if p.name != "latest.json"
    )

    for json_path in files:
        md_path = json_path.with_suffix(
            ".md"
        )

        if (
            not md_path.exists()
            or md_path.stat().st_size == 0
        ):
            if rebuild(
                json_path
            ):
                rebuilt += 1
        else:
            skipped += 1

    # Rebuild latest.md from latest.json independently.
    for json_path in sorted(
        ROOT.rglob("latest.json")
    ):
        md_path = json_path.with_name(
            "latest.md"
        )

        if (
            not md_path.exists()
            or md_path.stat().st_size == 0
        ):
            if rebuild(
                json_path
            ):
                rebuilt += 1
        else:
            skipped += 1

    print()
    print(
        f"Rebuilt: {rebuilt}"
    )

    print(
        f"Already healthy: {skipped}"
    )


if __name__ == "__main__":
    main()
