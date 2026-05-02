#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_EVENT_QUERY = "时代少年团 广州"
DEFAULT_DEMAND_PATTERNS = [
    r"求票", r"收票", r"蹲票", r"还有票吗", r"求一张", r"求两张", r"连坐",
    r"没抢到", r"抢不到", r"求收", r"求张", r"求.*门票", r"收.*门票",
    r"让我进门", r"谁出", r"有没有人转", r"有票吗", r"想去.*没票", r"回流",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect weibo test leads from post detail pages.")
    parser.add_argument("--port", type=int, default=9222, help="CDP port")
    parser.add_argument("--event-query", default=DEFAULT_EVENT_QUERY, help="Event query, e.g. 郑州 汪苏泷")
    parser.add_argument("--max-leads", type=int, default=100, help="Target lead count")
    parser.add_argument("--max-pages-per-keyword", type=int, default=10, help="Max search result pages for each keyword")
    parser.add_argument("--max-posts-per-page", type=int, default=5, help="Max high-priority posts to open on each search page")
    parser.add_argument("--max-comments-per-post", type=int, default=200, help="Max comments to parse from each detail page")
    parser.add_argument("--comment-recent-days", type=int, default=5, help="Only keep / keep scrolling for comments within recent N days")
    parser.add_argument("--max-comment-scroll-rounds", type=int, default=30, help="Max scroll rounds while deep-scanning comments")
    parser.add_argument("--max-comment-pages", type=int, default=20, help="Max comment pagination turns per post when available")
    parser.add_argument("--run-root", default="", help="Optional explicit run output directory")
    parser.add_argument("--task-id", default="", help="Optional task id when the collector is called by task framework")
    parser.add_argument("--search-since", default="", help="Optional lower bound time for search results (reserved for task framework)")
    parser.add_argument("--comment-since", default="", help="Optional lower bound time for comments; older comments can stop deep scan early")
    return parser.parse_args()


def build_keywords(event_query: str) -> list[str]:
    base = event_query.strip()
    return [
        base,
        f"{base} 求票",
        f"{base} 收票",
        f"{base} 没抢到",
        f"{base} 蹲票",
        f"{base} 票",
    ]


def make_task_id(event_query: str) -> str:
    normalized = re.sub(r"\s+", "", event_query.strip())
    return f"weibo_lead:{normalized}"


def emit_event(path: Path, run_id: str, event: str, level: str = "info", **payload) -> None:
    record = {
        "ts": now_iso(),
        "run_id": run_id,
        "level": level,
        "event": event,
        **payload,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def norm_href(href: str) -> str:
    href = (href or "").strip()
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return "https://s.weibo.com" + href
    return href


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def signal_score(text: str) -> tuple[int, list[str]]:
    hits = []
    for pat in DEFAULT_DEMAND_PATTERNS:
        if re.search(pat, text or "", flags=re.I):
            hits.append(pat)
    return len(hits), hits


def human_pause(page, low_ms: int = 700, high_ms: int = 1600) -> None:
    page.wait_for_timeout(random.randint(low_ms, high_ms))


def human_scroll(page, min_delta: int = 300, max_delta: int = 900, times: int = 1) -> None:
    for _ in range(times):
        page.mouse.wheel(0, random.randint(min_delta, max_delta))
        human_pause(page, 500, 1200)


def parse_comment_count(text: str) -> int:
    txt = normalize_text(text)
    m = re.search(r"共\s*(\d+)\s*条", txt)
    if m:
        return int(m.group(1))
    nums = re.findall(r"\d+", txt)
    return int(nums[0]) if nums else 0


def score_time_text(text: str) -> int:
    txt = normalize_text(text)
    if not txt:
        return 0
    if "分钟前" in txt or "秒" in txt or "今天" in txt:
        return 5
    if re.search(r"^\d{2}:\d{2}$", txt):
        return 4
    if "月" in txt and "日" in txt:
        return 3
    if re.search(r"^\d{2}-\d{1,2}-\d{1,2}$", txt) or re.search(r"^\d{4}年", txt):
        return 1
    return 2


def extract_cards(page) -> list[dict]:
    js = r'''
() => {
  return Array.from(document.querySelectorAll('div[action-type="feed_list_item"]')).map((card, idx) => {
    const q = (sel) => card.querySelector(sel);
    const bodyNode = q('p[node-type="feed_list_content"]') || q('p.txt');
    const bodyText = bodyNode ? (bodyNode.innerText || bodyNode.textContent || '').trim() : '';
    const nameNode = q('a.name');
    const fromNode = q('div.from a');
    const commentNode = q('[action-type="feed_list_comment"]');
    return {
      index: idx,
      mid: card.getAttribute('mid') || '',
      author: nameNode ? (nameNode.innerText || nameNode.textContent || '').trim() : '',
      author_href: nameNode ? (nameNode.href || '') : '',
      time_text: fromNode ? (fromNode.innerText || fromNode.textContent || '').trim() : '',
      time_href: fromNode ? (fromNode.getAttribute('href') || '') : '',
      body_text: bodyText,
      card_text: (card.innerText || '').trim(),
      comment_text: commentNode ? (commentNode.innerText || commentNode.textContent || '').trim() : '',
      comment_count: commentNode ? parseInt(((commentNode.innerText || commentNode.textContent || '').match(/\d+/) || ['0'])[0], 10) : 0
    };
  });
}
'''
    return page.evaluate(js)


def candidate_priority(card: dict) -> tuple[int, int, int]:
    return (
        score_time_text(card.get("time_text", "")),
        parse_comment_count(card.get("comment_text", "")) or int(card.get("comment_count") or 0),
        -int(card.get("index") or 0),
    )


def parse_weibo_time_text(text: str, now_dt: datetime) -> datetime | None:
    txt = normalize_text(text)
    if not txt:
        return None
    txt = txt.replace("今天", now_dt.strftime("%Y-%m-%d"))

    m = re.search(r"(\d+)分钟前", txt)
    if m:
        return now_dt - timedelta(minutes=int(m.group(1)))

    m = re.search(r"(\d+)小时前", txt)
    if m:
        return now_dt - timedelta(hours=int(m.group(1)))

    m = re.search(r"(\d{4})[-年](\d{1,2})[-月](\d{1,2})[日\s]+(\d{1,2}):(\d{2})", txt)
    if m:
        year, month, day, hour, minute = map(int, m.groups())
        return datetime(year, month, day, hour, minute, tzinfo=now_dt.tzinfo)

    m = re.search(r"(\d{2})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})", txt)
    if m:
        year, month, day, hour, minute = map(int, m.groups())
        year += 2000
        return datetime(year, month, day, hour, minute, tzinfo=now_dt.tzinfo)

    m = re.search(r"(\d{1,2})月(\d{1,2})日\s+(\d{1,2}):(\d{2})", txt)
    if m:
        month, day, hour, minute = map(int, m.groups())
        year = now_dt.year
        dt = datetime(year, month, day, hour, minute, tzinfo=now_dt.tzinfo)
        if dt - now_dt > timedelta(days=1):
            dt = datetime(year - 1, month, day, hour, minute, tzinfo=now_dt.tzinfo)
        return dt

    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})", txt)
    if m:
        year, month, day, hour, minute = map(int, m.groups())
        return datetime(year, month, day, hour, minute, tzinfo=now_dt.tzinfo)

    return None


