"""CLI entry: python -m eval_lab.cli score"""
from __future__ import annotations

import argparse
import json
import sys

from eval_lab.scorer import score_default


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eval_lab")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_score = sub.add_parser("score", help="Score golden set offline")
    p_score.add_argument("--json", action="store_true", help="Print full JSON")
    args = parser.parse_args(argv)

    if args.cmd == "score":
        report = score_default()
        if args.json:
            json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
        else:
            m = report["macro"]
            print(f"macro  n={m['n']}  Hit@3={m['hit@k']:.3f}  MRR={m['mrr']:.3f}  nDCG@5={m['ndcg@k']:.3f}")
            print("by_tag:")
            for tag, v in report["by_tag"].items():
                print(f"  {tag:16s} n={v['n']}  Hit@3={v['hit@k']:.3f}  MRR={v['mrr']:.3f}  nDCG@5={v['ndcg@k']:.3f}")
            print("failures:", report["failures"])
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
