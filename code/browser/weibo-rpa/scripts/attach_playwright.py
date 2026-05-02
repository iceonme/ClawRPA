#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "attach-playwright"
RUN_ROOT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    port = 9222
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    endpoint = f"http://127.0.0.1:{port}"

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(endpoint)
        contexts = browser.contexts

        payload: dict = {
            "ok": True,
            "endpoint": endpoint,
            "contextCount": len(contexts),
            "contexts": [],
        }

        for idx, context in enumerate(contexts):
            pages_info = []
            for page in context.pages:
                try:
                    title = page.title()
                except Exception:
                    title = ""
                pages_info.append(
                    {
                        "title": title,
                        "url": page.url,
                    }
                )
            payload["contexts"].append(
                {
                    "index": idx,
                    "pageCount": len(context.pages),
                    "pages": pages_info,
                }
            )

        out = RUN_ROOT / f"attach_{port}.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"ok": True, "endpoint": endpoint, "output": str(out)}, ensure_ascii=False))
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
