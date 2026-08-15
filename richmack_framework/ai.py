from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .database import get_topic, topic_sessions
from .tracker import topic_summary
from .knowledge import knowledge_summary

from richmack_ollama import chat_url

DEFAULT_OLLAMA_URL = chat_url()
DEFAULT_MODEL = "huihui_ai/qwen3.5-abliterated:4B"


@dataclass
class FrameworkAIContext:
    topic: str
    description: str
    summary: dict[str, Any]
    sessions: list[dict[str, Any]]
    knowledge: dict[str, Any]


def _row_to_dict(row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def load_framework_context(
    topic_name: str,
    db_path: Path | str | None = None,
    *,
    history_limit: int = 12,
) -> FrameworkAIContext:
    topic = get_topic(topic_name, db_path)

    if topic is None:
        raise ValueError(f"unknown topic: {topic_name}")

    if history_limit < 1:
        raise ValueError("history_limit must be >= 1")

    summary = topic_summary(topic_name, db_path)
    rows = topic_sessions(topic_name, db_path)

    return FrameworkAIContext(
        topic=topic["name"],
        description=topic["description"],
        summary=summary,
        sessions=[
            _row_to_dict(row)
            for row in rows[-history_limit:]
        ],
        knowledge=knowledge_summary(
            topic_name,
            db_path,
        ),
    )


def _format_optional(value, digits: int = 4) -> str:
    if value is None:
        return "not recorded"

    if isinstance(value, (int, float)):
        return f"{float(value):.{digits}f}"

    return str(value)


def _append_metric_context(
    lines: list[str],
    context: FrameworkAIContext,
):
    summary = context.summary

    lines.extend([
        "RICHMACK FRAMEWORK LEARNING PROFILE",
        "",
        f"Topic: {context.topic}",
        (
            f"Description: {context.description}"
            if context.description
            else "Description: not supplied"
        ),
        "",
        "ACCUMULATED METRICS",
        f"Sessions: {summary['sessions']}",
        f"Raw repetitions: {summary['raw_reps']:.2f}",
        f"Stable repetitions: {summary['stable_reps']:.2f}",
        f"Retention: {summary['retention'] * 100:.2f}%",
        f"Leakage: {summary['leakage']:.2f}",
        f"Learning Units: {summary['learning_units']:.2f}",
        f"Refresh Units: {summary['refresh_units']:.2f}",
        f"Connections: {summary['connections']:.2f}",
        f"Growth multiplier: {summary['growth_multiplier']:.4f}x",
        f"Net information mass: {summary['net_mass']:.4f}",
        f"Information density: {summary['density']:.4f}",
        (
            "Latest capability: "
            + _format_optional(
                summary[
                    "latest_capability"
                ]
            )
        ),
    ])


def _append_session_context(
    lines: list[str],
    context: FrameworkAIContext,
):
    lines.extend([
        "",
        "RECENT LEARNING SESSIONS",
    ])

    if not context.sessions:
        lines.append(
            "No sessions recorded."
        )
        return

    for index, row in enumerate(
        context.sessions,
        1,
    ):
        lines.extend([
            "",
            (
                f"Session {index} "
                f"— {row['created_at']}"
            ),
            (
                f"Raw reps: "
                f"{row['raw_reps']:.2f}"
            ),
            (
                f"Stable reps: "
                f"{row['stable_reps']:.2f}"
            ),
            (
                f"Learning Units: "
                f"{row['learning_units']:.2f}"
            ),
            (
                f"Refresh Units: "
                f"{row['refresh_units']:.2f}"
            ),
            (
                f"Connections: "
                f"{row['connections']:.2f}"
            ),
            (
                "Capability: "
                + _format_optional(
                    row[
                        "capability"
                    ]
                )
            ),
            (
                "Solo capability: "
                + _format_optional(
                    row[
                        "solo_capability"
                    ]
                )
            ),
            (
                "Assisted capability: "
                + _format_optional(
                    row[
                        "assisted_capability"
                    ]
                )
            ),
        ])

        if row["notes"]:
            lines.append(
                f"Notes: {row['notes']}"
            )


def _append_concept_context(
    lines: list[str],
    context: FrameworkAIContext,
):
    knowledge = context.knowledge

    lines.extend([
        "",
        "KNOWLEDGE GRAPH",
    ])

    concepts = knowledge.get(
        "concepts",
        [],
    )

    if not concepts:
        lines.append(
            "Concepts: none recorded."
        )
        return

    lines.append(
        "Concepts:"
    )

    for item in concepts[:50]:
        confidence = item.get(
            "confidence"
        )

        if confidence is None:
            confidence_text = (
                "confidence not recorded"
            )
        else:
            confidence_text = (
                f"confidence "
                f"{float(confidence) * 100:.1f}%"
            )

        description = (
            item.get(
                "description",
                ""
            )
            or ""
        ).strip()

        line = (
            f"- {item['name']} "
            f"({confidence_text})"
        )

        if description:
            line += (
                f" — {description}"
            )

        lines.append(
            line
        )


def _append_knowledge_records(
    lines: list[str],
    context: FrameworkAIContext,
):
    knowledge = context.knowledge

    record_groups = (
        (
            "Knowledge notes",
            "notes",
        ),
        (
            "Recorded mistakes",
            "mistakes",
        ),
        (
            "Open questions",
            "questions",
        ),
    )

    for heading, key in record_groups:
        values = knowledge.get(
            key,
            [],
        )

        if not values:
            continue

        lines.append(
            f"{heading}:"
        )

        for item in values[:25]:
            concept = (
                item.get(
                    "concept"
                )
                or ""
            ).strip()

            prefix = (
                f"[{concept}] "
                if concept
                else ""
            )

            lines.append(
                f"- {prefix}"
                f"{item['body']}"
            )


def _append_relationship_context(
    lines: list[str],
    context: FrameworkAIContext,
):
    relations = context.knowledge.get(
        "relations",
        [],
    )

    if not relations:
        return

    lines.append(
        "Concept relationships:"
    )

    for item in relations[:25]:
        lines.append(
            f"- {item['concept_a']} "
            f"--{item['relation']}--> "
            f"{item['concept_b']} "
            f"(strength "
            f"{float(item['strength']):.2f})"
        )


def build_framework_context_text(
    context: FrameworkAIContext,
) -> str:
    lines: list[str] = []

    _append_metric_context(
        lines,
        context,
    )

    _append_session_context(
        lines,
        context,
    )

    _append_concept_context(
        lines,
        context,
    )

    _append_knowledge_records(
        lines,
        context,
    )

    _append_relationship_context(
        lines,
        context,
    )

    return "\n".join(
        lines
    )


def build_system_prompt() -> str:
    return '''
You are Richmack Personal Tutor, a local AI assistant inside RichmackOS.

You receive a structured Richmack Framework learning profile containing
measured learning history for one topic.

Rules:
1. Ground personal claims in the supplied profile.
2. Do not invent sessions, measurements, strengths, weaknesses, or progress.
3. Clearly distinguish measured facts from your interpretation.
4. Treat Richmack Framework growth formulas as planning models, not
   established biological laws.
5. Tie recommendations to recorded retention, leakage, Learning Units,
   Refresh Units, capability, connections, or session notes.
6. If the profile lacks information needed to answer, state what is missing.
7. Be concise but useful.
8. Do not claim that a calculated growth multiplier proves literal human
   ability multiplied by that amount.
9. When useful, suggest one concrete next learning action.
10. Never invent future dates, times, deadlines, appointments, or schedules.
    Only use a specific future date or time if the user explicitly supplied it
    or it is present in the supplied learning profile.
11. If recommending another study session without a supplied date, refer to
    it as "your next session" or "within your normal study schedule."
12. Do not invent numeric targets unless they are directly calculated from
    supplied measurements or clearly labeled as optional suggestions.
13. Treat recorded concepts, notes, mistakes, questions, confidence
    scores, and relationships as the authoritative personal knowledge
    record for this topic.
14. Never claim the user studied a concept unless it appears in the
    supplied profile, session notes, or knowledge graph.
15. When discussing weaknesses, distinguish recorded mistakes and low
    confidence from your own inference.
'''.strip()


def build_user_prompt(
    context: FrameworkAIContext,
    question: str,
) -> str:
    question = question.strip()

    if not question:
        raise ValueError("question cannot be empty")

    return (
        build_framework_context_text(context)
        + "\n\nUSER QUESTION\n"
        + question
    )


def ollama_chat(
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
    url: str = DEFAULT_OLLAMA_URL,
    timeout: float = 600.0,
) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            body = response.read()
    except TimeoutError as exc:
        raise RuntimeError(
            f"Ollama timed out after {timeout:.0f} seconds "
            f"while waiting for model {model}."
        ) from exc

    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Unable to reach Ollama. "
            "Confirm the configured Ollama host is reachable."
        ) from exc

    try:
        result = json.loads(body.decode("utf-8"))
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise RuntimeError(
            "Ollama returned an invalid response."
        ) from exc

    answer = result.get("message", {}).get("content", "")

    if not isinstance(answer, str):
        raise RuntimeError(
            "Ollama response did not contain text."
        )

    answer = answer.strip()

    if not answer:
        raise RuntimeError(
            "Ollama returned an empty answer."
        )

    return answer


def ask_framework(
    topic_name: str,
    question: str,
    *,
    model: str = DEFAULT_MODEL,
    db_path: Path | str | None = None,
    url: str = DEFAULT_OLLAMA_URL,
    history_limit: int = 12,
    timeout: float = 600.0,
) -> tuple[str, FrameworkAIContext]:
    context = load_framework_context(
        topic_name,
        db_path,
        history_limit=history_limit,
    )

    answer = ollama_chat(
        model=model,
        system_prompt=build_system_prompt(),
        user_prompt=build_user_prompt(
            context,
            question,
        ),
        url=url,
        timeout=timeout,
    )

    return answer, context
