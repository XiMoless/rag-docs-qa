# 评测集出题规范（v1，100 题）

> 目标：每题都能**判对错**、都能**定位到原文 chunk**。这是全项目唯一不能砍的东西。

## 输出格式

UTF-8、每行一个 JSON 对象、无空行，写到 `eval/parts/v1_partX.jsonl`：

```json
{"qid": "v1-A-001", "question": "用户会怎么问（自然语言，可以中英混写）", "gold_answer": "标准答案要点，2-4 句，必须能在 source_ids 指向的 chunk 原文里找到依据", "source_ids": ["oss__python__langchain__agents#012"], "type": "single-hop", "difficulty": "easy", "notes": "为什么出这题 / 考什么能力"}
```

字段约束：

| 字段 | 要求 |
|---|---|
| `qid` | `v1-<part>-<三位序号>`，如 `v1-A-007`，全集合内唯一 |
| `question` | ≥8 字符，像真实用户提问（不要照抄小标题，不要带「根据第 12 个 chunk」这种痕迹） |
| `gold_answer` | 2–4 句，覆盖要点；**每个事实都必须真的出现在 source chunk 里**；无答案题固定写 `本题无答案` |
| `source_ids` | 至少 1 个真实存在于 `data/processed/chunks.jsonl` 的 `chunk_id`；multi-hop 必须 ≥2 个且来自不同文档或不同章节 |
| `type` | `single-hop` / `multi-hop` / `paraphrase` / `no-answer` |
| `difficulty` | `easy` / `medium` / `hard` |
| `notes` | 一句话：这题考什么（如「考 interrupt 的 per-call 与 batched 区别」） |

## 题型配比（每人 25 题）

| type | 数量 | 说明 |
|---|---|---|
| single-hop | 13 | 答案在单个 chunk 里，直接查得到 |
| multi-hop | 6 | 需要 2 个以上 chunk 拼起来（如「A 和 B 的区别」「先做 X 再做 Y」） |
| paraphrase | 4 | 用**完全不同于文档措辞**的口语问法问同一件事（考语义检索），如文档写「interruptOn policy」，题目问「怎么让 Agent 停下来等人点确认」 |
| no-answer | 2 | 语料里**确实没有**答案的题，必须验证过：见下 |

### no-answer 题怎么出（最容易出错，严格按此做）

只能问**明显不属于 LangChain 文档范围**的东西，并在 `notes` 里写清你如何验证「文档里没有」：

- 问竞品库：LlamaIndex、Haystack、DSPy、Semantic Kernel、vLLM、Ollama（作为推理引擎时的显存参数）
- 问不存在的能力：LangChain 的付费价格表、LangSmith 的 SLA、某个编造的 API 名

禁止用「文档可能有但我没找到」的东西出无答案题。

**验证方式（照抄这段，别再找不存在的 flag）**：`validate_eval.py` 没有 `--check-no-answer` 这个参数，它只校验结构与 source 存在性，**判断不了「语料里真的没有」**。必须自己全库计数，把命令和结果写进该题 `notes`：

```powershell
cd D:\dshwork\rag-docs-qa
Select-String -Path data\processed\chunks.jsonl -Pattern 'IngestionPipeline','docstore','cost_limit','max_cost' -SimpleMatch | Measure-Object -Line
```

要求：**核心术语命中 0**。若命中的是「竞品名在对比表里被提了一句」（例如 LlamaIndex 出现在 Runtime/Framework/Harness 选型表），要说明「只作为产品名出现、无实现细节」，这类仍可用于无答案题；若命中的是真实现细节，换题。

## 怎么取材（重要）

1. `data/processed/chunks.jsonl` 有 10994 行、4.2MB，**不要整文件读进上下文**。用 python 抽样：

```powershell
cd D:\dshwork\rag-docs-qa
.\.venv\Scripts\python.exe -c "import json;rows=[json.loads(l) for l in open('data/processed/chunks.jsonl',encoding='utf-8')];sub=[r for r in rows if r['doc_id'].startswith('oss__python__langchain')];print(len(sub));import random;random.seed(7);[print(r['chunk_id'],'|',r['heading_path'][:70],'|',r['chars']) for r in random.sample(sub,60)]"
```

2. 挑「有实质内容」的 chunk：`chars >= 200`，跳过纯链接页、纯代码页、纯报错码表。
3. 选题覆盖不同主题（concepts / agents / middleware / tools / memory / streaming / retrieval / testing…），不要全挤在一个页面。
4. 每题写完，立刻用 chunk 原文核对 `gold_answer` 的每个事实——**写不出原文依据的题直接删**。

## 自检（提交前必须全绿）

```powershell
cd D:\dshwork\rag-docs-qa
.\.venv\Scripts\python.exe -m src.validate_eval --file eval/parts/v1_partA.jsonl --part A --expect 25
```

规范：`gold_answer` 里出现数字/API 名时，validator 会检查该字符串是否出现在 source chunk 中；不通过就改题或换 source。
