# 03 · 失败分类与修复闭环

## 当时我怎么看这个问题

有了指标和黄金集，我以为「离线分掉了就去调 chunk / top-k」就行。现实是：同样掉 0.1 的 MRR，根因可能完全不同——有时是 query 改写词不在 chunk 里（词面鸿沟），有时是相关文档被切碎到两段各一半（chunking），有时是负样本太像正样本（近义干扰），有时是标注本身错了。

如果不分类，团队会陷入「玄学调参」：今天加 hybrid，明天改 embedding，后天扩 k，分数晃来晃去，没人说得清因果。

## 试过什么

1. **只看错题列表**：把 Hit@3=0 的 query 打出来给人看。信息量不够，开会时各猜各的。
2. **按模型锅 / 数据锅二分**：过于粗，推不动具体改动。
3. **端到端再跑一遍生成**：贵，而且把检索失败和幻觉搅在一起。

## 为什么否决

否决「不分类直接调参」。评测的价值不只是一个标量分数，而是**把失败指到可执行的修复动作上**。没有 taxonomy，指标只是仪表盘上的红灯，不是工单。

## 最终怎么解

本仓定义一组**检索层**失败类型（`lab/src/eval_lab/taxonomy.py`），对每条错题自动打标（规则版，离线可跑）：

| 类型 | 含义 | 典型修复 |
|------|------|----------|
| `MISS_ALL` | 相关文档全不在 top-k | 改写增强 / embedding / 召回通道 |
| `LOW_RANK` | 进了窗口但太靠后 | rerank、调 k、微调相似度 |
| `NEAR_MISS` | 命中「部分相关」却当完全相关用 | 调 grade、补正样本、加重排序特征 |
| `LABEL_SUSPECT` | 高分但人工抽查像标错 | 回标 qrels |
| `UNANSWERABLE_LEAK` | 不可答题却捞到高分文档 | 拒答策略 / 阈值 |

`scorer` 在逐条打分后调用 `taxonomy.classify_case(...)`，报告里除了 macro 指标，还有**失败类型直方图**。我的习惯是：每次改动只宣称「消灭某一类失败」，而不是「总分 +2%」——后者太容易用别的回归换来。

## 用到的具体 skill / 技巧清单

| Skill | 怎么用 |
|-------|--------|
| **Failure taxonomy** | `taxonomy.py` 枚举 + 规则分类 |
| **Case-level report** | 每条 query 保留 ranked_ids / grades / failure_type |
| **切片对比** | 按 tag × failure_type 交叉看 |
| **Rerank 触发条件** | `LOW_RANK` 占比高再上 cross-encoder，避免过早加复杂度 |
| **Chunking 回溯** | `MISS_ALL` 且相关 doc 文本被截断时，回查切分 |
| **Regression gate** | CI 跑 `smoke_check` + `score`，失败类型增多即红灯 |

## 代码解析（按文件路径）

### `lab/src/eval_lab/taxonomy.py`

- `FailureType`：字符串枚举
- `classify_case(ranked_ids, grades, k, tags)`：纯规则  
  - 无相关且 tag 含 unanswerable → 看是否「捞得太欢」  
  - 相关全不在 top-k → `MISS_ALL`  
  - 相关在 top-k 但首位不是 → `LOW_RANK`  
  - 否则 `OK`

刻意做成规则引擎而不是再调一个 LLM：分类器本身必须稳定，否则「失败分类」也会漂移。

### `lab/src/eval_lab/scorer.py` + `cli.py`

`cli score` 打印：

1. 整体 Hit@3 / MRR / nDCG@5  
2. 按 tag 的切片  
3. 失败类型计数  

JSON 可重定向到文件，便于跟上次 diff。

### `lab/scripts/smoke_check.py`

除了指标单测，还跑两条人造 case：一条 `MISS_ALL`、一条 `OK`，锁定分类器不被重构改坏。

---

这三篇合在一起，是我做 RAG 评测的最小闭环：**指标不骗人 → 黄金集不自嗨 → 失败能归类到动作**。代码都在 `lab/src/eval_lab/`，可以当模板往真实语料上长。
