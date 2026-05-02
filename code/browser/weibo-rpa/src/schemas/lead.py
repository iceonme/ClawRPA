"""微博潜在线索数据结构定义。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(slots=True)
class Lead:
    platform: str = "weibo"
    event_query: str = ""
    normalized_event_name: str = ""
    event_city: str = ""
    inferred_date: str = ""
    inferred_venue: str = ""

    commenter_nickname: str = ""
    commenter_unique_id: str = ""
    commenter_profile_url: str = ""
    commenter_homepage_hint: str = ""

    source_post_id: str = ""
    source_post_url: str = ""
    source_post_title: str = ""
    source_post_author: str = ""
    source_post_published_at: str = ""

    signal_text: str = ""
    signal_type: str = "comment"
    signal_url: str = ""
    signal_published_at: str = ""

    intent_label: str = "普通讨论"
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)
    recommended_action: str = "skip"
    outreach_angle: str = ""
    risk_flags: list[str] = field(default_factory=list)
    needs_agent_review: bool = False
    review_reason: str = ""

    captured_at: str = field(default_factory=_utc_now_iso)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Lead":
        payload = dict(data)
        payload.setdefault("evidence", [])
        payload.setdefault("risk_flags", [])
        payload.setdefault("extra", {})
        return cls(**payload)
