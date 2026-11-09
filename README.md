# ai-eval-lab — RAG / Agent Evaluation Lab

> Open technical lab + Chinese deep-dives on **how to evaluate retrieval and agents offline** — metrics, golden sets, failure taxonomy, and a runnable scorer. Not a checklist of buzzwords.

**Author:** 马健文 / Evans Owen ([jianwen049-hub](https://github.com/jianwen049-hub)) · Java backend → AI Agent / RAG engineering lab

| | |
|---|---|
| **Lab** | [`lab/`](./lab/) — offline retrieval scorer + golden set + smoke check |
| **Blog** | [`docs/blog/`](./docs/blog/) — Chinese narrative posts with real path citations |
| **Bio** | [`PROFILE.md`](./PROFILE.md) |

---

## Reading guide (EN)

1. Skim [`docs/blog/README.md`](./docs/blog/README.md) for the post map.
2. Read **01** (metrics & why Hit@k alone lies) → **02** (golden set design) → **03** (failure taxonomy & remediation loops).
3. Run the lab offline (no API key):

```bash
cd lab
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
python3 scripts/smoke_check.py
python3 -m eval_lab.cli score
```

Every blog cites real modules under `lab/src/eval_lab/`.

---

## 中文简介

当检索「感觉还行」却在线上翻车时，缺的往往不是更大的模型，而是**可复现的评测闭环**。本仓把 Hit@k / MRR / nDCG、黄金集构建、失败分类写成可跑的 lab，并配套中文深拆博客。

---

## Repo layout

```
ai-eval-lab/
├── README.md
├── PROFILE.md
├── LICENSE
├── docs/blog/          # Chinese deep posts
└── lab/
    ├── requirements.txt
    ├── data/golden/    # queries + relevance judgments
    ├── scripts/smoke_check.py
    └── src/eval_lab/   # metrics, ranker, scorer, taxonomy, cli
```

## License

MIT — see [`LICENSE`](./LICENSE).
