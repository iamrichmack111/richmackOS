from __future__ import annotations

import sqlite3
from pathlib import Path


DEFAULT_DB = (
    Path.home()
    / ".richmackos"
    / "framework.db"
)


def connect(
    db_path: Path | str | None = None,
):
    path = Path(
        db_path or DEFAULT_DB
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    conn = sqlite3.connect(
        path
    )

    conn.row_factory = sqlite3.Row

    return conn


def initialize(
    db_path: Path | str | None = None,
):
    with connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                raw_reps REAL NOT NULL DEFAULT 0,
                stable_reps REAL NOT NULL DEFAULT 0,
                learning_units REAL NOT NULL DEFAULT 0,
                refresh_units REAL NOT NULL DEFAULT 0,
                connections REAL NOT NULL DEFAULT 0,
                anti_mass REAL NOT NULL DEFAULT 0,
                capability REAL,
                assisted_capability REAL,
                solo_capability REAL,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(topic_id)
                    REFERENCES topics(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_sessions_topic
                ON sessions(topic_id);

            CREATE INDEX IF NOT EXISTS idx_sessions_created
                ON sessions(created_at);
            """
        )


def add_topic(
    name: str,
    description: str = "",
    db_path: Path | str | None = None,
):
    initialize(
        db_path
    )

    cleaned = name.strip()

    if not cleaned:
        raise ValueError(
            "topic name cannot be empty"
        )

    with connect(db_path) as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO topics (
                    name,
                    description
                )
                VALUES (?, ?)
                """,
                (
                    cleaned,
                    description.strip(),
                ),
            )

        except sqlite3.IntegrityError as exc:
            raise ValueError(
                f"topic already exists: {cleaned}"
            ) from exc

        return cursor.lastrowid


def get_topic(
    name: str,
    db_path: Path | str | None = None,
):
    initialize(
        db_path
    )

    with connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT
                id,
                name,
                description,
                created_at
            FROM topics
            WHERE name = ? COLLATE NOCASE
            """,
            (
                name.strip(),
            ),
        ).fetchone()

    return row


def list_topics(
    db_path: Path | str | None = None,
):
    initialize(
        db_path
    )

    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT
                t.id,
                t.name,
                t.description,
                t.created_at,
                COUNT(s.id) AS session_count
            FROM topics AS t
            LEFT JOIN sessions AS s
                ON s.topic_id = t.id
            GROUP BY t.id
            ORDER BY t.name COLLATE NOCASE
            """
        ).fetchall()

    return rows


def add_session(
    topic_name: str,
    *,
    raw_reps: float = 0,
    stable_reps: float = 0,
    learning_units: float = 0,
    refresh_units: float = 0,
    connections: float = 0,
    anti_mass: float = 0,
    capability: float | None = None,
    assisted_capability: float | None = None,
    solo_capability: float | None = None,
    notes: str = "",
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

    values = (
        raw_reps,
        stable_reps,
        learning_units,
        refresh_units,
        connections,
        anti_mass,
    )

    if any(
        float(value) < 0
        for value in values
    ):
        raise ValueError(
            "session numeric values must be >= 0"
        )

    if float(stable_reps) > float(raw_reps):
        raise ValueError(
            "stable reps cannot exceed raw reps"
        )

    with connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO sessions (
                topic_id,
                raw_reps,
                stable_reps,
                learning_units,
                refresh_units,
                connections,
                anti_mass,
                capability,
                assisted_capability,
                solo_capability,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                topic["id"],
                float(raw_reps),
                float(stable_reps),
                float(learning_units),
                float(refresh_units),
                float(connections),
                float(anti_mass),
                capability,
                assisted_capability,
                solo_capability,
                notes.strip(),
            ),
        )

        return cursor.lastrowid


def topic_sessions(
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

    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                raw_reps,
                stable_reps,
                learning_units,
                refresh_units,
                connections,
                anti_mass,
                capability,
                assisted_capability,
                solo_capability,
                notes,
                created_at
            FROM sessions
            WHERE topic_id = ?
            ORDER BY id
            """,
            (
                topic["id"],
            ),
        ).fetchall()

    return rows
