"""评测：Recall@k / MRR 自动算；答案正确率与拒答率用 DeepSeek judge。

用法：
    python -m src.eval --set eval/eval_set_v1.jsonl --retrieval rrf --dry-run   # 只算检索指标
    python -m src.eval --set eval/eval_set_v1.jsonl --retrieval rrf --judge     # 含生成+判分
    python -m src.eval --set eval/eval_set_v1.jsonl --retrieval rrf --judge --append-results E003

评测集每行字段（清单 §2）：
    qid / question / gold_answer / source_ids / type / difficulty / notes
    type ∈ single-hop | multi-hop | paraphrase | no-answer
    source_ids 形如 ["oss__python__langgraph__checkpointers#031", ...]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

JUDGE_PROMPT = """你在给一个文档问答系统的回答打分。

【问题】{question}
【标准答案要点】{gold}
【系统回答】{answer}

判断系统回答是否覆盖标准答案要点（允许措辞不同，不允许张冠李戴）：
- 完全正确：要点全对，无错误断言 → 输出 1
- 部分正确：覆盖主要要点但有遗漏或轻微错误 → 输出 0.5
- 错误：关键事实错误或答非所问 → 输出 0
- 若标准答案要点标注为「本题无答案」，而系统明确拒答/说找不到 → 输出 1；系统硬答 → 输出 0

