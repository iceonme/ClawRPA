#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COLLECTOR = ROOT / "scripts" / "weibo_collect_test_leads.py"
REVIEW_PREFIX = "OPENCLAW_REVIEW_REQUEST "


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run collector with built-in interactive review controller")
    parser.add_argument("--event-query", required=True)
    parser.add_argument("--port", type=int, default=9222)
    parser.add_argument("--max-leads", type=int, default=50)
    parser.add_argument("--max-pages-per-keyword", type=int, default=10)
    parser.add_argument("--max-posts-per-page", type=int, default=8)
    parser.add_argument("--max-comments-per-post", type=int, default=200)
    parser.add_argument("--comment-recent-days", type=int, default=5)
    parser.add_argument("--max-comment-scroll-rounds", type=int, default=30)
    parser.add_argument("--max-comment-pages", type=int, default=20)
    parser.add_argument("--search-since", default="")
    parser.add_argument("--comment-since", default="")
    parser.add_argument("--print-review-json", action="store_true")
    return parser.parse_args()


def build_review_item(candidate: dict[str, Any]) -> dict[str, Any]:
    idx = int(candidate.get("candidate_idx") or 0)
    text = str(candidate.get("comment_text") or "")
    uid = str(candidate.get("commenter_unique_id") or "")
    hard_exclude = bool(candidate.get("hard_exclude"))
    rule_score = int(candidate.get("rule_score") or 0)

    positive_patterns = ["求票", "收票", "没抢到", "抢不到", "蹲票", "有票吗", "带id", "带ID", "无偿带id", "无偿带ID"]
    weak_positive_patterns = ["帮我带", "能带id", "能带ID", "可无偿带id", "可无偿带ID"]

    if hard_exclude:
        return {
            "candidate_idx": idx,
            "review_status": "rejected",
            "ai_is_lead": False,
            "ai_confidence": 0.99,
            "ai_reason": f"hard excluded: {candidate.get('exclude_reason', '')}",
            "should_fetch_chat_url": False,
        }

    lower = text.lower()
    if any(p.lower() in lower for p in positive_patterns):
        return {
            "candidate_idx": idx,
            "review_status": "accepted",
            "ai_is_lead": True,
            "ai_confidence": 0.88,
            "ai_reason": "explicit demand/ticket-help signal in comment text",
            "should_fetch_chat_url": bool(uid),
        }

    if any(p.lower() in lower for p in weak_positive_patterns) or rule_score > 0:
        return {
            "candidate_idx": idx,
            "review_status": "accepted",
            "ai_is_lead": True,
            "ai_confidence": 0.72,
            "ai_reason": "weak but actionable intent signal",
            "should_fetch_chat_url": bool(uid),
        }

    return {
        "candidate_idx": idx,
        "review_status": "rejected",
        "ai_is_lead": False,
        "ai_confidence": 0.9,
        "ai_reason": "no actionable lead signal in controller fallback",
        "should_fetch_chat_url": False,
    }


def build_response(payload: dict[str, Any]) -> dict[str, Any]:
    items = [build_review_item(x) for x in (payload.get("candidates") or [])]
    return {"batch_id": payload.get("batch_id"), "items": items}


def build_cmd(args: argparse.Namespace) -> list[str]:
    cmd = [sys.executable, str(COLLECTOR), "--interactive-review", "--event-query", args.event_query,
           "--port", str(args.port),
           "--max-leads", str(args.max_leads),
           "--max-pages-per-keyword", str(args.max_pages_per_keyword),
           "--max-posts-per-page", str(args.max_posts_per_page),
           "--max-comments-per-post", str(args.max_comments_per_post),
           "--comment-recent-days", str(args.comment_recent_days),
           "--max-comment-scroll-rounds", str(args.max_comment_scroll_rounds),
           "--max-comment-pages", str(args.max_comment_pages)]
    if args.search_since:
        cmd.extend(["--search-since", args.search_since])
    if args.comment_since:
        cmd.extend(["--comment-since", args.comment_since])
    return cmd


def main() -> int:
    args = parse_args()
    cmd = build_cmd(args)
    print(json.dumps({"event": "interactive_runner_started", "cmd": cmd}, ensure_ascii=False), file=sys.stderr, flush=True)
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    assert proc.stdout is not None and proc.stdin is not None
    try:
        for line in proc.stdout:
            text = line.rstrip("\n")
            if text.startswith(REVIEW_PREFIX):
                payload = json.loads(text[len(REVIEW_PREFIX):])
                response = build_response(payload)
                if args.print_review_json:
                    print(json.dumps({"event": "interactive_runner_review", "payload": response}, ensure_ascii=False), file=sys.stderr, flush=True)
                proc.stdin.write(json.dumps(response, ensure_ascii=False) + "\n")
                proc.stdin.flush()
                accepted_count = sum(1 for x in response.get("items") or [] if x.get("review_status") == "accepted" and x.get("ai_is_lead") is True)
                print(json.dumps({"event": "interactive_review_applied", "batch_id": response.get("batch_id"), "candidate_count": len(payload.get("candidates") or []), "accepted_count": accepted_count}, ensure_ascii=False), flush=True)
            else:
                print(text, flush=True)
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
    return proc.wait()


if __name__ == "__main__":
    raise SystemExit(main())
