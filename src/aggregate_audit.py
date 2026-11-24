"""汇总 4 段人工审计结果 → 幻觉率/弃答率/正确率总表。

口径（写死，改口径必须改这里并在 RESULTS.md 注明）：
- HALLUC：回答里出现片段不支持的**具体断言**（名称、数值、API、机制替换）→ 计入幻觉。
- WRONG：断言可溯源但结论与 gold 相反 / 机制选错 → 计入答案错误，不计幻觉。
- MISS：模型声明「片段没给」而未作答 → 计入弃答，**不计入幻觉**。
  例外：判定为 no-answer 的题，正确拒答记 OK，不记 MISS。
- OK：回答正确，或措辞不同但结论等价。

幻觉率定义二选一（两个都报，避免选择性引用）：
- strict  = HALLUC / (HALLUC + WRONG + OK)        # 分母排除弃答
- guarded = HALLUC / (HALLUC + WRONG + OK + MISS) # 分母含弃答，回答越谨慎越好看
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

AUDIT_DIR = Path("eval/audit")
EVAL_SET = Path("eval/eval_set_v1.jsonl")
OUT = Path("results/hallucination_summary.md")

PARTS = ["A", "B", "C", "D"]
VERDICTS = {"OK", "MISS", "HALLUC", "WRONG"}
NO_ANSWER_GOLD = "本题无答案"


def load_types() -> dict[str, str]:
    types = {}
    for line in EVAL_SET.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        q = json.loads(line)
        types[q["qid"]] = q.get("type", "?")
    return types


def main() -> int:
    types = load_types()
    rows: list[dict] = []
    missing_files = []
    for part in PARTS:
        p = AUDIT_DIR / f"part{part}.jsonl"
        if not p.exists():
            missing_files.append(str(p))
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            r["part"] = part
            r["type"] = types.get(r["qid"], "?")
            rows.append(r)

    if missing_files:
        print("缺审计文件：", ", ".join(missing_files))

    bad = [r["qid"] for r in rows if r.get("verdict") not in VERDICTS]
    if bad:
        print(f"非法 verdict {len(bad)} 条：{bad[:5]}")

    total = len(rows)
    overall = Counter(r["verdict"] for r in rows)
    by_part: dict[str, Counter] = defaultdict(Counter)
    by_type: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        by_part[r["part"]][r["verdict"]] += 1
        by_type[r["type"]][r["verdict"]] += 1

    halluc, wrong, ok = overall["HALLUC"], overall["WRONG"], overall["OK"]
    miss = overall["MISS"]
    denom_strict = halluc + wrong + ok
    denom_guarded = denom_strict + miss
    strict = halluc / denom_strict if denom_strict else 0.0
    guarded = halluc / denom_guarded if denom_guarded else 0.0
    acc = ok / total if total else 0.0

    lines = []
    lines.append("# 幻觉与答案质量人工审计汇总（v1 评测集，E004 配置）\n")
    lines.append(f"- 审计条目：**{total}**（A/B/C/D 各 25，缺文件：{missing_files or '无'}）")
    lines.append(f"- 判定分布：OK {ok} / MISS {miss} / HALLUC {halluc} / WRONG {wrong}")
    lines.append(f"- **幻觉率（strict）= {strict:.1%}**（{halluc}/{denom_strict}，分母排除弃答）")
    lines.append(f"- **幻觉率（guarded）= {guarded:.1%}**（{halluc}/{denom_guarded}，分母含弃答）")
    lines.append(f"- 弃答率 = {miss / total:.1%}（{miss}/{total}）")
    lines.append(f"- 答案正确率（OK/全部，与 eval.py 的 judge 口径不同，勿混用）= {acc:.1%}\n")

    lines.append("## 分题型\n")
    lines.append("| 题型 | OK | MISS | HALLUC | WRONG | 幻觉率(strict) |")
    lines.append("|---|---|---|---|---|---|")
    for t in sorted(by_type):
        c = by_type[t]
        d = c["HALLUC"] + c["WRONG"] + c["OK"]
        rate = f"{c['HALLUC'] / d:.1%}" if d else "—"
        lines.append(f"| {t} | {c['OK']} | {c['MISS']} | {c['HALLUC']} | {c['WRONG']} | {rate} |")

    lines.append("\n## 分段\n")
    lines.append("| 段 | OK | MISS | HALLUC | WRONG |")
    lines.append("|---|---|---|---|---|")
    for p in PARTS:
        c = by_part[p]
        lines.append(f"| {p} | {c['OK']} | {c['MISS']} | {c['HALLUC']} | {c['WRONG']} |")

    lines.append("\n## 被判定为 HALLUC 的条目（逐条复核）\n")
    hl = [r for r in rows if r["verdict"] == "HALLUC"]
    if not hl:
        lines.append("无。\n")
    for r in hl:
        claims = r.get("hallucinated_claims") or []
        if isinstance(claims, str):
            claims = [claims]
        lines.append(f"- `{r['qid']}`（{r['type']}｜{r['part']} 段）：{r.get('reason', '')}")
        for c in claims:
            lines.append(f"  - 断言：{c}")

    lines.append("\n## 被判定为 MISS 的条目（召回缺失，不计幻觉）\n")
    ms = [r for r in rows if r["verdict"] == "MISS"]
    if not ms:
        lines.append("无。\n")
    for r in ms:
        lines.append(f"- `{r['qid']}`（{r['type']}）：{r.get('reason', '')[:160]}")

    lines.append("\n## 口径说明\n")
    lines.append("- 本表只统计 **v1 评测集（100 题）+ E004 配置** 的一次运行。换配置/换评测集必须重跑并新起 RESULTS 行。")
    lines.append("- MISS 与 HALLUC 严格区分：模型说「片段里没有」不算幻觉，但算「答不出」。")
    lines.append("- 若某条被两个审计员判得不同，以本表为准；改动需在此注明。")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"OK {ok} MISS {miss} HALLUC {halluc} WRONG {wrong} | strict {strict:.1%} guarded {guarded:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
