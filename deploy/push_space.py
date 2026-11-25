"""把 deploy/hf-space 发布成 Hugging Face Space（含设置 DEEPSEEK_API_KEY secret）。

前置：
1. 在 https://huggingface.co/settings/tokens 建一个 **write** 权限的 token
2. 本机设置环境变量（不要贴进聊天）：
   PowerShell:  $env:HF_TOKEN = "hf_xxx"
               $env:HF_SPACE_ID = "<你的用户名>/rag-docs-qa"
3. .env 里有 DEEPSEEK_API_KEY（脚本会把它写成 Space secret，不打印）

用法：
    .\\.venv\\Scripts\\python.exe -m deploy.push_space
    .\\.venv\\Scripts\\python.exe -m deploy.push_space --no-secret   # 先不设 secret
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPACE_DIR = ROOT / "deploy" / "hf-space"


def load_env_key() -> str:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return ""
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("DEEPSEEK_API_KEY="):
            return line.split("=", 1)[1].strip()
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-secret", action="store_true", help="不设置 DEEPSEEK_API_KEY secret")
    ap.add_argument("--space-id", default=os.environ.get("HF_SPACE_ID", ""), help="<用户名>/<space 名>")
    args = ap.parse_args()

    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        print("缺少环境变量 HF_TOKEN（write 权限）。设置方法见脚本顶部注释。")
        return 10
    if not args.space_id or "/" not in args.space_id:
        print("缺少 HF_SPACE_ID，形如 <用户名>/rag-docs-qa")
        return 10

    from huggingface_hub import HfApi, create_repo

    api = HfApi(token=token)
    print(f"创建/复用 Space: {args.space_id} (gradio, public)")
    url = create_repo(
        repo_id=args.space_id,
        repo_type="space",
        space_sdk="gradio",
        private=False,
        exist_ok=True,
        token=token,
    )
    print("space:", url)

    size_mb = sum(p.stat().st_size for p in SPACE_DIR.rglob("*") if p.is_file()) / 1e6
    print(f"上传 {SPACE_DIR}（{size_mb:.1f} MB）...")
    api.upload_folder(
        folder_path=str(SPACE_DIR),
        repo_id=args.space_id,
        repo_type="space",
        commit_message="demo: LangChain docs RAG (bge-small + BM25 + rerank, CPU)",
        ignore_patterns=["__pycache__/*", "*.pyc", ".git/*"],
    )
    print("上传完成")

    if not args.no_secret:
        key = load_env_key()
        if key:
            api.add_space_secret(repo_id=args.space_id, key="DEEPSEEK_API_KEY", value=key)
            print("已写入 Space secret: DEEPSEEK_API_KEY（值不打印）")
        else:
            print("本地 .env 里没有 DEEPSEEK_API_KEY，跳过 secret；请去 Space 设置页手动加。")

    print(f"页面地址：https://huggingface.co/spaces/{args.space_id}")
    print("首次构建需要几分钟，构建日志在 Space 的 Logs 标签。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
