from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class RiskProfile:
    pre_send_delay_ms: tuple[int, int] = (3500, 9000)
    post_send_delay_ms: tuple[int, int] = (3000, 7000)


class RiskController:
    def __init__(self, profile: RiskProfile | None = None) -> None:
        self.profile = profile or RiskProfile()

    def before_send_message(self, page, *, target_id: str = "") -> dict:
        delay = random.randint(*self.profile.pre_send_delay_ms)
        page.wait_for_timeout(delay)
        return {"ok": True, "delay_ms": delay, "target_id": target_id}

    def after_send_message(self, page, *, ok: bool) -> dict:
        delay = random.randint(*self.profile.post_send_delay_ms)
        page.wait_for_timeout(delay)
        return {"ok": ok, "delay_ms": delay}
