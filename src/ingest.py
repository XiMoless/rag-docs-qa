"""把 data/raw/*.md 切成 chunk，落 data/processed/chunks.jsonl。

用法：
    python -m src.ingest                 # 默认 heading 切分（config 里改）
    python -m src.ingest --strategy fixed
    python -m src.ingest --size 500 --overlap 80

chunk 字段：
    chunk_id  doc_id  slug  url  title  section  heading_path  order  start  end  chars  text
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "chunks.jsonl"

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def parse_doc(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    meta: dict = {}
    body = text
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            raw = text[4:end]
            try:
                meta = json.loads(raw)
            except json.JSONDecodeError:
                meta = {}
            body = text[end + 5 :]
    return meta, body.lstrip("\n")


def split_blocks(body: str) -> list[tuple[str, str]]:
    """返回 [(heading_path, block_text)]，heading_path 形如 'Guide > Middleware'。

    代码块内部不切分（``` 内的空行保留在同一个块）。
    """
    out: list[tuple[str, str]] = []
    stack: list[tuple[int, str]] = []
    buf: list[str] = []

    def flush() -> None:
        text = "\n\n".join(buf).strip()
        if text:
            path = " > ".join(t for _, t in stack) or "ROOT"
            out.append((path, text))
        buf.clear()

    in_code = False
    for line in body.split("\n"):
        if line.startswith("```"):
            in_code = not in_code
            buf.append(line)
            continue
        if in_code:
            buf.append(line)
            continue
        m = HEADING_RE.match(line)
        if m:
            flush()
            level = len(m.group(1))
            title = m.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            continue
        if not line.strip():
            flush()
            continue
        buf.append(line)
    flush()
    return out


def hard_split(text: str, size: int, overlap: int) -> list[str]:
    """按句子边界尽量切到 size 字符，块间保留 overlap。"""
    if len(text) <= size:
        return [text]
    sentences = re.split(r"(?<=[。！？.!?:：])\s+|\n+", text)
    chunks: list[str] = []
    cur = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(s) > size:  # 单句超长（比如巨长代码行），直接硬切
            if cur:
                chunks.append(cur)
                cur = ""
            for i in range(0, len(s), size - overlap):
                chunks.append(s[i : i + size])
            continue
        if len(cur) + len(s) + 1 > size and cur:
            chunks.append(cur)
            tail = cur[-overlap:] if overlap else ""
            cur = (tail + " " + s).strip() if tail else s
        else:
            cur = (cur + " " + s).strip() if cur else s
    if cur:
        chunks.append(cur)
    return chunks


def chunk_doc(meta: dict, body: str, strategy: str, size: int, overlap: int, min_chars: int) -> list[dict]:
    slug = meta.get("slug") or ""
    title = meta.get("title") or ""
    url = meta.get("url") or ""
    out: list[dict] = []
    order = 0

    if strategy == "fixed":
        text = body.strip()
        for i, piece in enumerate(hard_split(text, size, overlap)):
            if len(piece) < min_chars:
                continue
            out.append(
                {
                    "doc_id": slug,
                    "slug": slug,
                    "url": url,
                    "title": title,
                    "section": "",
                    "heading_path": title,
                    "order": i,
                    "start": i * max(size - overlap, 1),
                    "end": i * max(size - overlap, 1) + len(piece),
                    "chars": len(piece),
                    "text": piece,
                }
            )
        return out

    offset = 0
    for path, block in split_blocks(body):
        for piece in hard_split(block, size, overlap):
            if len(piece) < min_chars:
                continue
            idx = body.find(piece, offset)
            start = idx if idx >= 0 else offset
            offset = start + len(piece)
            out.append(
                {
                    "doc_id": slug,
                    "slug": slug,
                    "url": url,
                    "title": title,
                    "section": path.split(" > ")[-1],
                    "heading_path": path,
                    "order": order,
                    "start": start,
                    "end": start + len(piece),
                    "chars": len(piece),
                    "text": piece,
                }
            )
            order += 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default="heading", choices=["heading", "fixed"])
    ap.add_argument("--size", type=int, default=700)
    ap.add_argument("--overlap", type=int, default=120)
    ap.add_argument("--min-chars", type=int, default=80)
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    files = sorted(RAW_DIR.glob("*.md"))
    if not files:
        print("data/raw 里没有 md，先跑 src.fetch_corpus")
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    total_chunks = 0
    total_chars = 0
    per_doc: list[tuple[str, int]] = []

    with out_path.open("w", encoding="utf-8") as f:
        for path in files:
            meta, body = parse_doc(path)
            meta.setdefault("slug", path.stem)
            chunks = chunk_doc(meta, body, args.strategy, args.size, args.overlap, args.min_chars)
            for c in chunks:
                c["chunk_id"] = f"{c['doc_id']}#{c['order']:03d}"
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
            total_chunks += len(chunks)
            total_chars += sum(c["chars"] for c in chunks)
            per_doc.append((path.stem, len(chunks)))

    print(f"strategy={args.strategy} size={args.size} overlap={args.overlap}")
    print(f"docs={len(files)} chunks={total_chunks} chars={total_chars:,} avg={total_chars // max(total_chunks,1):,}/chunk")
    print(f"-> {out_path}")
    per_doc.sort(key=lambda x: -x[1])
    print("top docs by chunks:", per_doc[:5])
    print("docs with 0 chunks:", [d for d, n in per_doc if n == 0][:10])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
