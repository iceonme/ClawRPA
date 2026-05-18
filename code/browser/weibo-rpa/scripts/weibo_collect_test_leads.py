#!/usr/bin/env python3
"""Compatibility entrypoint for the formal weibo lead collector.

The lead implementation now lives in `src.flows.weibo_lead_collect`.
Keep this file temporarily so older commands keep working while the project
settles on `scripts/run_lead_task.py` as the public lead entrypoint.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.flows.weibo_lead_collect import collect_leads, parse_args


def main() -> int:
    result = collect_leads(parse_args())
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
