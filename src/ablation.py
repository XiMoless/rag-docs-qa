"""娑堣瀺锛? 绉嶅垏鍒?脳 4 绉嶆绱紝鍙畻妫€绱㈡寚鏍囷紙Recall@k / MRR / 妫€绱㈠欢杩燂級銆?
涓嶉渶瑕?API key鈥斺€斿彫鍥炴寚鏍囧彲浠ュ畬鍏ㄧ绾跨畻銆傜瓟妗堟纭巼銆佸够瑙夌巼瑕佸彟璺?src.eval --judge銆?
鐢ㄦ硶锛?    python -m src.ablation --set eval/eval_set_v1.jsonl
    python -m src.ablation --set eval/eval_set_v1.jsonl --modes vec,rff --chunkings heading
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "results" / "ablation_v1.json"

CHUNKINGS = {
    "heading": (ROOT / "data" / "processed" / "chunks.jsonl", ROOT / "index"),
    "fixed": (ROOT / "data" / "processed" / "chunks_fixed.jsonl", ROOT / "index" / "fixed"),
}

MODES = ["vec", "bm25", "rrf", "rerank"]
MODE_LABEL = {"vec": "绾悜閲?, "bm25": "BM25", "rrf": "娣峰悎RRF", "rerank": "娣峰悎RRF+rerank"}


def recall_at(ranked: list[str], gold: list[str], k: int) -> float:
    return 1.0 if any(g in set(ranked[:k]) for g in gold) else 0.0


def mrr(ranked: list[str], gold: list[str]) -> float:
    for i, cid in enumerate(ranked, 1):
        if cid in gold:
            return 1.0 / i
    return 0.0


def p95(vals: list[float]) -> float:
    s = sorted(vals)
    return s[min(int(round(0.95 * (len(s) - 1))), len(s) - 1)] if s else 0.0


def run_combo(retriever, qs: list[dict], mode: str, k_retrieve: int, k_context: int) -> dict:
    rec = {"r1": [], "r5": [], "r10": [], "mrr": [], "lat": []}
    for q in qs:
        gold = q.get("source_ids") or []
        if not gold:
            continue
        t0 = time.time()
        if mode == "vec":
            hits = retriever.vector(q["question"], k_retrieve)
        elif mode == "bm25":
            hits = retriever.keyword(q["question"], k_retrieve)
        elif mode == "rrf":
            hits = retriever.rrf(q["question"], k_retrieve, k_retrieve, 60)[:k_retrieve]
        elif mode == "rerank":
            base = retriever.rrf(q["question"], k_retrieve, k_retrieve, 60)[:k_retrieve]
            hits = retriever.rerank(q["question"], base, max(k_context, 10))  # 取到 10 深，否则 R@10 退化等于 R@5
        else:
            raise ValueError(mode)
        ranked = [retriever.chunks[i]["chunk_id"] for i, _ in hits]
        rec["lat"].append(time.time() - t0)
        rec["r1"].append(recall_at(ranked, gold, 1))
        rec["r5"].append(recall_at(ranked, gold, 5))
        rec["r10"].append(recall_at(ranked, gold, 10))
        rec["mrr"].append(mrr(ranked, gold))
    return {
        "n": len(rec["r1"]),
        "recall@1": statistics.mean(rec["r1"]),
        "recall@5": statistics.mean(rec["r5"]),
        "recall@10": statistics.mean(rec["r10"]),
        "mrr": statistics.mean(rec["mrr"]),
        "p50": statistics.median(rec["lat"]),
        "p95": p95(rec["lat"]),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default=str(ROOT / "eval" / "eval_set_v1.jsonl"))
    ap.add_argument("--chunkings", default="heading,fixed")
    ap.add_argument("--modes", default="vec,bm25,rrf,rerank")
    ap.add_argument("--k-retrieve", type=int, default=20)
    ap.add_argument("--k-context", type=int, default=5)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-rerank", action="store_true")
    args = ap.parse_args()

    from src.ask import Retriever

    qs = [json.loads(line) for line in Path(args.set).open(encoding="utf-8")]
    if args.limit:
        qs = qs[: args.limit]
    modes = [m for m in args.modes.split(",") if m]
    if args.no_rerank:
        modes = [m for m in modes if m != "rerank"]
    chunkings = [c for c in args.chunkings.split(",") if c]

    print(f"eval set: {len(qs)} questions; chunkings={chunkings}; modes={modes}")
    results: list[dict] = []
    for ck in chunkings:
        chunks_file, index_dir = CHUNKINGS[ck]
        if not chunks_file.exists() or not (index_dir / "langchain_docs.faiss").exists():
            print(f"skip {ck}: 缂?{chunks_file} 鎴?{index_dir}锛堝厛璺?ingest --strategy fixed / index --out-dir锛?)
            continue
        print(f"\n== chunking={ck} ({index_dir}) ==")
        r = Retriever(chunks_file, index_dir)
        print(f"chunks={len(r.chunks)}")
        for mode in modes:
            t0 = time.time()
            m = run_combo(r, qs, mode, args.k_retrieve, args.k_context)
            m.update({"chunking": ck, "retrieval": mode, "label": MODE_LABEL.get(mode, mode)})
            results.append(m)
            print(
                f"  {MODE_LABEL.get(mode, mode):14s} n={m['n']:3d} "
                f"R@1={m['recall@1']:.3f} R@5={m['recall@5']:.3f} R@10={m['recall@10']:.3f} "
                f"MRR={m['mrr']:.3f} p50={m['p50'] * 1000:.0f}ms ({time.time() - t0:.0f}s)"
            )

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {OUT_JSON}")

    # 鐩存帴鐢熸垚鍙洿鎺ョ矘杩?RESULTS.md 鐨勮
    print("\n=== RESULTS.md rows ===")
    for i, m in enumerate(results, 1):
        print(
            f"| E{100 + i} | {m['chunking']} | heading | {m['label']} | "
            f"{m['recall@5']:.3f} | {m['mrr']:.3f} | - | - | {m['p95'] * 1000:.0f}ms | - | "
            f"妫€绱?only锛寋m['n']} 棰橈紙R@1={m['recall@1']:.3f}, R@10={m['recall@10']:.3f}锛?|"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

