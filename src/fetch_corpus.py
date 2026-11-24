"""抓取 LangChain OSS 文档正文，落到 data/raw/*.md（带 front-matter）。

用法：
    .venv/Scripts/python.exe -m src.fetch_corpus                # 全量
    .venv/Scripts/python.exe -m src.fetch_corpus --limit 5      # 只抓 5 篇试跑
    .venv/Scripts/python.exe -m src.fetch_corpus --force        # 重抓已存在的

产出：
    data/raw/<slug>.md          每页一个文件，正文转 Markdown（保留标题层级与代码块）
    data/raw/manifest.jsonl     每行一条：url / slug / title / chars / sha256 / fetched_at
    data/sitemap_langchain.xml  sitemap 原件（可追溯当天抓的是哪个版本）
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
SITEMAP_CACHE = ROOT / "data" / "sitemap_langchain.xml"
MANIFEST = RAW_DIR / "manifest.jsonl"

SITEMAP_URL = "https://docs.langchain.com/sitemap.xml"
INCLUDE_PREFIX = "https://docs.langchain.com/oss/"
MIN_CHARS = 200
DELAY_SEC = 0.25
WORKERS = 4
UA = "Mozilla/5.0 (research crawler for offline QA evaluation)"

SKIP_TAGS = {"nav", "footer", "aside", "script", "style", "svg", "form", "button"}

# 页面里的交互噪音：复制按钮、面包屑、目录锚点条、工具栏
NOISE_SELECTORS = (
    "[class*=copy]",
    "[aria-label*=opy]",
    "button",
    "nav",
    "footer",
    "aside",
    "script",
    "style",
    "svg",
    "form",
    "[class*=breadcrumb]",
    "[class*=toc]",
    "[role=toolbar]",
    "[data-floating-buttons]",
    "[aria-hidden=true]",
)


@dataclass
class Page:
    url: str
    slug: str
    title: str
    chars: int
    sha256: str
    fetched_at: str
    depth: int  # 路径层级，用于过滤索引页
    err: str = ""


def slugify(url: str) -> str:
    path = url.replace("https://docs.langchain.com/", "").rstrip("/")
    return re.sub(r"[^a-zA-Z0-9._-]+", "__", path)


def load_sitemap(session: requests.Session, force: bool = False) -> list[str]:
    if force or not SITEMAP_CACHE.exists():
        r = session.get(SITEMAP_URL, timeout=30)
        r.raise_for_status()
        SITEMAP_CACHE.parent.mkdir(parents=True, exist_ok=True)
        SITEMAP_CACHE.write_bytes(r.content)
    text = SITEMAP_CACHE.read_text(encoding="utf-8")
    urls = re.findall(r"<loc>([^<]+)</loc>", text)
    return [u for u in urls if u.startswith(INCLUDE_PREFIX)]


def _inline_text(node: Tag) -> str:
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True))


def _table_to_md(table: Tag) -> str:
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = [_inline_text(c).replace("|", "\\|") for c in tr.find_all(["th", "td"])]
        if cells:
            rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    head = "| " + " | ".join(rows[0]) + " |"
    sep = "| " + " | ".join(["---"] * width) + " |"
    body = ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join([head, sep, *body])


def html_to_markdown(root: Tag) -> str:
    """把文档正文转成 Markdown：保留 h1-h4、段落、列表、代码块、表格；丢弃导航/侧栏。"""
    out: list[str] = []

    def emit(text: str) -> None:
        text = text.rstrip()
        if text:
            out.append(text)

    def walk(node: Tag) -> None:
        for child in node.children:
            if isinstance(child, NavigableString):
                continue
            if not isinstance(child, Tag):
                continue
            name = child.name.lower()
            if name in SKIP_TAGS:
                continue
            if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                level = int(name[1])
                emit("#" * level + " " + _inline_text(child))
            elif name == "p":
                emit(_inline_text(child))
            elif name == "pre":
                code = child.get_text()
                lang = ""
                code_tag = child.find("code")
                if code_tag:
                    classes = " ".join(code_tag.get("class") or [])
                    m = re.search(r"language-([\w+-]+)", classes)
                    lang = m.group(1) if m else ""
                emit(f"```{lang}\n{code.rstrip()}\n```")
            elif name in {"ul", "ol"}:
                for i, li in enumerate(child.find_all("li", recursive=False), 1):
                    mark = f"{i}." if name == "ol" else "-"
                    emit(f"{mark} {_inline_text(li)}")
            elif name == "table":
                emit(_table_to_md(child))
            elif name == "blockquote":
                emit("> " + _inline_text(child))
            elif name in {"div", "section", "article", "main", "span", "details"}:
                walk(child)
            else:
                text = _inline_text(child)
                if len(text) > 40:
                    emit(text)

    walk(root)
    # 合并多余空行
    md = "\n\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", md).strip()


def strip_noise(soup: BeautifulSoup) -> None:
    """删掉交互控件与导航，避免正文里混进 "Copy page" 之类的噪音。"""
    for sel in NOISE_SELECTORS:
        for el in soup.select(sel):
            el.decompose()


def pick_main(soup: BeautifulSoup) -> Tag | None:
    for sel in ("article", "div.theme-doc-markdown", "div.markdown", "main"):
        node = soup.select_one(sel)
        if node and len(node.get_text(strip=True)) > MIN_CHARS:
            return node
    return soup.body


def fetch_one(session: requests.Session, url: str) -> tuple[Page, str]:
    slug = slugify(url)
    try:
        r = session.get(url, timeout=45)
    except requests.RequestException as exc:
        return Page(url, slug, "", 0, "", _now(), 0, err=f"{type(exc).__name__}: {exc}"), ""
    if r.status_code != 200:
        return Page(url, slug, "", 0, "", _now(), 0, err=f"HTTP {r.status_code}"), ""

    soup = BeautifulSoup(r.content.decode("utf-8", errors="replace"), "lxml")
    strip_noise(soup)
    main = pick_main(soup)
    if main is None:
        return Page(url, slug, "", 0, "", _now(), 0, err="no main content"), ""

    title_tag = soup.find("h1") or soup.title
    title = _inline_text(title_tag) if title_tag else slug
    body = html_to_markdown(main)
    depth = url.replace("https://docs.langchain.com/", "").strip("/").count("/")

    front = {
        "url": url,
        "title": title,
        "fetched_at": _now(),
        "depth": depth,
        "chars": len(body),
    }
    doc = "---\n" + json.dumps(front, ensure_ascii=False) + "\n---\n\n" + body + "\n"
    sha = hashlib.sha256(doc.encode("utf-8")).hexdigest()[:16]
    page = Page(url, slug, title, len(body), sha, front["fetched_at"], depth)
    return page, doc


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true", help="重抓已存在的文件")
    ap.add_argument("--min-chars", type=int, default=MIN_CHARS)
    args = ap.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = UA

    urls = load_sitemap(session, force=False)
    print(f"sitemap: {len(urls)} URLs under {INCLUDE_PREFIX}")
    if args.limit:
        urls = urls[: args.limit]

    todo = []
    for u in urls:
        p = RAW_DIR / f"{slugify(u)}.md"
        if args.force or not p.exists():
            todo.append(u)
    print(f"to fetch: {len(todo)} (skip existing: {len(urls) - len(todo)})")

    pages: list[Page] = []
    ok = fail = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {}
        for u in todo:
            futures[ex.submit(fetch_one, session, u)] = u
            time.sleep(DELAY_SEC / WORKERS)
        for i, fut in enumerate(as_completed(futures), 1):
            page, doc = fut.result()
            if page.err or page.chars < args.min_chars:
                fail += 1
                page.err = page.err or f"too short ({page.chars} chars)"
            else:
                (RAW_DIR / f"{page.slug}.md").write_text(doc, encoding="utf-8")
                ok += 1
            pages.append(page)
            if i % 25 == 0 or i == len(todo):
                print(f"  [{i}/{len(todo)}] ok={ok} fail={fail} {time.time() - t0:.0f}s")

    # 重写 manifest（全量，按 slug 去重）
    all_pages: dict[str, Page] = {}
    if MANIFEST.exists():
        for line in MANIFEST.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(line)
                all_pages[d["slug"]] = Page(**d)
            except Exception:
                pass
    for p in pages:
        if not (p.err and p.chars == 0):
            all_pages[p.slug] = p
    with MANIFEST.open("w", encoding="utf-8") as f:
        for p in sorted(all_pages.values(), key=lambda x: x.url):
            f.write(json.dumps(asdict(p), ensure_ascii=False) + "\n")

    good = [p for p in all_pages.values() if not p.err]
    total_chars = sum(p.chars for p in good)
    print(f"\ndone: {ok} saved / {fail} failed in {time.time() - t0:.0f}s")
    print(f"corpus: {len(good)} pages, {total_chars:,} chars, avg {total_chars // max(len(good), 1):,} chars/page")
    by_depth: dict[int, int] = {}
    for p in good:
        by_depth[p.depth] = by_depth.get(p.depth, 0) + 1
    print("by depth:", dict(sorted(by_depth.items())))

    failed = [p for p in pages if p.err]
    if failed:
        print("\nfailures:")
        for p in failed[:15]:
            print(f"  {p.url}  -> {p.err}")
    return 0 if not fail else 0


if __name__ == "__main__":
    sys.exit(main())
