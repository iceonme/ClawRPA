from __future__ import annotations

import re

from src.core.errors import ErrorCode
from src.core.human_actions import HumanActor


TEXTBOX_SELECTORS = [
    "#webchat-textarea",
    "textarea.editor",
    "textarea",
    'div[contenteditable="true"]',
    '[role="textbox"]',
    "div.woo-input-wrap textarea",
    'div[class*="input"] textarea',
]

SEND_BUTTON_CANDIDATES = [
    {"selector": ".sendbox_bar .send"},
    {"selector": '.sendbox_bar [class*="send"]'},
    {"role": "button", "name": re.compile(r"^(发送|发 送|Send)$", re.I)},
    {"selector": 'button:has-text("发送")'},
    {"selector": 'a:has-text("发送")'},
    {"selector": '[role="button"]:has-text("发送")'},
]

LOGIN_REQUIRED_TOKENS = [
    "扫码登录",
    "重新登录",
    "浏览器缓存发生变更",
    "还没有微博手机版",
]


class WeiboChatPage:
    def __init__(self, page, actor: HumanActor | None = None) -> None:
        self.page = page
        self.actor = actor or HumanActor()

    def open(self, chat_url: str) -> None:
        self.page.goto("about:blank", timeout=5000)
        self.actor.goto(self.page, chat_url, wait_until="domcontentloaded", timeout=30000)
        self.page.wait_for_timeout(8000)

    def find_input(self):
        for selector in TEXTBOX_SELECTORS:
            locator = self.page.locator(selector).first
            try:
                locator.wait_for(state="visible", timeout=1500)
                return locator, selector
            except Exception:
                continue
        return None, ""

    def fill_message(self, message: str) -> dict:
        locator, selector = self.find_input()
        if not locator:
            body_text = self.body_excerpt()
            error_code = ErrorCode.LOGIN_REQUIRED if self.looks_login_required(body_text) else ErrorCode.CHAT_INPUT_NOT_FOUND
            return {"ok": False, "error_code": error_code, "body_excerpt": body_text}
        input_kind = self.actor.fill_text(locator, message)
        return {"ok": True, "selector": selector, "input_kind": input_kind}

    def click_send(self) -> tuple[bool, str]:
        for candidate in SEND_BUTTON_CANDIDATES:
            try:
                if "role" in candidate:
                    locator = self.page.get_by_role(candidate["role"], name=candidate["name"]).first
                else:
                    locator = self.page.locator(candidate["selector"]).first
                if locator.count() and locator.is_visible(timeout=1200):
                    self.actor.click(locator, timeout=3000)
                    return True, str(candidate)
            except Exception:
                continue
        self.page.keyboard.press("Enter")
        return True, "keyboard:Enter"

    def body_excerpt(self, limit: int = 1200) -> str:
        try:
            return self.page.locator("body").inner_text(timeout=1000)[:limit]
        except Exception:
            return ""

    def looks_login_required(self, body_text: str) -> bool:
        return any(token in body_text for token in LOGIN_REQUIRED_TOKENS)
