"""微博搜索流程骨架。"""

from __future__ import annotations

from typing import Any

from src.schemas.task_input import TaskInput


def plan_search(task: TaskInput) -> dict[str, Any]:
    keywords = task.normalized_keywords()
    return {
        "platform": "weibo",
        "event_query": task.event_query,
        "keywords": keywords,
        "limits": {
            "max_posts_per_platform": task.max_posts_per_platform,
            "max_comments_per_post": task.max_comments_per_post,
            "max_nested_comments_per_post": task.max_nested_comments_per_post,
            "max_leads": task.max_leads,
        },
        "status": "planned_only",
    }
