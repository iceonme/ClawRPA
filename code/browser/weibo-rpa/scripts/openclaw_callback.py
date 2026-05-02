#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _build_message(payload: dict[str, Any], prompt: str = "") -> str:
    lines = [
        "任务已跑完。",
        f"- task_id: {payload.get('task_id', '')}",
        f"- run_id: {payload.get('run_id', '')}",
        f"- status: {payload.get('status', '')}",
        f"- stop_reason: {payload.get('stop_reason', '')}",
        f"- run_raw_leads: {payload.get('run_raw_leads', 0)}",
        f"- run_new_leads: {payload.get('run_new_leads', 0)}",
        f"- run_updated_leads: {payload.get('run_updated_leads', 0)}",
        f"- total_leads: {payload.get('total_leads', 0)}",
        f"- task_summary_path: {payload.get('task_summary_path', '')}",
        f"- current_leads_path: {payload.get('current_leads_path', '')}",
    ]
    if prompt:
        lines.extend(["", prompt])
    return "\n".join(lines)


def resolve_openclaw_bin(preferred: str = "openclaw") -> str:
    candidates = [preferred, "openclaw", "openclaw.cmd", "openclaw.exe"]
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return preferred


def notify_session(*, session_id: str, payload: dict[str, Any], prompt: str = "已经跑完，请检验结果并进入下一步。", openclaw_bin: str = "openclaw", agent_timeout_sec: int = 120) -> subprocess.CompletedProcess[str] | None:
    if not session_id:
        return None
    message = _build_message(payload, prompt=prompt)
    cmd = [
        resolve_openclaw_bin(openclaw_bin),
        "agent",
        "--session-id",
        session_id,
        "--message",
        message,
        "--timeout",
        str(agent_timeout_sec),
        "--json",
    ]
    try:
        return subprocess.run(cmd, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=max(agent_timeout_sec + 30, 60))
    except FileNotFoundError:
        return subprocess.CompletedProcess(cmd, 127, stdout="", stderr="openclaw executable not found")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a finish callback into an OpenClaw session")
    parser.add_argument("--session-id", default="")
    parser.add_argument("--prompt", default="已经跑完，请检验结果并进入下一步。")
    parser.add_argument("--payload-json", default="", help="inline JSON payload")
    parser.add_argument("--payload-path", default="", help="JSON file path")
    parser.add_argument("--openclaw-bin", default="openclaw")
    parser.add_argument("--agent-timeout", type=int, default=120)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload: dict[str, Any] = {}
    if args.payload_json:
        payload = json.loads(args.payload_json)
    elif args.payload_path:
        payload = json.loads(Path(args.payload_path).read_text(encoding="utf-8"))
    result = notify_session(session_id=args.session_id, payload=payload, prompt=args.prompt, openclaw_bin=args.openclaw_bin, agent_timeout_sec=args.agent_timeout)
    if result is None:
        print(json.dumps({"ok": False, "reason": "missing_session_id"}, ensure_ascii=False))
        return 2
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    print(json.dumps({"ok": result.returncode == 0, "returncode": result.returncode, "stdout": stdout, "stderr": stderr}, ensure_ascii=False, indent=2))
    return 0 if result.returncode == 0 else result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
