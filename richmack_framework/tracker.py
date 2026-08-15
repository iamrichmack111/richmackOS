from __future__ import annotations

from pathlib import Path

from .database import (
    get_topic,
    topic_sessions,
)

from .formulas import (
    growth_multiplier,
    information_mass,
)


def topic_summary(
    topic_name: str,
    db_path: Path | str | None = None,
):
    topic = get_topic(
        topic_name,
        db_path
    )

    if topic is None:
        raise ValueError(
            f"unknown topic: {topic_name}"
        )

    sessions = topic_sessions(
        topic_name,
        db_path
    )

    raw_reps = sum(
        row["raw_reps"]
        for row in sessions
    )

    stable_reps = sum(
        row["stable_reps"]
        for row in sessions
    )

    learning_units = sum(
        row["learning_units"]
        for row in sessions
    )

    refresh_units = sum(
        row["refresh_units"]
        for row in sessions
    )

    connections = sum(
        row["connections"]
        for row in sessions
    )

    anti_mass = sum(
        row["anti_mass"]
        for row in sessions
    )

    retention = (
        stable_reps / raw_reps
        if raw_reps
        else 0.0
    )

    leakage = (
        raw_reps
        - stable_reps
    )

    bits = (
        learning_units
        + refresh_units
    )

    gross_mass = information_mass(
        bits,
        connections,
    )

    net_mass = (
        gross_mass
        - anti_mass
    )

    density = (
        net_mass / bits
        if bits
        else 0.0
    )

    capability_values = [
        row["capability"]
        for row in sessions
        if row["capability"] is not None
    ]

    latest_capability = (
        capability_values[-1]
        if capability_values
        else None
    )

    return {
        "topic": topic["name"],
        "description": topic["description"],
        "sessions": len(sessions),
        "raw_reps": raw_reps,
        "stable_reps": stable_reps,
        "retention": retention,
        "leakage": leakage,
        "learning_units": learning_units,
        "refresh_units": refresh_units,
        "connections": connections,
        "anti_mass": anti_mass,
        "gross_mass": gross_mass,
        "net_mass": net_mass,
        "density": density,
        "growth_multiplier": growth_multiplier(
            stable_reps
        ),
        "latest_capability": latest_capability,
    }
