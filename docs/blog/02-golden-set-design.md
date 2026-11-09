# 02 · 黄金集怎么建才不自嗨

## 当时我怎么看这个问题

指标定了之后，下一个坑更大：我一度用「开发时随手问的 15 个问题」当评测集。结果很漂亮——因为这些问题本来就是我对着文档写出来的，chunk 边界、用词、甚至例子都跟语料同源。等于用训练集考自己，还对外说「离线 0.9+」。

真正打脸的是一次需求变更：产品加了「退款时效」类问题。旧黄金集里几乎没有 paraphrase、没有否定句、没有「文档里没写」的应拒答 case。上线后这三类全炸，离线分却纹丝不动。

## 试过什么

1. **从日志里随机抽 query**：真实，但长尾噪声极大，很多是错别字或闲聊，标注成本打穿。
2. **让运营「随便出 50 题」**：覆盖面看人品，容易全是「标准问法」，缺 adversarial。
3. **合成 query（LLM 生成问题再人工过一遍）**：量大，但模型爱生成「文档摘要式问句」，和用户口语差一截；不过滤的话，评测会偏向「会做阅读理解」而不是「会检索」。

## 为什么否决

- 纯开发自问：**分布太甜**，测不出改写、多跳、缺文档。
- 纯日志随机：**标注重复劳动**，且难保证每类失败模式都有最小样本量。
- 纯合成不加约束：**问句分布像模型**，不像用户。

否决「一套题打天下」。黄金集必须**分层、可增量、带标签**，并且把「文档中无答案」显式收进去——否则系统会学会胡编，而 Hit@k 还在涨（因为你根本没测拒答）。

## 最终怎么解

本仓黄金集拆成三份文件（都在 `lab/data/golden/`）：

1. **`corpus.jsonl`**：被检索的段落/文档，带稳定 `doc_id`。
2. **`queries.jsonl`**：每条含 `query_id`、文本、`tags`（如 `paraphrase` / `multi_hop` / `unanswerable`）。
3. **`qrels.jsonl`**：`query_id, doc_id, grade`（2=完全相关，1=部分，0=不写也行，本仓只存 >0）。

构建原则（我现在固定执行的）：

- **至少四类 tags**：原样问法、改写、对比/多约束、不可答。
- **每类不少于 N 条**（本 demo N 较小，但结构在；真实项目我会卡 N≥20）。
- **qrels 允许空**：`unanswerable` 的相关集为空，Hit/MRR 期望为 0，另用 taxonomy 盯「乱答」。
- **doc_id 永不复用改义**：换内容就换 id，避免历史 qrels 脏掉。

加载逻辑在 `lab/src/eval_lab/loader.py`，CLI 一键 `score` 会读这套结构。

## 用到的具体 skill / 技巧清单

| Skill | 怎么用 |
|-------|--------|
| **分层抽样 tags** | `queries.jsonl` 的 `tags` 字段，便于按切片看分数 |
| **分级 relevance（grade）** | qrels 用 1/2，喂给 nDCG，而不是二值一刀切 |
| **稳定 doc_id** | corpus 主键；禁止「同 id 改正文」 |
| **不可答用例** | tag=`unanswerable`，相关集为空 |
| **最小可增量子集** | 先 8–12 条把管道跑通（本仓 demo），再按失败模式加题 |
| **与 ranker 解耦** | loader 只产数据结构，不关心用 embedding 还是词袋 |

## 代码解析（按文件路径）

### `lab/data/golden/corpus.jsonl`

每行一个 JSON：`{"doc_id":"d1","title":"...","text":"..."}`。文本保持短段落，模拟「切好的 chunk」——这样评测的是排序，而不是再切一遍。

### `lab/data/golden/queries.jsonl`

示例字段：`query_id`, `query`, `tags`。博客和 scorer 都靠 `tags` 做切片报告（见 `scorer.score_report` 里按 tag 聚合的分支）。

### `lab/data/golden/qrels.jsonl`

稀疏相关：不是笛卡尔积。只写真正相关的对。`loader.load_qrels()` 会建成 `dict[query_id, dict[doc_id, grade]]`。

### `lab/src/eval_lab/loader.py`

- `load_jsonl(path)`：通用读取
- `load_golden(root)`：返回 `GoldenSet` dataclass（corpus / queries / qrels）
- 校验：query 引用的 doc_id 必须存在；否则直接 fail-fast——脏黄金集比坏指标更危险

### `lab/src/eval_lab/ranker.py`

`BagOfWordsRanker`：tokenize + 余弦。不是生产检索器，而是**可复现的假体**，让评测框架、博客、CI 都能离线绿。真要接 Chroma / 自家 embedding，只换 `ranker` 实现，指标与黄金集不动。

黄金集一旦建对，下一篇的失败分类才有意义——否则你只是在给噪声贴标签。
