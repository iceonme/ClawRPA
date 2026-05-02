"""潜在客户判断流程骨架。"""

from __future__ import annotations

from typing import Any


def judge_candidates(comment_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    comments = comment_rows or []
    return {
        "status": "planned_only",
        "input_comments": len(comments),
        "rule_hits": 0,
        "review_queue": 0,
        "accepted_leads": 0,
    }
