"""Load golden set JSONL files."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {e}") from e
    return rows


@dataclass
class GoldenSet:
    corpus: list[dict[str, Any]]
    queries: list[dict[str, Any]]
    qrels: dict[str, dict[str, float]]  # query_id -> {doc_id: grade}


def load_golden(root: Path) -> GoldenSet:
    corpus = load_jsonl(root / "corpus.jsonl")
    queries = load_jsonl(root / "queries.jsonl")
    raw_qrels = load_jsonl(root / "qrels.jsonl")

    corpus_ids = {d["doc_id"] for d in corpus}
    qrels: dict[str, dict[str, float]] = {}
    for row in raw_qrels:
        qid, did, grade = row["query_id"], row["doc_id"], float(row["grade"])
        if did not in corpus_ids:
            raise ValueError(f"qrels doc_id={did!r} not in corpus")
        qrels.setdefault(qid, {})[did] = grade

    query_ids = {q["query_id"] for q in queries}
    for qid in qrels:
        if qid not in query_ids:
            raise ValueError(f"qrels query_id={qid!r} not in queries")

    return GoldenSet(corpus=corpus, queries=queries, qrels=qrels)
