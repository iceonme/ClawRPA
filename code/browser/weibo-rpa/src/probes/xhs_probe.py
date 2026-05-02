"""小红书探针实现（第一版底座）。"""

from __future__ import annotations

import json
from pathlib import Path

from src.core.io_protocol import log_debug
from src.schemas.task_input import TaskInput
from src.schemas.task_output import PlatformProbeResult


def run(task: TaskInput, run_dir: Path) -> PlatformProbeResult:
    run_dir.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = ["当前仅完成 probe 底座，尚未执行真实小红书页面探测。"]
    checks = {
        "event_query": task.event_query,
        "max_posts_per_platform": task.max_posts_per_platform,
        "max_comments_per_post": task.max_comments_per_post,
    }

    playwright_importable = False
    try:
        import playwright  # type: ignore  # noqa: F401

        playwright_importable = True
    except Exception as exc:  # pragma: no cover - best effort env check
        warnings.append(f"Playwright 未就绪或不可导入: {exc}")

    checks["playwright_importable"] = playwright_importable

    probe_report = {
        "platform": "xiaohongshu",
        "probe_type": "skeleton",
        "status": "ready_for_real_navigation" if playwright_importable else "dependency_missing",
        "checks": checks,
        "warnings": warnings,
    }
    report_path = run_dir / "probe_report.json"
    report_path.write_text(json.dumps(probe_report, ensure_ascii=False, indent=2), encoding="utf-8")

    log_debug("xiaohongshu probe prepared", run_dir=str(run_dir), playwright_importable=playwright_importable)

    return PlatformProbeResult(
        platform="xiaohongshu",
        ok=True,
        summary="小红书 probe 底座已运行，已完成依赖探测与报告落盘。",
        run_dir=str(run_dir),
        artifacts=[str(report_path)],
        warnings=warnings,
        checks=checks,
    )