def extract_comment_candidates(detail_page) -> list[dict]:
    """Extract comment candidates from detail page.

    Prefer structured DOM extraction so comment leads can carry stable
    commenter identity fields (`commenter_profile_url`, `commenter_unique_id`,
    and downstream `chat_url`). Fall back to the old body-text heuristic when
    the page structure changes or the DOM probe fails.
    """
    js = r'''
() => {
  const items = [];
  const seen = new Set();
  const nodes = Array.from(document.querySelectorAll('div.text'));
  for (const node of nodes) {
    const userAnchor = node.querySelector('a[href^="/u/"], a[href*="weibo.com/u/"]');
    if (!userAnchor) continue;
    const nickname = (userAnchor.innerText || userAnchor.textContent || '').replace(/\s+/g, ' ').trim();
    const profileUrl = userAnchor.getAttribute('href') || '';
    const usercard = userAnchor.getAttribute('usercard') || '';

    const clone = node.cloneNode(true);
    const firstUserAnchor = clone.querySelector('a[href^="/u/"], a[href*="weibo.com/u/"]');
    if (firstUserAnchor) firstUserAnchor.remove();
    const text = (clone.innerText || clone.textContent || '').replace(/\s+/g, ' ').trim().replace(/^[:：]\s*/, '');
    if (!nickname || !text || text.length < 2) continue;

    let wrap = node.parentElement;
    let timeText = '';
    for (let depth = 0; wrap && depth < 6; depth += 1, wrap = wrap.parentElement) {
      const allText = (wrap.innerText || wrap.textContent || '').replace(/\s+/g, ' ').trim();
      const m = allText.match(/(\d+分钟前|\d+小时前|今天\s*\d{1,2}:\d{2}|\d{1,2}月\d{1,2}日\s*\d{1,2}:\d{2}|\d{2}-\d{1,2}-\d{1,2}\s*\d{1,2}:\d{2}|\d{4}[-年]\d{1,2}[-月]\d{1,2}[日\s]*\d{1,2}:\d{2})(?:\s*来自[^\s]+)?/);
      if (m) {
        timeText = m[0];
        break;
      }
    }

    const key = `${nickname}::${text.slice(0, 80)}`;
    if (seen.has(key)) continue;
    seen.add(key);
    items.push({
      commenter_nickname: nickname,
      commenter_profile_url: profileUrl,
      commenter_usercard: usercard,
      comment_text: text,
      comment_time_text: timeText,
    });
  }
  return items;
}
'''
    try:
        comments = detail_page.evaluate(js) or []
        if comments:
            return [
                {
                    "commenter_nickname": normalize_text(item.get("commenter_nickname", "")),
                    "commenter_profile_url": norm_href(item.get("commenter_profile_url", "")),
                    "commenter_usercard": normalize_text(item.get("commenter_usercard", "")),
                    "comment_text": normalize_text(item.get("comment_text", "")),
                    "comment_time_text": normalize_text(item.get("comment_time_text", "")),
                }
                for item in comments
                if normalize_text(item.get("commenter_nickname", "")) and normalize_text(item.get("comment_text", ""))
            ]
    except Exception:
        pass

    body_text = detail_page.inner_text("body")
    lines = [normalize_text(x) for x in body_text.splitlines() if normalize_text(x)]
    comments = []
    seen: set[str] = set()
    skip_tokens = {
        "评论", "按热度", "按时间", "分享这条博文", "同时转发", "微博智搜",
        "关注", "返回", "全部关注", "最新微博", "查看个人主页", "相关推荐"
    }
    for i in range(len(lines) - 1):
        nickname = lines[i]
        text = lines[i + 1] if i + 1 < len(lines) else ""
        if nickname in skip_tokens:
            continue
        if len(nickname) > 30 or not text.startswith(":"):
            continue
        comment_text = normalize_text(text.lstrip(":"))
        if not comment_text or len(comment_text) < 2:
            continue
        key = f"{nickname}::{comment_text[:80]}"
        if key in seen:
            continue
        comment_time = ""
        for j in range(i + 2, min(i + 8, len(lines))):
            if re.search(r"(分钟前|小时前|今天|月|日|\d{2}:\d{2}|来自|\d{2}-\d{1,2}-\d{1,2})", lines[j]):
                comment_time = lines[j]
                break
        comments.append({
            "commenter_nickname": nickname,
            "commenter_profile_url": "",
            "commenter_usercard": "",
            "comment_text": comment_text,
            "comment_time_text": comment_time,
        })
        seen.add(key)
    return comments


