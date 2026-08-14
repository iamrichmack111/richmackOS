from __future__ import annotations

import os
import sys


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
WHITE = "\033[37m"

AI = MAGENTA


def supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False

    if not sys.stdout.isatty():
        return False

    term = os.environ.get(
        "TERM",
        "",
    )

    if term.lower() == "dumb":
        return False

    return True


def color(
    text: str,
    ansi: str,
) -> str:
    if not supports_color():
        return text

    return (
        f"{ansi}"
        f"{text}"
        f"{RESET}"
    )


def panel(
    title: str,
    *,
    subtitle: str | None = None,
    width: int = 60,
    ansi: str = CYAN,
) -> str:
    inner = max(
        10,
        width - 2,
    )

    title_text = (
        f" {title} "
    )

    top = (
        "╭"
        + "─" * (
            inner
            - len(title_text)
        )
        + title_text
        + "╮"
    )

    lines = [
        top
    ]

    if subtitle:
        body = (
            "│ "
            + subtitle[: inner - 2].ljust(
                inner - 2
            )
            + " │"
        )

        lines.append(
            body
        )

    bottom = (
        "╰"
        + "─" * inner
        + "╯"
    )

    lines.append(
        bottom
    )

    output = "\n".join(
        lines
    )

    return color(
        output,
        ansi,
    )


def metric_bar(
    value: float,
    *,
    maximum: float = 1.0,
    width: int = 20,
) -> str:
    if maximum <= 0:
        ratio = 0.0
    else:
        ratio = (
            float(value)
            / float(maximum)
        )

    ratio = max(
        0.0,
        min(
            1.0,
            ratio,
        ),
    )

    filled = round(
        ratio
        * width
    )

    empty = (
        width
        - filled
    )

    bar = (
        "█" * filled
        + "░" * empty
    )

    return bar


def _metric_color(
    ratio: float,
) -> str:
    if ratio >= 0.80:
        return GREEN

    if ratio >= 0.60:
        return YELLOW

    return RED


def print_metric(
    label: str,
    value: float,
    *,
    maximum: float = 1.0,
    suffix: str = "",
    width: int = 20,
):
    ratio = (
        float(value) / maximum
        if maximum
        else 0.0
    )

    ansi = _metric_color(
        ratio
    )

    bar = metric_bar(
        value,
        maximum=maximum,
        width=width,
    )

    rendered = color(
        bar,
        ansi,
    )

    if maximum == 1.0:
        display = (
            f"{value * 100:.1f}%"
        )
    else:
        display = (
            f"{value:.2f}"
        )

    print(
        f"{label:<24} "
        f"{rendered} "
        f"{display}{suffix}"
    )


def print_success(
    message: str,
):
    print(
        color(
            f"✔ {message}",
            GREEN,
        )
    )


def print_warning(
    message: str,
):
    print(
        color(
            f"⚠ {message}",
            YELLOW,
        )
    )


def print_error(
    message: str,
):
    print(
        color(
            f"✖ {message}",
            RED,
        )
    )


def print_info(
    message: str,
):
    print(
        color(
            f"ℹ {message}",
            CYAN,
        )
    )


def print_ai(
    message: str,
):
    print(
        color(
            message,
            AI,
        )
    )
