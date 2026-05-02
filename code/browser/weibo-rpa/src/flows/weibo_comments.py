"""微博评论提取流程骨架。"""

from __future__ import annotations

from typing import Any


def plan_comment_collection(post_records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    posts = post_records or []
    return {
        "status": "planned_only",
        "post_count": len(posts),
        "comment_targets": [item.get("source_post_url", "") for item in posts if item.get("source_post_url")],
    }
