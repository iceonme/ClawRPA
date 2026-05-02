"""任务输出结构定义。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(slots=True)
class PlatformProbeResult:
    platform: str
    ok: bool
    summary: str
    run_dir: str
    artifacts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TaskOutput:
    task_id: str
    event_query: str
    ok: bool
    platform_results: list[PlatformProbeResult] = field(default_factory=list)
    output_root: str = ""
    generated_at: str = field(default_factory=_utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["platform_results"] = [result.to_dict() for result in self.platform_results]
        return data
