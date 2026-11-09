# 01 · 评测指标：Hit@k 为什么会骗人

## 当时我怎么看这个问题

最早做 RAG 的时候，我跟很多人一样：切好文档、塞进向量库、问几个「感觉相关」的问题，看 top-3 里有没有正确答案，然后就敢说「检索质量 OK」。上线两周后，客服开始转发一堆「答非所问」——有的是问句改写了一下就挂；有的是正确答案排在第 4、第 5，被我们写死的 `k=3` 切掉；还有的是 Hit@3 满分，但排第一的是「看起来像、其实偏题」的段落，生成模型一本正经地复述了错误前提。

那时我才意识到：**「召回里出现过正确答案」和「系统能稳定用上正确答案」根本不是一回事。** Hit@k 只回答了前者，却被我当成了后者的代理指标。

## 试过什么

1. **只看 Hit@3 / Hit@5**：快速、好懂，适合 demo。我写了个脚本扫 30 条手工问题，Hit@3 到了 0.87，心里很踏实。
2. **加一层「人工抽查生成答案」**：每周抽 20 条看对不对。主观、不可复现，换个人打分就不一样，也解释不了「到底是检索差还是生成胡编」。
3. **直接上 LLM-as-judge**：用大模型给答案打 1–5 分。成本高、漂移大，而且 judge 经常被「文笔流畅」收买，放过检索错位。

## 为什么否决

- 纯 Hit@k：**位置不敏感**。正确答案在第 1 和第 k 名，分数一样；真实链路却几乎只用 top 几段。
- 纯人工抽查：**没有回归基线**。改完 chunk 大小、换 embedding，说不清是变好还是运气好。
- 过早上 LLM judge：**把两个问题揉在一起**——检索排序问题和生成忠实度问题混在一个分数里，修起来无从下手。

我否决「只用 Hit@k 宣布胜利」，也否决「一上来就全靠 LLM 打分」。先把**检索层**用可复现的离线指标钉死，再谈生成层。

## 最终怎么解

最终方案是三层指标叠在一起，全部可离线、可脚本化：

1. **Hit@k**：仍保留，作为「有没有进窗口」的下限报警。
2. **MRR（Mean Reciprocal Rank）**：惩罚「正确答案太靠后」。倒数排名一平均，排序变差立刻显形。
3. **nDCG@k**：允许「多个相关档位」（完全相关 / 部分相关），对「勉强沾边却排第一」更敏感。

同时强制：**每条 query 必须有 relevance judgment（qrels）**，不能用「我觉得这篇相关」口头说了算。打分入口是 `lab/src/eval_lab/scorer.py`，指标实现在 `metrics.py`，黄金集在 `lab/data/golden/`。

线上仍可以有 LLM judge，但那是**另一条管线**；本仓先把检索离线分打稳。

## 用到的具体 skill / 技巧清单

| Skill | 怎么用在本仓 |
|-------|----------------|
| **Hit@k** | `metrics.hit_at_k`：集合交集，位置不敏感 |
| **MRR** | `metrics.mrr`：首个相关文档的倒数排名 |
| **nDCG@k** | `metrics.ndcg_at_k`：分级相关性 + 折扣增益 |
| **qrels / golden labels** | `data/golden/qrels.jsonl`：query_id → doc_id → grade |
| **离线假排序器** | `ranker.py`：用 bag-of-words 余弦模拟检索，无 API、可复现 |
| **失败切片** | 先按指标掉点的 query 切片，再进 taxonomy（见 03） |

## 代码解析（按文件路径）

### `lab/src/eval_lab/metrics.py`

三个纯函数，输入都是「有序列表 + 相关集合/分级」，方便单测：

- `hit_at_k(ranked_ids, relevant_ids, k)` → 0/1
- `mrr(ranked_ids, relevant_ids)` → 0~1
- `ndcg_at_k(ranked_ids, relevance_grades, k)` → 0~1，内部算 DCG / IDCG

设计原则：**指标层零 I/O**。不读文件、不打日志，只做数学。这样博客里讲「为什么 nDCG 更严」时，可以直接指到公式实现，而不是被文件格式干扰。

### `lab/src/eval_lab/scorer.py`

把「加载黄金集 → 对每条 query 跑 ranker → 聚合指标 → 打印/返回 JSON」串起来。关键点：

- 用 `loader.load_golden()` 读 `queries.jsonl` + `qrels.jsonl` + `corpus.jsonl`
- 对每条 query 调 `ranker.rank(query, corpus, top_k=10)`
- 逐条算 Hit@3 / MRR / nDCG@5，再 macro-average

这里刻意**不**接真实 embedding API：评测框架要先在假检索器上跑通，否则「指标代码」和「模型漂移」会缠在一起，排障极痛。

### `lab/scripts/smoke_check.py`

离线绿灯：导入包、算一组手写 fixture 的指标、确认 golden 文件非空。不需要网络、不需要 key。

### 怎么跑

```bash
cd lab && export PYTHONPATH=src
python3 scripts/smoke_check.py
python3 -m eval_lab.cli score
```

下一篇会讲：黄金集如果建歪了，上面这些指标会一起变成「精致的自嗨」。
