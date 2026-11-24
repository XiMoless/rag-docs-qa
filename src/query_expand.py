"""查询翻译/改写：中文提问 → 英文检索关键词。

为什么需要：语料是英文文档、提问是中文，BM25 的词法通道基本失效（E102：R@5 只有 0.185），
RRF 等权融合反而比纯向量低 7.6pp。根因不是 BM25 实现，而是**两侧词面零重叠**，所以解法是
把查询翻译成英文再喂词法通道，而不是去调 BM25 参数。

不引 FlagEmbedding（会带来 datasets/peft 等一串传递依赖，风险大于收益），
用一次便宜的 DeepSeek 调用完成改写，结果按问题缓存到 `tmp/qe_cache.json`。
"""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "tmp" / "qe_cache.json"

PROMPT = """You rewrite a user question into an English keyword query for searching technical documentation.

Rules:
- Output ONLY space-separated English keywords / identifiers / API names. No sentence, no explanation, no quotes.
- Keep identifiers exactly as written (e.g. `checkpointer`, `return_direct`, `interrupt_mode`).
- Prefer the 6-10 words that a documentation page answering this question would contain.
- If the question is already English, just normalise it into keywords.

Question: {question}

Keywords:"""


def _load_cache() -> dict[str, str]:
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


_CACHE: dict[str, str] = _load_cache()


def save_cache() -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(_CACHE, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")


def expand(question: str, client=None, model: str = "deepseek-chat") -> str:
    """把问题改写成英文关键词串（带缓存）。没有 client 时返回原问题。"""
    q = question.strip()
    if q in _CACHE:
        return _CACHE[q]
    if client is None:
        return q
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": PROMPT.format(question=q)}],
        temperature=0.0,
        max_tokens=64,
    )
    kw = (resp.choices[0].message.content or "").strip().strip('"').replace("\n", " ")
    kw = " ".join(kw.split())
    _CACHE[q] = kw or q
    return _CACHE[q]


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    from src.ask import Retriever, load_dotenv

    load_dotenv()
    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("缺少 DEEPSEEK_API_KEY", file=__import__("sys").stderr)
        return 2
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    kw = expand(args.question, client)
    print(f"问题：{args.question}")
    print(f"改写：{kw}")

    r = Retriever()
    print("\nBM25（用改写后的英文查询）：")
    for i, s in r.keyword(kw, 5):
        c = r.chunks[i]
        print(f"  {s:8.3f}  {c['chunk_id']}")
    print("\nBM25（用原始中文查询）：")
    for i, s in r.keyword(args.question, 5):
        c = r.chunks[i]
        print(f"  {s:8.3f}  {c['chunk_id']}")
    save_cache()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