只输出一个数字（1 / 0.5 / 0），不要解释。"""


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


def recall_at(ranked_ids: list[str], gold: list[str], k: int) -> float:
    top = set(ranked_ids[:k])
    return 1.0 if any(g in top for g in gold) else 0.0


def mrr(ranked_ids: list[str], gold: list[str]) -> float:
    for i, cid in enumerate(ranked_ids, 1):
        if cid in gold:
            return 1.0 / i
    return 0.0


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(int(round(0.95 * (len(s) - 1))), len(s) - 1)
    return s[idx]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default=str(ROOT / "eval" / "eval_set_v1.jsonl"))
    ap.add_argument("--retrieval", default="rrf", choices=["rrf", "vec", "bm25"])
    ap.add_argument("--k-retrieve", type=int, default=20)
    ap.add_argument("--k-context", type=int, default=5)
    ap.add_argument("--judge", action="store_true", help="真跑生成并判分（要 API key）")
    ap.add_argument("--dry-run", action="store_true", help="只算检索指标")
    ap.add_argument("--rerank", action="store_true", help="候选再走 cross-encoder 重排（bge-reranker-v2-m3）")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--append-results", default="", help="把结果追加到 RESULTS.md，填实验 id")
    ap.add_argument("--out", default="", help="逐题明细落盘路径")
    args = ap.parse_args()

    load_dotenv()
    if args.judge and not os.environ.get("DEEPSEEK_API_KEY"):
        print("缺少 DEEPSEEK_API_KEY，无法判分；可先 --dry-run", file=sys.stderr)
        return 2

    from src.ask import Retriever, build_context, SYSTEM_PROMPT

    qs = [json.loads(line) for line in Path(args.set).open(encoding="utf-8")]
    if args.limit:
        qs = qs[: args.limit]
    print(f"eval set: {len(qs)} questions from {args.set}")

    r = Retriever()
    client = None
    if args.judge:
        from openai import OpenAI

        client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))

    rows: list[dict] = []
    latencies: list[float] = []
    t_all = time.time()

    for n, q in enumerate(qs, 1):
        t0 = time.time()
        if args.retrieval == "vec":
            hits = r.vector(q["question"], args.k_retrieve)
        elif args.retrieval == "bm25":
            hits = r.keyword(q["question"], args.k_retrieve)
        else:
            hits = r.rrf(q["question"], args.k_retrieve, args.k_retrieve)  # 融合后保留 k_retrieve 个候选，供 R@10/rerank 使用
        if args.rerank:
            hits = r.rerank(q["question"], hits, args.k_retrieve)
        ranked_ids = [r.chunks[i]["chunk_id"] for i, _ in hits]
        gold = q.get("source_ids") or []
        row = {
            "qid": q["qid"],
            "type": q.get("type", ""),
            "recall@1": recall_at(ranked_ids, gold, 1),
            "recall@5": recall_at(ranked_ids, gold, 5),
            "recall@10": recall_at(ranked_ids, gold, 10),
            "mrr": mrr(ranked_ids, gold),
            "top5": ranked_ids[:5],
        }

        if client and q.get("type") != "no-answer":
            context = build_context(hits[: args.k_context], r.chunks)
            prompt = SYSTEM_PROMPT.format(context=context, question=q["question"])
            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=1200,
            )
            answer = resp.choices[0].message.content or ""
            j = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": JUDGE_PROMPT.format(question=q["question"], gold=q.get("gold_answer", ""), answer=answer)}],
                temperature=0.0,
                max_tokens=8,
            )
            raw = (j.choices[0].message.content or "").strip()
            try:
                row["score"] = float(raw.replace("分", "")[:3])
            except ValueError:
                row["score"] = 0.0
            row["answer"] = answer
        elif client and q.get("type") == "no-answer":
            context = build_context(hits[: args.k_context], r.chunks)
            prompt = SYSTEM_PROMPT.format(context=context, question=q["question"])
            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=800,
            )
            answer = resp.choices[0].message.content or ""
            refused = any(k in answer for k in ["没有找到", "找不到", "无法回答", "文档里没有", "不足以回答"])
            row["abstained"] = 1.0 if refused else 0.0
            row["answer"] = answer

        dt = time.time() - t0
        row["latency"] = dt
        latencies.append(dt)
        rows.append(row)
        if n % 20 == 0:
            print(f"  [{n}/{len(qs)}] {time.time() - t_all:.0f}s")

    def agg(key: str, subset: list[dict]) -> float:
        vals = [x[key] for x in subset if key in x]
        return statistics.mean(vals) if vals else 0.0

    scored = [x for x in rows if x.get("type") != "no-answer"]
    na = [x for x in rows if x.get("type") == "no-answer"]
    summary = {
        "n": len(rows),
        "retrieval": args.retrieval,
        "recall@1": agg("recall@1", scored),
        "recall@5": agg("recall@5", scored),
        "recall@10": agg("recall@10", scored),
        "mrr": agg("mrr", scored),
        "acc": agg("score", rows) if client else None,
        "abstain_rate": agg("abstained", na) if client and na else None,
        "p50": statistics.median(latencies) if latencies else 0.0,
        "p95": p95(latencies),
    }

    print("\n== summary ==")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    by_type: dict[str, list[dict]] = {}
    for x in rows:
        by_type.setdefault(x["type"], []).append(x)
    print("\nby type:")
    for t, xs in sorted(by_type.items()):
        print(f"  {t:12s} n={len(xs):3d} r@5={agg('recall@5', xs):.3f} mrr={agg('mrr', xs):.3f}")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with Path(args.out).open("w", encoding="utf-8") as f:
            for x in rows:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
        print(f"detail -> {args.out}")

    if args.append_results:
        from datetime import date

        # 评测集列从 --set 文件名推断（eval_set_v2.jsonl → v2(240)），不再写死 v1
        set_name = Path(args.set).stem
        m = re.search(r"(v\d+)", set_name)
        ver = m.group(1) if m else set_name.replace("eval_set_", "")
        set_label = f"{ver}({len(rows)})"

        line = (
            f"| {args.append_results} | {date.today()} | {set_label} | heading/700/120 | {args.retrieval} | "
            f"{'on' if args.rerank else 'off'} | {summary['recall@5']:.3f} | {summary['mrr']:.3f} | "
            f"{(summary['acc'] if summary['acc'] is not None else float('nan')):.3f} | "
            f"- | {summary['p95']:.2f}s | - | {len(rows)} 题，k_context={args.k_context}，k_retrieve={args.k_retrieve} |\n"
        )
        with (ROOT / "results" / "RESULTS.md").open("a", encoding="utf-8") as f:
            f.write(line)
        print(f"appended to RESULTS.md as {args.append_results}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
