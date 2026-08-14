from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .complexity import analyze_python
from .git_metrics import collect_git_metrics
from .repository import (
    iter_source_files,
    line_count,
    read_text,
)
from .scoring import (
    automation_score,
    calculate_scores,
    complexity_score,
    debt_score,
    testing_score,
    throughput_score,
)


DEFAULT_ACTIVE_HOURS = 13.0


def _is_test_file(
    root: Path,
    path: Path,
) -> bool:
    relative = path.relative_to(root)

    parts = {
        part.lower()
        for part in relative.parts
    }

    name = path.name.lower()

    return (
        "tests" in parts
        or name.startswith("test_")
        or name.endswith("_test.py")
    )


def collect_metrics(
    root: Path,
    active_hours: float = DEFAULT_ACTIVE_HOURS,
) -> dict:
    root = root.resolve()

    all_files = list(
        iter_source_files(root)
    )

    test_files = [
        path
        for path in all_files
        if _is_test_file(root, path)
    ]

    test_set = set(test_files)

    source_files = [
        path
        for path in all_files
        if path not in test_set
    ]

    python_files = [
        path
        for path in source_files
        if path.suffix.lower() == ".py"
    ]

    source_lines = sum(
        line_count(path)
        for path in source_files
    )

    test_lines = sum(
        line_count(path)
        for path in test_files
    )

    todo_count = 0
    fixme_count = 0

    for path in source_files:
        upper = read_text(path).upper()

        todo_count += upper.count("TODO")
        fixme_count += upper.count("FIXME")

    complexity = analyze_python(
        python_files
    )

    git = collect_git_metrics(root)

    complexity_value = complexity_score(
        complexity.average_complexity,
        complexity.maximum_complexity,
        complexity.syntax_errors,
        complexity.long_functions,
    )

    test_value = testing_score(
        source_lines,
        test_lines,
        len(test_files),
    )

    debt_value = debt_score(
        source_lines,
        todo_count,
        fixme_count,
    )

    automation_value = automation_score(
        [
            (
                root
                / ".github"
                / "workflows"
            ).exists(),
            (root / "Makefile").exists(),
            (root / "VERSION").exists(),
            (root / "CHANGELOG.md").exists(),
            (root / "tests").exists(),
            (root / "scripts").exists(),
        ]
    )

    throughput_value = throughput_score(
        source_lines,
        git.commits,
        git.changed_files_30d,
        active_hours,
    )

    scores = calculate_scores(
        complexity=complexity_value,
        testing=test_value,
        debt=debt_value,
        automation=automation_value,
        throughput=throughput_value,
    )

    return {
        "generated_at": (
            datetime.now()
            .astimezone()
            .isoformat(timespec="seconds")
        ),
        "repository": str(root),
        "active_hours": active_hours,
        "source": {
            "files": len(source_files),
            "lines": source_lines,
            "python_files": len(python_files),
        },
        "tests": {
            "files": len(test_files),
            "lines": test_lines,
            "source_ratio": round(
                test_lines / source_lines,
                4,
            )
            if source_lines
            else 0.0,
        },
        "debt": {
            "todo": todo_count,
            "fixme": fixme_count,
        },
        "complexity": asdict(
            complexity
        ),
        "git": asdict(git),
        "scores": {
            "complexity": complexity_value,
            "testing": test_value,
            "technical_debt": debt_value,
            "automation": automation_value,
            "throughput": throughput_value,
            **scores,
        },
    }
