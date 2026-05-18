from __future__ import annotations

from pathlib import Path
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from src.adapters.weibo_adapter import WeiboAdapter
from src.core.artifacts import ArtifactRecorder
from src.core.errors import ErrorCode, stop_reason_for_error
from src.core.session import BrowserSession


def _base_result(*, endpoint: str, chat_url: str, message: str, run_dir: Path, screenshot_name: str) -> dict[str, Any]:
    return {
        "ok": False,
        "status": "failed",
        "stop_reason": "unknown",
        "endpoint": endpoint,
        "chat_url": chat_url,
        "message": message,
        "run_root": str(run_dir),
        "screenshot_path": str(run_dir / screenshot_name),
        "html_path": str(run_dir / "page.html"),
    }


def send_weibo_chat_message(
    *,
    chat_url: str,
    message: str,
    run_root: str,
    port: int = 9222,
    screenshot_name: str = "after_send.png",
) -> dict[str, Any]:
    """Send one Weibo chat message through the layered browser stack.

    Public signature is kept stable for `scripts/run_chat_task.py`.
    """
    run_dir = Path(run_root)
    recorder = ArtifactRecorder(run_dir)
    session_config = BrowserSession(port=port)
    result = _base_result(
        endpoint=session_config.endpoint,
        chat_url=chat_url,
        message=message,
        run_dir=run_dir,
        screenshot_name=screenshot_name,
    )
    recorder.event("chat_run_started", chat_url=chat_url, port=port)

    page = None
    try:
        with BrowserSession(port=port) as session:
            page = session.get_or_create_page(WeiboAdapter.CHAT_URL_PREFIX)
            adapter = WeiboAdapter(recorder=recorder)
            send_result = adapter.send_chat_message(
                page,
                chat_url=chat_url,
                message=message,
                screenshot_name=screenshot_name,
            )
            result.update(send_result)
            return result
    except PlaywrightTimeoutError as exc:
        recorder.event("timeout", error=str(exc))
        result.update({
            "stop_reason": stop_reason_for_error(ErrorCode.PAGE_LOAD_TIMEOUT),
            "error_code": ErrorCode.PAGE_LOAD_TIMEOUT.value,
            "error": str(exc),
            "page_url": page.url if page else "",
        })
        _try_snapshot(recorder, page, result, screenshot_name=screenshot_name)
        return result
    except Exception as exc:
        recorder.event("exception", error=str(exc), error_type=type(exc).__name__)
        result.update({
            "stop_reason": stop_reason_for_error(ErrorCode.UNKNOWN_SITE_ERROR),
            "error_code": ErrorCode.UNKNOWN_SITE_ERROR.value,
            "error": str(exc),
            "page_url": page.url if page else "",
        })
        _try_snapshot(recorder, page, result, screenshot_name=screenshot_name)
        return result
    finally:
        try:
            if page:
                page.close()
        except Exception:
            pass


def _try_snapshot(recorder: ArtifactRecorder, page, result: dict[str, Any], *, screenshot_name: str) -> None:
    if not page:
        return
    try:
        result.update(recorder.snapshot(page, screenshot_name=screenshot_name))
    except Exception:
        pass
