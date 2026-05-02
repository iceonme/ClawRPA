from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


TEXTBOX_SELECTORS = [
    '#webchat-textarea',
    'textarea.editor',
    'textarea',
    'div[contenteditable="true"]',
    '[role="textbox"]',
    'div.woo-input-wrap textarea',
    'div[class*="input"] textarea',
]

SEND_BUTTON_CANDIDATES = [
    {"selector": '.sendbox_bar .send'},
    {"selector": '.sendbox_bar [class*="send"]'},
    {"role": "button", "name": re.compile(r"^(发送|发 送|Send)$", re.I)},
    {"selector": 'button:has-text("发送")'},
    {"selector": 'a:has-text("发送")'},
    {"selector": '[role="button"]:has-text("发送")'},
]


def _append_event(events_path: Path, event: str, **payload: Any) -> None:
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with events_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"event": event, **payload}, ensure_ascii=False) + "\n")


def _find_input(page):
    for selector in TEXTBOX_SELECTORS:
        locator = page.locator(selector).first
        try:
            locator.wait_for(state="visible", timeout=1500)
            return locator, selector
        except Exception:
            continue
    return None, ""


def _fill_message(locator, message: str) -> str:
    tag_name = (locator.evaluate("el => el.tagName") or "").lower()
    if tag_name == "textarea":
        locator.click(timeout=3000)
        locator.fill(message)
        return "textarea"

    content_editable = locator.evaluate("el => el.getAttribute('contenteditable') || ''")
    locator.click(timeout=3000)
    if content_editable:
        locator.evaluate("(el) => { el.innerHTML = ''; el.textContent = ''; }")
        locator.fill(message)
        return "contenteditable"

    locator.click(timeout=3000)
    locator.fill("")
    locator.type(message, delay=35)
    return tag_name or "unknown"


def _click_send(page) -> tuple[bool, str]:
    for candidate in SEND_BUTTON_CANDIDATES:
        try:
            if "role" in candidate:
                locator = page.get_by_role(candidate["role"], name=candidate["name"]).first
            else:
                locator = page.locator(candidate["selector"]).first
            if locator.count() and locator.is_visible(timeout=1200):
                locator.click(timeout=3000)
                return True, str(candidate)
        except Exception:
            continue
    return False, ""


def send_weibo_chat_message(*, chat_url: str, message: str, run_root: str, port: int = 9222, screenshot_name: str = "after_send.png") -> dict[str, Any]:
    run_dir = Path(run_root)
    run_dir.mkdir(parents=True, exist_ok=True)
    events_path = run_dir / "events.jsonl"
    screenshot_path = run_dir / screenshot_name
    html_path = run_dir / "page.html"

    _append_event(events_path, "chat_run_started", chat_url=chat_url, port=port)

    endpoint = f"http://127.0.0.1:{port}"
    result: dict[str, Any] = {
        "ok": False,
        "status": "failed",
        "stop_reason": "unknown",
        "endpoint": endpoint,
        "chat_url": chat_url,
        "message": message,
        "run_root": str(run_dir),
        "screenshot_path": str(screenshot_path),
        "html_path": str(html_path),
    }

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(endpoint)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = None
        for existing_page in context.pages:
            try:
                if existing_page.url.startswith("https://api.weibo.com/chat/#/"):
                    page = existing_page
                    break
            except Exception:
                continue
        if page is None:
            page = context.new_page()
        try:
            page.goto("about:blank", timeout=5000)
            page.goto(chat_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(8000)
            _append_event(events_path, "navigated", url=page.url, title=page.title())

            input_locator, input_selector = _find_input(page)
            if not input_locator:
                body_text = ""
                try:
                    body_text = page.locator("body").inner_text(timeout=1000)[:1200]
                except Exception:
                    pass
                page.screenshot(path=str(screenshot_path), full_page=True)
                html_path.write_text(page.content(), encoding="utf-8")

                stop_reason = "input_not_found"
                if any(token in body_text for token in ["扫描登录", "重新登录", "浏览器缓存发生变更", "还没有微博手机版"]):
                    stop_reason = "login_required"

                _append_event(events_path, "input_not_found", url=page.url, body_excerpt=body_text, stop_reason=stop_reason)
                result.update({
                    "stop_reason": stop_reason,
                    "page_url": page.url,
                    "page_title": page.title(),
                    "body_excerpt": body_text,
                })
                return result

            input_kind = _fill_message(input_locator, message)
            _append_event(events_path, "message_filled", selector=input_selector, input_kind=input_kind)
            page.wait_for_timeout(800)

            clicked, button_used = _click_send(page)
            if not clicked:
                page.keyboard.press("Enter")
                button_used = "keyboard:Enter"
            page.wait_for_timeout(2500)
            page.screenshot(path=str(screenshot_path), full_page=True)
            html_path.write_text(page.content(), encoding="utf-8")

            result.update({
                "ok": True,
                "status": "success",
                "stop_reason": "message_sent",
                "page_url": page.url,
                "page_title": page.title(),
                "input_selector": input_selector,
                "input_kind": input_kind,
                "send_action": button_used,
            })
            _append_event(events_path, "message_sent", send_action=button_used, page_url=page.url)
            return result
        except PlaywrightTimeoutError as exc:
            try:
                page.screenshot(path=str(screenshot_path), full_page=True)
                html_path.write_text(page.content(), encoding="utf-8")
            except Exception:
                pass
            _append_event(events_path, "timeout", error=str(exc))
            result.update({"stop_reason": "timeout", "error": str(exc), "page_url": page.url})
            return result
        except Exception as exc:
            try:
                page.screenshot(path=str(screenshot_path), full_page=True)
                html_path.write_text(page.content(), encoding="utf-8")
            except Exception:
                pass
            _append_event(events_path, "exception", error=str(exc))
            result.update({"stop_reason": "exception", "error": str(exc), "page_url": page.url if 'page' in locals() else ''})
            return result
        finally:
            page.close()
            browser.close()
