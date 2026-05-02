"""线索汇总与落盘流程。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.schemas.lead import Lead
from src.schemas.task_input import TaskInput


OUTPUT_FILES = {
    "leads": "leads.jsonl",
    "review_queue": "review_queue.jsonl",
    "raw_posts": "raw_posts.jsonl",
    "raw_comments": "raw_comments.jsonl",
    "summary": "summary.json",
}


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_task_outputs(
    task: TaskInput,
    task_root: Path,
    leads: list[Lead] | None = None,
    review_queue: list[dict[str, Any]] | None = None,
    raw_posts: list[dict[str, Any]] | None = None,
    raw_comments: list[dict[str, Any]] | None = None,
    extra_summary: dict[str, Any] | None = None,
) -> dict[str, str]:
    task_root.mkdir(parents=True, exist_ok=True)

    lead_rows = [item.to_dict() for item in (leads or [])]
    review_rows = review_queue or []
    post_rows = raw_posts or []
    comment_rows = raw_comments or []

    paths = {name: task_root / filename for name, filename in OUTPUT_FILES.items()}

    _write_jsonl(paths["leads"], lead_rows)
    _write_jsonl(paths["review_queue"], review_rows)
    _write_jsonl(paths["raw_posts"], post_rows)
    _write_jsonl(paths["raw_comments"], comment_rows)

    summary = {
        "mode": "weibo_only_skeleton",
        "task_id": task.task_id,
        "event_query": task.event_query,
        "search_keywords": task.normalized_keywords(),
        "max_posts_per_platform": task.max_posts_per_platform,
        "max_comments_per_post": task.max_comments_per_post,
        "max_nested_comments_per_post": task.max_nested_comments_per_post,
        "max_leads": task.max_leads,
        "allow_agent_review": task.allow_agent_review,
        "counts": {
            "leads": len(lead_rows),
            "review_queue": len(review_rows),
            "raw_posts": len(post_rows),
            "raw_comments": len(comment_rows),
        },
    }
    if extra_summary:
        summary.update(extra_summary)

    paths["summary"].write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {name: str(path) for name, path in paths.items()}
