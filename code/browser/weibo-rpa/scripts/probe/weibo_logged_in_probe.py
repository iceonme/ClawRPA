#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "weibo-logged-in-probe" / datetime.now().strftime("%Y%m%d_%H%M%S")
RUN_ROOT.mkdir(parents=True, exist_ok=True)

QUERY = "时代少年团 广州"
SEARCH_URL = f"https://s.weibo.com/weibo?q={quote(QUERY)}"


COMMENT_KEYWORDS = ["评论", "全部评论", "条评论", "回复", "展开", "查看更多", "留言", "私信", "消息"]
POST_LINK_HINTS = ["/detail/", "m.weibo.cn/detail/", "weibo.com/"]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def save_text(name: str, text: str) -> str:
    path = RUN_ROOT / name
    path.write_text(text, encoding="utf-8")
    return str(path)


def screenshot(page, name: str) -> str:
    path = RUN_ROOT / name
    page.screenshot(path=str(path), full_page=True)
    return str(path)


def collect_controls(page, limit: int = 150) -> list[dict]:
    js = """
() => Array.from(document.querySelectorAll('a, button, [role="button"]')).map((el, i) => ({
  idx: i,
  tag: el.tagName,
  text: (el.innerText || el.textContent || '').trim(),
  aria: el.getAttribute('aria-label') || '',
  title: el.getAttribute('title') || '',
  href: el.href || '',
  cls: String(el.className || ''),
  visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
}))
"""
    raw = page.evaluate(js)
    picked = []
    for item in raw:
        text = normalize_text(" ".join([item.get("text", ""), item.get("aria", ""), item.get("title", "")]))
        href = item.get("href", "")
        if any(k in text for k in COMMENT_KEYWORDS) or any(h in href for h in POST_LINK_HINTS):
            item["norm"] = text
            picked.append(item)
    return picked[:limit]


def collect_post_candidates(page, limit: int = 20) -> list[dict]:
    js = """
() => Array.from(document.querySelectorAll('a[href]')).map((a, i) => ({
  idx: i,
  text: (a.innerText || a.textContent || '').trim(),
  href: a.href || '',
  title: a.getAttribute('title') || '',
  visible: !!(a.offsetWidth || a.offsetHeight || a.getClientRects().length)
}))
"""
    raw = page.evaluate(js)
    out = []
    seen = set()
    for item in raw:
        href = item.get("href", "")
        if not href or href in seen:
            continue
        if any(h in href for h in POST_LINK_HINTS) and not href.startswith("javascript:"):
            seen.add(href)
            item["norm"] = normalize_text(" ".join([item.get("text", ""), item.get("title", "")]))
            out.append(item)
        if len(out) >= limit:
            break
    return out


def try_open_first_post(page) -> dict:
    candidates = collect_post_candidates(page, limit=30)
    result = {"opened": False, "candidates": candidates}

    for candidate in candidates:
        href = candidate.get("href", "")
        if href.startswith("https://passport.weibo.com"):
            continue
        try:
            page.goto(href, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2500)
            result.update({"opened": True, "target_href": href, "target_text": candidate.get("norm", "")})
            return result
        except Exception as exc:
            candidate["open_error"] = str(exc)
    return result


def detect_login(page) -> bool:
    text = normalize_text(page.inner_text("body")[:3000])
    return ("登录" in text and "注册" in text) or ("扫码登录" in text)


def main() -> int:
    port = 9222
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    endpoint = f"http://127.0.0.1:{port}"

    result: dict = {
        "ok": False,
        "endpoint": endpoint,
        "query": QUERY,
        "search_url": SEARCH_URL,
        "run_root": str(RUN_ROOT),
        "steps": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(endpoint)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()

        try:
            page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(4000)
            search_text = page.inner_text("body")[:15000]
            search_logged_in = not detect_login(page)
            search_controls = collect_controls(page)
            post_candidates = collect_post_candidates(page)
            result["steps"].append({
                "step": "search",
                "url": page.url,
                "title": page.title(),
                "logged_in_result": search_logged_in,
                "text_path": save_text("search.txt", search_text),
                "html_path": save_text("search.html", page.content()),
                "screenshot_path": screenshot(page, "search.png"),
                "controls": search_controls,
                "post_candidates": post_candidates,
            })

            open_result = try_open_first_post(page)
            detail_text = page.inner_text("body")[:15000]
            detail_controls = collect_controls(page)
            result["steps"].append({
                "step": "detail",
                "url": page.url,
                "title": page.title(),
                "opened": open_result.get("opened", False),
                "target_href": open_result.get("target_href", ""),
                "target_text": open_result.get("target_text", ""),
                "text_path": save_text("detail.txt", detail_text),
                "html_path": save_text("detail.html", page.content()),
                "screenshot_path": screenshot(page, "detail.png"),
                "controls": detail_controls,
                "post_candidates": open_result.get("candidates", []),
            })

            result["ok"] = True
        except PlaywrightTimeoutError as exc:
            result["error"] = {"type": "timeout", "message": str(exc)}
        except Exception as exc:
            result["error"] = {"type": exc.__class__.__name__, "message": str(exc)}
        finally:
            try:
                page.close()
            except Exception:
                pass
            browser.close()

    out = RUN_ROOT / "result.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": "error" not in result, "result_path": str(out), "run_root": str(RUN_ROOT)}, ensure_ascii=False))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
