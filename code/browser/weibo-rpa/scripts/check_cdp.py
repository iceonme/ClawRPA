#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import urllib.request


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    port = 9222
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    version_url = f"http://127.0.0.1:{port}/json/version"
    list_url = f"http://127.0.0.1:{port}/json/list"

    try:
        version = fetch_json(version_url)
        pages = fetch_json(list_url)
    except Exception as exc:
        print(json.dumps({
            "ok": False,
            "port": port,
            "error": str(exc),
            "version_url": version_url,
        }, ensure_ascii=False, indent=2))
        return 1

    result = {
        "ok": True,
        "port": port,
        "version_url": version_url,
        "browser": version.get("Browser"),
        "protocolVersion": version.get("Protocol-Version"),
        "webSocketDebuggerUrl": version.get("webSocketDebuggerUrl"),
        "pageCount": len(pages),
        "pages": [
            {
                "id": p.get("id"),
                "type": p.get("type"),
                "title": p.get("title"),
                "url": p.get("url"),
            }
            for p in pages
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
