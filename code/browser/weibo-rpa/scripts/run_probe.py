#!/usr/bin/env python3
"""lead-discovery 探针入口。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.io_protocol import emit_artifact, emit_result, emit_status, log_debug, log_error
from src.probes.weibo_probe import run as run_weibo_probe
from src.probes.xhs_probe import run as run_xhs_probe
from src.schemas.task_input import TaskInput
from src.schemas.task_output import TaskOutput


PROBE_RUNNERS = {
    "weibo": run_weibo_probe,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run lead-discovery platform probes.")
    parser.add_argument("--input", required=True, help="任务输入 JSON 文件路径")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        task = TaskInput.from_json_file(args.input)
        task_root = task.task_root()
        task_root.mkdir(parents=True, exist_ok=True)

        emit_status("bootstrap", "probe 任务已启动", task_id=task.task_id, event_query=task.event_query)
        log_debug("task input loaded", input_path=args.input, task_root=str(task_root))

        input_copy_path = task_root / "task_input.json"
        input_copy_path.write_text(json.dumps(task.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        emit_artifact("task_input", str(input_copy_path))

        platform_results = []
        for platform in task.platforms:
            emit_status(f"probe_{platform}", f"开始执行 {platform} probe")
            platform_dir = task_root / platform
            result = PROBE_RUNNERS[platform](task, platform_dir)
            platform_results.append(result)
            for artifact_path in result.artifacts:
                emit_artifact(f"{platform}_artifact", artifact_path, platform=platform)
            emit_status(
                f"probe_{platform}",
                f"{platform} probe 完成",
                ok=result.ok,
                warnings=len(result.warnings),
            )

        task_output = TaskOutput(
            task_id=task.task_id,
            event_query=task.event_query,
            ok=all(item.ok for item in platform_results),
            platform_results=platform_results,
            output_root=str(task_root),
        )
        result_path = task_root / "probe_result.json"
        result_path.write_text(json.dumps(task_output.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        emit_artifact("probe_result", str(result_path))
        emit_result(
            ok=task_output.ok,
            task_id=task.task_id,
            platform_count=len(platform_results),
            output_path=str(result_path),
        )
        return 0
    except Exception as exc:
        log_error("probe run failed", error=str(exc))
        emit_result(ok=False, error=str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
