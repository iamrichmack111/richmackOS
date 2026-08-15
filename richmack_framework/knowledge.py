from __future__ import annotations

from pathlib import Path
from typing import Any

from .database import connect, get_topic, initialize


def initialize_knowledge(
    db_path: Path | str | None = None,
):
    initialize(db_path)

    with connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS knowledge_concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                name TEXT NOT NULL COLLATE NOCASE,
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(topic_id, name),
                FOREIGN KEY(topic_id)
                    REFERENCES topics(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS knowledge_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                concept_id INTEGER,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(topic_id)
                    REFERENCES topics(id)
                    ON DELETE CASCADE,
                FOREIGN KEY(concept_id)
                    REFERENCES knowledge_concepts(id)
                    ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS knowledge_mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                concept_id INTEGER,
                body TEXT NOT NULL,
                resolved INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(topic_id)
                    REFERENCES topics(id)
                    ON DELETE CASCADE,
                FOREIGN KEY(concept_id)
                    REFERENCES knowledge_concepts(id)
                    ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS knowledge_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                concept_id INTEGER,
                body TEXT NOT NULL,
                answered INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(topic_id)
                    REFERENCES topics(id)
                    ON DELETE CASCADE,
                FOREIGN KEY(concept_id)
                    REFERENCES knowledge_concepts(id)
                    ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS knowledge_confidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                concept_id INTEGER NOT NULL,
                score REAL NOT NULL,
                source TEXT NOT NULL DEFAULT 'manual',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(topic_id)
                    REFERENCES topics(id)
                    ON DELETE CASCADE,
                FOREIGN KEY(concept_id)
                    REFERENCES knowledge_concepts(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS knowledge_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                concept_a_id INTEGER NOT NULL,
                concept_b_id INTEGER NOT NULL,
                relation TEXT NOT NULL DEFAULT 'related',
                strength REAL NOT NULL DEFAULT 1.0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(topic_id)
                    REFERENCES topics(id)
                    ON DELETE CASCADE,
                FOREIGN KEY(concept_a_id)
                    REFERENCES knowledge_concepts(id)
                    ON DELETE CASCADE,
                FOREIGN KEY(concept_b_id)
                    REFERENCES knowledge_concepts(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_concepts_topic
                ON knowledge_concepts(topic_id);

            CREATE INDEX IF NOT EXISTS idx_notes_topic
                ON knowledge_notes(topic_id);

            CREATE INDEX IF NOT EXISTS idx_mistakes_topic
                ON knowledge_mistakes(topic_id);

            CREATE INDEX IF NOT EXISTS idx_questions_topic
                ON knowledge_questions(topic_id);

            CREATE INDEX IF NOT EXISTS idx_confidence_concept
                ON knowledge_confidence(concept_id);

            CREATE INDEX IF NOT EXISTS idx_relations_topic
                ON knowledge_relations(topic_id);
            """
        )


def _topic(
    topic_name: str,
    db_path: Path | str | None = None,
):
    initialize_knowledge(db_path)

    topic = get_topic(
        topic_name,
        db_path,
    )

    if topic is None:
        raise ValueError(
            f"unknown topic: {topic_name}"
        )

    return topic


def _concept(
    topic_name: str,
    concept_name: str,
    db_path: Path | str | None = None,
):
    topic = _topic(
        topic_name,
        db_path,
    )

    with connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT
                id,
                topic_id,
                name,
                description,
                created_at
            FROM knowledge_concepts
            WHERE topic_id = ?
              AND name = ? COLLATE NOCASE
            """,
            (
                topic["id"],
                concept_name.strip(),
            ),
        ).fetchone()

    if row is None:
        raise ValueError(
            f"unknown concept: {concept_name}"
        )

    return row


def add_concept(
    topic_name: str,
    name: str,
    *,
    description: str = "",
    db_path: Path | str | None = None,
) -> int:
    topic = _topic(
        topic_name,
        db_path,
    )

    name = name.strip()

    if not name:
        raise ValueError(
            "concept name cannot be empty"
        )

    with connect(db_path) as conn:
        existing = conn.execute(
            """
            SELECT id
            FROM knowledge_concepts
            WHERE topic_id = ?
              AND name = ? COLLATE NOCASE
            """,
            (
                topic["id"],
                name,
            ),
        ).fetchone()

        if existing:
            raise ValueError(
                f"concept already exists: {name}"
            )

        cursor = conn.execute(
            """
            INSERT INTO knowledge_concepts (
                topic_id,
                name,
                description
            )
            VALUES (?, ?, ?)
            """,
            (
                topic["id"],
                name,
                description.strip(),
            ),
        )

        return int(cursor.lastrowid)


def list_concepts(
    topic_name: str,
    db_path: Path | str | None = None,
):
    topic = _topic(
        topic_name,
        db_path,
    )

    with connect(db_path) as conn:
        return conn.execute(
            """
            SELECT
                c.id,
                c.name,
                c.description,
                (
                    SELECT score
                    FROM knowledge_confidence
                    WHERE concept_id = c.id
                    ORDER BY id DESC
                    LIMIT 1
                ) AS confidence
            FROM knowledge_concepts AS c
            WHERE c.topic_id = ?
            ORDER BY c.name COLLATE NOCASE
            """,
            (
                topic["id"],
            ),
        ).fetchall()


def _add_record(
    table: str,
    topic_name: str,
    body: str,
    *,
    concept_name: str | None = None,
    db_path: Path | str | None = None,
) -> int:
    allowed = {
        "knowledge_notes",
        "knowledge_mistakes",
        "knowledge_questions",
    }

    if table not in allowed:
        raise ValueError(
            "invalid knowledge table"
        )

    topic = _topic(
        topic_name,
        db_path,
    )

    body = body.strip()

    if not body:
        raise ValueError(
            "text cannot be empty"
        )

    concept_id = None

    if concept_name:
        concept_id = _concept(
            topic_name,
            concept_name,
            db_path,
        )["id"]

    with connect(db_path) as conn:
        cursor = conn.execute(
            f"""
            INSERT INTO {table} (
                topic_id,
                concept_id,
                body
            )
            VALUES (?, ?, ?)
            """,
            (
                topic["id"],
                concept_id,
                body,
            ),
        )

        return int(cursor.lastrowid)


def add_note(
    topic_name: str,
    body: str,
    *,
    concept_name: str | None = None,
    db_path: Path | str | None = None,
) -> int:
    return _add_record(
        "knowledge_notes",
        topic_name,
        body,
        concept_name=concept_name,
        db_path=db_path,
    )


def add_mistake(
    topic_name: str,
    body: str,
    *,
    concept_name: str | None = None,
    db_path: Path | str | None = None,
) -> int:
    return _add_record(
        "knowledge_mistakes",
        topic_name,
        body,
        concept_name=concept_name,
        db_path=db_path,
    )


def add_question(
    topic_name: str,
    body: str,
    *,
    concept_name: str | None = None,
    db_path: Path | str | None = None,
) -> int:
    return _add_record(
        "knowledge_questions",
        topic_name,
        body,
        concept_name=concept_name,
        db_path=db_path,
    )


def set_confidence(
    topic_name: str,
    concept_name: str,
    score: float,
    *,
    source: str = "manual",
    db_path: Path | str | None = None,
) -> int:
    score = float(score)

    if not 0 <= score <= 1:
        raise ValueError(
            "confidence must be between 0 and 1"
        )

    topic = _topic(
        topic_name,
        db_path,
    )

    concept = _concept(
        topic_name,
        concept_name,
        db_path,
    )

    with connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO knowledge_confidence (
                topic_id,
                concept_id,
                score,
                source
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                topic["id"],
                concept["id"],
                score,
                source,
            ),
        )

        return int(cursor.lastrowid)


def add_relation(
    topic_name: str,
    concept_a: str,
    concept_b: str,
    *,
    relation: str = "related",
    strength: float = 1.0,
    db_path: Path | str | None = None,
) -> int:
    strength = float(strength)

    if not 0 <= strength <= 1:
        raise ValueError(
            "strength must be between 0 and 1"
        )

    if (
        concept_a.strip().lower()
        == concept_b.strip().lower()
    ):
        raise ValueError(
            "concept cannot relate to itself"
        )

    topic = _topic(
        topic_name,
        db_path,
    )

    left = _concept(
        topic_name,
        concept_a,
        db_path,
    )

    right = _concept(
        topic_name,
        concept_b,
        db_path,
    )

    with connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO knowledge_relations (
                topic_id,
                concept_a_id,
                concept_b_id,
                relation,
                strength
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                topic["id"],
                left["id"],
                right["id"],
                relation.strip() or "related",
                strength,
            ),
        )

        return int(cursor.lastrowid)


