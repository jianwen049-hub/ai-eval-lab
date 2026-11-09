# eval_lab — offline RAG evaluation

No API key. Bag-of-words ranker + Hit@k / MRR / nDCG + failure taxonomy.

```bash
cd lab
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
python3 scripts/smoke_check.py
python3 -m eval_lab.cli score
```

Layout: `src/eval_lab/{metrics,ranker,loader,taxonomy,scorer,cli}.py` + `data/golden/`.
