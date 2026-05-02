"""任务输入结构定义。"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


SUPPORTED_PLATFORMS = {"weibo"}


def _default_task_id() -> str:
    return datetime.now().strftime("task_%Y%m%d_%H%M%S")


@dataclass(slots=True)
class TaskInput:
    event_query: str
    platforms: list[str] = field(default_factory=lambda: ["weibo"])
    search_keywords: list[str] = field(default_factory=list)
    inferred_date: str = ""
    inferred_venue: str = ""
    max_posts_per_platform: int = 30
    max_comments_per_post: int = 100
    max_nested_comments_per_post: int = 30
    max_leads: int = 200
    output_dir: str = "runs"
    task_id: str = field(default_factory=_default_task_id)
    headless: bool = False
    allow_agent_review: bool = True
    notes: dict[str, Any] = field(default_factory=dict)

    @property
    def event_name(self) -> str:
        """Backward-compatible alias for older code/docs."""
        return self.event_query

    def validate(self) -> None:
        if not self.event_query.strip():
            raise ValueError("event_query 不能为空")
        if not self.platforms:
            raise ValueError("platforms 不能为空")
        unknown = [name for name in self.platforms if name not in SUPPORTED_PLATFORMS]
        if unknown:
            raise ValueError(f"不支持的平台: {unknown}")
        if self.max_posts_per_platform <= 0:
            raise ValueError("max_posts_per_platform 必须大于 0")
        if self.max_comments_per_post <= 0:
            raise ValueError("max_comments_per_post 必须大于 0")
        if self.max_nested_comments_per_post < 0:
            raise ValueError("max_nested_comments_per_post 不能小于 0")
        if self.max_leads <= 0:
            raise ValueError("max_leads 必须大于 0")

    def normalized_keywords(self) -> list[str]:
        base = [kw.strip() for kw in self.search_keywords if kw.strip()]
        if self.event_query.strip() not in base:
            base.insert(0, self.event_query.strip())
        return base

    def resolved_output_dir(self) -> Path:
        return Path(self.output_dir).expanduser().resolve()

    def task_root(self) -> Path:
        return self.resolved_output_dir() / self.task_id

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskInput":
        payload = dict(data)
        if "event_name" in payload and "event_query" not in payload:
            payload["event_query"] = payload.pop("event_name")
        obj = cls(**payload)
        obj.validate()
        return obj

    @classmethod
    def from_json_file(cls, path: str | Path) -> "TaskInput":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(payload)
