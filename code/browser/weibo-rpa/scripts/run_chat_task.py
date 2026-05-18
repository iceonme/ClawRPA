#!/usr/bin/env python3
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
from src.flows.weibo_chat_send import send_weibo_chat_message
from scripts.task_store import now_iso, read_jsonl, write_jsonl, read_json, write_json, append_jsonl

TASK_SHARE_ROOT = Path(r"C:\Users\iceon\.openclaw\workspace\main\task_share")
GLOBAL_SCRIPT_MD = TASK_SHARE_ROOT / "话术.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one weibo chat send task")
    parser.add_argument("--task-id", default="", help="task_share task id for pipeline mode")
    parser.add_argument("--target-id", default="")
    parser.add_argument("--chat-url", default="", help="Direct chat URL for ad-hoc test mode")
    parser.add_argument("--port", type=int, default=9222)
    parser.add_argument("--message", default="")
    parser.add_argument("--callback-session-id", default="")
    parser.add_argument("--callback-prompt", default="chat 自测已跑完，请检查发送结果。")
    args = parser.parse_args()
    if not args.task_id and not args.chat_url:
        parser.error("one of --task-id or --chat-url is required")
    if args.chat_url and not args.message.strip():
        parser.error("--message is required when using --chat-url")
    return args


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def choose_message(task_payload: dict, target: dict, override: str = "") -> str:
    if override.strip():
        return override.strip()
    if (target.get("final_message") or "").strip():
        return target["final_message"].strip()
    if target.get("source") == "manual_test":
        return "嗨，来做个私信链路自测，打扰啦～"
    keyword = (task_payload.get("keyword") or "").strip()
    if keyword:
        return f"嗨，看到你在看{keyword}，如果你还在找票的话可以直接回我～"
    return "嗨，看到你在找票，如果你还没定下来可以直接回我～"


def load_target(task_dir: Path, target_id: str = "") -> tuple[list[dict], dict]:
    current_targets_path = task_dir / "chat" / "current_targets.jsonl"
    targets = read_jsonl(current_targets_path)
    if not targets:
        raise SystemExit("chat/current_targets.jsonl is empty")
    if target_id:
        for item in targets:
            if item.get("target_id") == target_id:
                return targets, item
        raise SystemExit(f"target_id not found: {target_id}")
    return targets, targets[0]


def count_sent(sent_records: list[dict]) -> tuple[int, int]:
    sent = 0
    failed = 0
    for row in sent_records:
        if row.get("send_result") == "success":
            sent += 1
        elif row.get("send_result") in {"failed", "blocked"}:
            failed += 1
    return sent, failed


