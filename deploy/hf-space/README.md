---
title: LangChain 文档问答 RAG（演示）
emoji: 📚
colorFrom: indigo
colorTo: green
sdk: gradio
sdk_version: 6.32.0
app_file: app.py
pinned: false
license: mit
short_description: 手写 240 题评测集的 LangChain 文档问答系统演示
---

# LangChain 文档问答 RAG（演示版）

这是一个**演示站点**，让人不用 `git clone` 就能点开看效果。完整项目、评测与实验记录在
[XiMoless/rag-docs-qa](https://github.com/XiMoless/rag-docs-qa)。

## 这里和仓库主实验的差别

| 项 | 本演示（免费 CPU） | 仓库主实验（RTX 4060） |
|---|---|---|
| embedding | `BAAI/bge-small-en-v1.5`（384 维，纯英文模型） | `BAAI/bge-m3`（1024 维，多语言） |
| 查询处理 | 必须先把中文问题译成英文关键词，否则向量通道几乎无效 | 中文问题直接进 bge-m3，翻译只用于 BM25 通道 |
| rerank | `cross-encoder/ms-marco-MiniLM-L-6-v2`（约 90MB） | `BAAI/bge-reranker-v2-m3` |
| 用途 | 秒开、可交互 | 产出 `RESULTS.md` 里的指标 |

所以**本页不要引用任何 R@5 / 正确率数字**；所有指标以仓库 `RESULTS.md` 的 E015 / E016 为准。

## 检索链路

中文问题 → DeepSeek 译成英文关键词（保留 API 名与参数名）→ `bge-small-en` 向量 + BM25 两路各取 20 条 →
RRF 融合 → cross-encoder 重排 → 取前 5 段 → DeepSeek 只依据片段生成答案（片段不足就明说没找到）。

## 需要配置的 Secret

- `DEEPSEEK_API_KEY`（必需，否则只能看检索结果、不生成回答）
- 可选：`DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL`

## 语料

LangChain 官方文档 OSS 部分，401 页 → 10994 个 chunk（标题感知切分，size 700 / overlap 120）。
语料只含文档正文与 URL，供问答检索使用，版权归 LangChain 所有。
