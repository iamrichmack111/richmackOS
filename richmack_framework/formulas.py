from __future__ import annotations

import math
from collections.abc import Iterable


# ============================================================
# VALIDATION
# ============================================================


def _require_nonnegative(
    value: float,
    name: str,
) -> float:
    value = float(value)

    if value < 0:
        raise ValueError(
            f"{name} must be >= 0"
        )

    return value


def _require_positive(
    value: float,
    name: str,
) -> float:
    value = float(value)

    if value <= 0:
        raise ValueError(
            f"{name} must be > 0"
        )

    return value


def _require_rate(
    value: float,
    name: str = "rate",
) -> float:
    value = float(value)

    if not 0 <= value <= 1:
        raise ValueError(
            f"{name} must be between 0 and 1"
        )

    return value


# ============================================================
# 1. RICHMACK IMPROVEMENT FORMULA
# ============================================================


def generic_growth(
    baseline: float,
    rate: float,
    repetitions: float,
) -> float:
    """
    C_N = C_0(1+p)^N
    """

    baseline = _require_nonnegative(
        baseline,
        "baseline",
    )

    repetitions = _require_nonnegative(
        repetitions,
        "repetitions",
    )

    if rate <= -1:
        raise ValueError(
            "rate must be greater than -1"
        )

    return (
        baseline
        * (1 + rate) ** repetitions
    )


def seven_rep_growth(
    baseline: float,
    stable_repetitions: float,
) -> float:
    """
    C_N = C_0 * 2^(N/7)
    """

    baseline = _require_nonnegative(
        baseline,
        "baseline",
    )

    stable_repetitions = _require_nonnegative(
        stable_repetitions,
        "stable_repetitions",
    )

    return (
        baseline
        * growth_multiplier(
            stable_repetitions
        )
    )


def growth_multiplier(
    stable_repetitions: float,
) -> float:
    """
    G = 2^(N/7)
    """

    stable_repetitions = _require_nonnegative(
        stable_repetitions,
        "stable_repetitions",
    )

    return (
        2 ** (
            stable_repetitions
            / 7
        )
    )


def stable_reps_for_growth(
    growth: float,
) -> float:
    """
    N = 7 ln(G) / ln(2)
    """

    growth = _require_positive(
        growth,
        "growth",
    )

    return (
        7
        * math.log(growth)
        / math.log(2)
    )


def days_for_growth(
    growth: float,
    approaches_per_day: float,
) -> float:
    """
    d = 7 ln(G) / (m ln(2))
    """

    approaches_per_day = _require_positive(
        approaches_per_day,
        "approaches_per_day",
    )

    return (
        stable_reps_for_growth(
            growth
        )
        / approaches_per_day
    )


def per_rep_improvement() -> float:
    """
    p = 2^(1/7) - 1
    """

    return (
        2 ** (1 / 7)
        - 1
    )


# ============================================================
# 2. STABILITY, RETENTION, AND LEAKAGE
# ============================================================


def stable_reps(
    retention: float,
    repetitions: float,
) -> float:
    """
    S = rN
    """

    retention = _require_rate(
        retention,
        "retention",
    )

    repetitions = _require_nonnegative(
        repetitions,
        "repetitions",
    )

    return (
        retention
        * repetitions
    )


def raw_reps_for_stable(
    stable: float,
    retention: float,
) -> float:
    """
    N = S/r
    """

    stable = _require_nonnegative(
        stable,
        "stable",
    )

    retention = _require_positive(
        retention,
        "retention",
    )

    if retention > 1:
        raise ValueError(
            "retention must be <= 1"
        )

    return (
        stable
        / retention
    )


def leakage(
    repetitions: float,
    stable: float,
) -> float:
    """
    L = N - S
    """

    repetitions = _require_nonnegative(
        repetitions,
        "repetitions",
    )

    stable = _require_nonnegative(
        stable,
        "stable",
    )

    if stable > repetitions:
        raise ValueError(
            "stable repetitions cannot exceed total repetitions"
        )

    return (
        repetitions
        - stable
    )


def leakage_from_rate(
    repetitions: float,
    retention: float,
) -> float:
    """
    L = N(1-r)
    """

    repetitions = _require_nonnegative(
        repetitions,
        "repetitions",
    )

    retention = _require_rate(
        retention,
        "retention",
    )

    return (
        repetitions
        * (1 - retention)
    )


def growth_from_stable_reps(
    baseline: float,
    stable: float,
) -> float:
    """
    C_S = C_0 * 2^(S/7)
    """

    return seven_rep_growth(
        baseline,
        stable,
    )


