from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from playwright.sync_api import sync_playwright


@dataclass
class BrowserSession:
    port: int = 9222

    @property
    def endpoint(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def __enter__(self) -> "BrowserSession":
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.connect_over_cdp(self.endpoint)
        self.context = self.browser.contexts[0] if self.browser.contexts else self.browser.new_context()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        try:
            self.browser.close()
        finally:
            self._playwright.stop()

    def get_or_create_page(self, url_prefix: str = ""):
        if url_prefix:
            for page in self.context.pages:
                try:
                    if page.url.startswith(url_prefix):
                        return page
                except Exception:
                    continue
        return self.context.new_page()
