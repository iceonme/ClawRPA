#!/usr/bin/env python3
"""Filesystem task/run state helpers for weibo-rpa.

Naming / data-flow glossary used across the first task/run framework:

- run_raw_leads:
  Leads captured by the current run before task-level merge.
  Stored in `runs/<run_id>/leads.jsonl` and `leads.csv`.

- run_new_leads:
  Subset of run_raw_leads that are truly new relative to the task-level
  `current_leads` pool. Stored in `runs/<run_id>/new_leads.jsonl` and
  `new_leads.csv`. This is the best handoff set for the next outreach agent.

- current_leads:
  Task-level cumulative working pool. It is incrementally updated after each
  run by merging old pool + current run results with de-dup rules.
  Stored in `<task_dir>/current_leads.jsonl` and `.csv`.

- total_leads:
  A count, not a separate table. It equals `len(current_leads)` after merge.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


TASK_NO_PATTERN = re.compile(r"^task(\d+)_")

ROOT = Path(__file__).resolve().parents[1]
TASKS_ROOT = ROOT / "tasks"
TASK_LIST_PATH = TASKS_ROOT / "task_list.json"
TASK_LOGS_ROOT = TASKS_ROOT / "logs"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def compact_keyword(keyword: str) -> str:
    return re.sub(r"\s+", "", (keyword or "").strip())


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def task_identity(payload: dict) -> tuple[str, str, str]:
    return (
        compact_keyword(payload.get("keyword", "")),
        payload.get("start_date", "") or "",
        payload.get("end_date", "") or "",
    )


def scan_existing_task_history() -> dict[tuple[str, str, str], int]:
    history: dict[tuple[str, str, str], int] = {}
    if not TASKS_ROOT.exists():
        return history

    for task_json_path in TASKS_ROOT.glob("task*/task.json"):
        try:
            payload = read_json(task_json_path, default={})
        except Exception:
            continue
        if not payload:
            continue
        identity = task_identity(payload)
        task_no = int(payload.get("task_no") or 0)
        if not task_no:
            m = TASK_NO_PATTERN.match(task_json_path.parent.name)
            task_no = int(m.group(1)) if m else 0
        if identity[0] and task_no:
            history[identity] = task_no
    return history


def normalize_task_entries(raw: list[dict], *, used_nos: set[int] | None = None, max_no: int = 0) -> tuple[list[dict], set[int], int]:
    history = scan_existing_task_history()
    normalized: list[dict] = []
    used_nos = set(used_nos or set()) | set(history.values())
    max_no = max([max_no, *used_nos], default=0)

    for item in raw:
        payload = dict(item)
        identity = task_identity(payload)
        historical_no = history.get(identity)
        proposed_no = int(payload.get("task_no") or 0)

        if historical_no:
            task_no = historical_no
        else:
            task_no = proposed_no
            if task_no <= 0 or task_no in used_nos:
                max_no += 1
                task_no = max_no
            else:
                max_no = max(max_no, task_no)

        payload["task_no"] = task_no
        used_nos.add(task_no)
        normalized.append(payload)

    return normalized, used_nos, max_no


def normalize_task_list_payload(raw) -> dict:
    if isinstance(raw, list):
        active, _, _ = normalize_task_entries(raw)
        return {"active": active, "inactive": []}

    if not isinstance(raw, dict):
        return {"active": [], "inactive": []}

    active_raw = raw.get("active") or []
    inactive_raw = raw.get("inactive") or []

    active, used_nos, max_no = normalize_task_entries(active_raw)
    inactive, _, _ = normalize_task_entries(inactive_raw, used_nos=used_nos, max_no=max_no)
    return {"active": active, "inactive": inactive}


def flatten_task_list_payload(raw) -> list[dict]:
    normalized = normalize_task_list_payload(raw)
    return list(normalized.get("active") or []) + list(normalized.get("inactive") or [])


def write_json(path: Path, payload) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, payload: dict) -> None:
    ensure_parent(path)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, items: Iterable[dict]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def write_csv(path: Path, items: list[dict]) -> None:
    ensure_parent(path)
    if not items:
        path.write_text("", encoding="utf-8")
        return
    fields = list(items[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(items)


@dataclass
class TaskSpec:
    task_no: int
    keyword: str
    start_date: str
    end_date: str = ""
    enabled: bool = True

    @property
    def task_dirname(self) -> str:
        date_token = (self.start_date or "").replace("-", "")
        return f"task{self.task_no:02d}_{compact_keyword(self.keyword)}{date_token}"

    @property
    def task_id(self) -> str:
        return self.task_dirname

    @property
    def task_dir(self) -> Path:
        return TASKS_ROOT / self.task_dirname

    @classmethod
    def from_dict(cls, payload: dict) -> "TaskSpec":
        return cls(
            task_no=int(payload["task_no"]),
            keyword=payload["keyword"],
            start_date=payload.get("start_date", ""),
            end_date=payload.get("end_date", ""),
            enabled=bool(payload.get("enabled", True)),
        )

    def to_task_json(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_no": self.task_no,
            "keyword": self.keyword,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "enabled": self.enabled,
            "created_at": now_iso(),
        }


def load_task_list() -> list[TaskSpec]:
    raw = read_json(TASK_LIST_PATH, default={"active": [], "inactive": []})
    normalized = normalize_task_list_payload(raw)
    if normalized != raw:
        write_json(TASK_LIST_PATH, normalized)
    return [TaskSpec.from_dict(x) for x in flatten_task_list_payload(normalized)]


def get_task_by_id(task_id: str) -> TaskSpec:
    for spec in load_task_list():
        if spec.task_id == task_id:
            return spec
    raise KeyError(f"task_id not found: {task_id}")


def get_task_by_no(task_no: int) -> TaskSpec:
    for spec in load_task_list():
        if spec.task_no == task_no:
            return spec
    raise KeyError(f"task_no not found: {task_no}")


def ensure_task_structure(spec: TaskSpec) -> dict[str, Path]:
    TASKS_ROOT.mkdir(parents=True, exist_ok=True)
    TASK_LOGS_ROOT.mkdir(parents=True, exist_ok=True)
    task_dir = spec.task_dir
    runs_dir = task_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    task_json_path = task_dir / "task.json"
    status_path = task_dir / "status.json"
    summary_path = task_dir / "task_summary.json"
    task_log_path = task_dir / "task_log.jsonl"
    current_jsonl_path = task_dir / "current_leads.jsonl"
    current_csv_path = task_dir / "current_leads.csv"

    if not task_json_path.exists():
        write_json(task_json_path, spec.to_task_json())
    if not status_path.exists():
        write_json(status_path, {
            "task_id": spec.task_id,
            "status": "active" if spec.enabled else "paused",
            "last_run_at": None,
            "last_successful_run_at": None,
            "latest_run_id": None,
            "run_count": 0,
            "total_leads": 0,
            "new_leads_last_run": 0,
            "updated_leads_last_run": 0,
            "consecutive_no_update_runs": 0,
            "last_stop_reason": None,
            "search_since": None,
            "comment_since": None,
            "updated_at": now_iso(),
        })
    if not summary_path.exists():
        write_json(summary_path, {
            "task_id": spec.task_id,
            "keyword": spec.keyword,
            "status": "active" if spec.enabled else "paused",
            "total_runs": 0,
            "total_leads": 0,
            "last_run_id": None,
            "last_run_status": None,
            "last_run_new_leads": 0,
            "updated_at": now_iso(),
        })
    if not current_jsonl_path.exists():
        current_jsonl_path.write_text("", encoding="utf-8")
    if not current_csv_path.exists():
        current_csv_path.write_text("", encoding="utf-8")

    return {
        "task_dir": task_dir,
        "runs_dir": runs_dir,
        "task_json_path": task_json_path,
        "status_path": status_path,
        "summary_path": summary_path,
        "task_log_path": task_log_path,
        "current_jsonl_path": current_jsonl_path,
        "current_csv_path": current_csv_path,
    }


def lead_identity_key(lead: dict) -> str:
    platform = lead.get("platform", "weibo")
    uid = (lead.get("commenter_unique_id") or "").strip()
    profile = (lead.get("commenter_profile_url") or "").strip()
    nickname = re.sub(r"\s+", "", lead.get("commenter_nickname") or "")
    signal = re.sub(r"\s+", " ", lead.get("signal_text") or "").strip()[:120]
    if uid:
        return f"{platform}|uid|{uid}"
    if profile:
        return f"{platform}|profile|{profile}"
    return f"{platform}|fallback|{nickname}|{signal}"


def signal_strength(lead: dict) -> tuple[int, int, str]:
    evidence = lead.get("evidence") or []
    signal_type = lead.get("signal_type") or ""
    signal_score = len(evidence)
    type_score = 1 if signal_type == "detail_comment" else 0
    captured_at = lead.get("captured_at") or ""
    return signal_score, type_score, captured_at


def merge_lead_pools(old_current_leads: list[dict], run_raw_leads: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Merge task-level lead pool with the latest run.

    Returns:
    - merged_current_leads: updated task pool
    - run_new_leads: leads that are new identities for this task
    - run_updated_leads: existing identities improved by the current run
    """
    merged: dict[str, dict] = {lead_identity_key(x): x for x in old_current_leads}
    run_new_leads: list[dict] = []
    run_updated_leads: list[dict] = []

    for lead in run_raw_leads:
        key = lead_identity_key(lead)
        old = merged.get(key)
        if old is None:
            merged[key] = lead
            run_new_leads.append(lead)
            continue
        if signal_strength(lead) > signal_strength(old):
            merged[key] = lead
            run_updated_leads.append(lead)

    merged_current_leads = sorted(
        merged.values(),
        key=lambda x: (x.get("captured_at") or "", x.get("commenter_nickname") or ""),
        reverse=True,
    )
    return merged_current_leads, run_new_leads, run_updated_leads