def growth_from_raw_reps(
    baseline: float,
    retention: float,
    repetitions: float,
) -> float:
    """
    C_N = C_0 * 2^(rN/7)
    """

    stable = stable_reps(
        retention,
        repetitions,
    )

    return seven_rep_growth(
        baseline,
        stable,
    )


# ============================================================
# 3. IERAMAYU APPROACH METHOD
# ============================================================


def approach_score(
    clarity: float,
    relevance: float,
    integration: float,
    stability: float,
) -> float:
    """
    A_i = C_i * R_i * I_i * S_i
    """

    return (
        float(clarity)
        * float(relevance)
        * float(integration)
        * float(stability)
    )


def approach_total(
    scores: Iterable[float],
) -> float:
    """
    A_total = Σ A_i
    """

    return sum(
        float(score)
        for score in scores
    )


# ============================================================
# 4. LEARNING AND REFRESH UNITS
# ============================================================


def learning_unit_components(
    happened: float,
    why: float,
    connection: float,
) -> float:
    """
    LU = H + W + K
    """

    return (
        float(happened)
        + float(why)
        + float(connection)
    )


def learning_unit_strict(
    happened: bool,
    why: bool,
    connection: bool,
) -> int:
    """
    LU = 1 when H=1, W=1, K=1;
    otherwise LU = 0.
    """

    return int(
        bool(happened)
        and bool(why)
        and bool(connection)
    )


def refresh_unit(
    learning_units: float,
) -> float:
    """
    RU = LU / 3
    """

    learning_units = _require_nonnegative(
        learning_units,
        "learning_units",
    )

    return (
        learning_units
        / 3
    )


def refresh_unit_connected(
    new_learning: float,
    old_learning: float,
    connections: float,
) -> float:
    """
    RU = (LU_new + LU_old + C) / 3
    """

    return (
        (
            float(new_learning)
            + float(old_learning)
            + float(connections)
        )
        / 3
    )


# ============================================================
# 5. MASS, ANTI-MASS, AND DENSITY
# ============================================================


def information_mass(
    bits: float,
    relationships: float,
) -> float:
    """
    M = B * log(B+1) * (R+1)

    Natural logarithm is used for log().
    """

    bits = _require_nonnegative(
        bits,
        "bits",
    )

    relationships = _require_nonnegative(
        relationships,
        "relationships",
    )

    if bits == 0:
        return 0.0

    return (
        bits
        * math.log(
            bits + 1
        )
        * (
            relationships + 1
        )
    )


def net_information_mass(
    mass: float,
    anti_mass: float,
) -> float:
    """
    M_net = M - M_anti
    """

    return (
        float(mass)
        - float(anti_mass)
    )


def information_density(
    mass: float,
    bits: float,
) -> float:
    """
    D = M/B
    """

    bits = _require_positive(
        bits,
        "bits",
    )

    return (
        float(mass)
        / bits
    )


# ============================================================
# 6. RICHMACK CAPABILITY ASSESSMENT
# ============================================================


def capability_gap(
    target: float,
    baseline: float,
) -> float:
    """
    Gap = C_t - C_0
    """

    return (
        float(target)
        - float(baseline)
    )


def target_multiplier(
    target: float,
    baseline: float,
) -> float:
    """
    G = C_t / C_0
    """

    baseline = _require_positive(
        baseline,
        "baseline",
    )

    return (
        float(target)
        / baseline
    )


def independence(
    solo: float,
    assisted: float,
) -> float:
    """
    I = C_solo / C_assisted
    """

    assisted = _require_positive(
        assisted,
        "assisted",
    )

    return (
        float(solo)
        / assisted
    )


def readiness(
    capability: float,
    stability: float,
    independence_score: float,
) -> float:
    """
    R = C * S * I
    """

    return (
        float(capability)
        * float(stability)
        * float(independence_score)
    )


# ============================================================
# 7. FOCUS AND ENTROPY
# ============================================================


def entropy_cost(
    active_items: float,
) -> float:
    """
    Entropy Cost = Active Items - 3

    Cost begins only after three active items.
    """

    active_items = _require_nonnegative(
        active_items,
        "active_items",
    )

    return max(
        0.0,
        active_items - 3
    )


def effective_progress(
    raw_progress: float,
    entropy: float,
) -> float:
    """
    Effective Progress = Raw Progress - Entropy Cost
    """

    return (
        float(raw_progress)
        - float(entropy)
    )


def adjusted_wpm(
    raw_wpm: float,
    error_penalty: float,
) -> float:
    """
    Adjusted WPM = Raw WPM - Error Penalty
    """

    return (
        float(raw_wpm)
        - float(error_penalty)
    )
