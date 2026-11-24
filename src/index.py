"""建索引：bge-m3 向量（faiss）+ BM25。

用法：
    python -m src.index                     # 全量重建
    python -m src.index --no-embed          # 只重建 BM25

产出：
    index/chunks_emb.npy      (N, 1024) float32 归一化向量
    index/langchain_docs.faiss
    index/langchain_docs_bm25.pkl
    index/meta.json           块数 / 模型名 / 建库时间
"""

from __future__ import annotations

import argparse
import json
import pickle
import re
import time
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CHUNKS = ROOT / "data" / "processed" / "chunks.jsonl"
INDEX_DIR = ROOT / "index"

MODEL_NAME = "BAAI/bge-m3"
BATCH = 16


def load_chunks() -> list[dict]:
    with CHUNKS.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def embed_input(c: dict) -> str:
    """给 embedding 的文本带上标题路径，提升同类问题的召回。"""
    head = c.get("heading_path") or c.get("title") or ""
    return f"{head}\n{c['text']}"


def build_embeddings(chunks: list[dict], out_dir: Path) -> np.ndarray:
    from sentence_transformers import SentenceTransformer

    print(f"loading {MODEL_NAME} ...")
    t0 = time.time()
    model = SentenceTransformer(MODEL_NAME, device="cuda")
    print(f"model ready in {time.time() - t0:.0f}s, dim={model.get_sentence_embedding_dimension()}")

    texts = [embed_input(c) for c in chunks]
    vecs = model.encode(
        texts,
        batch_size=BATCH,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return vecs.astype("float32")


def build_faiss(vecs: np.ndarray, out_dir: Path) -> None:
    import faiss

    out_dir.mkdir(parents=True, exist_ok=True)
    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)
    faiss.write_index(index, str(out_dir / "langchain_docs.faiss"))
    np.save(out_dir / "chunks_emb.npy", vecs)
    print(f"faiss: {index.ntotal} vectors, dim={vecs.shape[1]}")


TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def build_bm25(chunks: list[dict], out_dir: Path) -> None:
    from rank_bm25 import BM25Okapi

    corpus = [tokenize(embed_input(c)) for c in chunks]
    bm25 = BM25Okapi(corpus, k1=1.5, b=0.75)
    with (out_dir / "langchain_docs_bm25.pkl").open("wb") as f:
        pickle.dump({"bm25": bm25, "tokens": corpus}, f)
    print(f"bm25: {len(corpus)} docs, vocab={len(bm25.idf)}")


def main() -> int:
    global CHUNKS
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-embed", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--chunks", default=str(CHUNKS), help="chunk 表路径（消融用另一份切分）")
    ap.add_argument("--out-dir", default=str(INDEX_DIR), help="索引输出目录")
    args = ap.parse_args()

    CHUNKS = Path(args.chunks)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    chunks = load_chunks()
    if args.limit:
        chunks = chunks[: args.limit]
    print(f"chunks: {len(chunks)} from {CHUNKS}")

    if not args.no_embed:
        vecs = build_embeddings(chunks, out_dir)
        build_faiss(vecs, out_dir)

    build_bm25(chunks, out_dir)

    meta = {
        "chunks": len(chunks),
        "chunks_file": str(CHUNKS),
        "model": MODEL_NAME,
        "built_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "chunking": CHUNKS.stem,
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("done:", meta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
