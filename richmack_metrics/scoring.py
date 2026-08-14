from __future__ import annotations


def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 10.0,
) -> float:
    return max(
        minimum,
        min(maximum, value),
    )


def complexity_score(
    average: float,
    maximum: int,
    syntax_errors: int,
    long_functions: int,
) -> float:

    if average <= 0:
        score = 5.0

    elif average <= 3:
        score = 10.0

    elif average <= 5:
        score = 9.0

    elif average <= 7:
        score = 8.0

    elif average <= 10:
        score = 7.0

    elif average <= 15:
        score = 5.0

    else:
        score = 3.0

    if maximum > 20:
        score -= 0.5

    if maximum > 30:
        score -= 0.5

    score -= min(
        2.0,
        long_functions * 0.05,
    )

    score -= min(
        5.0,
        syntax_errors * 2.0,
    )

    return round(
        clamp(score),
        2,
    )


def testing_score(
    source_lines: int,
    test_lines: int,
    test_files: int,
) -> float:

    if source_lines <= 0:
        return 0.0

    ratio = test_lines / source_lines

    ratio_component = min(
        8.0,
        ratio / 0.30 * 8.0,
    )

    file_component = min(
        2.0,
        test_files * 0.25,
    )

    return round(
        clamp(
            ratio_component
            + file_component
        ),
        2,
    )


def debt_score(
    source_lines: int,
    todos: int,
    fixmes: int,
) -> float:

    if source_lines <= 0:
        return 5.0

    weighted = (
        todos
        + fixmes * 2
    )

    per_kloc = weighted / max(
        1.0,
        source_lines / 1000,
    )

    return round(
        clamp(
            10.0
            - per_kloc * 0.5
        ),
        2,
    )


def automation_score(
    signals: list[bool],
) -> float:

    if not signals:
        return 0.0

    return round(
        10.0
        * sum(signals)
        / len(signals),
        2,
    )


def throughput_score(
    source_lines: int,
    commits: int,
    changed_files_30d: int,
    active_hours: float,
) -> float:
    """
    RichmackOS throughput proxy.

    The score rewards useful repository output relative
    to recorded active engineering hours.

    It intentionally avoids using commit count alone because
    commit frequency is a workflow choice, not productivity.
    """

    if active_hours <= 0:
        return 0.0

    loc_per_hour = (
        source_lines
        / active_hours
    )

    commits_per_hour = (
        commits
        / active_hours
    )

    changed_per_hour = (
        changed_files_30d
        / active_hours
    )

    loc_component = min(
        6.0,
        loc_per_hour / 180.0,
    )

    commit_component = min(
        2.0,
        commits_per_hour * 1.5,
    )

    change_component = min(
        2.0,
        changed_per_hour * 0.5,
    )

    return round(
        clamp(
            loc_component
            + commit_component
            + change_component
        ),
        2,
    )


def calculate_scores(
    *,
    complexity: float,
    testing: float,
    debt: float,
    automation: float,
    throughput: float,
) -> dict[str, float]:

    maintainability = clamp(
        complexity * 0.35
        + testing * 0.25
        + debt * 0.20
        + automation * 0.20
    )

    engineering_index = clamp(
        throughput * 0.25
        + maintainability * 0.25
        + automation * 0.20
        + testing * 0.15
        + complexity * 0.10
        + debt * 0.05
    )

    weissman = clamp(
        throughput * 0.35
        + maintainability * 0.20
        + automation * 0.15
        + complexity * 0.10
        + testing * 0.10
        + debt * 0.10
    )

    return {
        "maintainability": round(
            maintainability,
            2,
        ),
        "engineering_index": round(
            engineering_index,
            2,
        ),
        "weissman": round(
            weissman,
            2,
        ),
    }
