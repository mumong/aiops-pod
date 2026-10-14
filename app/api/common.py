"""Helpers shared by the HTTP route modules."""
import logging
from typing import Iterable

from fastapi.responses import StreamingResponse

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


def streaming_response(body: Iterable[str], media_type: str = "text/plain; charset=utf-8") -> StreamingResponse:
    """Wrap a text generator with the no-buffering headers every stream uses."""
    return StreamingResponse(body, media_type=media_type, headers=dict(STREAM_HEADERS))
