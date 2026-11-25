# LangChain 文档问答（垂直 RAG）

把 LangChain 官方 OSS 文档（401 页 / 450 万字符）建成可检索的知识库，用 RAG 回答「某个 API 到底怎么用、v0.x 到 v1 改了什么」这类问题，并给出可点开的原文出处。

> 为什么需要它：LangChain 正处在 v1 改名期，模型凭记忆回答会给出**已废弃的 API**——这类幻觉在文档问答里最贵。同时 401 页塞不进任何上下文，必须检索。

## 当前进度

| 环节 | 状态 |
|---|---|
| 语料抓取 + 清洗 | ✅ 401 页 / 4,500,016 字符 / 7 页短页跳过 |
| 切分 | ✅ heading 感知，size 700 / overlap 120 → 10994 chunks |
| 向量索引 | ✅ `BAAI/bge-m3` 1024 维 + faiss IndexFlatIP |
| 关键词索引 | ✅ rank_bm25，vocab 14794 |
| 检索（vec / bm25 / RRF 混合 / +rerank） | ✅ 可跑，4 路都进过消融 |
| 生成 + 引用 | ✅ `src/ask.py`（需 `DEEPSEEK_API_KEY`） |
| 邻接 chunk 扩展（small-to-big，锚点优先） | ✅ E007：正确率 +7.0pp，P95 +0.37s |
| 查询翻译（中文问 → 英文关键词，修词法通道） | ✅ E008：正确率再 +8.7pp |
| 评测集 v1（100 题，4 种题型） | ✅ 52 单跳 / 24 综合 / 16 改写 / 8 无答案，0 error 0 warning |
| 消融表（2 切分 × 4 检索 = 8 行） | ✅ E101–E108 |
| 主结果（扩展 + 翻译 + rerank + 证据窗口 8） | ✅ **E015：240 题 R@5 0.664 / 正确率 0.761 / 无答案 20-20 / P95 6.11s**（v1 子集 0.766、v2 子集 0.758，两套题不反转；重复跑波动 ±2.7pp） |
| 扩展集 240 题复跑 | ✅ E015 在 240 题上复跑主配置：v1 子集 0.766 vs v2 子集 0.758，结论不随题集反转 |
| 幻觉率人工全量审计 | ✅ **240 条全量复核：幻觉率 2.1%（guarded）/ 2.3%（strict）· 弃答率 9.2% · 人工正确率 88.8%**（E015 配置） |
| 多跳专项（提示词加规则 / 压低词法权重） | ❌ 两个方向都证伪：E009 acc −7.1pp；权重 1:0.5 R@5 −6.5pp（负结果已入台账） |
| 「主题在、事实不在」拒答题（v3） | ✅ 12 道，全部经全库词面检索 0 命中验证；`eval_set_v3.jsonl` = 252 题（无答案 32 道） |
| 成本计量 | ✅ `docs/成本.md`：240 题评测实测 561K in / 100K out，查询翻译另计 33K / 3K |
| 网页 Demo | ✅ `demo/app.py`（Gradio） |

真实数字只认 `results/RESULTS.md` 的表格行，README 不单独宣称任何指标。

## 结果（数字全部来自 `results/RESULTS.md`，按行 id 可查）

**检索消融（E101–E108）**：评测集 v1 的 92 道可答题，只算检索指标。

| 切分 | 检索 | Recall@5 | MRR |
|---|---|---|---|
| heading | 纯向量 | 0.446 | 0.318 |
| heading | BM25 | 0.185 | 0.124 |
| heading | 混合 RRF | 0.370 | 0.267 |
| heading | **混合 RRF + rerank** | **0.522** | **0.369** |
| fixed | 纯向量 | 0.163 | 0.099 |
| fixed | BM25 | 0.065 | 0.054 |
| fixed | 混合 RRF | 0.152 | 0.096 |
| fixed | 混合 RRF + rerank | 0.185 | 0.107 |

三个反直觉结论（分析见 `RESULTS.md`）：① BM25 在这套「中文提问 × 英文语料」里词法失效（R@5 0.185），② RRF 等权融合反而比纯向量低 7.6pp，因为弱的那一路把对的挤下去，③ 加 rerank 才回到 0.522——cross-encoder 天然跨语言，能吃掉融合噪音，代价 P95 ×4.4。④ 固定长度切分全线崩（最好 0.185），切分必须跟文档结构走。

