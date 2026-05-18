from __future__ import annotations

from src.core.artifacts import ArtifactRecorder
from src.core.errors import stop_reason_for_error
from src.core.human_actions import HumanActionProfile, HumanActor
from src.pages.weibo_chat_page import WeiboChatPage
from src.policies.weibo_chat_policy import WeiboChatPacer, WeiboChatSendPolicy


class WeiboAdapter:
    CHAT_URL_PREFIX = "https://api.weibo.com/chat/#/"

    def __init__(
        self,
        *,
        actor: HumanActor | None = None,
        chat_policy: WeiboChatSendPolicy | None = None,
        pacer: WeiboChatPacer | None = None,
        recorder: ArtifactRecorder | None = None,
    ) -> None:
        self.chat_policy = chat_policy or WeiboChatSendPolicy()
        self.actor = actor or HumanActor(HumanActionProfile(typing_delay_ms=self.chat_policy.typing_delay_ms))
        self.pacer = pacer or WeiboChatPacer(self.chat_policy)
        self.recorder = recorder

    def send_chat_message(self, page, *, chat_url: str, message: str, screenshot_name: str = "after_send.png") -> dict:
        chat_page = WeiboChatPage(page, actor=self.actor)
        pacing = {"before_open_chat": self.pacer.before_open_chat(page)}
        chat_page.open(chat_url)
        pacing["after_open_chat"] = self.pacer.after_open_chat(page)
        if self.recorder:
            self.recorder.event("navigated", url=page.url, title=page.title(), pacing=pacing)

        filled = chat_page.fill_message(message)
        if not filled.get("ok"):
            snapshot = self._snapshot(page, screenshot_name=screenshot_name)
            error_code = filled["error_code"]
            return {
                "ok": False,
                "status": "failed",
                "stop_reason": stop_reason_for_error(error_code),
                "error_code": error_code.value,
                "page_url": page.url,
                "page_title": page.title(),
                "body_excerpt": filled.get("body_excerpt", ""),
                **snapshot,
            }

        if self.recorder:
            self.recorder.event("message_filled", selector=filled["selector"], input_kind=filled["input_kind"])

        pacing["before_send_message"] = self.pacer.before_send_message(page)
        clicked, send_action = chat_page.click_send()
        pacing["after_send_message"] = self.pacer.after_send_message(page)
        snapshot = self._snapshot(page, screenshot_name=screenshot_name)

        if self.recorder:
            self.recorder.event("message_sent", send_action=send_action, page_url=page.url)

        return {
            "ok": True,
            "status": "success",
            "stop_reason": "message_sent",
            "page_url": page.url,
            "page_title": page.title(),
            "input_selector": filled["selector"],
            "input_kind": filled["input_kind"],
            "send_action": send_action,
            "pacing": pacing,
            **snapshot,
        }

    def _snapshot(self, page, *, screenshot_name: str) -> dict[str, str]:
        if not self.recorder:
            return {}
        return self.recorder.snapshot(page, screenshot_name=screenshot_name)
