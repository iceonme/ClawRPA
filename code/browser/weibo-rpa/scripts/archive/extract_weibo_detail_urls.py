#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

HTML_PATH = Path(r"C:\Projects\CloudPhone\code\browser\lead-discovery\runs\weibo-logged-in-probe\20260419_180731\search.html")


def main() -> int:
    html = HTML_PATH.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(r"https://weibo\.com/\d+/[A-Za-z0-9]+(?:\?[^\"'\s<>]*)?")
    seen: list[str] = []
    for url in pattern.findall(html):
        if url not in seen:
            seen.append(url)
    for url in seen[:120]:
        print(url)
    print(f"COUNT={len(seen)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
