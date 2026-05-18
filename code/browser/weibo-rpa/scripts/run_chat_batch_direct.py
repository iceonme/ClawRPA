#!/usr/bin/env python3
"""Run a direct weibo chat batch from a UTF-8 targets JSON file."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from src.adapters.weibo_adapter import WeiboAdapter
from src.core.artifacts import ArtifactRecorder
from src.core.session import BrowserSession
from src.policies.weibo_chat_policy import WeiboChatPacer, WeiboChatSendPolicy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a direct weibo chat batch with shared pacing")
    parser.add_argument("--targets-json", required=True, help="UTF-8 JSON list of targets with chat_url/final_message")
    parser.add_argument("--port", type=int, default=9222)
    parser.add_argument("--run-root", default="", help="Optional output directory")
    parser.add_argument("--stop-on-failure", action="store_true")
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_targets(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("targets JSON must be a list")
    for idx, target in enumerate(payload, 1):
        if not str(target.get("chat_url") or "").strip():
            raise ValueError(f"target {idx} missing chat_url")
        if not str(target.get("final_message") or "").strip():
            raise ValueError(f"target {idx} missing final_message")
    return payload


def main() -> int:
    args = parse_args()
    targets_path = Path(args.targets_json)
    targets = load_targets(targets_path)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_root = Path(args.run_root) if args.run_root else ROOT / "runs" / "weibo-chat-batch" / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    sent_records_path = run_root / "sent_records.jsonl"
    summary_path = run_root / "summary.json"

    (run_root / "targets.json").write_text(json.dumps(targets, ensure_ascii=False, indent=2), encoding="utf-8")

    policy = WeiboChatSendPolicy()
    pacer = WeiboChatPacer(policy)
    records: list[dict[str, Any]] = []

    with BrowserSession(port=args.port) as session:
        page = session.get_or_create_page(WeiboAdapter.CHAT_URL_PREFIX)
        for idx, target in enumerate(targets, 1):
            target_id = str(target.get("target_id") or f"target_{idx:03d}")
            target_run = run_root / f"{idx:02d}_{target_id}"
            recorder = ArtifactRecorder(target_run)
            adapter = WeiboAdapter(pacer=pacer, recorder=recorder)
            started_at = now_iso()
            print(json.dumps({
                "event": "send_started",
                "idx": idx,
                "target_id": target_id,
                "uid": target.get("uid", ""),
                "nickname": target.get("nickname", ""),
                "started_at": started_at,
            }, ensure_ascii=False), flush=True)

            result = adapter.send_chat_message(
                page,
                chat_url=str(target["chat_url"]),
                message=str(target["final_message"]),
                screenshot_name="after_send.png",
            )
            finished_at = now_iso()
            record = {
                "idx": idx,
                "target_id": target_id,
                "uid": target.get("uid", ""),
                "nickname": target.get("nickname", ""),
                "priority": target.get("priority", ""),
                "chat_url": target["chat_url"],
                "context": target.get("context", ""),
                "final_message": target["final_message"],
                "send_result": "success" if result.get("ok") else "failed",
                "status": result.get("status"),
                "stop_reason": result.get("stop_reason"),
                "started_at": started_at,
                "finished_at": finished_at,
                "run_root": str(target_run),
                "screenshot_path": result.get("screenshot_path", ""),
                "html_path": result.get("html_path", ""),
                "pacing": result.get("pacing", {}),
                "result": result,
            }
            records.append(record)
            with sent_records_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(json.dumps({
                "event": "send_finished",
                "idx": idx,
                "target_id": target_id,
                "ok": result.get("ok"),
                "stop_reason": result.get("stop_reason"),
                "finished_at": finished_at,
            }, ensure_ascii=False), flush=True)
            if args.stop_on_failure and not result.get("ok"):
                break

    summary = {
        "ok": all(record["send_result"] == "success" for record in records) and len(records) == len(targets),
        "run_id": run_id,
        "run_root": str(run_root),
        "planned": len(targets),
        "attempted": len(records),
        "success_count": sum(1 for record in records if record["send_result"] == "success"),
        "failed_count": sum(1 for record in records if record["send_result"] != "success"),
        "targets_path": str(run_root / "targets.json"),
        "sent_records_path": str(sent_records_path),
        "generated_at": now_iso(),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
