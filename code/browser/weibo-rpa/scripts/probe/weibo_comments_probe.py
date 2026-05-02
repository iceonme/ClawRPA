#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "weibo-comments-probe" / datetime.now().strftime("%Y%m%d_%H%M%S")
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


def save(name: str, content: str) -> str:
    path = RUN_ROOT / name
    path.write_text(content, encoding="utf-8")
    return str(path)


def pick_detail_url(page) -> str:
    cards = page.locator('div[action-type="feed_list_item"]')
    card_count = cards.count()
    for i in range(min(card_count, 8)):
        card = cards.nth(i)
        try:
            href = norm_href(card.locator("div.from a").first.get_attribute("href") or "")
        except Exception:
            href = ""
        if href and "/" in href.replace("https://weibo.com/", ""):
            return href
    return ""


def extract_comments_via_dom(page) -> list[dict]:
    js = r'''
() => {
  const results = [];
  const seen = new Set();
  const walkers = Array.from(document.querySelectorAll('a, div, span, li'));
  for (const el of walkers) {
    const text = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
    if (!text) continue;
    if (!(/^\d{2}-\d{1,2}-\d{1,2}/.test(text) || text.includes('来自'))) continue;
    let container = el;
    for (let i = 0; i < 5 && container; i++) container = container.parentElement;
    if (!container) continue;
    const blockText = (container.innerText || '').replace(/\s+/g, ' ').trim();
    if (!blockText || blockText.length < 5) continue;
    if (blockText.includes('微博热搜') || blockText.includes('帮助中心')) continue;
    const lines = blockText.split(/\n+/).map(s => s.trim()).filter(Boolean);
    const maybeName = lines[0] || '';
    const maybeMeta = lines.find(x => /^\d{2}-\d{1,2}-\d{1,2}/.test(x)) || text;
    const maybeContent = lines.slice(1).find(x => !/^\d{2}-\d{1,2}-\d{1,2}/.test(x) && !/^共\d+条回复/.test(x) && !/^关注$/.test(x) && !/^粉丝$/.test(x));
    const profileLink = Array.from(container.querySelectorAll('a[href]')).map(a => a.href).find(h => /weibo\.com\/(u\/)?\d+/.test(h) && !/\/Q[A-Za-z0-9]+/.test(h)) || '';
    const key = [maybeName, maybeMeta, maybeContent].join('|');
    if (!maybeContent || seen.has(key)) continue;
    seen.add(key);
    results.push({
      commenter_nickname: maybeName,
      meta: maybeMeta,
      comment_text: maybeContent,
      commenter_profile_url: profileLink
    });
    if (results.length >= 30) break;
  }
  return results;
}
'''
    return page.evaluate(js)


def main() -> int:
    port = 9222
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    endpoint = f"http://127.0.0.1:{port}"
    result: dict = {"ok": False, "endpoint": endpoint, "query": QUERY, "search_url": SEARCH_URL, "run_root": str(RUN_ROOT)}

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(endpoint)
        context = browser.contexts[0]
        search = context.new_page()
        try:
            print("step=goto_search", flush=True)
            search.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=30000)
            search.wait_for_timeout(2500)
            detail_url = pick_detail_url(search)
            print(f"step=detail_url url={detail_url}", flush=True)
            if not detail_url:
                raise RuntimeError("未能从搜索结果中提取详情页链接")

            detail = context.new_page()
            try:
                print("step=goto_detail", flush=True)
                detail.goto(detail_url, wait_until="domcontentloaded", timeout=30000)
                detail.wait_for_timeout(3000)
                body_text = detail.inner_text("body")[:20000]
                comments = extract_comments_via_dom(detail)
                result.update({
                    "ok": True,
                    "detail_url": detail_url,
                    "detail_title": detail.title(),
                    "detail_text_path": save("detail.txt", body_text),
                    "detail_html_path": save("detail.html", detail.content()),
                    "comments": comments,
                    "comment_count": len(comments),
                })
                save("comments.json", json.dumps(comments, ensure_ascii=False, indent=2))
            finally:
                detail.close()
        finally:
            search.close()
            browser.close()

    out = RUN_ROOT / "result.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": result.get("ok", False), "comment_count": result.get("comment_count", 0), "result_path": str(out)}, ensure_ascii=False), flush=True)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
