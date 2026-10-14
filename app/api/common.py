"""Helpers shared by the HTTP route modules."""
import logging
import threading
from typing import Iterable, Optional

import anyio
from fastapi.responses import StreamingResponse
from starlette.types import Receive, Scope, Send

# All route modules log under the historical name so existing log filters
# (LOG_FORMAT includes %(name)s) keep matching after the module split.
logger = logging.getLogger("app.api.routes")

STREAM_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def current_service():
    """Return the HolmesService singleton.

    Resolved through ``app.api.routes.get_service`` at call time: that module
    attribute is the long-standing patch seam used by tests.
    """
    from app.api import routes

    return routes.get_service()


def fix_double_encoding(text: str) -> str:
    """
    修复客户端双重 UTF-8 编码的问题

    某些客户端会先 UTF-8 编码，再被错误地当作 Latin-1 解码，
    导致中文变成乱码。这个函数尝试修复这个问题。
    """
    try:
        # 尝试将错误的字符串编码回字节，再用正确的编码解码
        fixed = text.encode('latin-1').decode('utf-8')
        logger.debug("修复了双重编码: %s -> %s", text[:20], fixed[:20])
        return fixed
    except (UnicodeDecodeError, UnicodeEncodeError):
        # 如果修复失败，说明原始数据就是正确的
        return text


class CancellableStreamingResponse(StreamingResponse):
    """StreamingResponse that releases a blocking generator as soon as the response ends.

    On client disconnect Starlette only stops iterating; the sync generator stays
    suspended until garbage collection, so its GeneratorExit handler (which cancels
    the workflow) may never run. Here the cancel event is set and the generator is
    closed explicitly when the response finishes for any reason.
    """

    def __init__(self, content: Iterable[str], *, cancel_event: Optional[threading.Event] = None, **kwargs):
        super().__init__(content, **kwargs)
        self._source = content
        self._cancel_event = cancel_event

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await super().__call__(scope, receive, send)
        finally:
            if self._cancel_event is not None:
                self._cancel_event.set()
            close = getattr(self._source, "close", None)
            if close is not None:
                with anyio.CancelScope(shield=True):
                    try:
                        await anyio.to_thread.run_sync(close)
                    except ValueError:  # generator still executing elsewhere; cancel_event covers it
                        logger.debug("stream generator busy at close", exc_info=True)


def streaming_response(
    body: Iterable[str],
    media_type: str = "text/plain; charset=utf-8",
    cancel_event: Optional[threading.Event] = None,
) -> StreamingResponse:
    """Wrap a text generator with the no-buffering headers every stream uses."""
    return CancellableStreamingResponse(
        body, cancel_event=cancel_event, media_type=media_type, headers=dict(STREAM_HEADERS)
    )