def try_click_comment_next_page(detail_page) -> bool:
    js = r'''
() => {
  const nodes = Array.from(document.querySelectorAll('a, button, span'));
  const target = nodes.find((el) => {
    const txt = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
    return txt === '下一页' || txt === '下页' || txt.includes('下一页');
  });
  if (!target) return false;
  target.click();
  return true;
}
'''
    try:
        return bool(detail_page.evaluate(js))
    except Exception:
        return False


def extract_detail_comments(
    detail_page,
    max_comments: int = 200,
    recent_days: int = 5,
    max_scroll_rounds: int = 30,
    max_comment_pages: int = 20,
    comment_since: str = "",
) -> list[dict]:
    now_dt = datetime.now().astimezone()
    cutoff = now_dt - timedelta(days=recent_days)
    since_dt = datetime.fromisoformat(comment_since) if comment_since else None
    comments: list[dict] = []
    seen: set[str] = set()
    oldest_seen: datetime | None = None
    stagnant_rounds = 0
    comment_pages_visited = 0

    human_scroll(detail_page, 500, 1200, times=5)

    while len(comments) < max_comments and comment_pages_visited < max_comment_pages:
        page_progress = False
        for _ in range(max_scroll_rounds):
            candidates = extract_comment_candidates(detail_page)
            new_count = 0
            hit_old_comment = False
            for comment in candidates:
                key = f"{comment.get('commenter_nickname','')}::{normalize_text(comment.get('comment_text',''))[:80]}"
                if key in seen:
                    continue
                parsed_dt = parse_weibo_time_text(comment.get("comment_time_text", ""), now_dt)
                if parsed_dt:
                    oldest_seen = parsed_dt if oldest_seen is None else min(oldest_seen, parsed_dt)
                    if parsed_dt < cutoff:
                        hit_old_comment = True
                        continue
                    if since_dt and parsed_dt < since_dt:
                        hit_old_comment = True
                        continue
                comments.append(comment)
                seen.add(key)
                new_count += 1
                if len(comments) >= max_comments:
                    break
            if len(comments) >= max_comments:
                break
            if new_count > 0:
                page_progress = True
                stagnant_rounds = 0
            else:
                stagnant_rounds += 1
            if hit_old_comment:
                return comments[:max_comments]
            if stagnant_rounds >= 3:
                break
            human_scroll(detail_page, 700, 1400, times=2)

        comment_pages_visited += 1
        if len(comments) >= max_comments:
            break
        if oldest_seen and oldest_seen < cutoff:
            break
        if not try_click_comment_next_page(detail_page):
            break
        page_progress = True
        stagnant_rounds = 0
        human_pause(detail_page, 1800, 2800)

        if not page_progress:
            break

    return comments[:max_comments]