def load_status(status_path: Path) -> dict:
    return read_json(status_path, default={})


def log_task_event(task_log_path: Path, event: str, **payload) -> None:
    append_jsonl(task_log_path, {"ts": now_iso(), "event": event, **payload})


def update_task_files(
    *,
    spec: TaskSpec,
    status_path: Path,
    summary_path: Path,
    task_log_path: Path,
    current_jsonl_path: Path,
    current_csv_path: Path,
    run_id: str,
    run_status: str,
    run_started_at: str,
    run_finished_at: str,
    stop_reason: str,
    run_raw_leads: list[dict],
    run_new_leads: list[dict],
    run_updated_leads: list[dict],
    merged_current_leads: list[dict],
) -> None:
    old_status = load_status(status_path)
    no_update_runs = int(old_status.get("consecutive_no_update_runs") or 0)
    no_update_runs = no_update_runs + 1 if not run_new_leads and not run_updated_leads else 0

    new_status = {
        **old_status,
        "task_id": spec.task_id,
        "status": "active" if spec.enabled else "paused",
        "last_run_at": run_started_at,
        "last_successful_run_at": run_finished_at if run_status in {"success", "partial_success"} else old_status.get("last_successful_run_at"),
        "latest_run_id": run_id,
        "run_count": int(old_status.get("run_count") or 0) + 1,
        "total_leads": len(merged_current_leads),
        "new_leads_last_run": len(run_new_leads),
        "updated_leads_last_run": len(run_updated_leads),
        "consecutive_no_update_runs": no_update_runs,
        "last_stop_reason": stop_reason,
        "search_since": run_finished_at if run_status in {"success", "partial_success"} else old_status.get("search_since"),
        "comment_since": run_finished_at if run_status in {"success", "partial_success"} else old_status.get("comment_since"),
        "updated_at": now_iso(),
    }
    write_json(status_path, new_status)

    write_json(summary_path, {
        "task_id": spec.task_id,
        "keyword": spec.keyword,
        "status": new_status["status"],
        "total_runs": new_status["run_count"],
        "total_leads": len(merged_current_leads),
        "last_run_id": run_id,
        "last_run_status": run_status,
        "last_run_raw_leads": len(run_raw_leads),
        "last_run_new_leads": len(run_new_leads),
        "last_run_updated_leads": len(run_updated_leads),
        "updated_at": now_iso(),
    })

    write_jsonl(current_jsonl_path, merged_current_leads)
    write_csv(current_csv_path, merged_current_leads)
    log_task_event(
        task_log_path,
        "run_finished",
        run_id=run_id,
        run_status=run_status,
        stop_reason=stop_reason,
        raw_leads=len(run_raw_leads),
        new_leads=len(run_new_leads),
        updated_leads=len(run_updated_leads),
        total_leads=len(merged_current_leads),
    )
