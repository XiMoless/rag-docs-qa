"""构建 HF Space 演示用的小体积索引（bge-small-en，384 维）。

与主实验的区别写在 artifacts/meta.json 里，避免口径混淆：
- 主实验（RESULTS.md E015/E016）用 BAAI/bge-m3（1024 维，GPU）
- 演示站点用 BAAI/bge-small-en-v1.5（384 维，CPU 可跑），只为「能点开」

用法：
    .\\.venv\\Scripts\\python.exe -m deploy.build_demo_space
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CHUNKS = ROOT / "data" / "processed" / "chunks.jsonl"
OUT = ROOT / "deploy" / "hf-space" / "artifacts"
MODEL = "BAAI/bge-small-en-v1.5"
KEEP_FIELDS = ("chunk_id", "doc_id", "url", "title", "heading_path", "order", "text")


def embed_input(c: dict) -> str:
    """与 src/index.py 保持一致的拼接方式：标题路径 + 正文。"""
    hp = c.get("heading_path") or ""
    return f"{hp}\n{c['text']}" if hp else c["text"]


def main() -> int:
    from sentence_transformers import SentenceTransformer

    t0 = time.time()
    chunks = [json.loads(line) for line in CHUNKS.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"chunks: {len(chunks)}")
    OUT.mkdir(parents=True, exist_ok=True)

    slim = [{k: c.get(k) for k in KEEP_FIELDS} for c in chunks]
    slim_path = OUT / "chunks.jsonl"
    with slim_path.open("w", encoding="utf-8", newline="\n") as f:
        for c in slim:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"wrote {slim_path.name}: {slim_path.stat().st_size / 1e6:.2f} MB")

    device = "cuda"
    print(f"loading {MODEL} on {device} ...")
    model = SentenceTransformer(MODEL, device=device)
    dim = model.get_sentence_embedding_dimension()
    texts = [embed_input(c) for c in chunks]
    vecs = model.encode(
        texts,
        batch_size=64,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=True,
    ).astype(np.float16)
    print(f"encoded dim={dim} in {time.time() - t0:.0f}s")

    vec_path = OUT / "vectors.npy"
    np.save(vec_path, vecs)
    print(f"wrote {vec_path.name}: {vec_path.stat().st_size / 1e6:.2f} MB (float16)")

    meta = {
        "count": len(chunks),
        "dim": int(dim),
        "model": MODEL,
        "dtype": "float16 (L2-normalized)",
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "chunking": "heading/size700/overlap120",
        "note": "演示站点专用小模型；正式实验指标（RESULTS.md E015/E016）用的是 BAAI/bge-m3 1024 维，二者不可混用。",
    }
    meta_path = OUT / "meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {meta_path.name}")
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    total = sum(p.stat().st_size for p in OUT.iterdir())
    print(f"artifacts total: {total / 1e6:.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
