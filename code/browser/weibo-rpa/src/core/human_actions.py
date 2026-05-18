from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class HumanActionProfile:
    pre_action_ms: tuple[int, int] = (250, 700)
    post_action_ms: tuple[int, int] = (300, 900)
    typing_delay_ms: tuple[int, int] = (45, 130)
    paste_threshold: int = 200


class HumanActor:
    def __init__(self, profile: HumanActionProfile | None = None) -> None:
        self.profile = profile or HumanActionProfile()

    def pause(self, page, delay_range: tuple[int, int] | None = None) -> int:
        low, high = delay_range or self.profile.post_action_ms
        delay = random.randint(low, high)
        page.wait_for_timeout(delay)
        return delay

    def goto(self, page, url: str, *, wait_until: str = "domcontentloaded", timeout: int = 30000) -> None:
        self.pause(page, self.profile.pre_action_ms)
        page.goto(url, wait_until=wait_until, timeout=timeout)
        self.pause(page)

    def click(self, locator, *, timeout: int = 3000) -> None:
        page = locator.page
        self.pause(page, self.profile.pre_action_ms)
        locator.click(timeout=timeout)
        self.pause(page)

    def fill_text(self, locator, text: str) -> str:
        tag_name = (locator.evaluate("el => el.tagName") or "").lower()
        self.click(locator)
        delay = random.randint(*self.profile.typing_delay_ms)
        if tag_name == "textarea":
            locator.fill("")
            if len(text) <= self.profile.paste_threshold:
                locator.type(text, delay=delay)
                return "textarea:type"
            locator.fill(text)
            return "textarea:fill"

        content_editable = locator.evaluate("el => el.getAttribute('contenteditable') || ''")
        if content_editable:
            locator.evaluate("(el) => { el.innerHTML = ''; el.textContent = ''; }")
            if len(text) <= self.profile.paste_threshold:
                locator.type(text, delay=delay)
                return "contenteditable:type"
            locator.fill(text)
            return "contenteditable:fill"

        locator.fill("")
        locator.type(text, delay=delay)
        return f"{tag_name or 'unknown'}:type"