def main() -> int:
    args = parse_args()
    if args.chat_url:
        return run_direct_chat(args)

    task_dir = TASK_SHARE_ROOT / args.task_id
    if not task_dir.exists():
        raise SystemExit(f"task dir not found: {task_dir}")

    task_payload = read_json(task_dir / "task.json", default={})
    script_md = read_text(GLOBAL_SCRIPT_MD)
    targets, target = load_target(task_dir, args.target_id)
    sent_records_path = task_dir / "chat" / "sent_records.jsonl"
    status_path = task_dir / "chat" / "status.json"
    summary_path = task_dir / "chat" / "summary.json"
    handoff_path = task_dir / "chat" / "handoff.json"
    pipeline_status_path = task_dir / "pipeline_status.json"

    existing_sent_records = read_jsonl(sent_records_path)
    if any((row.get("target_id") == target.get("target_id") and row.get("send_result") == "success") for row in existing_sent_records):
        output = {
            "ok": False,
            "task_id": args.task_id,
            "target_id": target.get("target_id"),
            "status": "blocked",
            "stop_reason": "already_sent",
            "sent_records_path": str(sent_records_path),
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 2

    run_id = now_iso().replace("-", "").replace(":", "").replace("+", "_").replace("T", "_")
    run_root = task_dir / "chat" / "runs" / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    message = choose_message(task_payload, target, args.message)
    run_payload = {
        "task_id": args.task_id,
        "target_id": target.get("target_id"),
        "chat_url": target.get("chat_url"),
        "message": message,
        "global_script_path": str(GLOBAL_SCRIPT_MD),
        "global_script_excerpt": script_md[:800],
        "started_at": now_iso(),
        "status": "running",
    }
    write_json(run_root / "run.json", run_payload)

    result = send_weibo_chat_message(
        chat_url=target.get("chat_url", ""),
        message=message,
        run_root=str(run_root),
        port=args.port,
    )

    finished_at = now_iso()
    run_payload.update({
        "finished_at": finished_at,
        "status": result.get("status"),
        "stop_reason": result.get("stop_reason"),
        "result": result,
    })
    write_json(run_root / "run.json", run_payload)
    write_json(run_root / "summary.json", {
        "task_id": args.task_id,
        "target_id": target.get("target_id"),
        "status": result.get("status"),
        "stop_reason": result.get("stop_reason"),
        "message": message,
        "updated_at": finished_at,
    })

    send_result = "success" if result.get("ok") else ("blocked" if result.get("stop_reason") in {"already_sent", "input_not_found"} else "failed")
    sent_record = {
        "task_id": args.task_id,
        "run_id": run_id,
        "target_id": target.get("target_id"),
        "chat_url": target.get("chat_url"),
        "final_message": message,
        "send_result": send_result,
        "stop_reason": result.get("stop_reason"),
        "is_first_contact": True,
        "sent_at": finished_at,
        "run_root": str(run_root),
        "screenshot_path": result.get("screenshot_path", ""),
    }
    append_jsonl(sent_records_path, sent_record)

    updated_targets: list[dict] = []
    for item in targets:
        if item.get("target_id") == target.get("target_id"):
            item = {
                **item,
                "final_message": message,
                "status": "sent_first_message" if result.get("ok") else "send_blocked",
                "last_run_id": run_id,
                "last_sent_at": finished_at,
                "last_stop_reason": result.get("stop_reason"),
            }
        updated_targets.append(item)
    write_jsonl(task_dir / "chat" / "current_targets.jsonl", updated_targets)

    all_sent_records = read_jsonl(sent_records_path)
    sent_count, failed_count = count_sent(all_sent_records)
    write_json(status_path, {
        "stage": "chat",
        "status": "self_test_success" if result.get("ok") else "self_test_blocked",
        "latest_run_id": run_id,
        "latest_target_id": target.get("target_id"),
        "updated_at": finished_at,
        "last_stop_reason": result.get("stop_reason"),
    })
    write_json(summary_path, {
        "task_id": args.task_id,
        "stage": "chat",
        "status": "self_test_success" if result.get("ok") else "self_test_blocked",
        "total_targets": len(updated_targets),
        "sent": sent_count,
        "failed": failed_count,
        "latest_run_id": run_id,
        "updated_at": finished_at,
    })
    write_json(handoff_path, {
        "stage": "chat",
        "ready_for_next_stage": bool(result.get("ok")),
        "source_task_id": args.task_id,
        "current_targets_path": "chat/current_targets.jsonl",
        "sent_records_path": "chat/sent_records.jsonl",
        "latest_run_id": run_id,
        "notes": [
            "Self-test target executed through weibo-rpa chat runner.",
            "If this run is successful, the minimal chat send chain is considered connected."
        ],
    })

    pipeline = read_json(pipeline_status_path, default={})
    pipeline.update({
        "chat_status": "self_test_success" if result.get("ok") else "self_test_blocked",
        "overall_status": "chat_tested" if result.get("ok") else pipeline.get("overall_status", "lead_ready"),
        "updated_at": finished_at,
    })
    write_json(pipeline_status_path, pipeline)

    output = {
        "ok": bool(result.get("ok")),
        "task_id": args.task_id,
        "target_id": target.get("target_id"),
        "run_id": run_id,
        "run_root": str(run_root),
        "status": result.get("status"),
        "stop_reason": result.get("stop_reason"),
        "message": message,
        "chat_url": target.get("chat_url"),
        "sent_records_path": str(sent_records_path),
        "status_path": str(status_path),
        "summary_path": str(summary_path),
        "screenshot_path": result.get("screenshot_path", ""),
        "html_path": result.get("html_path", ""),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

    if args.callback_session_id:
        callback_result = notify_session(
            session_id=args.callback_session_id,
            payload=output,
            prompt=args.callback_prompt,
        )
        print(json.dumps({
            "callback": {
                "attempted": True,
                "session_id": args.callback_session_id,
                "ok": bool(callback_result and callback_result.returncode == 0),
                "returncode": callback_result.returncode if callback_result else None,
            }
        }, ensure_ascii=False, indent=2))

    return 0 if result.get("ok") else 1


def run_direct_chat(args: argparse.Namespace) -> int:
    run_id = now_iso().replace("-", "").replace(":", "").replace("+", "_").replace("T", "_")
    run_root = ROOT / "runs" / "weibo-chat" / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    result = send_weibo_chat_message(
        chat_url=args.chat_url,
        message=args.message,
        run_root=str(run_root),
        port=args.port,
    )

    output = {
        "ok": bool(result.get("ok")),
        "mode": "direct",
        "run_id": run_id,
        "run_root": str(run_root),
        "status": result.get("status"),
        "stop_reason": result.get("stop_reason"),
        "message": args.message,
        "chat_url": args.chat_url,
        "screenshot_path": result.get("screenshot_path", ""),
        "html_path": result.get("html_path", ""),
        "result": result,
    }
    write_json(run_root / "summary.json", output)
    print(json.dumps(output, ensure_ascii=False, indent=2))

    if args.callback_session_id:
        callback_result = notify_session(
            session_id=args.callback_session_id,
            payload=output,
            prompt=args.callback_prompt,
        )
        print(json.dumps({
            "callback": {
                "attempted": True,
                "session_id": args.callback_session_id,
                "ok": bool(callback_result and callback_result.returncode == 0),
                "returncode": callback_result.returncode if callback_result else None,
            }
        }, ensure_ascii=False, indent=2))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
