"""把一次 eval 明细切成 N 份审计材料（问题/gold/answer/top5 片段正文），供人工或子 agent 逐条判定。

用法：
  python -m src.split_audit --detail results/eval_E015.jsonl --parts 8
产物：
  eval/audit240/ctx_1.md ... ctx_N.md
  eval/audit240/SPEC.md
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHUNK_MAX = 1400


def load_chunks(path: Path) -> dict[str, dict]:
    return {json.loads(line)["chunk_id"]: json.loads(line) for line in path.open(encoding="utf-8") if line.strip()}


def load_gold(path: Path) -> dict[str, dict]:
    out = {}
    for line in path.open(encoding="utf-8"):
        if not line.strip():
            continue
        d = json.loads(line)
        out[d["qid"]] = d
    return out


SPEC = """# 审计任务说明

你负责 `{part}` 号材料（{n} 条）。逐条判断模型回答里**有没有片段不支持的断言**（幻觉），并把判定写进 JSONL。

## 判定
- `OK`：结论正确，且所有可核查断言都能在片段里找到依据（措辞不同、答不全、只给部分要点都算 OK）
- `MISS`：模型明确说「片段里没有 / 找不到」而弃答，且**它说没有的东西确实不在片段里**（=召回缺失，不算幻觉）
- `HALLUC`：回答了，但（a）编造了 API 名/参数/默认值/数值/行为，或（b）斩钉截铁地断言「片段里没有 X」而片段里其实有 X，或（c）把片段里 A 语境的 API 当成 B 语境的解法
- `WRONG`：结论与片段可推出的结论相反（不是缺证据，而是与证据冲突）

注意两个常见误判：
1. 示例代码里自造变量名/工具名，但已标注「示意」→ 不算幻觉。
2. 自称「没有找到」却顺带把 gold 答案说对了 → 判 OK，不判 MISS。

## 输出（严格 JSONL，每条一行，字段顺序固定）
{"qid": "...", "verdict": "OK|MISS|HALLUC|WRONG", "hallucinated_claims": ["原句"], "reason": "一句话依据（引用片段编号）", "evidence": "片段里的反证原文，不超过 200 字"}

只写判定，不要复述问题；`hallucinated_claims` 非 HALLUC 时给空数组。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--detail", default="results/eval_E015.jsonl")
    ap.add_argument("--eval-set", default="eval/eval_set_all.jsonl")
    ap.add_argument("--chunks", default="data/processed/chunks.jsonl")
    ap.add_argument("--parts", type=int, default=8)
    ap.add_argument("--out-dir", default="eval/audit240")
    ap.add_argument("--part", default="all", help="只导出某一号材料，如 1")
    args = ap.parse_args()

    rows = [json.loads(line) for line in (ROOT / args.detail).open(encoding="utf-8") if line.strip()]
    gold = load_gold(ROOT / args.eval_set)
    chunks = load_chunks(ROOT / args.chunks)
    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    total = len(rows)
    size = -(-total // args.parts)
    parts = [rows[i : i + size] for i in range(0, total, size)]

    for idx, part_rows in enumerate(parts, 1):
        name = f"ctx_{idx}.md"
        if args.part != "all" and str(idx) != str(args.part):
            continue
        lines = [f"# 审计材料 {idx}/{len(parts)}（{len(part_rows)} 条，明细文件第 {rows.index(part_rows[0]) + 1}–{rows.index(part_rows[-1]) + 1} 行）", ""]
        for r in part_rows:
            q = gold.get(r["qid"], {})
            lines.append(f"## {r['qid']}（{r['type']}）")
            lines.append("")
            lines.append(f"**问题**：{q.get('question', '(缺失)')}")
            lines.append("")
            lines.append(f"**gold**：{q.get('gold_answer') or q.get('gold') or '(无答案题)'}")
            lines.append("")
            lines.append(f"**judge 分**：{r.get('score')}　**拒答标记**：{r.get('abstained')}")
            lines.append("")
            lines.append("**回答**：")
            lines.append("")
            lines.append((r.get("answer") or "").strip())
            lines.append("")
            lines.append("**top5 片段**：")
            for i, cid in enumerate(r.get("top5") or [], 1):
                c = chunks.get(cid, {})
                text = (c.get("text") or "(未找到该 chunk)").strip()
                if len(text) > CHUNK_MAX:
                    text = text[:CHUNK_MAX] + " …（截断）"
                lines.append("")
                lines.append(f"片段[{i}] `{cid}` ｜ {c.get('title','')} ｜ {c.get('heading_path','')}")
                lines.append("")
                lines.append("```text")
                lines.append(text)
                lines.append("```")
            lines.append("")
            lines.append("---")
            lines.append("")
        (out_dir / name).write_text("\n".join(lines), encoding="utf-8")
        print(f"{name}: {len(part_rows)} 条")

    (out_dir / "SPEC.md").write_text(SPEC.replace("{part}", "N").replace("{n}", "30"), encoding="utf-8")
    print(f"SPEC -> {out_dir / 'SPEC.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
