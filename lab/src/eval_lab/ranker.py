"""Deterministic bag-of-words ranker for offline demos (no embeddings / API)."""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Sequence

_TOKEN = re.compile(r"[A-Za-z0-9_\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text)]


def _bow(text: str) -> Counter[str]:
    return Counter(tokenize(text))


def _cos(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return 0.0
    keys = set(a) | set(b)
    dot = sum(a[k] * b[k] for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class BagOfWordsRanker:
    """Ranks corpus docs by cosine similarity over bag-of-words."""

    def rank(
        self,
        query: str,
        corpus: Sequence[dict],
        top_k: int = 10,
    ) -> list[str]:
        q = _bow(query)
        scored: list[tuple[float, str]] = []
        for doc in corpus:
            text = f"{doc.get('title', '')} {doc.get('text', '')}"
            scored.append((_cos(q, _bow(text)), doc["doc_id"]))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [doc_id for _, doc_id in scored[:top_k]]
