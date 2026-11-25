"""问答 CLI：检索（向量 / BM25 / RRF 混合）→ 拼 prompt → DeepSeek 生成带引用回答。

用法：
    python -m src.ask "LangGraph 的 checkpointer 怎么用"
    python -m src.ask "..." --retrieval bm25 --show-chunks

先决：
    1. 跑过 src.ingest 与 src.index
    2. .env 里有 DEEPSEEK_API_KEY（或进程环境变量）
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import re
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = ROOT / "index"
CHUNKS = ROOT / "data" / "processed" / "chunks.jsonl"

MODEL_NAME = "BAAI/bge-m3"

SYSTEM_PROMPT = """你是 LangChain 官方文档的问答助手。规则：

1. 只根据下面给出的【文档片段】回答，不要用你记忆里的知识补充。
2. 每个结论后面用 [编号] 标注来源，例如 [2]。编号必须来自片段列表。
3. 如果片段不足以回答，直接说「给出的文档里没有找到能回答这个问题的内容」，并说明缺什么，不要猜。
4. 如果片段里 API 名称、参数看起来与用户说法不一致，以片段为准，并指出差异。
5. 回答用中文，代码块保留原语言。先给结论，再给最小可用示例。

【文档片段】
{context}

【问题】
{question}
"""


# v2：针对「多跳题好检不好答」加的生成端约束（E005 分析：v2 多跳 R@5 涨 24pp 而正确率只涨 1.3pp）
SYSTEM_PROMPT_V2 = """你是 LangChain 官方文档的问答助手。规则：

1. 只根据下面给出的【文档片段】回答，不要用你记忆里的知识补充。
2. 每个结论后面用 [编号] 标注来源，例如 [2]。编号必须来自片段列表。
3. 如果片段不足以回答，直接说「给出的文档里没有找到能回答这个问题的内容」，并说明缺什么，不要猜。
4. 如果片段里 API 名称、参数看起来与用户说法不一致，以片段为准，并指出差异。
5. 回答用中文，代码块保留原语言。先给结论，再给最小可用示例。
6. 如果答案需要**拼接多个片段**才能成立：先逐条写出每个相关片段各自说明了什么（每条带 [编号]），再写出合并后的结论。不要只引一个片段就给结论。
7. 数字、默认值、枚举值、函数名必须与片段原文逐字一致，不得改写、估算或四舍五入；片段没写默认值就说「片段未给出默认值」。
8. 标注为「同页相邻片段·非检索命中」的片段只用于补全上下文，引用它时要说明它是补全片段而非检索命中。

【文档片段】
{context}

