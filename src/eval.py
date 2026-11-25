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
    ap.add_argument("--expand", type=int, default=0, help="邻接扩展：每个命中并入同页前后各 N 个 chunk（0=关）")
    ap.add_argument("--rrf-weights", default="1,1", help="RRF 通道权重：向量,词法（如 1,0.5 表示压低词法通道）")
    ap.add_argument("--prompt", default="v1", choices=["v1", "v2"], help="生成提示词版本（v2 加多跳拼接与数字逐字约束）")
    ap.add_argument("--query-expand", action="store_true", help="把中文问题改写成英文关键词后再走 BM25 通道（修复中英错配）")
    ap.add_argument("--max-chars", type=int, default=6000, help="送入上下文的片段总字符预算（E017 扫描：k 加大但 max_chars 不变时其实没生效）")
    ap.add_argument("--qe-dense", action="store_true", help="dense 通道也用改写后的英文关键词（默认只用原中文问题）")
    ap.add_argument("--repeat", type=int, default=1, help="同一配置重复跑 N 次取均值（生成/judge 有随机性，2.7pp 级差异必须重复跑）")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--append-results", default="", help="把结果追加到 RESULTS.md，填实验 id")
    ap.add_argument("--out", default="", help="逐题明细落盘路径")
    args = ap.parse_args()

    load_dotenv()
    if args.judge and not os.environ.get("DEEPSEEK_API_KEY"):
        print("缺少 DEEPSEEK_API_KEY，无法判分；可先 --dry-run", file=sys.stderr)
        return 2

    from src.ask import Retriever, build_context, SYSTEM_PROMPT, SYSTEM_PROMPT_V2

    qs = [json.loads(line) for line in Path(args.set).open(encoding="utf-8")]
    if args.limit:
        qs = qs[: args.limit]
    print(f"eval set: {len(qs)} questions from {args.set}")

    prompt_tpl = SYSTEM_PROMPT_V2 if args.prompt == "v2" else SYSTEM_PROMPT
    r = Retriever()
    client = None
    if args.judge or args.query_expand:
        from openai import OpenAI

        client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))

    def run_once(rep: int) -> tuple[list[dict], list[float], int, int]:
        rows: list[dict] = []
        latencies: list[float] = []
        tok_in = 0
        tok_out = 0
        t_all = time.time()

        for n, q in enumerate(qs, 1):
            t0 = time.time()
            kw_query = None
            if args.query_expand:
                from src.query_expand import expand as qe_expand

                kw_query = qe_expand(q["question"], client)
            if args.retrieval == "vec":
                hits = r.vector(q["question"], args.k_retrieve)
            elif args.retrieval == "bm25":
                hits = r.keyword(kw_query or q["question"], args.k_retrieve)
            else:
                w_vec, w_kw = (float(x) for x in args.rrf_weights.split(","))
                hits = r.rrf(q["question"], args.k_retrieve, args.k_retrieve, kw_query=kw_query, w_vec=w_vec, w_kw=w_kw, vec_query=(kw_query if args.qe_dense else None))  # 融合后保留 k_retrieve 个候选，供 R@10/rerank 使用
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
                ctx_hits, n_anchor = r.expand(hits[: args.k_context], args.expand)
                context = build_context(ctx_hits, r.chunks, max_chars=args.max_chars, n_anchor=n_anchor)
                prompt = prompt_tpl.format(context=context, question=q["question"])
                resp = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=1200,
                )
                answer = resp.choices[0].message.content or ""
                tok_in += resp.usage.prompt_tokens
                tok_out += resp.usage.completion_tokens
                j = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": JUDGE_PROMPT.format(question=q["question"], gold=q.get("gold_answer", ""), answer=answer)}],
                    temperature=0.0,
                    max_tokens=8,
                )
                tok_in += j.usage.prompt_tokens
                tok_out += j.usage.completion_tokens
                raw = (j.choices[0].message.content or "").strip()
                try:
                    row["score"] = float(raw.replace("分", "")[:3])
                except ValueError:
                    row["score"] = 0.0
                row["answer"] = answer
            elif client and q.get("type") == "no-answer":
                ctx_hits, n_anchor = r.expand(hits[: args.k_context], args.expand)
                context = build_context(ctx_hits, r.chunks, max_chars=args.max_chars, n_anchor=n_anchor)
                prompt = prompt_tpl.format(context=context, question=q["question"])
                resp = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=800,
                )
                answer = resp.choices[0].message.content or ""
                tok_in += resp.usage.prompt_tokens
                tok_out += resp.usage.completion_tokens
                refused = any(k in answer for k in ["没有找到", "找不到", "无法回答", "文档里没有", "不足以回答"])
                row["abstained"] = 1.0 if refused else 0.0
                row["answer"] = answer

            dt = time.time() - t0
            row["latency"] = dt
            latencies.append(dt)
            rows.append(row)
            if n % 20 == 0:
                print(f"  [{n}/{len(qs)}] {time.time() - t_all:.0f}s")
        return rows, latencies, tok_in, tok_out

    def agg(key: str, subset: list[dict]) -> float:
        vals = [x[key] for x in subset if key in x]
        return statistics.mean(vals) if vals else 0.0

    def summarize(rows_r: list[dict], lat_r: list[float], tin: int, tout: int) -> dict:
        scored_r = [x for x in rows_r if x.get("type") != "no-answer"]
        na_r = [x for x in rows_r if x.get("type") == "no-answer"]
        return {
            "n": len(rows_r),
            "recall@1": agg("recall@1", scored_r),
            "recall@5": agg("recall@5", scored_r),
            "recall@10": agg("recall@10", scored_r),
            "mrr": agg("mrr", scored_r),
            "acc": agg("score", rows_r) if client else None,
            "abstain_rate": agg("abstained", na_r) if client and na_r else None,
            "p50": statistics.median(lat_r) if lat_r else 0.0,
            "p95": p95(lat_r),
            "tokens_in": tin,
            "tokens_out": tout,
        }

    reps = max(1, args.repeat)
    per_rep: list[dict] = []
    rows: list[dict] = []
    for rep in range(reps):
        if reps > 1:
            print(f"\n-- repeat {rep + 1}/{reps} --")
        rows_r, lat_r, tin, tout = run_once(rep)
        per_rep.append(summarize(rows_r, lat_r, tin, tout))
        if args.out and reps > 1:
            pr = Path(args.out)
            pr = pr.with_name(f"{pr.stem}_rep{rep + 1}{pr.suffix}")
            pr.parent.mkdir(parents=True, exist_ok=True)
            with pr.open("w", encoding="utf-8") as f:
                for x in rows_r:
                    f.write(json.dumps(x, ensure_ascii=False) + "\n")
            print(f"detail -> {pr}")
        rows = rows_r

    keys = [k for k in per_rep[0] if k not in ("n", "tokens_in", "tokens_out")]
    summary: dict = {"n": len(rows), "retrieval": args.retrieval, "reps": reps}
    for k in keys:
        vals = [x[k] for x in per_rep if x[k] is not None]
        summary[k] = statistics.mean(vals) if vals else None
    summary["tokens_in"] = sum(x["tokens_in"] for x in per_rep)
    summary["tokens_out"] = sum(x["tokens_out"] for x in per_rep)
    for k in ("acc", "recall@5", "mrr"):
        vals = [x[k] for x in per_rep if x[k] is not None]
        summary["std_" + k] = statistics.stdev(vals) if len(vals) > 1 else 0.0

    print("\n== summary ==")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    by_type: dict[str, list[dict]] = {}
    for x in rows:
        by_type.setdefault(x["type"], []).append(x)
    print("\nby type (最后一轮):")
    for t, xs in sorted(by_type.items()):
        print(f"  {t:12s} n={len(xs):3d} r@5={agg('recall@5', xs):.3f} mrr={agg('mrr', xs):.3f} acc={agg('score', xs):.3f}")

    if args.out and reps == 1:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with Path(args.out).open("w", encoding="utf-8") as f:
            for x in rows:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
        print(f"detail -> {args.out}")

    if reps > 1:
        Path(ROOT / "results").mkdir(exist_ok=True)
        out_rep = ROOT / "results" / ("reps_" + (args.append_results or "run") + ".json")
        out_rep.write_text(json.dumps({"reps": per_rep, "summary": summary}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"reps -> {out_rep}")

    if args.query_expand:
        from src.query_expand import save_cache

        save_cache()  # 落盘翻译缓存：同一批题重跑时复用同一批关键词，指标才可复现
        print(f"qe cache -> tmp/qe_cache.json")

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
            f"{(summary['acc'] if summary['acc'] is not None else float('nan')):.3f}" f"{'±' + format(summary['std_acc'], '.3f') if summary.get('reps', 1) > 1 else ''} | "
            f"- | {summary['p95']:.2f}s | in {summary['tokens_in'] / 1000:.0f}K / out {summary['tokens_out'] / 1000:.0f}K | {len(rows)} 题，k_context={args.k_context}，k_retrieve={args.k_retrieve}，expand=±{args.expand}"
            f"{'，repeat=' + str(args.repeat) if args.repeat > 1 else ''}{'，qe=on' if args.query_expand else ''}{'，qe_dense' if args.qe_dense else ''}{'（max_chars=' + str(args.max_chars) + '）' if args.max_chars != 6000 else ''}{'，w=' + args.rrf_weights if args.rrf_weights != '1,1' else ''}{'，prompt=' + args.prompt if args.prompt != 'v1' else ''} |\n"
        )
        with (ROOT / "results" / "RESULTS.md").open("a", encoding="utf-8") as f:
            f.write(line)
        print(f"appended to RESULTS.md as {args.append_results}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
