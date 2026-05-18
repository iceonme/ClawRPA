from __future__ import annotations

import random
import time
from dataclasses import dataclass


@dataclass
class WeiboChatSendPolicy:
    min_seconds_per_target: int = 20
    after_open_delay_sec: tuple[int, int] = (5, 7)
    before_send_delay_sec: tuple[int, int] = (1, 5)
    after_send_delay_sec: tuple[int, int] = (5, 10)
    typing_delay_ms: tuple[int, int] = (80, 180)


class WeiboChatPacer:
    def __init__(self, policy: WeiboChatSendPolicy | None = None) -> None:
        self.policy = policy or WeiboChatSendPolicy()
        self._last_target_started_at: float | None = None

    def before_open_chat(self, page) -> dict:
        now = time.monotonic()
        waited = 0.0
        if self._last_target_started_at is not None:
            elapsed = now - self._last_target_started_at
            remaining = self.policy.min_seconds_per_target - elapsed
            if remaining > 0:
                page.wait_for_timeout(int(remaining * 1000))
                waited = remaining
        self._last_target_started_at = time.monotonic()
        return {"waited_ms": int(waited * 1000)}

    def after_open_chat(self, page) -> dict:
        return self._wait(page, self.policy.after_open_delay_sec)

    def before_send_message(self, page) -> dict:
        return self._wait(page, self.policy.before_send_delay_sec)

    def after_send_message(self, page) -> dict:
        return self._wait(page, self.policy.after_send_delay_sec)

    def _wait(self, page, delay_range_sec: tuple[int, int]) -> dict:
        delay_sec = random.uniform(*delay_range_sec)
        page.wait_for_timeout(int(delay_sec * 1000))
        return {"waited_ms": int(delay_sec * 1000)}
