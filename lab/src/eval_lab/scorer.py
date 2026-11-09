"""Score a golden set with the bag-of-words ranker."""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from eval_lab.loader import GoldenSet, load_golden
from eval_lab.metrics import hit_at_k, mrr, ndcg_at_k
from eval_lab.ranker import BagOfWordsRanker
from eval_lab.taxonomy import FailureType, classify_case


def score_golden(golden: GoldenSet, *, top_k: int = 10, hit_k: int = 3, ndcg_k: int = 5) -> dict[str, Any]:
    ranker = BagOfWordsRanker()
    cases: list[dict[str, Any]] = []
    hits, mrrs, ndcgs = [], [], []
    by_tag: dict[str, dict[str, list[float]]] = defaultdict(lambda: {"hit": [], "mrr": [], "ndcg": []})
    failures: Counter[str] = Counter()

    for q in golden.queries:
        qid = q["query_id"]
        grades = golden.qrels.get(qid, {})
        relevant = {d for d, g in grades.items() if g > 0}
        ranked = ranker.rank(q["query"], golden.corpus, top_k=top_k)
        h = hit_at_k(ranked, relevant, hit_k)
        m = mrr(ranked, relevant)
        n = ndcg_at_k(ranked, grades, ndcg_k)
        tags = list(q.get("tags") or [])
        ft = classify_case(ranked, grades, k=hit_k, tags=tags)
        failures[ft.value] += 1
        hits.append(h)
        mrrs.append(m)
        ndcgs.append(n)
        for tag in tags or ["untagged"]:
            by_tag[tag]["hit"].append(h)
            by_tag[tag]["mrr"].append(m)
            by_tag[tag]["ndcg"].append(n)
        cases.append(
            {
                "query_id": qid,
                "query": q["query"],
                "tags": tags,
                "ranked_ids": ranked,
                "hit@k": h,
                "mrr": m,
                "ndcg@k": n,
                "failure_type": ft.value,
            }
        )

    def avg(xs: list[float]) -> float:
        return sum(xs) / len(xs) if xs else 0.0

    tag_report = {
        tag: {"hit@k": avg(v["hit"]), "mrr": avg(v["mrr"]), "ndcg@k": avg(v["ndcg"]), "n": len(v["hit"])}
        for tag, v in sorted(by_tag.items())
    }
    return {
        "macro": {"hit@k": avg(hits), "mrr": avg(mrrs), "ndcg@k": avg(ndcgs), "n": len(cases)},
        "by_tag": tag_report,
        "failures": dict(failures),
        "cases": cases,
    }


def score_default(data_root: Path | None = None) -> dict[str, Any]:
    root = data_root or Path(__file__).resolve().parents[2] / "data" / "golden"
    return score_golden(load_golden(root))
