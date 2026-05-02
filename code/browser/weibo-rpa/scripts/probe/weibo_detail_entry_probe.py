#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "weibo-detail-entry-probe" / datetime.now().strftime("%Y%m%d_%H%M%S")
RUN_ROOT.mkdir(parents=True, exist_ok=True)

QUERY = "时代少年团 广州"
SEARCH_URL = f"https://s.weibo.com/weibo?q={quote(QUERY)}"


def norm_href(href: str) -> str:
    href = (href or "").strip()
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return "https://s.weibo.com" + href
    return href


def save(path: str, content: str) -> str:
    p = RUN_ROOT / path
    p.write_text(content, encoding="utf-8")
    return str(p)


def log(msg: str) -> None:
    print(msg, flush=True)


def main() -> int:
    port = 9222
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    endpoint = f"http://127.0.0.1:{port}"
    result: dict = {"ok": False, "endpoint": endpoint, "query": QUERY, "search_url": SEARCH_URL, "run_root": str(RUN_ROOT)}

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(endpoint)
        context = browser.contexts[0]
        page = context.new_page()
        try:
            log("step=goto_search")
            page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2500)

            cards = page.locator('div[action-type="feed_list_item"]')
            card_count = cards.count()
            log(f"step=cards card_count={card_count}")
            extracted = []
            visited = []

            for i in range(min(card_count, 4)):
                log(f"step=card index={i}")
                card = cards.nth(i)
                mid = card.get_attribute("mid") or ""
                author = ""
                try:
                    author = (card.locator("a.name").first.inner_text(timeout=1200) or "").strip()
                except Exception:
                    pass
                time_href = ""
                try:
                    time_href = norm_href(card.locator("div.from a").first.get_attribute("href") or "")
                except Exception:
                    pass

                comment_clicked = False
                repeat_links = []
                try:
                    comment_btn = card.locator('[action-type="feed_list_comment"]').first
                    if comment_btn.count() > 0:
                        comment_btn.click(timeout=2000)
                        page.wait_for_timeout(1800)
                        comment_clicked = True
                        repeat = card.locator(".feed_list_repeat")
                        if repeat.count() > 0:
                            links = repeat.first.locator(".card-more-a a")
                            link_count = links.count()
                            for j in range(min(link_count, 3)):
                                href = norm_href(links.nth(j).get_attribute("href") or "")
                                text = ""
                                try:
                                    text = (links.nth(j).inner_text(timeout=600) or "").strip()
                                except Exception:
                                    pass
                                if href:
                                    repeat_links.append({"href": href, "text": text})
                except Exception as exc:
                    repeat_links.append({"error": str(exc)})

                extracted.append({
                    "index": i,
                    "mid": mid,
                    "author": author,
                    "time_href": time_href,
                    "comment_clicked": comment_clicked,
                    "repeat_links": repeat_links,
                })

                target = time_href or next((x["href"] for x in repeat_links if isinstance(x, dict) and x.get("href")), "")
                if target and len(visited) < 1:
                    log(f"step=visit_detail target={target}")
                    detail = context.new_page()
                    try:
                        detail.goto(target, wait_until="domcontentloaded", timeout=30000)
                        detail.wait_for_timeout(2500)
                        visited.append({
                            "target": target,
                            "final_url": detail.url,
                            "title": detail.title(),
                            "text_path": save("detail_1.txt", detail.inner_text("body")[:12000]),
                            "html_path": save("detail_1.html", detail.content()),
                        })
                    finally:
                        detail.close()

            result.update({
                "ok": True,
                "card_count": card_count,
                "search_html_path": save("search.html", page.content()),
                "search_text_path": save("search.txt", page.inner_text("body")[:12000]),
                "extracted": extracted,
                "visited": visited,
            })
        finally:
            page.close()
            browser.close()

    out = RUN_ROOT / "result.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": result.get("ok", False), "result_path": str(out), "run_root": str(RUN_ROOT)}, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
