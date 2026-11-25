"""LangChain 文档问答 RAG —— 演示版（ModelScope 创空间）

与 HF Space 版（deploy/hf-space/app.py）的差别：
- 模型从 ModelScope 模型库下载（国内直连），embedding 用 AI-ModelScope/bge-small-en-v1.5
- 免费 CPU 上跑不动 cross-encoder 重排（可用的 278M/1.1GB 底座在 CPU 上单次要数秒），
  因此本版**不做 rerank**，靠「翻译成英文 + 向量 + BM25 + RRF 融合」把召回撑起来
- 与仓库主实验（bge-m3 + bge-reranker-v2-m3）不可混用，本页不宣称任何 R@5 / 正确率数字
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import gradio as gr
import numpy as np

ART = Path(__file__).parent / "artifacts"
TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]")
API_BASE = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
API_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
MS_MODEL_ID = os.environ.get("MS_EMBED_MODEL", "AI-ModelScope/bge-small-en-v1.5")

SYSTEM_PROMPT = """你是 LangChain 官方文档的问答助手。规则：

1. 只根据下面给出的【文档片段】回答，不要用你记忆里的知识补充。
2. 每个结论后面用 [编号] 标注来源，例如 [2]；编号必须来自片段列表。
3. 如果片段只能部分回答：先给出片段能支持的部分（标好来源），再明确说明还缺什么。如果片段完全无关，才说「给出的文档里没有找到能回答这个问题的内容」。
4. 如果片段里 API 名称、参数看起来与用户说法不一致，以片段为准，并指出差异。
5. 用中文回答，代码块保留原语言；先给结论，再给最小可用示例。

【文档片段】
{context}

【问题】
{question}
"""

TRANSLATE_PROMPT = """把下面的中文技术问题翻译成用于检索英文技术文档的关键词。

要求：
1. 只输出空格分隔的英文关键词或短语，6-10 个，不要解释、不要标点。
2. 保留原文里的 API 名、参数名、类名（如 checkpointer、interrupt_on）。
3. 补上英文文档里更可能出现的同义技术词（如「续跑」→ resume, restore, invoke）。

