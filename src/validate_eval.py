"""评测集校验：结构 / chunk 存在性 / 题型配比 / 事实可回溯。

用法：
    python -m src.validate_eval --file eval/parts/v1_partA.jsonl --part A --expect 25
    python -m src.validate_eval --file eval/eval_set_v1.jsonl --merge-check
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHUNKS = ROOT / "data" / "processed" / "chunks.jsonl"

REQUIRED = {"qid", "question", "gold_answer", "source_ids", "type", "difficulty", "notes"}
TYPES = {"single-hop", "multi-hop", "paraphrase", "no-answer"}
DIFF = {"easy", "medium", "hard"}

# 英文 token / 数字 / API 名，用来验证 gold_answer 里的事实确实在原文出现过
FACT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.\-]{3,}|\d+(?:\.\d+)?")

STOP = {
    "this", "that", "with", "from", "have", "when", "what", "which", "them", "they",
    "your", "will", "been", "were", "into", "than", "then", "also", "such", "each",
    "does", "doing", "done", "uses", "used", "using", "some", "more", "most", "only",
    "like", "just", "make", "made", "must", "need", "over", "same", "should", "there",
    "these", "those", "very", "well", "where", "while", "would", "about", "after",
    "before", "between", "cannot", "could", "other", "under", "until", "without",
}


def load_chunks() -> dict[str, dict]:
    out: dict[str, dict] = {}
    with CHUNKS.open(encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            out[c["chunk_id"]] = c
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--part", default="")
    ap.add_argument("--expect", type=int, default=0)
    ap.add_argument("--merge-check", action="store_true", help="整个评测集走一遍唯一性与配比")
    args = ap.parse_args()

    chunks = load_chunks()
    path = Path(args.file)
    rows = [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]
    errors: list[str] = []
    warns: list[str] = []

    seen_qid: set[str] = set()
    seen_q: set[str] = set()

    for i, r in enumerate(rows, 1):
        tag = r.get("qid") or f"line{i}"
        missing = REQUIRED - set(r)
        if missing:
            errors.append(f"{tag}: 缺字段 {sorted(missing)}")
            continue
        if r["qid"] in seen_qid:
            errors.append(f"{tag}: qid 重复")
        seen_qid.add(r["qid"])
        norm = re.sub(r"\s+", "", r["question"]).lower()
        if norm in seen_q:
            errors.append(f"{tag}: 题目重复")
        seen_q.add(norm)
        if len(r["question"]) < 8:
            errors.append(f"{tag}: question 太短")
        if r["type"] not in TYPES:
            errors.append(f"{tag}: type 非法 {r['type']}")
        if r["difficulty"] not in DIFF:
            errors.append(f"{tag}: difficulty 非法 {r['difficulty']}")
        if not r["notes"]:
            warns.append(f"{tag}: notes 为空")

        ids = r["source_ids"] or []
        if r["type"] == "no-answer":
            if ids:
                warns.append(f"{tag}: 无答案题不该带 source_ids")
            if r["gold_answer"] != "本题无答案":
                errors.append(f"{tag}: 无答案题 gold_answer 必须是「本题无答案」")
        else:
            if not ids:
                errors.append(f"{tag}: 缺 source_ids")
            if r["type"] == "multi-hop" and len(ids) < 2:
                errors.append(f"{tag}: multi-hop 需要 ≥2 个 source_ids")
            for cid in ids:
                if cid not in chunks:
                    errors.append(f"{tag}: source_id 不存在 {cid}")

        # 事实回溯：gold_answer 里的英文标识与数字，至少要能在 source 原文里找到
        if r["type"] != "no-answer" and ids:
            src = "\n".join(chunks[c]["text"] for c in ids if c in chunks)
            src_low = src.lower()
            facts = [t for t in FACT_RE.findall(r["gold_answer"]) if t.lower() not in STOP and len(t) >= 4]
            miss = [t for t in facts if t.lower() not in src_low]
            if miss:
                ratio = len(miss) / max(len(facts), 1)
                msg = f"{tag}: gold_answer 里 {len(miss)}/{len(facts)} 个术语没出现在 source 原文（{', '.join(miss[:6])}）"
                if ratio > 0.5:
                    errors.append(msg + " ← 大概率 gold 写飞了")
                else:
                    warns.append(msg)

    dist = Counter(r["type"] for r in rows)
    print(f"file: {path}  rows: {len(rows)}")
    print(f"type distribution: {dict(dist)}")
    if args.part:
        # 从文件名推断评测集版本（v2_partF.jsonl → v2），避免把 v2 稿误判成前缀错误
        m = re.match(r"(v\d+)_part", Path(path).name)
        ver = m.group(1) if m else "v1"
        want = f"{ver}-{args.part}-"
        bad = [qid for qid in seen_qid if not qid.startswith(want)]
        if bad:
            errors.append(f"qid 前缀不是 {want}：{bad[:5]}")
    if args.expect and len(rows) != args.expect:
        errors.append(f"行数 {len(rows)} != 期望 {args.expect}")

    print(f"errors: {len(errors)}  warnings: {len(warns)}")
    for e in errors:
        print("  ERROR", e)
    for w in warns[:25]:
        print("  WARN ", w)
    if len(warns) > 25:
        print(f"  ... {len(warns) - 25} more warnings")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
