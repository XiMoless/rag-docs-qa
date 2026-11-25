"""汇总 240 题人工审计（E015 配置）→ 幻觉率/正确率/弃答率，含 v1 vs v2 分集对比。

与 `src/aggregate_audit.py` 的区别：那个是 v1 100 题（E004 口径）的历史产物，不要改它。
本脚本固定读 `eval/audit240/part*.jsonl`，按 qid 前缀拆 v1/v2 两套题分别统计。

口径沿用 aggregate_audit.py（写死）：
- strict  = HALLUC / (HALLUC + WRONG + OK)
- guarded = HALLUC / (HALLUC + WRONG + OK + MISS)
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT_DIR = ROOT / "eval" / "audit240"
EVAL_SET = ROOT / "eval" / "eval_set_all.jsonl"
DETAIL = ROOT / "results" / "eval_E015.jsonl"
OUT = ROOT / "results" / "hallucination_summary_240.md"
VERDICTS = {"OK", "MISS", "HALLUC", "WRONG"}


def load_meta() -> tuple[dict[str, str], dict[str, str]]:
    types, sets = {}, {}
    for line in EVAL_SET.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        q = json.loads(line)
        types[q["qid"]] = q.get("type", "?")
        sets[q["qid"]] = "v2" if q["qid"].startswith("v2-") else "v1"
    return types, sets


def rate(c: Counter, key: str = "HALLUC") -> tuple[float, float]:
    denom_strict = c["HALLUC"] + c["WRONG"] + c["OK"]
    denom_guarded = denom_strict + c["MISS"]
    strict = c[key] / denom_strict if denom_strict else 0.0
    guarded = c[key] / denom_guarded if denom_guarded else 0.0
    return strict, guarded


def main() -> int:
    types, sets = load_meta()
    files = sorted(AUDIT_DIR.glob("part*.jsonl"))
    if not files:
        print(f"没有审计文件：{AUDIT_DIR}")
        return 1

    rows: list[dict] = []
    for p in files:
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            r["part"] = p.stem.replace("part", "")
            r["type"] = types.get(r["qid"], "?")
            r["set"] = sets.get(r["qid"], "?")
            rows.append(r)

    detail_qids = set()
    if DETAIL.exists():
        for line in DETAIL.read_text(encoding="utf-8").splitlines():
            if line.strip():
                detail_qids.add(json.loads(line)["qid"])

    audited = {r["qid"] for r in rows}
    missing = sorted(detail_qids - audited)
    extra = sorted(audited - detail_qids)
    bad = [r["qid"] for r in rows if r.get("verdict") not in VERDICTS]

    total = len(rows)
    overall = Counter(r["verdict"] for r in rows)
    by_set: dict[str, Counter] = defaultdict(Counter)
    by_type: dict[str, Counter] = defaultdict(Counter)
    by_part: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        by_set[r["set"]][r["verdict"]] += 1
        by_type[r["type"]][r["verdict"]] += 1
        by_part[r["part"]][r["verdict"]] += 1

    strict, guarded = rate(overall)
    acc = overall["OK"] / total if total else 0.0

    lines: list[str] = []
    lines.append("# 幻觉与答案质量人工审计汇总（240 题 · E015 配置）\n")
    lines.append(f"- 审计条目：**{total} / {len(detail_qids)}**（{len(files)} 份材料；缺 {len(missing)} 条，多 {len(extra)} 条）")
    if missing:
        lines.append(f"- ⚠️ 缺审条目：{', '.join(missing[:20])}{' …' if len(missing) > 20 else ''}")
    if extra:
        lines.append(f"- ⚠️ 多出条目（不在明细里）：{', '.join(extra[:20])}")
    if bad:
        lines.append(f"- ⚠️ 非法 verdict：{bad[:10]}")
    lines.append(f"- 判定分布：OK {overall['OK']} / MISS {overall['MISS']} / HALLUC {overall['HALLUC']} / WRONG {overall['WRONG']}")
    lines.append(f"- **幻觉率（strict）= {strict:.1%}**（{overall['HALLUC']}/{overall['HALLUC'] + overall['WRONG'] + overall['OK']}，分母排除弃答）")
    lines.append(f"- **幻觉率（guarded）= {guarded:.1%}**（{overall['HALLUC']}/{total}，分母含弃答）")
    lines.append(f"- 弃答率 = {overall['MISS'] / total:.1%}（{overall['MISS']}/{total}）")
    lines.append(f"- 人工正确率 = {acc:.1%}（OK/全部；**与 judge 的 0.761 不是同一口径**，judge 允许部分分）\n")

    lines.append("## 分题集\n")
    lines.append("| 题集 | n | OK | MISS | HALLUC | WRONG | 幻觉率(strict) | 弃答率 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for s in sorted(by_set):
        c = by_set[s]
        n = sum(c.values())
        st, _ = rate(c)
        lines.append(f"| {s} | {n} | {c['OK']} | {c['MISS']} | {c['HALLUC']} | {c['WRONG']} | {st:.1%} | {c['MISS'] / n:.1%} |")

    lines.append("\n## 分题型\n")
    lines.append("| 题型 | n | OK | MISS | HALLUC | WRONG | 幻觉率(strict) |")
    lines.append("|---|---|---|---|---|---|---|")
    for t in sorted(by_type):
        c = by_type[t]
        n = sum(c.values())
        st, _ = rate(c)
        lines.append(f"| {t} | {n} | {c['OK']} | {c['MISS']} | {c['HALLUC']} | {c['WRONG']} | {st:.1%} |")

    lines.append("\n## 分段\n")
    lines.append("| 材料 | OK | MISS | HALLUC | WRONG |")
    lines.append("|---|---|---|---|---|")
    for p in sorted(by_part, key=lambda x: int(x)):
        c = by_part[p]
        lines.append(f"| {p} | {c['OK']} | {c['MISS']} | {c['HALLUC']} | {c['WRONG']} |")

    lines.append("\n## HALLUC 逐条\n")
    hl = [r for r in rows if r["verdict"] == "HALLUC"]
    if not hl:
        lines.append("无。\n")
    for r in hl:
        claims = r.get("hallucinated_claims") or []
        if isinstance(claims, str):
            claims = [claims]
        lines.append(f"- `{r['qid']}`（{r['type']}｜{r['set']}）：{r.get('reason', '')}")
        for c in claims:
            lines.append(f"  - 断言：{c}")

    lines.append("\n## WRONG 逐条\n")
    wr = [r for r in rows if r["verdict"] == "WRONG"]
    if not wr:
        lines.append("无。\n")
    for r in wr:
        lines.append(f"- `{r['qid']}`（{r['type']}｜{r['set']}）：{r.get('reason', '')}")

    lines.append("\n## 口径说明\n")
    lines.append("- 本表统计 **240 题 + E015 主配置**（k=8 / qe / rerank / expand±1）的一次运行。")
    lines.append("- 与 `results/hallucination_summary.md`（v1 100 题 + E004 配置）不可混引：题集不同、配置不同。")
    lines.append("- 「引用片段超出材料」的条目在 reason 里注明；只要没有与所给片段冲突就判 OK。")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"OK {overall['OK']} MISS {overall['MISS']} HALLUC {overall['HALLUC']} WRONG {overall['WRONG']} | strict {strict:.1%} guarded {guarded:.1%} | 缺 {len(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
