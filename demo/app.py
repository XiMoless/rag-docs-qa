"""最小网页 Demo：Gradio 单页面，问题 → 带引用的回答 + 可展开的检索结果。

启动：
    cd D:\\dshwork\\rag-docs-qa
    .\\.venv\\Scripts\\python.exe demo\\app.py
然后浏览器打开终端里打印的 http://127.0.0.1:7860
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import gradio as gr  # noqa: E402

from src.ask import Retriever, SYSTEM_PROMPT, build_context, load_dotenv  # noqa: E402

load_dotenv()

RETRIEVAL_MODES = {"混合 RRF": "rrf", "纯向量": "vec", "纯 BM25": "bm25"}

_retriever: Retriever | None = None
_client = None


def _get() -> tuple[Retriever, object]:
    global _retriever, _client
    if _retriever is None:
        _retriever = Retriever()
    if _client is None:
        from openai import OpenAI

        key = os.environ.get("DEEPSEEK_API_KEY")
        if not key:
            raise gr.Error("缺少 DEEPSEEK_API_KEY：请写入 D:\\dshwork\\rag-docs-qa\\.env")
        _client = OpenAI(api_key=key, base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    return _retriever, _client


def answer(question: str, mode_label: str, k_context: int):
    if not question.strip():
        raise gr.Error("先输入问题")
    r, client = _get()
    mode = RETRIEVAL_MODES.get(mode_label, "rrf")
    if mode == "vec":
        hits = r.vector(question, int(k_context))
    elif mode == "bm25":
        hits = r.keyword(question, int(k_context))
    else:
        hits = r.rrf(question, max(20, int(k_context)), int(k_context))

    context = build_context(hits, r.chunks)
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": SYSTEM_PROMPT.format(context=context, question=question)}],
        temperature=0.0,
        max_tokens=1200,
    )
    text = resp.choices[0].message.content or ""

    src_rows = []
    for n, (i, score) in enumerate(hits, 1):
        c = r.chunks[i]
        src_rows.append([n, round(score, 4), c["chunk_id"], c["heading_path"], c["url"]])

    usage = resp.usage
    meta = f"检索={mode_label} · tokens in {usage.prompt_tokens} / out {usage.completion_tokens}"
    return text, src_rows, meta


with gr.Blocks(title="LangChain 文档 RAG 问答") as demo:
    gr.Markdown(
        "## LangChain 文档问答（RAG · 401 页中文语料索引）\n"
        "答案只来自检索到的原文片段，每条结论后面带 `[编号]`，编号对应下面「检索结果」表。"
    )
    with gr.Row():
        q = gr.Textbox(label="问题", placeholder="例：checkpointer 和 store 分别存什么？", scale=4)
        mode = gr.Dropdown(list(RETRIEVAL_MODES), value="混合 RRF", label="检索方式", scale=1)
        k = gr.Slider(1, 10, value=5, step=1, label="送入上下文的片段数", scale=1)
    btn = gr.Button("提问", variant="primary")
    out = gr.Markdown(label="回答")
    meta = gr.Markdown()
    with gr.Accordion("检索结果（chunk 级可追溯）", open=False):
        table = gr.Dataframe(headers=["#", "score", "chunk_id", "标题路径", "url"], wrap=True)

    btn.click(answer, inputs=[q, mode, k], outputs=[out, table, meta])
    q.submit(answer, inputs=[q, mode, k], outputs=[out, table, meta])


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)