问题：{question}
"""


# ---------------------------------------------------------------- 资源加载
def _env_diag() -> None:
    """启动时打印环境变量诊断，只输出变量名与是否存在，绝不输出值。"""
    names = sorted(k for k in os.environ if ("KEY" in k.upper() or "SECRET" in k.upper() or "TOKEN" in k.upper()))
    print(f"[env] 相关变量名: {names}")
    print(f"[env] DEEPSEEK_API_KEY 已配置: {bool(os.environ.get('DEEPSEEK_API_KEY', '').strip())}")


def _load() -> tuple[list[dict], np.ndarray, dict]:
    chunks = [json.loads(line) for line in (ART / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    try:
        vecs = np.load(ART / "vectors.npy").astype(np.float32)
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] vectors.npy 不可用（{exc}），本次只用 BM25 检索")
        vecs = None
    meta = json.loads((ART / "meta.json").read_text(encoding="utf-8"))
    return chunks, vecs, meta


CHUNKS, VECS, META = _load()
BM25 = None
_EMBEDDER = None


def get_embedder():
    """从 ModelScope 模型库取本地路径（国内直连），失败再退回 HF 模型名。"""
    global _EMBEDDER
    if _EMBEDDER is None:
        from sentence_transformers import SentenceTransformer

        model_path = os.environ.get("MS_EMBED_PATH", "")
        if not model_path:
            try:
                from modelscope import snapshot_download

                model_path = snapshot_download(MS_MODEL_ID)
                print(f"[model] modelscope local path: {model_path}")
            except Exception as exc:  # noqa: BLE001
                print(f"[model] modelscope download failed ({exc}), fallback to HF id {META['model']}")
                model_path = META["model"]
        _EMBEDDER = SentenceTransformer(model_path, device="cpu")
    return _EMBEDDER


def get_bm25():
    global BM25
    if BM25 is None:
        from rank_bm25 import BM25Okapi

        corpus = [TOKEN_RE.findall((c.get("heading_path") or "") + " " + c["text"]) for c in CHUNKS]
        BM25 = BM25Okapi(corpus, k1=1.5, b=0.75)
    return BM25


def api_client():
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        return None
    from openai import OpenAI

    return OpenAI(api_key=key, base_url=API_BASE)


# ---------------------------------------------------------------- 检索
def search_vector(q: str, k: int) -> list[tuple[int, float]]:
    if not _DENSE_ON:
        return []
    try:
        emb = get_embedder().encode([q], normalize_embeddings=True, convert_to_numpy=True)[0].astype(np.float32)
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] dense 通道不可用（{exc}），退回 BM25")
        return []
    scores = VECS @ emb
    top = np.argsort(-scores)[:k]
    return [(int(i), float(scores[i])) for i in top]


def search_bm25(q: str, k: int) -> list[tuple[int, float]]:
    toks = TOKEN_RE.findall(q)
    if not toks:
        return []
    scores = get_bm25().get_scores(toks)
    top = np.argsort(-scores)[:k]
    return [(int(i), float(scores[i])) for i in top]


def rrf(q: str, k: int, kw_query: str | None = None, rrf_k: int = 60) -> list[tuple[int, float]]:
    """三路融合：向量(中文原句) + 向量(英文关键词) + BM25(英文关键词)。

    实测（演示语料）：中文原句进 bge-small-en 并不总是噪音——「durability 设成 exit」这类
    问题，原句能直接把 Durability modes 排到第一，而纯关键词反而被 interrupt/resume 的讲法带走。
    所以两路向量都保留，让 RRF 去融合；BM25 只用英文关键词（中文对它等于零重叠）。
    """
    channels = [c for c in [search_vector(q, k)] if c]
    if kw_query:
        channels += [c for c in [search_vector(kw_query, k), search_bm25(kw_query, k)] if c]
    fused: dict[int, float] = {}
    for hits in channels:
        for rank, (idx, _) in enumerate(hits, start=1):
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (rrf_k + rank)
    return sorted(fused.items(), key=lambda x: -x[1])[:k]


def translate(q: str, client) -> str:
    if client is None:
        return ""
    try:
        r = client.chat.completions.create(
            model=API_MODEL,
            messages=[{"role": "user", "content": TRANSLATE_PROMPT.format(question=q)}],
            temperature=0,
            max_tokens=80,
        )
        return (r.choices[0].message.content or "").strip()
    except Exception as exc:  # noqa: BLE001
        print(f"translate failed: {exc}")
        return ""


def build_context(hits: list[tuple[int, float]], max_chars: int = 6000) -> str:
    parts, total = [], 0
    for n, (idx, _) in enumerate(hits, start=1):
        c = CHUNKS[idx]
        block = f"【片段 {n}】{c.get('title') or ''} · {c.get('heading_path') or ''}\n{c.get('url') or ''}\n{c['text'].strip()}"
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n\n".join(parts)


def dedupe(hits: list[tuple[int, float]], top_n: int) -> list[tuple[int, float]]:
    """Python / JavaScript 两份文档常有逐字相同的段落，去重后避免 top5 被同一段占满。"""
    seen: set[str] = set()
    out: list[tuple[int, float]] = []
    for idx, score in hits:
        key = CHUNKS[idx]["text"][:160].strip()
        if key in seen:
            continue
        seen.add(key)
        out.append((idx, score))
        if len(out) >= top_n:
            break
    return out


def rows(hits: list[tuple[int, float]]) -> list[list]:
    return [
        [n, (CHUNKS[i].get("title") or "")[:40], (CHUNKS[i].get("heading_path") or "")[:50], round(s, 4), CHUNKS[i].get("url") or ""]
        for n, (i, s) in enumerate(hits, start=1)
    ]


# ---------------------------------------------------------------- 主流程
def answer(question: str, mode: str, k: int, use_translate: bool):
    question = (question or "").strip()
    if not question:
        return "先输入一个问题。", [], ""
    t0 = time.time()
    client = api_client()
    kw = translate(question, client) if (use_translate and client) else ""
    # bge-small-en 是纯英文模型：中文原句与英文关键词各有胜负，所以两路向量都跑、交给 RRF 融合
    pool = 20
    if mode == "纯向量":
        candidates = search_vector(question, pool)
    elif mode == "纯 BM25":
        candidates = search_bm25(kw or question, pool)
    else:
        candidates = rrf(question, pool, kw_query=kw or None)
    hits = dedupe(candidates, k)
    elapsed_ms = (time.time() - t0) * 1000
    context = build_context(hits)
    meta_line = (
        f"检索 {len(hits)} 段（候选 {len(candidates)}，无 rerank）· {elapsed_ms:.0f} ms · 模式 {mode}"
        + (f" · 英文关键词：{kw}" if kw else " · 未做查询翻译（向量通道用中文原句，效果会明显变差）")
    )
    if client is None:
        return (
            f"⚠️ 未配置 DEEPSEEK_API_KEY，只展示检索结果，不生成回答。\n\n{meta_line}",
            rows(hits),
            context,
        )
    try:
        r = client.chat.completions.create(
            model=API_MODEL,
            messages=[{"role": "user", "content": SYSTEM_PROMPT.format(context=context, question=question)}],
            temperature=0,
            max_tokens=1200,
        )
        reply = (r.choices[0].message.content or "").strip()
    except Exception as exc:  # noqa: BLE001
        reply = f"生成失败：{exc}\n\n只保留检索结果。"
    return f"{reply}\n\n---\n{meta_line}", rows(hits), context


def _dense_available() -> bool:
    """向量文件在 + 真的能 import sentence-transformers，才算 dense 可用。"""
    if VECS is None:
        return False
    try:
        import sentence_transformers  # noqa: F401

        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] sentence-transformers 不可用（{exc}），本次只用 BM25")
        return False


_env_diag()
_DENSE_ON = _dense_available()
_CHAIN = ("中文问题 → DeepSeek 译成英文关键词 → 英文向量 + BM25 两路各取候选 → RRF 融合 → 去重取前 5 段"
          if _DENSE_ON else
          "中文问题 → DeepSeek 译成英文关键词 → BM25 召回候选 → 去重取前 5 段")
_NO_KEY_NOTE = ("" if os.environ.get("DEEPSEEK_API_KEY", "").strip() else
                "\n> ⚠️ 本页未读到 `DEEPSEEK_API_KEY`：只展示检索结果、不生成回答。请在「设置 → 环境变量」添加后重启空间。")
_MODE_NOTE = ("" if _DENSE_ON else
              "\n> 本次运行未启用向量通道（免费 CPU 不装 torch），只用 BM25 + 查询翻译；主实验的检索指标不适用于本页。")

BANNER = f"""
### LangChain 文档问答 RAG（演示版 · ModelScope 创空间）

