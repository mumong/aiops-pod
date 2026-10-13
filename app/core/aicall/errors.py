"""Public model transport errors; presentation only, never retries requests."""
from openai import APIError, APIConnectionError, APITimeoutError, APIStatusError, InternalServerError, APIResponseValidationError


class ModelStreamInterrupted(RuntimeError):
    """Fatal model transport failure; never a partial successful answer."""


def raise_on_model_disconnect(exc):
    if isinstance(exc, ModelStreamInterrupted):
        raise exc
    if isinstance(exc, (APITimeoutError, APIResponseValidationError)) or (
        isinstance(exc, APIStatusError) and not isinstance(exc, InternalServerError)
    ):
        return
    message = model_transport_message(exc)
    if message and not isinstance(exc, APITimeoutError):
        raise ModelStreamInterrupted('LLM API 服务连接中断，本次运行已终止。已采集内容保留，请重新发起。') from exc


def model_transport_message(exc):
    current = exc
    seen = set()
    for _ in range(5):
        if current is None or id(current) in seen:
            break
        seen.add(id(current))
        if isinstance(current, ModelStreamInterrupted):
            return str(current)
        if isinstance(current, APITimeoutError):
            return 'LLM API 服务响应超时，请稍后重试。'
        if isinstance(current, APIConnectionError):
            return 'LLM API 服务连接中断或暂时无法连接，请稍后重试。'
        if isinstance(current, APIError) and any(signature in str(current).lower() for signature in (
            'stream disconnected', 'closed before response.completed',
            'unexpected eof', 'empty_stream', 'closed before first payload',
        )):
            return 'LLM API 服务连接中断，未能完成本次回答，请稍后重试。'
        current = current.__cause__ or current.__context__
    return None
