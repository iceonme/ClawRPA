from __future__ import annotations

from enum import Enum


class ErrorCode(str, Enum):
    LOGIN_REQUIRED = "LOGIN_REQUIRED"
    CHAT_INPUT_NOT_FOUND = "CHAT_INPUT_NOT_FOUND"
    PAGE_LOAD_TIMEOUT = "PAGE_LOAD_TIMEOUT"
    SELECTOR_CHANGED = "SELECTOR_CHANGED"
    UNKNOWN_SITE_ERROR = "UNKNOWN_SITE_ERROR"


def stop_reason_for_error(error_code: ErrorCode) -> str:
    return {
        ErrorCode.LOGIN_REQUIRED: "login_required",
        ErrorCode.CHAT_INPUT_NOT_FOUND: "input_not_found",
        ErrorCode.PAGE_LOAD_TIMEOUT: "timeout",
        ErrorCode.SELECTOR_CHANGED: "selector_changed",
        ErrorCode.UNKNOWN_SITE_ERROR: "exception",
    }[error_code]