def _records(
    table: str,
    topic_id: int,
    db_path: Path | str | None = None,
):
    with connect(db_path) as conn:
        rows = conn.execute(
            f"""
            SELECT
                r.id,
                r.body,
                r.created_at,
                c.name AS concept
            FROM {table} AS r
            LEFT JOIN knowledge_concepts AS c
                ON c.id = r.concept_id
            WHERE r.topic_id = ?
            ORDER BY r.id DESC
            """,
            (
                topic_id,
            ),
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def knowledge_summary(
    topic_name: str,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    topic = _topic(
        topic_name,
        db_path,
    )

    concepts = [
        dict(row)
        for row in list_concepts(
            topic_name,
            db_path,
        )
    ]

    with connect(db_path) as conn:
        relations = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    a.name AS concept_a,
                    b.name AS concept_b,
                    r.relation,
                    r.strength
                FROM knowledge_relations AS r
                JOIN knowledge_concepts AS a
                    ON a.id = r.concept_a_id
                JOIN knowledge_concepts AS b
                    ON b.id = r.concept_b_id
                WHERE r.topic_id = ?
                ORDER BY r.id DESC
                """,
                (
                    topic["id"],
                ),
            ).fetchall()
        ]

    return {
        "topic": topic["name"],
        "concepts": concepts,
        "notes": _records(
            "knowledge_notes",
            topic["id"],
            db_path,
        ),
        "mistakes": _records(
            "knowledge_mistakes",
            topic["id"],
            db_path,
        ),
        "questions": _records(
            "knowledge_questions",
            topic["id"],
            db_path,
        ),
        "relations": relations,
    }