手写的 240 题评测集 + 切分×检索消融 + 全量人工幻觉审计，完整实验在
[GitHub](https://github.com/XiMoless/rag-docs-qa)。

**这是演示站点，不是实验配置**：为了在免费 CPU 上跑，向量用 `bge-small-en-v1.5`（{META['dim']} 维，纯英文模型，
所以中文问题会先译成英文关键词），且**不做 cross-encoder 重排**；仓库主实验用 `bge-m3`（1024 维，多语言）
+ `bge-reranker-v2-m3`。**本页不要引用任何 R@5 / 正确率数字**，指标看仓库 `RESULTS.md` 的 E015/E016。

语料：LangChain 官方文档 OSS 部分 {META['count']} 个 chunk，切分方式 {META['chunking']}。

检索链路：{_CHAIN}
→ DeepSeek 只依据片段生成答案（没答案就说没找到）。{_MODE_NOTE}{_NO_KEY_NOTE}
"""

EXAMPLES = [
    ["LangGraph 的 checkpointer 解决了什么问题？"],
    ["durability 设成 exit 是什么意思？"],
    ["怎么在 middleware 里拒绝一个工具调用？"],
    ["interpreter 默认能不能读文件、发网络请求？"],
    ["MCP 工具返回 isError=True 和传输层失败有什么区别？"],
]


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="LangChain 文档问答 RAG（ModelScope）", theme=gr.themes.Soft()) as demo:
        gr.Markdown(BANNER)
        with gr.Row():
            with gr.Column(scale=3):
                q = gr.Textbox(label="问题（中文/英文都行）", lines=2, placeholder="例：checkpointer 和 store 有什么区别？")
                with gr.Row():
                    mode = gr.Radio(["混合检索", "纯向量", "纯 BM25"], value="混合检索", label="检索方式")
                    k = gr.Slider(3, 10, value=5, step=1, label="送进上下文的片段数")
                use_translate = gr.Checkbox(value=True, label="查询翻译（中文问题 → 英文关键词，走 DeepSeek）")
                btn = gr.Button("提问", variant="primary")
                gr.Examples(EXAMPLES, inputs=q)
            with gr.Column(scale=4):
                out = gr.Markdown(label="回答")
        with gr.Row():
            table = gr.Dataframe(headers=["#", "文档标题", "小节", "分数", "URL"], label="召回的片段", wrap=True)
        with gr.Accordion("送给模型的上下文（可核对答案有没有超出片段）", open=False):
            ctx = gr.Textbox(lines=12, show_label=False)
        btn.click(answer, inputs=[q, mode, k, use_translate], outputs=[out, table, ctx])
        q.submit(answer, inputs=[q, mode, k, use_translate], outputs=[out, table, ctx])
    return demo


if __name__ == "__main__":
    build_ui().launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", "7860")))
