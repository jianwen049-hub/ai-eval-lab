#!/usr/bin/env python3
"""Offline smoke check — no network, no API keys."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eval_lab.metrics import hit_at_k, mrr, ndcg_at_k
from eval_lab.ranker import BagOfWordsRanker
from eval_lab.loader import load_golden
from eval_lab.taxonomy import FailureType, classify_case
from eval_lab.scorer import score_default


def main() -> int:
    assert hit_at_k(["a", "b", "c"], {"c"}, 3) == 1.0
    assert hit_at_k(["a", "b", "c"], {"z"}, 3) == 0.0
    assert abs(mrr(["a", "b", "c"], {"b"}) - 0.5) < 1e-9
    assert ndcg_at_k(["a", "b"], {"a": 2, "b": 1}, 2) > 0.9

    assert classify_case(["x", "y"], {"z": 2}, k=3) == FailureType.MISS_ALL
    assert classify_case(["z", "y"], {"z": 2}, k=3) == FailureType.OK

    golden = load_golden(ROOT / "data" / "golden")
    assert len(golden.corpus) >= 3
    assert len(golden.queries) >= 3

    ranker = BagOfWordsRanker()
    ranked = ranker.rank("退款多久到账", golden.corpus, top_k=5)
    assert isinstance(ranked, list) and ranked

    report = score_default(ROOT / "data" / "golden")
    assert "macro" in report and report["macro"]["n"] >= 3
    print("smoke_check OK", report["macro"], report["failures"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