> ① 后来被 E008 修正了归因：BM25 不是坏通道，是**查询语言错了**。同一个实现、同一批题，查询翻成英文后 R@5 从 0.185 到 0.500。

**注意噪声**：同一配置重复运行会差 **2.7pp**（E011 0.799 vs E013 0.772）。本表里 ≥3pp 的差异才算结论，2pp 级别的一律当噪声——细节见 `RESULTS.md` 的 E013 分析。

**端到端（E004 基线，heading + RRF + rerank，100 题）**：正确答案率 **0.582**（judge 三档，1/0.5/0 取均值），无答案题 **8/8 全部拒答**，P50 3.23s / P95 4.81s（RTX 4060 单卡，含检索）。当前主线 **E010 = 0.772**，见下表。

**三个改进各带来什么（同一条 100 题）**：

| 版本 | 改动 | R@5 | 正确率 | 单跳 | 多跳 | 改写 | P95 |
|---|---|---|---|---|---|---|---|
| E004 | 基线（RRF + rerank） | 0.522 | 0.582 | 0.692 | 0.438 | 0.438 | 4.81s |
| E007 | + 邻接扩展（锚点优先） | 0.522 | 0.652 | 0.760 | 0.500 | 0.531 | 5.18s |
| E008 | + 查询翻译（中文→英文关键词） | 0.587 | 0.739 | 0.827 | 0.562 | 0.719 | 5.47s |
| **E010** | + 证据窗口 5→8 段 | **0.598** | **0.772** | 0.846 | 0.625 | 0.750 | 4.72s |
| E011–E013 | 窗口 12 / 16 / 12（重复跑） | 0.598 | 0.799 / 0.772 / 0.772 | — | — | — | ~5s |
| **E015** | 主配置在 **240 题**上复跑（v1+v2） | **0.664** | **0.761** | 0.827 | 0.647 | 0.724 | 6.11s |
| E009 | 反例：提示词加「先列要点再合并」规则 | 0.598 | 0.668 | 0.750 | 0.542 | 0.594 | 7.02s |

- **邻接扩展**修复的是「切片把答案劈开」（人工审计里 D 段 8 条弃答全由此而来）。第一次实现用交错排列，+3.8pp 但出现 4 条 1.0→0.0 硬回归——长邻居把锚点挤出 6000 字符预算。改成**锚点优先 + 邻居标注**才拿到 +7.0pp。
- **查询翻译**修复的是词法通道：同一个 BM25 实现、同一批题，查询从中文换成英文关键词后 **R@5 0.185 → 0.500**。原来的结论「BM25 失效」对，但归因「BM25 不适合中文语料」是错的——它只是没拿到能匹配的语言。改写题因此从 0.531 涨到 0.719。
- **证据窗口 5→8** 是照着「多跳题答不对是因为一次只给 5 段、凑不齐两处证据」这个假设做的，多跳 0.562 → 0.625，而且**延迟反而从 P50 4.24s 降到 3.35s**——证据给够后模型不再反复「片段里没有找到」，答案更短更肯定。
- **反例 E009**：给提示词加「先逐片段列要点再合并」的规则，正确率反而 −7.1pp（答案长度 +59%）。judge 评的是结论，不是推理过程——这条负结果和三个正结果一样进了台账。

**人工全量审计（100 题，4 人分工，口径见 `results/hallucination_summary.md`）**：OK 71 / 弃答 27 / 幻觉 2 / 错答 0；**幻觉率 2.0%**（strict 2.7%，排除弃答）。两条幻觉性质不同：一条把 HITL 的 `Command(resume=)` 当成崩溃续跑（名词对、场景错），另一条是「片段里没有 X」被片段本身反证——**弃答也会撒谎，不能免检**。分题型看：单跳 0 幻觉，多跳 0 幻觉但 46% 弃答，改写题幻觉率 16.7%。主要失败模式是**答不出**（27%），不是编造。