def build_comment_lead(event_query: str, keyword: str, page_no: int, card: dict, comment: dict, score: int, hits: list[str]) -> dict:
    profile_url = norm_href(comment.get("commenter_profile_url", ""))
    uid_match = re.search(r"weibo\.com/(?:u/)?(\d+)", profile_url)
    uid = uid_match.group(1) if uid_match else ""
    if not uid:
        usercard = normalize_text(comment.get("commenter_usercard", ""))
        usercard_match = re.search(r"(?:^|name=@)?(\d{5,})$", usercard)
        uid = usercard_match.group(1) if usercard_match else ""
    post_url = norm_href(card.get("time_href", ""))
    signal_text = normalize_text(comment.get("comment_text") or "")
    recommended_action = "dm_first" if uid else "reply_first"
    return {
        "platform": "weibo",
        "event_query": event_query,
        "search_keyword": keyword,
        "search_page": page_no,
        "commenter_nickname": normalize_text(comment.get("commenter_nickname", "")),
        # For comment leads these three fields are critical handoff fields for the
        # downstream outreach agent. Prefer DOM-resolved uid/profile so chat_url is usable.
        "commenter_unique_id": uid,
        "commenter_profile_url": profile_url,
        "chat_url": f"https://api.weibo.com/chat/#/chat?to_uid={uid}&source_from=" if uid else "",
        "source_post_id": card.get("mid", ""),
        "source_post_url": post_url,
        "source_post_author": normalize_text(card.get("author", "")),
        "source_post_published_at": normalize_text(card.get("time_text", "")),
        "signal_type": "detail_comment",
        "signal_text": signal_text,
        "signal_url": post_url,
        "signal_published_at": normalize_text(comment.get("comment_time_text", "")),
        "intent_label": "明确求票" if score >= 2 else "疑似求票",
        "is_demand": True,
        "confidence": min(0.55 + score * 0.12, 0.95),
        "evidence": hits,
        "recommended_action": recommended_action,
        "outreach_angle": "从评论中的求票/没抢到/蹲票等表达切入，确认场次、张数与预算",
        "needs_agent_review": False if score >= 2 else True,
        "review_reason": "" if score >= 2 else "评论信号较弱，建议 agent 二次确认",
        "captured_at": now_iso(),
    }


