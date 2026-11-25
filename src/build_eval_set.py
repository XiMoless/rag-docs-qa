"""合并分片为 eval/eval_set_v{N}.jsonl，并做全局去重与配比检查。

用法：
    python -m src.build_eval_set                       # 默认 v1，期望 100 行
    python -m src.build_eval_set --expect 100
    python -m src.build_eval_set --version v2 --expect 0   # v2 分片还不全时先看配比
    python -m src.build_eval_set --version v2              # 五段齐了再正式合并（140 行）

配比目标（TARGETS）：
    v1: 100 行 = 52/24/16/8
    v2: 140 行 = 72/34/22/12
    v1+v2 = 240 行 = 124/58/38/20（分版本合并，不混在一个文件里）
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARTS = ROOT / "eval" / "parts"

TARGETS = {
    "v1": {"single-hop": 52, "multi-hop": 24, "paraphrase": 16, "no-answer": 8},
    "v2": {"single-hop": 72, "multi-hop": 34, "paraphrase": 22, "no-answer": 12},
    # v3 = v1 + v2 + 12 道「主题在语料里、但追问的具体事实不存在」的拒答题（no-answer 20+12=32）
    "v3": {"single-hop": 124, "multi-hop": 58, "paraphrase": 38, "no-answer": 32},
}
# all = v1 + v2（240 题，保持与 E005/E015 可比）。v3（252 题）另存 eval_set_v3.jsonl。
TARGETS["all"] = {
    k: TARGETS["v1"][k] + TARGETS["v2"][k] for k in TARGETS["v1"]
}
ALL_PARTS = ("v1", "v2")  # "all" 只收这两版，别把 v3 的 12 道混进 240 题基线


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v1", choices=sorted(TARGETS))
    ap.add_argument("--expect", type=int, default=None, help="期望行数；不给则只报配比不判错")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    target = TARGETS[args.version]
    expect = args.expect if args.expect is not None else sum(target.values())
    out = Path(args.out) if args.out else ROOT / "eval" / f"eval_set_{args.version}.jsonl"

    files = sorted(PARTS.glob(f"{args.version}_part*.jsonl"))
    if args.version == "all":
        files = [f for v in ALL_PARTS for f in sorted(PARTS.glob(f"{v}_part*.jsonl"))]
    elif args.version == "v3":
        files = [f for v in ("v1", "v2", "v3") for f in sorted(PARTS.glob(f"{v}_part*.jsonl"))]
    if not files:
        print(f"{PARTS} 里没有 {args.version}_part*.jsonl")
        return 1

    rows: list[dict] = []
    seen: set[str] = set()
    for f in files:
        n = 0
        for line in f.open(encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            key = r["qid"]
            if key in seen:
                print(f"  skip duplicate qid {key} in {f.name}")
                continue
            seen.add(key)
            rows.append(r)
            n += 1
        print(f"{f.name}: {n} rows")

    rows.sort(key=lambda r: r["qid"])
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    dist = Counter(r["type"] for r in rows)
    qs = [re.sub(r"\s+", "", r["question"]).lower() for r in rows]
    # 无答案题的 gold 是固定哨兵「本题无答案」，不参与重复检测
    golds = [
        re.sub(r"\s+", "", r["gold_answer"]).lower()
        for r in rows
        if r["type"] != "no-answer"
    ]
    print(f"\nmerged: {len(rows)} rows -> {out}")
    print(f"type distribution: {dict(dist)}")
    print(f"duplicate questions: {len(qs) - len(set(qs))}")
    print(f"duplicate gold（不含无答案题）: {len(golds) - len(set(golds))}")
    print(f"target({args.version}): {target}")

    off = []
    for t, want in target.items():
        got = dist.get(t, 0)
        flag = "OK" if abs(got - want) <= 3 else "OFF"
        if flag == "OFF":
            off.append(t)
        print(f"  {t:12s} got={got:3d} want={want:3d} {flag}")

    problems = 0
    if len(rows) != expect:
        print(f"WARNING: rows {len(rows)} != expect {expect}")
        problems += 1
    if off:
        print(f"WARNING: 题型配比偏离 >3：{off}")
        problems += 1
    dups = (len(qs) - len(set(qs))) + (len(golds) - len(set(golds)))
    if dups:
        print(f"WARNING: 重复题面/重复 gold 共 {dups} 条")
        problems += 1
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