**240 题全量复核（E015 配置，v1+v2，8 人分工，明细见 `results/hallucination_summary_240.md`）**：OK 213 / 弃答 22 / 幻觉 5 / 错答 0；**幻觉率 2.1%（guarded）、2.3%（strict）**，弃答率从 E004 的 27% 降到 **9.2%**，人工正确率 88.8%。两个新结论：①**改进压下去的是「答不出」，不是「编造」**——弃答率砍掉三分之二，幻觉率几乎不动；②**幻觉随题难上升**（v2 3.2% 是 v1 的 3 倍），5 条幻觉里 4 条都是「拿邻近语境的 API 硬凑」（JS 参数搬到 Python、HITL 的 resume 当崩溃续跑、`config["configurable"]` 当运行时配置）。judge 0.761 与人工 88.8% 差 12.7pp，引用时别混口径。

**两次 bug 也留在台账里**：E001 作废（prompt 漏传 `{question}`，模型答「你没提出问题」），E003 部分作废（rerank 作用在已截断的 5 个候选上）。修这两处共带来 +29pp。

## 快速开始

```powershell
cd D:\dshwork\rag-docs-qa
# 1) 装依赖（venv 复用全局 torch，避免重装 CUDA 版）
python -m venv --system-site-packages .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2) 填 key（.env 已被 gitignore）
#    DEEPSEEK_API_KEY=sk-xxxx

# 3) 建库（约 5 分钟，4060 上）
.\.venv\Scripts\python.exe -m src.fetch_corpus     # 抓语料 -> data/raw/*.md
.\.venv\Scripts\python.exe -m src.ingest           # 切分 -> data/processed/chunks.jsonl
.\.venv\Scripts\python.exe -m src.index            # 向量 + BM25 -> index/

# 4) 提问
.\.venv\Scripts\python.exe -m src.ask "checkpointer 和 store 分别存什么？" --show-chunks

# 5) 网页 Demo
.\.venv\Scripts\python.exe demo\app.py

# 6) 评测
.\.venv\Scripts\python.exe -m src.eval --set eval\eval_set_v1.jsonl --retrieval rrf --judge
#    加 rerank（E004 基线）：
.\.venv\Scripts\python.exe -m src.eval --retrieval rrf --judge --rerank --append-results E004
#    加邻接扩展（E007）：锚点优先，扩展只补全上下文、不改排序
.\.venv\Scripts\python.exe -m src.eval --retrieval rrf --judge --rerank --expand 1 --append-results E007
#    再加查询翻译（E008，当前主线）：
.\.venv\Scripts\python.exe -m src.eval --retrieval rrf --judge --rerank --expand 1 --query-expand --append-results E008
#    只测词法通道被翻译修好了多少（不跑生成，约 2 分钟）：
.\.venv\Scripts\python.exe -m src.eval --retrieval bm25 --query-expand --dry-run

# 7) 检索消融（不花 API 钱，约 6 分钟）
.\.venv\Scripts\python.exe -m src.ablation

# 8) 幻觉抽检表（跑完 eval --out 之后）
.\.venv\Scripts\python.exe -m src.sample_hallucination --detail results\eval_E004.jsonl --exp-id E004

# 9) 扩到 240 题（v1 100 + v2 五段 140，需要 API key，约 14 分钟）
.\.venv\Scripts\python.exe -m src.build_eval_set --version all   # -> eval/eval_set_all.jsonl
.\.venv\Scripts\python.exe -m src.validate_eval --file eval\eval_set_all.jsonl --merge-check --expect 240
.\.venv\Scripts\python.exe -m src.eval --set eval\eval_set_all.jsonl --retrieval rrf --judge --rerank --append-results E005
.\.venv\Scripts\python.exe -m src.split_metrics --detail results\eval_E005.jsonl --md   # v1 / v2 拆开看

# 10) 人工审计汇总（把 4 份 eval/audit/part*.jsonl 汇总成幻觉率）
.\.venv\Scripts\python.exe -m src.aggregate_audit              # -> results/hallucination_summary.md
```

## 目录

