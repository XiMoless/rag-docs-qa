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
| 评测集 v1（100 题，4 种题型） | ✅ 52 单跳 / 24 综合 / 16 改写 / 8 无答案，0 error 0 warning |
| 消融表（2 切分 × 4 检索 = 8 行） | ✅ E101–E108 |
| 主结果（rerank 版） | ✅ E004：R@5 0.522 / 正确率 0.582（v1 100 题，主口径） |
| 扩展集 240 题复跑 | ✅ E005：R@5 0.586 / 正确率 0.602；v1 子集精确复现（0.587） |
| 幻觉率人工抽检（100 条全量复核） | ✅ 幻觉率 2.0%（2/100）· 弃答率 27% |
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

**端到端（E004，heading + RRF + rerank，100 题）**：正确答案率 **0.582**（judge 三档，1/0.5/0 取均值），无答案题 **8/8 全部拒答**，P50 3.23s / P95 4.81s（RTX 4060 单卡，含检索）。

**人工全量审计（100 题，4 人分工，口径见 `results/hallucination_summary.md`）**：OK 71 / 弃答 27 / 幻觉 2 / 错答 0；**幻觉率 2.0%**（strict 2.7%，排除弃答）。两条幻觉性质不同：一条把 HITL 的 `Command(resume=)` 当成崩溃续跑（名词对、场景错），另一条是「片段里没有 X」被片段本身反证——**弃答也会撒谎，不能免检**。分题型看：单跳 0 幻觉，多跳 0 幻觉但 46% 弃答，改写题幻觉率 16.7%。主要失败模式是**答不出**（27%），不是编造。

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
#    加 rerank（E004 主结果）：
.\.venv\Scripts\python.exe -m src.eval --retrieval rrf --judge --rerank --append-results E004

# 7) 检索消融（不花 API 钱，约 6 分钟）
.\.venv\Scripts\python.exe -m src.ablation

# 8) 幻觉抽检表（跑完 eval --out 之后）
.\.venv\Scripts\python.exe -m src.sample_hallucination --detail results\eval_E004.jsonl --exp-id E004
```

## 目录

```
src/
  fetch_corpus.py   抓 sitemap 范围内的文档，转 Markdown，落 front-matter
  ingest.py         标题感知切分（heading / fixed 两种），带原文偏移
  index.py          bge-m3 向量 + faiss + BM25
  ask.py            检索（vec / bm25 / RRF）→ prompt → DeepSeek 生成，带引用
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

1. 语料是**英文文档 + 中文提问**的跨语言场景，bge-m3 能应对但不保证最优——代价是 BM25 这一路基本失效（E102/E106），混合检索的红利只能靠 rerank 兑现。
2. Python 与 JavaScript 双份文档语义近重复，会互相挤占 top-k（已在 `RESULTS.md`「已知问题」记录）。
3. 部分页面正文里混有产品名对比表（`concepts/products`），可能干扰领域判断。
4. 无 answerability 小模型，拒答依赖生成侧提示词；目前 8/8 无答案题拒答成功，但样本小。
5. 正确率仍只有 0.582：多跳题 R@5 仅 0.375 是主要瓶颈，单跳题已经到 0.654。

## 数据来源与合规

- 全部内容来自 `https://docs.langchain.com/`，通过其公开 `sitemap.xml` 抓取，仅用于本地离线评测，不重新分发全文；`data/` 已在 `.gitignore` 中排除。
- chunk 均保留 `url` 与 `heading_path`，任何答案都能回溯到原始页面。