def build_lead(event_query: str, keyword: str, page_no: int, card: dict, score: int, hits: list[str]) -> dict:
    profile_url = norm_href(card.get("author_href", ""))
    uid_match = re.search(r"weibo\.com/(?:u/)?(\d+)", profile_url)
    uid = uid_match.group(1) if uid_match else ""
    post_url = norm_href(card.get("time_href", ""))
    signal_text = normalize_text(card.get("body_text") or card.get("card_text") or "")
    recommended_action = "dm_first" if uid else "reply_first"
    return {
        "platform": "weibo",
        "event_query": event_query,
        "search_keyword": keyword,
        "search_page": page_no,
        "commenter_nickname": normalize_text(card.get("author", "")),
        "commenter_unique_id": uid,
        "commenter_profile_url": profile_url,
        "chat_url": f"https://api.weibo.com/chat/#/chat?to_uid={uid}&source_from=" if uid else "",
        "source_post_id": card.get("mid", ""),
        "source_post_url": post_url,
        "source_post_author": normalize_text(card.get("author", "")),
        "source_post_published_at": normalize_text(card.get("time_text", "")),
        "signal_type": "post",
        "signal_text": signal_text,
        "signal_url": post_url,
        "signal_published_at": normalize_text(card.get("time_text", "")),
        "intent_label": "明确求票" if score >= 2 else "疑似求票",
        "is_demand": True,
        "confidence": min(0.55 + score * 0.12, 0.95),
        "evidence": hits,
        "recommended_action": recommended_action,
        "outreach_angle": "从求票/没抢到切入，确认场次、张数与预算",
        "needs_agent_review": False if score >= 2 else True,
        "review_reason": "" if score >= 2 else "信号较弱，建议 agent 二次确认",
        "captured_at": now_iso(),
    }


