#!/usr/bin/env python3
"""weibo-rpa lead 正式任务入口。

当前已切到第一版 task/run 文件系统框架：
- `scripts/run_task.py` 负责单 task 执行
- `scripts/run_task_batch.py` 负责按 `tasks/task_list.json` 顺序调度
- `scripts/weibo_collect_test_leads.py` 负责单次 run 的微博抓取
"""

from run_task import main


if __name__ == "__main__":
    raise SystemExit(main())
