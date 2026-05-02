#!/usr/bin/env python3
"""Run enabled tasks from tasks/task_list.json sequentially.

First version rules:
- filesystem state only
- sequential execution only
- each task auto-loads last successful run time as incremental boundary
- disabled tasks are skipped
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from task_store import TASK_LIST_PATH, normalize_task_list_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run enabled weibo tasks sequentially")
    parser.add_argument("--port", type=int, default=9222)
    parser.add_argument("--max-leads", type=int, default=30)
    parser.add_argument("--max-pages-per-keyword", type=int, default=10)
    parser.add_argument("--max-posts-per-page", type=int, default=5)
    parser.add_argument("--max-comments-per-post", type=int, default=200)
    parser.add_argument("--comment-recent-days", type=int, default=5)
    parser.add_argument("--max-comment-scroll-rounds", type=int, default=30)
    parser.add_argument("--max-comment-pages", type=int, default=20)
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument("--callback-session-id", default="", help="OpenClaw session id to notify after each task run")
    parser.add_argument("--callback-prompt", default="已经跑完，请检验结果并进入下一步。", help="Prompt appended to each callback message")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw = json.loads(TASK_LIST_PATH.read_text(encoding="utf-8")) if TASK_LIST_PATH.exists() else {"active": [], "inactive": []}
    normalized = normalize_task_list_payload(raw)
    if normalized != raw:
        TASK_LIST_PATH.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")

    active_tasks = list(normalized.get("active") or [])
    inactive_tasks = list(normalized.get("inactive") or [])
    selected = [x for x in active_tasks if args.include_disabled or x.get("enabled", True)]

    results: list[dict] = []
    overall_ok = True

    for item in selected:
        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "run_task.py"),
            "--task-no",
            str(item["task_no"]),
            "--port",
            str(args.port),
            "--max-leads",
            str(args.max_leads),
            "--max-pages-per-keyword",
            str(args.max_pages_per_keyword),
            "--max-posts-per-page",
            str(args.max_posts_per_page),
            "--max-comments-per-post",
            str(args.max_comments_per_post),
            "--comment-recent-days",
            str(args.comment_recent_days),
            "--max-comment-scroll-rounds",
            str(args.max_comment_scroll_rounds),
            "--max-comment-pages",
            str(args.max_comment_pages),
        ]
        if args.callback_session_id:
            cmd.extend([
                "--callback-session-id",
                args.callback_session_id,
                "--callback-prompt",
                args.callback_prompt,
            ])
        completed = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        try:
            payload = json.loads(completed.stdout.strip() or "{}")
        except json.JSONDecodeError:
            payload = {"ok": False, "stdout": completed.stdout, "stderr": completed.stderr, "task_no": item["task_no"]}
        payload["returncode"] = completed.returncode
        payload["keyword"] = item["keyword"]
        results.append(payload)
        if completed.returncode != 0:
            overall_ok = False

    print(json.dumps({
        "ok": overall_ok,
        "task_count": len(selected),
        "active_count": len(active_tasks),
        "inactive_count": len(inactive_tasks),
        "results": results,
    }, ensure_ascii=False, indent=2))
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
