"""
RichmackOS Engineering Metrics.

This package provides measurable engineering-quality and productivity
metrics for the RichmackOS project.

The Richmack Weissman score is a custom RichmackOS longitudinal
engineering-efficiency metric inspired by the fictional Weissman Score
from HBO's Silicon Valley. It is not an industry-standard benchmark.
"""

from .collector import collect_metrics
from .scoring import calculate_scores

__all__ = [
    "collect_metrics",
    "calculate_scores",
]