def save_jsonl(path: Path, items: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def is_cdp_ready(endpoint: str, timeout_sec: float = 2.0) -> bool:
    version_url = endpoint.rstrip("/") + "/json/version"
    try:
        with urlopen(version_url, timeout=timeout_sec) as resp:
            return 200 <= getattr(resp, "status", 200) < 300
    except Exception:
        return False


def ensure_cdp_available(endpoint: str, port: int, events_path: Path | None = None, run_id: str = "") -> bool:
    if is_cdp_ready(endpoint):
        return True

    launch_script = ROOT / "scripts" / "launch_work_chrome.ps1"
    if not launch_script.exists():
        return False

    if events_path and run_id:
        emit_event(events_path, run_id, "cdp_launch_attempt", endpoint=endpoint, port=port, script=str(launch_script))

    try:
        subprocess.run(
            [
                "powershell",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(launch_script),
                "-Port",
                str(port),
            ],
            cwd=str(ROOT),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
    except Exception as exc:
        if events_path and run_id:
            emit_event(events_path, run_id, "cdp_launch_failed", level="warn", error=type(exc).__name__)
        return False

    for _ in range(20):
        if is_cdp_ready(endpoint):
            if events_path and run_id:
                emit_event(events_path, run_id, "cdp_ready", endpoint=endpoint, port=port)
            return True
        time.sleep(1)

    if events_path and run_id:
        emit_event(events_path, run_id, "cdp_unavailable", level="warn", endpoint=endpoint, port=port)
    return False


def append_lead(jsonl_path: Path, lead: dict) -> None:
    """Append a single lead to the JSONL file immediately (for crash-resilience)."""
    with jsonl_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(lead, ensure_ascii=False) + "\n")


def save_csv(path: Path, items: list[dict]) -> None:
    if not items:
        path.write_text("", encoding="utf-8")
        return
    fields = list(items[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(items)


def collect_leads(args: argparse.Namespace) -> dict[str, Any]:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_root = Path(args.run_root) if args.run_root else (ROOT / "runs" / "weibo-test-leads" / run_id)
    run_root.mkdir(parents=True, exist_ok=True)

    endpoint = f"http://127.0.0.1:{args.port}"
    search_keywords = build_keywords(args.event_query)
    task_id = args.task_id or make_task_id(args.event_query)
    events_path = run_root / "events.jsonl"
    run_path = run_root / "run.json"

    all_leads: list[dict] = []
    seen_keys: set[str] = set()
    raw_cards: list[dict] = []
    keyword_stats: list[dict] = []
    task_status = "running"
    started_at = now_iso()
    stop_reason = "finished_scan"

    run_payload = {
        "task_id": task_id,
        "run_id": run_id,
        "platform": "weibo",
        "task_type": "lead_collect",
        "event_query": args.event_query,
        "keywords": search_keywords,
        "status": task_status,
        "started_at": started_at,
        "finished_at": None,
        "search_since": args.search_since or None,
        "comment_since": args.comment_since or None,
        "max_leads": args.max_leads,
        "max_pages_per_keyword": args.max_pages_per_keyword,
        "max_posts_per_page": args.max_posts_per_page,
        "max_comments_per_post": args.max_comments_per_post,
        "comment_recent_days": args.comment_recent_days,
        "max_comment_scroll_rounds": args.max_comment_scroll_rounds,
        "max_comment_pages": args.max_comment_pages,
        "operator": "scripts/weibo_collect_test_leads.py",
    }
    run_path.write_text(json.dumps(run_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    emit_event(events_path, run_id, "task_started", task_id=task_id, event_query=args.event_query)

    try:
        if not ensure_cdp_available(endpoint, args.port, events_path=events_path, run_id=run_id):
            raise RuntimeError("cdp_unavailable")

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(endpoint)
            context = browser.contexts[0]
            page = context.new_page()
            try:
                for keyword in search_keywords:
                    emit_event(events_path, run_id, "keyword_started", keyword=keyword)
                    keyword_added = 0
                    keyword_scanned = 0
                    keyword_failed = False
                    for page_no in range(1, args.max_pages_per_keyword + 1):
                        if len(all_leads) >= args.max_leads:
                            stop_reason = "reached_max_leads"
                            break
                        url = f"https://s.weibo.com/weibo?q={quote(keyword)}&page={page_no}"
                        print(f"step=search keyword={keyword} page={page_no}", flush=True)
                        emit_event(events_path, run_id, "search_page_started", keyword=keyword, page=page_no, url=url)
                        try:
                            page.goto(url, wait_until="domcontentloaded", timeout=45000)
                        except Exception as exc:
                            emit_event(events_path, run_id, "search_page_error", level="warn", keyword=keyword, page=page_no, url=url, error=type(exc).__name__)
                            keyword_failed = True
                            stop_reason = "search_page_error"
                            break
                        human_pause(page, 1800, 3200)
                        human_scroll(page, 500, 1100, times=random.randint(1, 2))
                        cards = extract_cards(page)
                        if not cards:
                            print(f"step=empty keyword={keyword} page={page_no}", flush=True)
                            emit_event(events_path, run_id, "search_page_empty", keyword=keyword, page=page_no)
                            stop_reason = "no_valid_posts"
                            break
                        keyword_scanned += len(cards)
                        emit_event(events_path, run_id, "search_page_loaded", keyword=keyword, page=page_no, card_count=len(cards))
                        for c in cards:
                            c["priority"] = candidate_priority(c)
                        cards_sorted = sorted(cards, key=lambda x: x["priority"], reverse=True)
                        raw_cards.extend([{"search_keyword": keyword, "search_page": page_no, **c} for c in cards_sorted])

                        processed_posts = 0
                        for card in cards_sorted:
                            if len(all_leads) >= args.max_leads:
                                stop_reason = "reached_max_leads"
                                break
                            if processed_posts >= args.max_posts_per_page:
                                break
                            post_url = norm_href(card.get("time_href", ""))
                            if not post_url:
                                continue
                            processed_posts += 1
                            comment_count = parse_comment_count(card.get("comment_text", ""))
                            print(f"step=open_detail keyword={keyword} page={page_no} url={post_url} comments={comment_count} time={card.get('time_text', '')}", flush=True)
                            emit_event(events_path, run_id, "candidate_post_selected", keyword=keyword, page=page_no, url=post_url, comment_count=comment_count, time_text=card.get("time_text", ""))
                            detail = context.new_page()
                            try:
                                human_pause(page, 600, 1400)
                                detail.goto(post_url, wait_until="domcontentloaded", timeout=45000)
                                human_pause(detail, 2200, 3800)
                                emit_event(events_path, run_id, "detail_page_entered", keyword=keyword, page=page_no, url=post_url)
                                comments = extract_detail_comments(
                                    detail,
                                    max_comments=args.max_comments_per_post,
                                    recent_days=args.comment_recent_days,
                                    max_scroll_rounds=args.max_comment_scroll_rounds,
                                    max_comment_pages=args.max_comment_pages,
                                    comment_since=args.comment_since,
                                )
                                text = normalize_text(card.get("body_text") or card.get("card_text") or "")
                                score, hits = signal_score(text)
                                post_key = f"post::{post_url}"
                                if score > 0 and post_key not in seen_keys:
                                    lead = build_lead(args.event_query, keyword, page_no, card, score, hits)
                                    all_leads.append(lead)
                                    append_lead(jsonl_path, lead)
                                    seen_keys.add(post_key)
                                    keyword_added += 1
                                    emit_event(events_path, run_id, "lead_extracted", keyword=keyword, page=page_no, url=post_url, signal_type="post", total_leads=len(all_leads))
                                    print(f"step=post_lead count={len(all_leads)} keyword={keyword} page={page_no} url={post_url}", flush=True)
                                for comment in comments:
                                    if len(all_leads) >= args.max_leads:
                                        stop_reason = "reached_max_leads"
                                        break
                                    comment_text = normalize_text(comment.get("comment_text") or "")
                                    comment_score, comment_hits = signal_score(comment_text)
                                    if comment_score <= 0:
                                        continue
                                    comment_key = f"comment::{post_url}::{comment.get('commenter_nickname','')}::{comment_text[:80]}"
                                    if comment_key in seen_keys:
                                        emit_event(events_path, run_id, "lead_deduped", keyword=keyword, page=page_no, url=post_url, signal_type="detail_comment")
                                        continue
                                    lead = build_comment_lead(args.event_query, keyword, page_no, card, comment, comment_score, comment_hits)
                                    all_leads.append(lead)
                                    append_lead(jsonl_path, lead)
                                    seen_keys.add(comment_key)
                                    keyword_added += 1
                                    emit_event(events_path, run_id, "lead_extracted", keyword=keyword, page=page_no, url=post_url, signal_type="detail_comment", total_leads=len(all_leads))
                                    print(f"step=detail_comment_lead count={len(all_leads)} keyword={keyword} page={page_no} url={post_url}", flush=True)
                            except Exception as exc:
                                emit_event(events_path, run_id, "detail_page_error", level="warn", keyword=keyword, page=page_no, url=post_url, error=type(exc).__name__)
                                print(f"step=detail_error keyword={keyword} page={page_no} url={post_url} error={type(exc).__name__}", flush=True)
                            finally:
                                detail.close()
                        emit_event(events_path, run_id, "page_finished", keyword=keyword, page=page_no, processed_posts=processed_posts, total_leads=len(all_leads))
                    keyword_stats.append({"keyword": keyword, "cards_scanned": keyword_scanned, "leads_added": keyword_added, "status": "failed" if keyword_failed else "completed"})
                    emit_event(events_path, run_id, "keyword_finished", keyword=keyword, cards_scanned=keyword_scanned, leads_added=keyword_added, status=("failed" if keyword_failed else "completed"))
                    if len(all_leads) >= args.max_leads:
                        break
            finally:
                page.close()
                browser.close()
    except Exception as exc:
        task_status = "failed"
        stop_reason = "collector_error"
        emit_event(events_path, run_id, "task_error", level="error", error=type(exc).__name__)
    else:
        if any(x.get("status") == "failed" for x in keyword_stats):
            task_status = "partial_success" if all_leads else "failed"
        else:
            task_status = "success" if all_leads else "failed"
        if not all_leads and stop_reason == "finished_scan":
            stop_reason = "no_new_hits"

    raw_path = run_root / "raw_cards.json"
    raw_path.write_text(json.dumps(raw_cards, ensure_ascii=False, indent=2), encoding="utf-8")
    jsonl_path = run_root / "leads.jsonl"
    csv_path = run_root / "leads.csv"

    # Pre-create empty files so they exist even if killed early
    # JSONL: leads already appended in real-time via append_lead() — do NOT clear
    csv_path.write_text("", encoding="utf-8")
    summary_path = run_root / "summary.json"
    save_csv(csv_path, all_leads)  # CSV rewritten at end (not real-time)
    finished_at = now_iso()
    summary = {
        "ok": task_status in {"success", "partial_success"},
        "task_id": task_id,
        "run_id": run_id,
        "status": task_status,
        "stop_reason": stop_reason,
        "endpoint": endpoint,
        "event_query": args.event_query,
        "search_keywords": search_keywords,
        "max_leads": args.max_leads,
        "max_pages_per_keyword": args.max_pages_per_keyword,
        "max_posts_per_page": args.max_posts_per_page,
        "max_comments_per_post": args.max_comments_per_post,
        "comment_recent_days": args.comment_recent_days,
        "max_comment_scroll_rounds": args.max_comment_scroll_rounds,
        "max_comment_pages": args.max_comment_pages,
        "search_since": args.search_since or None,
        "comment_since": args.comment_since or None,
        "lead_count": len(all_leads),
        "keyword_stats": keyword_stats,
        "run_path": str(run_path),
        "events_path": str(events_path),
        "jsonl_path": str(jsonl_path),
        "csv_path": str(csv_path),
        "raw_cards_path": str(raw_path),
        "started_at": started_at,
        "finished_at": finished_at,
        "generated_at": finished_at,
        "note": "测试版结果优先按搜索结果页的时间/评论数挑选高热帖子，并进入帖子主页深翻评论；task 框架会将本次 run 结果与 task 级 current_leads 进行增量合并。",
    }
    run_payload["status"] = task_status
    run_payload["finished_at"] = finished_at
    run_payload["lead_count"] = len(all_leads)
    run_payload["summary_path"] = str(summary_path)
    run_payload["events_path"] = str(events_path)
    run_payload["stop_reason"] = stop_reason
    run_path.write_text(json.dumps(run_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    emit_event(events_path, run_id, "task_finished", status=task_status, lead_count=len(all_leads), stop_reason=stop_reason, summary_path=str(summary_path))
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return {
        "ok": task_status in {"success", "partial_success"},
        "run_id": run_id,
        "task_id": task_id,
        "status": task_status,
        "stop_reason": stop_reason,
        "started_at": started_at,
        "finished_at": finished_at,
        "run_root": str(run_root),
        "run_path": str(run_path),
        "events_path": str(events_path),
        "summary_path": str(summary_path),
        "raw_cards_path": str(raw_path),
        "leads_jsonl_path": str(jsonl_path),
        "leads_csv_path": str(csv_path),
        "lead_count": len(all_leads),
        "keyword_stats": keyword_stats,
        "run_raw_leads": all_leads,
    }


def main() -> int:
    result = collect_leads(parse_args())
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