【问题】
{question}
"""


def load_dotenv() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


class Retriever:
    def __init__(self, chunks_path: Path | str | None = None, index_dir: Path | str | None = None) -> None:
        import faiss
        from rank_bm25 import BM25Okapi
        from sentence_transformers import SentenceTransformer

        self.chunks_path = Path(chunks_path or CHUNKS)
        self.index_dir = Path(index_dir or INDEX_DIR)
        self.chunks = [json.loads(line) for line in self.chunks_path.open(encoding="utf-8")]
        self.index = faiss.read_index(str(self.index_dir / "langchain_docs.faiss"))
        with (self.index_dir / "langchain_docs_bm25.pkl").open("rb") as f:
            saved = pickle.load(f)
        self.bm25: BM25Okapi = saved["bm25"]
        self.embedder = SentenceTransformer(MODEL_NAME, device="cuda")
        self._reranker = None

    def embed(self, q: str) -> np.ndarray:
        return self.embedder.encode([q], normalize_embeddings=True, convert_to_numpy=True).astype("float32")

    def vector(self, q: str, k: int) -> list[tuple[int, float]]:
        k = min(k, len(self.chunks))
        scores, idx = self.index.search(self.embed(q), k)
        return [(int(i), float(s)) for i, s in zip(idx[0], scores[0]) if i >= 0]

    def keyword(self, q: str, k: int) -> list[tuple[int, float]]:
        tokens = [t.lower() for t in re.findall(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]", q)]
        scores = self.bm25.get_scores(tokens)
        top = np.argsort(scores)[::-1][:k]
        return [(int(i), float(scores[i])) for i in top]

    def rerank(self, q: str, hits: list[tuple[int, float]], top_n: int, model_name: str = "BAAI/bge-reranker-v2-m3") -> list[tuple[int, float]]:
        """对候选做 cross-encoder 重排；返回 (chunk_idx, rerank_score)。"""
        from sentence_transformers import CrossEncoder

        if self._reranker is None:
            self._reranker = CrossEncoder(model_name, device="cuda")
        pairs = [[q, self.chunks[i]["text"]] for i, _ in hits]
        scores = self._reranker.predict(pairs)
        order = np.argsort(scores)[::-1][:top_n]
        return [(hits[o][0], float(scores[o])) for o in order]

    def expand(self, hits: list[tuple[int, float]], window: int = 1) -> tuple[list[tuple[int, float]], int]:
        """邻接扩展（small-to-big）：把每个命中的同页前后 window 个 chunk 并入上下文。

        返回 (扩展后的列表, 锚点数)。**锚点全部排在前面**，邻居跟在后面——否则一条很长的
        邻居片段会把后面真正命中的锚点挤出 `max_chars` 预算（E006 里 4 条单跳题从 1.0 掉到
        0.0，就是这个原因）。邻居分数记 0.0，不参与排序，只做上下文补全。
        """
        if window <= 0:
            return hits, len(hits)
        pos = {(c["doc_id"], c["order"]): i for i, c in enumerate(self.chunks)}
        anchors: list[tuple[int, float]] = []
        neighbors: list[tuple[int, float]] = []
        seen: set[int] = set()
        for i, score in hits:
            if i in seen:
                continue
            seen.add(i)
            anchors.append((i, score))
            c = self.chunks[i]
            for d in range(1, window + 1):
                for step in (d, -d):
                    j = pos.get((c["doc_id"], c["order"] + step))
                    if j is not None and j not in seen:
                        seen.add(j)
                        neighbors.append((j, 0.0))
        return anchors + neighbors, len(anchors)

    def rrf(self, q: str, k_retrieve: int, k_context: int, rrf_k: int = 60, kw_query: str | None = None,
            w_vec: float = 1.0, w_kw: float = 1.0, vec_query: str | None = None) -> list[tuple[int, float]]:
        # vec_query：dense 通道也用改写后的英文关键词（E018 验证中文 query 打英文语料的跨语言损耗）
        vec = self.vector(vec_query or q, k_retrieve)
        kw = self.keyword(kw_query or q, k_retrieve)
        fused: dict[int, float] = {}
        for rank, (i, _) in enumerate(vec, 1):
            fused[i] = fused.get(i, 0.0) + w_vec / (rrf_k + rank)
        for rank, (i, _) in enumerate(kw, 1):
            fused[i] = fused.get(i, 0.0) + w_kw / (rrf_k + rank)
        ranked = sorted(fused.items(), key=lambda x: -x[1])
        return ranked[:k_context]


def build_context(hits: list[tuple[int, float]], chunks: list[dict], max_chars: int = 6000, n_anchor: int | None = None) -> str:
    """拼装上下文。`n_anchor` 之前的块视为检索命中，之后的视为同页邻接补全（会显式标注）。"""
    parts: list[str] = []
    used = 0
    for n, (i, _score) in enumerate(hits, 1):
        c = chunks[i]
        tag = "" if n_anchor is None or n <= n_anchor else "（同页相邻片段·非检索命中，仅作补全）"
        block = f"[{n}]{tag} 来源：{c['url']}\n标题路径：{c['heading_path']}\n\n{c['text']}"
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n\n---\n\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--retrieval", default="rrf", choices=["rrf", "vec", "bm25"])
    ap.add_argument("--k-retrieve", type=int, default=20)
    ap.add_argument("--k-context", type=int, default=5)
    ap.add_argument("--expand", type=int, default=1, help="邻接扩展：每个命中并入同页前后各 N 个 chunk（0=关）")
    ap.add_argument("--show-chunks", action="store_true")
    ap.add_argument("--model", default="deepseek-chat")
    args = ap.parse_args()

    load_dotenv()
    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("缺少 DEEPSEEK_API_KEY：请写入 D:\\dshwork\\rag-docs-qa\\.env", file=sys.stderr)
        return 2

    from openai import OpenAI

    t0 = time.time()
    r = Retriever()
    t_load = time.time() - t0

    t1 = time.time()
    if args.retrieval == "vec":
        hits = r.vector(args.question, args.k_context)
    elif args.retrieval == "bm25":
        hits = r.keyword(args.question, args.k_context)
    else:
        hits = r.rrf(args.question, args.k_retrieve, args.k_context)
    t_ret = time.time() - t1

    n_anchor = len(hits)
    if args.expand > 0:
        hits, n_anchor = r.expand(hits, args.expand)

    if args.show_chunks:
        print(f"\n== 检索（{args.retrieval}，{t_ret:.2f}s，锚点 {n_anchor} + 邻接 ±{args.expand}）==")
        for n, (i, s) in enumerate(hits, 1):
            c = r.chunks[i]
            mark = "" if n <= n_anchor else "  ~补全"
            print(f"[{n}] {s:.4f}  {c['chunk_id']}  {c['heading_path'][:60]}{mark}")
            print(f"    {c['url']}")

    context = build_context(hits, r.chunks, n_anchor=n_anchor)
    prompt = SYSTEM_PROMPT.format(context=context, question=args.question)

    client = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )
    t2 = time.time()
    resp = client.chat.completions.create(
        model=args.model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=1200,
    )
    t_gen = time.time() - t2

    answer = resp.choices[0].message.content or ""
    print(f"\n== 回答 ==")
    print(answer)
    usage = resp.usage
    print(
        f"\n== 用时 == load {t_load:.1f}s / 检索 {t_ret:.2f}s / 生成 {t_gen:.2f}s "
        f"| tokens in {usage.prompt_tokens} out {usage.completion_tokens}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
