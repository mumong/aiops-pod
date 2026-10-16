"""Public model transport errors; presentation only, never retries requests."""

from openai import (
    APIConnectionError,
    APIError,
    APIResponseValidationError,
    APIStatusError,
    APITimeoutError,
    InternalServerError,
)


class ModelStreamInterrupted(RuntimeError):
    """Fatal model transport failure; never a partial successful answer."""

    error_code = "model_disconnected"


class ModelStreamStalled(ModelStreamInterrupted):
    """The model stream went silent while the agent was waiting for model output."""

    error_code = "model_stalled"

    def __init__(self, idle_seconds: float, waiting_on: str = ""):
        self.idle_seconds = idle_seconds
        self.waiting_on = waiting_on
        detail = f"等待「{waiting_on}」" if waiting_on else "等待模型输出"
        super().__init__(
            f"模型服务停滞：{detail}已超过 {idle_seconds:g} 秒未收到任何数据（模型或 LLM 网关无响应），"
            "不是诊断流程卡住。本次运行已终止，已采集内容保留，请稍后重新发起。"
        )


def model_error_code(exc):
    """Stable machine-readable code for the public error event, or None."""
    current = exc
    seen = set()
    for _ in range(5):
        if current is None or id(current) in seen:
            break
        seen.add(id(current))
        if isinstance(current, ModelStreamInterrupted):
            return current.error_code
        if isinstance(current, APITimeoutError):
            return "model_timeout"
        if isinstance(current, APIConnectionError):
            return "model_disconnected"
        current = current.__cause__ or current.__context__
    return None


def raise_on_model_disconnect(exc):
    if isinstance(exc, ModelStreamInterrupted):
        raise exc
    if isinstance(exc, (APITimeoutError, APIResponseValidationError)) or (
        isinstance(exc, APIStatusError) and not isinstance(exc, InternalServerError)
    ):
        return
    message = model_transport_message(exc)
    if message and not isinstance(exc, APITimeoutError):
        raise ModelStreamInterrupted(
            "LLM API 服务连接中断，本次运行已终止。已采集内容保留，请重新发起。"
        ) from exc


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
            return "LLM API 服务响应超时，请稍后重试。"
        if isinstance(current, APIConnectionError):
            return "LLM API 服务连接中断或暂时无法连接，请稍后重试。"
        if isinstance(current, APIError) and any(
            signature in str(current).lower()
            for signature in (
                "stream disconnected",
                "closed before response.completed",
                "unexpected eof",
                "empty_stream",
                "closed before first payload",
                "tls handshake: eof",
            )
        ):
            return "LLM API 服务连接中断，未能完成本次回答，请稍后重试。"
        current = current.__cause__ or current.__context__
    return None


class RepeatLimitReached(RuntimeError):
    """The agent kept issuing one identical tool call past ``max_identical_calls``.

    Raised from the dedup middleware to end the tool loop deterministically; the
    run then delivers from what it already has (structured finalization).
    """

    def __init__(self, tool_name: str, repeats: int, limit: int):
        self.tool_name, self.repeats, self.limit = tool_name, repeats, limit
        super().__init__(
            f"同一工具调用 {tool_name} 已重复 {repeats} 次（上限 {limit}），停止本阶段调查并基于已有结果交付"
        )


class IdleRoundReached(RuntimeError):
    """A whole model round asked only for results it already had.

    Live runs (15d77453575a4ded, 7bdb83277e294cdc): the model's reasoning said
    "evidence complete, now output the structured result", yet the emitted turn
    was a copy of earlier tool calls. A round with zero new information requests
    is the model signalling completion; the loop ends and the stage delivers
    from its material instead of burning rounds on repeat notices.
    """

    def __init__(self, calls: int):
        self.calls = calls
        super().__init__(
            f"本轮 {calls} 个工具调用全部重复了此前已返回的调用，没有新的查询；视为调查完成，基于已有结果交付"
        )


def public_error_text(exc: BaseException) -> str:
    """Error text that may reach users and session history.

    Provider / transport errors (openai, httpx, anything carrying an HTTP status) are
    reduced to the exception class and status, never the provider body. Our own
    errors already carry a safe, meaningful message and are passed through.
    """
    status = getattr(exc, "status_code", None)
    if status is None:
        status = getattr(getattr(exc, "response", None), "status_code", None)
    provider_error = status is not None or type(exc).__module__.split(".")[0] in {
        "openai",
        "httpx",
        "httpcore",
    }
    if not provider_error:
        return str(exc) or type(exc).__name__
    suffix = f"，HTTP {status}" if status else ""
    return f"模型服务请求失败（{type(exc).__name__}{suffix}）"