```
src/
  fetch_corpus.py   抓 sitemap 范围内的文档，转 Markdown，落 front-matter
  ingest.py         标题感知切分（heading / fixed 两种），带原文偏移
  index.py          bge-m3 向量 + faiss + BM25
  ask.py            检索（vec / bm25 / RRF / rerank / 邻接扩展）→ prompt → DeepSeek 生成，带引用
  query_expand.py   中文问题 → 英文检索关键词（DeepSeek，带缓存），修 BM25 的中英错配
  eval.py           Recall@k / MRR 自动算 + judge 判答案正确率
  ablation.py       2 切分 × 4 检索的召回消融（不需要 API key）
  sample_hallucination.py  幻觉抽检表（H1 未拒答 / H2 引用不支持 / H3 无引用 / MISS 未作答）
  build_eval_set.py 合并分片评测集
  validate_eval.py  评测集结构校验 + 事实回溯校验
  config.yaml       全部可调参数（改一行就要在 RESULTS.md 新起一行）
data/               raw（语料，gitignored）/ processed（chunk 表，gitignored）
index/              faiss / bm25 / meta（gitignored，可重建）
eval/               AUTHORING.md（出题规范）/ parts/ / eval_set_v1.jsonl / trial10.md
results/RESULTS.md  实验台账（唯一的数字权威）
demo/app.py         Gradio 单页面
docs/项目定义.md     领域、指标口径、不做的事
```

## 设计决策

| 决策 | 选择 | 理由 |
|---|---|---|
| 语料范围 | `docs.langchain.com/oss/`（408 URL → 401 有效页） | 排除 langsmith 营销页与 1222 个 API reference 噪音；同源、结构稳定、可公开引用 |
| Embedding | 本地 `BAAI/bge-m3` | DeepSeek 无 embedding 接口；4060 可跑，不引入第二家 key；中英混检效果好 |
| 生成 / judge | DeepSeek `deepseek-chat`，temperature 0 | 便宜、稳定、JSON 可控；judge 与生成同模型但提示词固定版本，降低口径漂移 |
| 切分 | 标题感知为主，固定长度为对照 | 文档型语料按小节切，天然对齐「答案在哪一节」；两种切分正好做消融 |
| 混合检索 | RRF（k=60） | 不需要调权重，向量与 BM25 的分数尺度差异被排名抹平 |
| 拒答 | 无答案题单列一类 | 「找不到就说找不到」是文档问答的核心体验，必须有量化 |

## 评测口径（详见 `docs/项目定义.md`）

- **Recall@5**：前 5 个 chunk 命中 gold `source_ids` 任意一个记 1
- **答案正确率**：judge 三档 1 / 0.5 / 0
- **幻觉率**：100 条人工抽检「无依据」占比
- **P95 延迟**：端到端（检索 + 生成）P95

## 已知局限

1. 语料是**英文文档 + 中文提问**的跨语言场景：bge-m3 能应对，但 BM25 原来完全失效（R@5 0.185）；E008 用查询翻译把它修到 0.500，**代价是每问多一次翻译调用**，且翻译质量本身成为新的失败点。
2. 查询翻译是**额外的 API 依赖**：离线场景或断网时词法通道会退回 0.185 那个水平；`tmp/qe_cache.json` 只缓存跑过的题。
3. Python 与 JavaScript 双份文档语义近重复，会互相挤占 top-k（已在 `RESULTS.md`「已知问题」记录）。
4. 部分页面正文里混有产品名对比表（`concepts/products`），可能干扰领域判断。
5. 无 answerability 小模型，拒答依赖生成侧提示词；目前 8/8（v1）、20/20（240 题）拒答成功，但样本小。
6. 正确率 0.772（E010）里，**多跳题仍只有 0.625**，单跳 0.846——多跳天花板来自「一次检索凑不齐两处证据」，加提示词规则（E009）与压词法权重都试过、都无效（见 `docs/多跳改进方案.md`）。
7. E010 的代价是**上下文变长**：100 题共 230K input / 41K output tokens（约 2.3K input／题），P95 4.72s 反而低于 E008 的 5.47s。成本只按 token 计量，未折算金额。

## 数据来源与合规

- 全部内容来自 `https://docs.langchain.com/`，通过其公开 `sitemap.xml` 抓取，仅用于本地离线评测，不重新分发全文；`data/` 已在 `.gitignore` 中排除。
- chunk 均保留 `url` 与 `heading_path`，任何答案都能回溯到原始页面。
