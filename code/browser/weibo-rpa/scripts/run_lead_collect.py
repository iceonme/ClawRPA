#!/usr/bin/env python3
"""Run an ad-hoc weibo lead collection flow."""

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
