#!/usr/bin/env python3
"""Run one filesystem-backed weibo lead task.

This is the first practical task/run framework layer.
It wraps `src.flows.weibo_lead_collect`, creates a task directory if needed,
opens a new run directory under `<task>/runs/<run_id>/`, then merges the run
outputs into task-level status and current lead pool.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from openclaw_callback import notify_session

from task_store import (
    TASKS_ROOT,
    ensure_task_structure,
    get_task_by_id,
    get_task_by_no,
    load_status,
    log_task_event,
    merge_lead_pools,
    now_iso,
    read_jsonl,
    update_task_files,
    write_csv,
    write_jsonl,
)
from src.flows.weibo_lead_collect import collect_leads


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one weibo lead task from tasks/task_list.json")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--task-id", help="task id, e.g. task01_蔡依林苏州20260408")
    group.add_argument("--task-no", type=int, help="task number in task_list.json")
    parser.add_argument("--port", type=int, default=9222, help="CDP port")
    parser.add_argument("--max-leads", type=int, default=50)
    parser.add_argument("--max-pages-per-keyword", type=int, default=10)
    parser.add_argument("--max-posts-per-page", type=int, default=8)
    parser.add_argument("--max-comments-per-post", type=int, default=200)
    parser.add_argument("--comment-recent-days", type=int, default=5)
    parser.add_argument("--max-comment-scroll-rounds", type=int, default=30)
    parser.add_argument("--max-comment-pages", type=int, default=20)
    parser.add_argument("--search-since", default="", help="override status.search_since")
    parser.add_argument("--comment-since", default="", help="override status.comment_since")
    parser.add_argument("--callback-session-id", default="", help="OpenClaw session id to notify on finish")
    parser.add_argument("--callback-prompt", default="已经跑完，请检验结果并进入下一步。", help="Prompt appended to callback message")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    spec = get_task_by_id(args.task_id) if args.task_id else get_task_by_no(args.task_no)
    paths = ensure_task_structure(spec)
    status = load_status(paths["status_path"])

    search_since = args.search_since or status.get("last_successful_run_at") or status.get("search_since") or ""
    comment_since = args.comment_since or status.get("last_successful_run_at") or status.get("comment_since") or ""

    log_task_event(
        paths["task_log_path"],
        "run_started",
        task_id=spec.task_id,
        keyword=spec.keyword,
        search_since=search_since or None,
        comment_since=comment_since or None,
        requested_at=now_iso(),
    )

    precreated_run_root = paths["runs_dir"] / now_iso().replace("-", "").replace(":", "").replace("+", "_").replace("T", "_")
    result = collect_leads(
        argparse.Namespace(
            port=args.port,
            event_query=spec.keyword,
            max_leads=args.max_leads,
            max_pages_per_keyword=args.max_pages_per_keyword,
            max_posts_per_page=args.max_posts_per_page,
            max_comments_per_post=args.max_comments_per_post,
            comment_recent_days=args.comment_recent_days,
            max_comment_scroll_rounds=args.max_comment_scroll_rounds,
            max_comment_pages=args.max_comment_pages,
            run_root=str(precreated_run_root),
            task_id=spec.task_id,
            search_since=search_since,
            comment_since=comment_since,
        )
    )

    run_root = Path(result["run_root"])
    run_raw_leads = result["run_raw_leads"]

    # Data flow note:
    # - run_raw_leads: current run raw capture snapshot, stored under runs/<run_id>/leads.*
    # - run_new_leads: deduped new identities relative to task current_leads
    # - current_leads: task-level cumulative working pool used by the downstream agent
    # - total_leads: len(current_leads), recorded in status/summary as a count only
    old_current_leads = read_jsonl(paths["current_jsonl_path"])
    merged_current_leads, run_new_leads, run_updated_leads = merge_lead_pools(old_current_leads, run_raw_leads)

    new_jsonl_path = run_root / "new_leads.jsonl"
    new_csv_path = run_root / "new_leads.csv"
    write_jsonl(new_jsonl_path, run_new_leads)
    write_csv(new_csv_path, run_new_leads)

    updated_jsonl_path = run_root / "updated_leads.jsonl"
    updated_csv_path = run_root / "updated_leads.csv"
    write_jsonl(updated_jsonl_path, run_updated_leads)
    write_csv(updated_csv_path, run_updated_leads)

    run_json_path = run_root / "run.json"
    run_payload = json.loads(run_json_path.read_text(encoding="utf-8"))
    run_payload["new_leads_path"] = str(new_jsonl_path)
    run_payload["new_leads_csv_path"] = str(new_csv_path)
    run_payload["updated_leads_path"] = str(updated_jsonl_path)
    run_payload["updated_leads_csv_path"] = str(updated_csv_path)
    run_payload["run_raw_leads"] = len(run_raw_leads)
    run_payload["run_new_leads"] = len(run_new_leads)
    run_payload["run_updated_leads"] = len(run_updated_leads)
    run_payload["total_leads_after_merge"] = len(merged_current_leads)
    run_json_path.write_text(json.dumps(run_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_path = run_root / "summary.json"
    summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
    summary_payload["run_raw_leads"] = len(run_raw_leads)
    summary_payload["run_new_leads"] = len(run_new_leads)
    summary_payload["run_updated_leads"] = len(run_updated_leads)
    summary_payload["total_leads_after_merge"] = len(merged_current_leads)
    summary_payload["new_leads_path"] = str(new_jsonl_path)
    summary_payload["updated_leads_path"] = str(updated_jsonl_path)
    summary_path.write_text(json.dumps(summary_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    update_task_files(
        spec=spec,
        status_path=paths["status_path"],
        summary_path=paths["summary_path"],
        task_log_path=paths["task_log_path"],
        current_jsonl_path=paths["current_jsonl_path"],
        current_csv_path=paths["current_csv_path"],
        run_id=result["run_id"],
        run_status=result["status"],
        run_started_at=result["started_at"],
        run_finished_at=result["finished_at"],
        stop_reason=result["stop_reason"],
        run_raw_leads=run_raw_leads,
        run_new_leads=run_new_leads,
        run_updated_leads=run_updated_leads,
        merged_current_leads=merged_current_leads,
    )

    output = {
        "ok": result["ok"],
        "task_id": spec.task_id,
        "task_dir": str(paths["task_dir"]),
        "tasks_root": str(TASKS_ROOT),
        "run_id": result["run_id"],
        "run_root": result["run_root"],
        "status": result["status"],
        "stop_reason": result["stop_reason"],
        "run_raw_leads": len(run_raw_leads),
        "run_new_leads": len(run_new_leads),
        "run_updated_leads": len(run_updated_leads),
        "current_leads": len(merged_current_leads),
        "total_leads": len(merged_current_leads),
        "task_status_path": str(paths["status_path"]),
        "task_summary_path": str(paths["summary_path"]),
        "current_leads_path": str(paths["current_jsonl_path"]),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

    if args.callback_session_id:
        callback_result = notify_session(
            session_id=args.callback_session_id,
            payload=output,
            prompt=args.callback_prompt,
        )
        output["callback"] = {
            "attempted": True,
            "session_id": args.callback_session_id,
            "ok": bool(callback_result and callback_result.returncode == 0),
            "returncode": callback_result.returncode if callback_result else None,
            "stdout": (callback_result.stdout or "").strip() if callback_result else "",
            "stderr": (callback_result.stderr or "").strip() if callback_result else "",
        }
        print(json.dumps({"callback": output["callback"]}, ensure_ascii=False, indent=2))

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
