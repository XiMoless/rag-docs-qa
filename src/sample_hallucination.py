"""幻觉率抽检：把 eval 的逐题明细转成「可人工复核的表格」，并做三层自动预判。

口径（写死，README 同步）：
    幻觉率 = 被判为「有幻觉」的题数 / 参与抽检的题数
    判为幻觉的三种情形（任一命中即算）：
      H1 无答案题没有拒答（模型硬编了一个答案）
      H2 回答里的英文标识符 / 数字，在它自己引用的片段里找不到（编造 API 名、编造数值）
      H3 回答没有任何 [编号] 引用（无依据陈述）

自动预判只是**预标注**，最终以人工复核列为准：H2 会对「正确但换了说法」漏判，
H1/H3 会给「拒答但措辞不标准」误判，所以人工列一旦填了就以人工为准。

输入要求：
  --detail  src.eval --out 产生的逐题明细（字段：qid/type/top5/answer/score/recall@k）
  --set     评测集（提供 question / gold_answer / source_ids）
  --chunks  data/processed/chunks.jsonl（把 top5 的 chunk_id 还原成文本，用于 H2 回溯）

用法：
    python -m src.sample_hallucination --detail results/eval_E001.jsonl --limit 100
    python -m src.sample_hallucination --detail results/eval_E001.jsonl --exp-id E001 --out results/hallucination_check_E001.md
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SET = ROOT / "eval" / "eval_set_v1.jsonl"
DEFAULT_CHUNKS = ROOT / "data" / "processed" / "chunks.jsonl"
DEFAULT_OUT = ROOT / "results" / "hallucination_check.md"

# 英文标识符：下划线/驼峰 API 名、点号参数、全大写常量
IDENT_RE = re.compile(
    r"\b(?:[a-z][a-z0-9]*(?:_[a-z0-9]+)+|[a-zA-Z]*[A-Z][a-zA-Z0-9]*|[A-Z][A-Z0-9_]{2,}|[A-Za-z_]+\.[A-Za-z_]+)\b"
)
NUM_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w.])")
ABSTAIN_WORDS = (
    "没有找到", "找不到", "无法回答", "文档里没有", "不足以回答",
    "未提及", "没有提及", "不包含", "未说明", "本题无答案",
)


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def cited_ids(answer: str) -> list[int]:
    return sorted({int(m) for m in re.findall(r"\[(\d{1,2})\]", answer or "")})


def auto_label(row: dict, meta: dict, chunk_text: dict[str, str]) -> tuple[str, str]:
    """返回 (预判, 理由)。预判 ∈ {'H1','H2','H3','OK'}。"""
    ans = row.get("answer") or ""
    gold = meta.get("gold_answer") or ""
    is_na = meta.get("type") == "no-answer" or gold.strip() == "本题无答案"

    if is_na:
        for w in ABSTAIN_WORDS:
            if w in ans:
                return "OK", "无答案题已拒答"
        return "H1", "无答案题未拒答（疑似硬编答案）"

    # 未答（答案是「没找到」）属于召回失败，不算幻觉
    if any(w in ans for w in ABSTAIN_WORDS) and len(ans) < 400:
        return "MISS", "未作答（拒答/声明找不到）"

    cids = cited_ids(ans)
    if not cids:
        return "H3", "回答没有任何 [编号] 引用"

    ctx = "\n".join(chunk_text.get(c, "") for c in (row.get("top5") or []))
    ctx_low = ctx.lower()

    missing = []
    for tok in set(IDENT_RE.findall(ans)):
        if tok.lower() not in ctx_low:
            missing.append(tok)
    missing = [m for m in missing if len(m) >= 4 and not m.isalpha()]
    if len(missing) >= 2:
        return "H2", "标识符不在引用片段: " + ", ".join(sorted(missing)[:5])

    ans_wo_cite = re.sub(r"\[\d{1,2}\]", "", ans)  # 去掉引用标记再查数字
    bad_nums = [n for n in NUM_RE.findall(ans_wo_cite) if n not in ctx]
    if bad_nums:
        return "H2", "数字不在引用片段: " + ", ".join(sorted(set(bad_nums))[:5])

    return "OK", "有引用、标识符与数字均可回溯"


def render(rows: list[dict], metas: dict[str, dict], chunk_text: dict[str, str], exp_id: str) -> tuple[str, dict]:
    out = [
        f"# 幻觉率抽检表 · {exp_id}",
        "",
        "> 口径：幻觉率 = 判为「有幻觉」的题数 / 抽检题数。",
        "> 预判列（H1 无答案未拒答 / H2 引用不支持 / H3 无引用）由脚本自动给出，**最终以人工复核列为准**。",
        "> 人工复核列填 `OK` 或 `H1/H2/H3`；与预判不一致时在备注写原因（用来统计脚本误判率）。",
        "",
        "| # | qid | 题型 | 问题 | 回答（截断） | 预判 | 理由 | 人工复核 | 备注 |",
        "|---|-----|------|------|--------------|------|------|----------|------|",
    ]
    counts = {"H1": 0, "H2": 0, "H3": 0, "MISS": 0, "OK": 0}
    for i, r in enumerate(rows, 1):
        meta = metas.get(r.get("qid", ""), {})
        label, why = auto_label(r, meta, chunk_text)
        counts[label] += 1
        q = (meta.get("question") or "").replace("|", "\\|")[:80]
        a = (r.get("answer") or "").replace("\n", " ").replace("|", "\\|")[:120]
        out.append(
            f"| {i} | {r.get('qid','')} | {meta.get('type','')} | {q} | {a} | {label} | {why} |  |  |"
        )
    n = len(rows) or 1
    hallu = counts["H1"] + counts["H2"] + counts["H3"]
    out += [
        "",
        "## 自动预判汇总",
        "",
        f"- 抽检题数：{len(rows)}",
        f"- 预判 OK：{counts['OK']}（{counts['OK'] / n:.1%}）",
        f"- 预判 H1 无答案未拒答：{counts['H1']}",
        f"- 预判 H2 引用不支持：{counts['H2']}",
        f"- 预判 H3 无引用：{counts['H3']}",
        f"- **未作答（不算幻觉，算召回失败）：{counts['MISS']}**",
        f"- **预判幻觉率：{hallu} / {len(rows) - counts['MISS']} = {hallu / (len(rows) - counts['MISS'] or 1):.1%}**（分母为实际给出答案的题数）",
        "",
        "> 该数字是**自动预判**；写进 README/简历前必须完成人工复核列，并把两者不一致的题单列出来。",
    ]
    return "\n".join(out), counts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--detail", required=True, help="src.eval --out 产生的逐题明细 jsonl")
    ap.add_argument("--set", default=str(DEFAULT_SET), help="评测集 jsonl")
    ap.add_argument("--chunks", default=str(DEFAULT_CHUNKS), help="chunks.jsonl")
    ap.add_argument("--limit", type=int, default=0, help="抽检前 N 题（0=全量）")
    ap.add_argument("--exp-id", default="", help="实验 id，仅用于标题；默认取明细文件名")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    rows = read_jsonl(Path(args.detail))
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        print("明细为空，先跑 src.eval --judge")
        return 1
    metas = {r["qid"]: r for r in read_jsonl(Path(args.set))}
    chunk_text = {c["chunk_id"]: c["text"] for c in read_jsonl(Path(args.chunks))}

    exp = args.exp_id or Path(args.detail).stem
    md, counts = render(rows, metas, chunk_text, exp)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"rows={len(rows)} auto={counts} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
