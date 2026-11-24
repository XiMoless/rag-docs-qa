"""从 eval 明细里按「题集 / 题型」拆指标。

用途：一次跑 240 题（eval_set_all.jsonl），事后按 qid 前缀拆出 v1 / v2 两套数字，
避免为了拿两套数字跑两遍（环境漂移会让两组数字不可比）。

用法：
    python -m src.split_metrics --detail results/eval_E005.jsonl
    python -m src.split_metrics --detail results/eval_E005.jsonl --md
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def load(path: str) -> list[dict]:
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def pct(x: float) -> str:
    return f"{x:.3f}"


ABSTAIN_WORDS = (
    "没有找到", "找不到", "无法回答", "文档里没有", "不足以回答", "未找到", "没有提供",
)


def is_abstain(row: dict) -> bool:
    ans = row.get("answer") or ""
    return any(w in ans for w in ABSTAIN_WORDS)


def summarize(rows: list[dict]) -> dict:
    """rows 已按集合/题型过滤；召回只在可答题上算（no-answer 不参与召回）。"""
    answerable = [r for r in rows if r["type"] != "no-answer"]
    n_ans = len(answerable)
    out = {
        "n": len(rows),
        "n_answerable": n_ans,
        "r1": sum(r["recall@1"] for r in answerable) / n_ans if n_ans else 0.0,
        "r5": sum(r["recall@5"] for r in answerable) / n_ans if n_ans else 0.0,
        "r10": sum(r["recall@10"] for r in answerable) / n_ans if n_ans else 0.0,
        "mrr": sum(r["mrr"] for r in answerable) / n_ans if n_ans else 0.0,
    }
    scored = [r for r in rows if r.get("score") is not None]
    out["acc"] = sum(r["score"] for r in scored) / len(scored) if scored else None
    na = [r for r in rows if r["type"] == "no-answer"]
    out["na_n"] = len(na)
    # 无答案题判"拒答成功"：优先看 judge 分，judge 没打分时用关键词兜底
    out["na_ok"] = sum(1 for r in na if (r.get("score") or 0) >= 0.5 or is_abstain(r))
    out["abstain"] = sum(1 for r in rows if is_abstain(r)) / len(rows) if rows else 0.0
    lat = sorted(r["latency"] for r in rows if r.get("latency"))
    out["p50"] = lat[int(0.5 * (len(lat) - 1))] if lat else 0.0
    out["p95"] = lat[int(0.95 * (len(lat) - 1))] if lat else 0.0
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--detail", required=True)
    ap.add_argument("--md", action="store_true", help="输出 markdown 表格")
    args = ap.parse_args()

    rows = load(args.detail)
    sets = {
        "all": rows,
        "v1": [r for r in rows if r["qid"].startswith("v1-")],
        "v2": [r for r in rows if r["qid"].startswith("v2-")],
    }
    types = ["single-hop", "multi-hop", "paraphrase", "no-answer"]

    print(f"detail: {args.detail}  rows: {len(rows)}\n")
    print("== 按题集 ==")
    for name, sub in sets.items():
        if not sub:
            continue
        s = summarize(sub)
        acc = f"{s['acc']:.3f}" if s["acc"] is not None else "-"
        print(
            f"{name:4s} n={s['n']:3d} (可答 {s['n_answerable']:3d})  "
            f"R@1 {pct(s['r1'])}  R@5 {pct(s['r5'])}  R@10 {pct(s['r10'])}  "
            f"MRR {pct(s['mrr'])}  judge_acc {acc}  无答案 {s['na_ok']}/{s['na_n']}  "
            f"弃答 {s['abstain']:.0%}  P50 {s['p50']:.2f}s P95 {s['p95']:.2f}s"
        )

    print("\n== 按题型（全部 240）==")
    for t in types:
        sub = [r for r in sets["all"] if r["type"] == t]
        if not sub:
            continue
        s = summarize(sub)
        acc = f"{s['acc']:.3f}" if s["acc"] is not None else "-"
        print(
            f"{t:12s} n={s['n']:3d}  R@5 {pct(s['r5'])}  MRR {pct(s['mrr'])}  judge_acc {acc}"
        )

    print("\n== 按题集 × 题型 ==")
    grid: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for name, sub in sets.items():
        for r in sub:
            grid[name][r["type"]].append(r)
    if args.md:
        print("\n| 题集 | 题型 | n | R@5 | judge_acc |")
        print("|---|---|---|---|---|")
    for name in ("v1", "v2"):
        for t in types:
            sub = grid[name][t]
            if not sub:
                continue
            s = summarize(sub)
            acc = f"{s['acc']:.3f}" if s["acc"] is not None else "-"
            if args.md:
                print(f"| {name} | {t} | {s['n']} | {pct(s['r5'])} | {acc} |")
            else:
                print(f"{name} {t:12s} n={s['n']:3d} R@5 {pct(s['r5'])} judge_acc {acc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
