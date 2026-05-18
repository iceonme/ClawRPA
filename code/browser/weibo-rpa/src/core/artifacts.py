from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ArtifactRecorder:
    def __init__(self, run_root: str | Path) -> None:
        self.run_dir = Path(run_root)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.run_dir / "events.jsonl"

    def event(self, event: str, **payload: Any) -> None:
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"event": event, **payload}, ensure_ascii=False) + "\n")

    def snapshot(self, page, *, screenshot_name: str = "after_send.png", html_name: str = "page.html") -> dict[str, str]:
        screenshot_path = self.run_dir / screenshot_name
        html_path = self.run_dir / html_name
        page.screenshot(path=str(screenshot_path), full_page=True)
        html_path.write_text(page.content(), encoding="utf-8")
        return {"screenshot_path": str(screenshot_path), "html_path": str(html_path)}
