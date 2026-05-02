#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "manual-weibo-ui-probe" / datetime.now().strftime("%Y%m%d_%H%M%S")
RUN_ROOT.mkdir(parents=True, exist_ok=True)

QUERY = "时代少年团 广州"
SEARCH_URL = f"https://s.weibo.com/weibo?q={quote(QUERY)}"
PROFILE_URL = "https://weibo.com/u/6473606786?refer_flag=1001030106_"
CHAT_URL = "https://api.weibo.com/chat/#/chat?to_uid=6473606786&source_from="


def save_text(name: str, text: str) -> str:
    path = RUN_ROOT / name
    path.write_text(text, encoding="utf-8")
    return str(path)


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text


def pick_candidates(page) -> list[dict]:
    js = """
() => {
  const nodes = Array.from(document.querySelectorAll('a, button, [role="button"]'));
  return nodes.slice(0, 400).map((el) => ({
    tag: el.tagName,
    text: (el.innerText || el.textContent || '').trim(),
    aria: el.getAttribute('aria-label') || '',
    title: el.getAttribute('title') || '',
    href: el.href || '',
    cls: el.className || ''
  }));
}
"""
    raw = page.evaluate(js)
    interesting = []
    keywords = ["评论", "回复", "全部", "展开", "聊天", "私信", "发消息", "主页"]
    for item in raw:
        text = normalize_text(" ".join([item.get("text", ""), item.get("aria", ""), item.get("title", "")]))
        if not text and not item.get("href"):
            continue
        if any(k in text for k in keywords) or any(k in item.get("href", "") for k in ["comment", "chat", "/u/"]):
            interesting.append(item)
    return interesting[:80]


def main() -> int:
    result: dict = {
        "query": QUERY,
        "search_url": SEARCH_URL,
        "profile_url": PROFILE_URL,
        "chat_url": CHAT_URL,
        "run_root": str(RUN_ROOT),
        "steps": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1200})
        page = context.new_page()

        def record_step(name: str, url: str, title: str, ok: bool, **extra):
            item = {"step": name, "url": url, "title": title, "ok": ok}
            item.update(extra)
            result["steps"].append(item)

        try:
            page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(3000)
            search_html = save_text("search.html", page.content())
            search_txt = save_text("search.txt", page.inner_text("body")[:12000])
            search_shot = str(RUN_ROOT / "search.png")
            page.screenshot(path=search_shot, full_page=True)
            search_candidates = pick_candidates(page)
            record_step(
                "search",
                page.url,
                page.title(),
                True,
                html_path=search_html,
                text_path=search_txt,
                screenshot_path=search_shot,
                candidate_controls=search_candidates,
            )

            try:
                page.locator('a[href*="/detail/"]').first.click(timeout=5000)
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(3000)
                detail_source = "search_result_detail_link"
            except Exception:
                try:
                    page.locator('a[href*="weibo.com/"]').filter(has_text="全文").first.click(timeout=5000)
                    page.wait_for_timeout(3000)
                    detail_source = "full_text_link"
                except Exception:
                    detail_source = "not_opened"

            detail_html = save_text("detail.html", page.content())
            detail_txt = save_text("detail.txt", page.inner_text("body")[:12000])
            detail_shot = str(RUN_ROOT / "detail.png")
            page.screenshot(path=detail_shot, full_page=True)
            detail_candidates = pick_candidates(page)
            record_step(
                "detail",
                page.url,
                page.title(),
                detail_source != "not_opened",
                open_source=detail_source,
                html_path=detail_html,
                text_path=detail_txt,
                screenshot_path=detail_shot,
                candidate_controls=detail_candidates,
            )

            page.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(2500)
            profile_html = save_text("profile.html", page.content())
            profile_txt = save_text("profile.txt", page.inner_text("body")[:12000])
            profile_shot = str(RUN_ROOT / "profile.png")
            page.screenshot(path=profile_shot, full_page=True)
            record_step(
                "profile",
                page.url,
                page.title(),
                True,
                html_path=profile_html,
                text_path=profile_txt,
                screenshot_path=profile_shot,
                candidate_controls=pick_candidates(page),
            )

            page.goto(CHAT_URL, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(2500)
            chat_html = save_text("chat.html", page.content())
            chat_txt = save_text("chat.txt", page.inner_text("body")[:12000])
            chat_shot = str(RUN_ROOT / "chat.png")
            page.screenshot(path=chat_shot, full_page=True)
            record_step(
                "chat",
                page.url,
                page.title(),
                True,
                html_path=chat_html,
                text_path=chat_txt,
                screenshot_path=chat_shot,
                candidate_controls=pick_candidates(page),
            )

        except PlaywrightTimeoutError as exc:
            result["error"] = {"type": "timeout", "message": str(exc)}
        except Exception as exc:
            result["error"] = {"type": exc.__class__.__name__, "message": str(exc)}
        finally:
            browser.close()

    out = RUN_ROOT / "result.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": "error" not in result, "result_path": str(out), "run_root": str(RUN_ROOT)}, ensure_ascii=False))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
