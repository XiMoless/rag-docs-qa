"""抓取演示站点真实运行截图，用于拼 README 的 GIF。

用法：
    .\\.venv\\Scripts\\python.exe tmp\\capture_demo.py
"""

from __future__ import annotations

import pathlib
import sys
import time

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:7860"
OUT = pathlib.Path(r"D:\dshwork\rag-docs-qa\docs\figs\demo_frames")
OUT.mkdir(parents=True, exist_ok=True)

QUESTIONS = [
    "checkpointer 和 store 有什么区别？",
    "durability 设成 exit 是什么意思？",
]


def main() -> int:
    frames: list[pathlib.Path] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1180, "height": 1360}, device_scale_factor=1)
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2500)

        def shot(name: str) -> None:
            f = OUT / name
            page.screenshot(path=str(f))
            frames.append(f)
            print("shot", f.name)

        shot("01_home.png")

        box = page.locator("textarea").first
        box.fill(QUESTIONS[0])
        page.wait_for_timeout(600)
        shot("02_typed.png")

        page.get_by_role("button", name="提问").click()
        page.wait_for_timeout(22000)
        shot("03_answer1.png")

        box.fill(QUESTIONS[1])
        page.get_by_role("button", name="提问").click()
        page.wait_for_timeout(22000)
        shot("04_answer2.png")

        browser.close()

    # 拼 GIF：每帧 2.2s，最后一帧停 3s
    from PIL import Image

    imgs = [Image.open(f).convert("RGB").resize((944, 1088)) for f in frames]
    durations = [2200] * (len(imgs) - 1) + [3200]
    gif = OUT.parent / "demo.gif"
    imgs[0].save(gif, save_all=True, append_images=imgs[1:], duration=durations, loop=0, optimize=True)
    print("gif", gif, f"{gif.stat().st_size / 1e6:.2f} MB", "frames", len(imgs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
