"""把 deploy/ms-studio 发到 ModelScope 创空间（Studio）。

前置：
1. 在 https://modelscope.cn/my/myaccesstoken 建一个 Access Token
2. 在 https://modelscope.cn/studios 新建一个创空间，SDK 选 Gradio，记下 `<用户名>/<空间名>`
3. 本机设置环境变量（不要贴进聊天）：
   PowerShell:  $env:MODELSCOPE_TOKEN = "ms-xxxx"
               $env:MS_STUDIO_ID = "<用户名>/rag-docs-qa"

用法：
    .\\.venv\\Scripts\\python.exe -m deploy.push_ms_studio
    .\\.venv\\Scripts\\python.exe -m deploy.push_ms_studio --dry-run   # 只准备目录，不 push
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "deploy" / "ms-studio"
ART_SRC = ROOT / "deploy" / "hf-space" / "artifacts"
WORK = ROOT / "tmp" / "ms-studio"

REQUIRED = ["app.py", "requirements.txt", "README.md"]


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def prepare_files() -> None:
    """把应用文件 + 向量产物拼到 tmp/ms-studio。"""
    for name in REQUIRED:
        if not (SRC / name).exists():
            raise SystemExit(f"缺少文件：{SRC / name}")
    art = SRC / "artifacts"
    if not art.exists() or not (art / "vectors.npy").exists():
        if not ART_SRC.exists():
            raise SystemExit(f"缺少向量产物：{ART_SRC}（先跑 deploy/build_demo_space.py）")
        print(f"复制向量产物 {ART_SRC} -> {art}")
        art.mkdir(parents=True, exist_ok=True)
        for p in ART_SRC.iterdir():
            if p.is_file():
                shutil.copy2(p, art / p.name)
    size = sum(p.stat().st_size for p in art.iterdir() if p.is_file()) / 1e6
    print(f"artifacts: {size:.1f} MB")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只准备文件，不 clone/push")
    ap.add_argument('--studio-id', default=os.environ.get('MS_STUDIO_ID', ''))
    ap.add_argument('--studio-url', default='', help='创空间弹窗里复制的整条 clone 地址（已含 token）')
    args = ap.parse_args()

    prepare_files()
    if args.dry_run:
        print("dry-run：文件已就绪，未推送。")
        print(f"可用于手动上传的目录：{SRC}")
        return 0

    token = os.environ.get("MODELSCOPE_TOKEN", "").strip()
    studio_url = (os.environ.get("MS_STUDIO_URL", "").strip() or args.studio_url.strip())
    if studio_url:
        # 直接从创空间弹窗里复制的整条 clone 地址（已内嵌 token），不需要再单独给 token
        remote = studio_url
        if not remote.endswith(".git"):
            print("MS_STUDIO_URL 应以 .git 结尾，形如 https://oauth2:ms-xxx@www.modelscope.cn/studios/<用户名>/<空间名>.git")
            return 10
        safe_remote = remote.split("@")[-1]
    else:
        if not token:
            print("缺少环境变量 MODELSCOPE_TOKEN（或直接给 MS_STUDIO_URL）。见脚本顶部注释。")
            return 10
        if not args.studio_id or "/" not in args.studio_id:
            print("缺少 MS_STUDIO_ID，形如 <用户名>/rag-docs-qa")
            return 10
        remote = f"https://oauth2:{token}@www.modelscope.cn/studios/{args.studio_id}.git"
        safe_remote = f"https://www.modelscope.cn/studios/{args.studio_id}.git"

    if WORK.exists():
        print(f"复用已存在的克隆目录：{WORK}")
        code, out = run(["git", "remote", "set-url", "origin", remote], cwd=WORK)
    else:
        print(f"克隆创空间仓库 {safe_remote}")
        WORK.parent.mkdir(parents=True, exist_ok=True)
        code, out = run(["git", "clone", remote, str(WORK)])
        if code != 0:
            print(f"克隆失败（检查 token 与空间名）：\n{out}")
            return 20

    # 拷贝文件（保留创空间仓库自带的 .git 与平台配置）
    for name in REQUIRED:
        shutil.copy2(SRC / name, WORK / name)
    art_dst = WORK / "artifacts"
    if art_dst.exists():
        shutil.rmtree(art_dst)
    shutil.copytree(SRC / "artifacts", art_dst)

    # 创空间仓库自带 .gitattributes，会把 *.npy / *.bin 等交给 git-lfs 处理。
    # 缺 git-lfs 时 add 会报 `git-lfs filter-process: command not found`，这里先检查一次。
    code, _ = run(["git", "lfs", "version"])
    if code != 0:
        print("缺少 git-lfs：artifacts 里有 .npy，需要它才能提交。")
        print("安装：https://git-lfs.com/ ，或把 git-lfs.exe 放进 PATH 后重跑。")
        return 40
    run(["git", "lfs", "install", "--local"], cwd=WORK)
    run(["git", "config", "user.name", "Huang Zhenfeng"], cwd=WORK)
    run(["git", "config", "user.email", "167899533+XiMoless@users.noreply.github.com"], cwd=WORK)

    code, out = run(["git", "add", "-A"], cwd=WORK)
    code, out = run(["git", "commit", "-m", "demo: LangChain docs RAG (bge-small-en + BM25, CPU)"], cwd=WORK)
    print(out.strip()[:400])
    code, out = run(["git", "push", "origin", "HEAD"], cwd=WORK)
    print(out.strip()[-1500:])
    if code != 0:
        print("push 失败；若提示鉴权错误，重新确认 MODELSCOPE_TOKEN 是否有效。")
        return 30

    print(f"完成：https://www.modelscope.cn/studios/{args.studio_id}")
    print("去创空间「设置 → 环境变量」加 DEEPSEEK_API_KEY（本脚本不代填 ModelScope 的密钥）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
