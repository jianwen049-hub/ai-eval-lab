"""Failure taxonomy for retrieval cases."""
from __future__ import annotations

from enum import Enum
from typing import Mapping, Sequence


class FailureType(str, Enum):
    OK = "OK"
    MISS_ALL = "MISS_ALL"
    LOW_RANK = "LOW_RANK"
    NEAR_MISS = "NEAR_MISS"
    UNANSWERABLE_LEAK = "UNANSWERABLE_LEAK"
    LABEL_SUSPECT = "LABEL_SUSPECT"


def classify_case(
    ranked_ids: Sequence[str],
    grades: Mapping[str, float],
    *,
    k: int = 3,
    tags: Sequence[str] | None = None,
) -> FailureType:
    tags = list(tags or [])
    relevant = {d for d, g in grades.items() if g > 0}
    top = list(ranked_ids[:k])

    if "unanswerable" in tags:
        # If ranker still surfaces strong lexical hits, flag leak.
        if top and any(g >= 2 for g in grades.values()):
            return FailureType.LABEL_SUSPECT
        # No gold docs: OK means "retrieved nothing critical"; we treat empty relevant as OK
        # unless top docs are weirdly long matches — simplified: always OK for demo unanswerable.
        return FailureType.OK if not relevant else FailureType.UNANSWERABLE_LEAK

    if not relevant:
        return FailureType.OK

    if not (set(top) & relevant):
        # maybe relevant further down?
        if set(ranked_ids) & relevant:
            return FailureType.LOW_RANK
        return FailureType.MISS_ALL

    # relevant in top-k
    if top and top[0] in relevant and grades.get(top[0], 0) >= 2:
        return FailureType.OK
    if top and top[0] in relevant and grades.get(top[0], 0) == 1:
        return FailureType.NEAR_MISS
    if set(top) & relevant:
        return FailureType.LOW_RANK
    return FailureType.MISS_ALL
