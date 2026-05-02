"""stdout / stderr I/O helpers for lead-discovery.

约定：
- stdout 只输出结构化 JSON 行，供 agent / 调度层消费
- stderr 输出调试日志与错误细节
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any


JsonDict = dict[str, Any]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _compact_json(payload: JsonDict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def emit(payload: JsonDict) -> None:
    """Emit one structured JSON line to stdout."""
    sys.stdout.write(_compact_json(payload) + "\n")
    sys.stdout.flush()


def emit_status(stage: str, message: str, **extra: Any) -> None:
    payload: JsonDict = {
        "type": "status",
        "stage": stage,
        "message": message,
        "ts": utc_now_iso(),
    }
    payload.update(extra)
    emit(payload)


def emit_artifact(name: str, path: str, **extra: Any) -> None:
    payload: JsonDict = {
        "type": "artifact",
        "name": name,
        "path": path,
        "ts": utc_now_iso(),
    }
    payload.update(extra)
    emit(payload)


def emit_result(**extra: Any) -> None:
    payload: JsonDict = {
        "type": "result",
        "ts": utc_now_iso(),
    }
    payload.update(extra)
    emit(payload)


def log_debug(message: str, **extra: Any) -> None:
    payload: JsonDict = {
        "level": "debug",
        "message": message,
        "ts": utc_now_iso(),
    }
    payload.update(extra)
    sys.stderr.write(_compact_json(payload) + "\n")
    sys.stderr.flush()


def log_error(message: str, **extra: Any) -> None:
    payload: JsonDict = {
        "level": "error",
        "message": message,
        "ts": utc_now_iso(),
    }
    payload.update(extra)
    sys.stderr.write(_compact_json(payload) + "\n")
    sys.stderr.flush()
