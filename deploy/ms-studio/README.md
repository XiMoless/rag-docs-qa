# LangChain 文档问答 RAG（ModelScope 创空间演示版）

把 LangChain 官方文档 OSS 部分（401 页 / 450 万字符，切分后 10994 个 chunk）做成一个可提问的知识库：
中文问题 → 译成英文关键词 → 向量 + BM25 双路召回 → RRF 融合 → 取 5 段 → 只依据片段生成答案并给出来源链接。

## 与主实验的关系

仓库主实验（[GitHub: XiMoless/rag-docs-qa](https://github.com/XiMoless/rag-docs-qa)）用 `bge-m3`（1024 维，多语言）
+ `bge-reranker-v2-m3` 重排，240 题评测集上 R@5 0.664、正确率 0.761、240 条全量人工复核幻觉率 2.1%。

**本演示站点为免费 CPU 做的妥协**：

| 项 | 演示（这里） | 主实验 |
|---|---|---|
| embedding | `bge-small-en-v1.5`（384 维，纯英文） | `bge-m3`（1024 维，多语言） |
| 查询处理 | 必须先译成英文关键词 | 中文直打 |
| 重排 | ❌ 不做（免费 CPU 跑不动可用的 cross-encoder） | ✅ `bge-reranker-v2-m3` |
| 指标 | 不宣称 | R@5 0.664 / acc 0.761 / P95 6.11s（E015） |

所以：**本页不引用任何 R@5 或正确率数字**，要数字请看主仓库 `results/RESULTS.md`。

## 文件

- `app.py`：Gradio 应用（启动时加载 `artifacts/` 的向量与 chunk）
- `artifacts/`：`chunks.jsonl`（10994 条）、`vectors.npy`（384 维，float16，8.4MB）、`meta.json`
- `requirements.txt`：依赖

## 环境变量

在创空间「设置 → 环境变量」里加：

- `DEEPSEEK_API_KEY`：必填，否则只展示检索结果不生成答案

## 数据来源与合规

语料为 `https://docs.langchain.com/oss/` 下的公开文档，只做检索问答使用，页面内均给出来源 URL。
