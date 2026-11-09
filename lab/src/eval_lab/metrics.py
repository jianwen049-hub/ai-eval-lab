"""Retrieval metrics: Hit@k, MRR, nDCG@k (pure functions, no I/O)."""
from __future__ import annotations

import math
from typing import Mapping, Sequence


def hit_at_k(ranked_ids: Sequence[str], relevant_ids: set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    top = set(ranked_ids[:k])
    return 1.0 if top & relevant_ids else 0.0


def mrr(ranked_ids: Sequence[str], relevant_ids: set[str]) -> float:
    for i, doc_id in enumerate(ranked_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / i
    return 0.0


def _dcg(relevances: Sequence[float]) -> float:
    total = 0.0
    for i, rel in enumerate(relevances, start=1):
        total += (2**rel - 1) / math.log2(i + 1)
    return total


def ndcg_at_k(
    ranked_ids: Sequence[str],
    relevance_grades: Mapping[str, float],
    k: int,
) -> float:
    if k <= 0:
        return 0.0
    gained = [float(relevance_grades.get(doc_id, 0.0)) for doc_id in ranked_ids[:k]]
    ideal = sorted((float(g) for g in relevance_grades.values() if g > 0), reverse=True)[:k]
    if not ideal:
        return 0.0
    idcg = _dcg(ideal)
    if idcg == 0:
        return 0.0
    return _dcg(gained) / idcg
