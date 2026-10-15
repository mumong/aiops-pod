import httpx
import pytest
from openai import APIConnectionError, APIError, APITimeoutError, AuthenticationError

from app.core.aicall.errors import model_transport_message
from app.core.workflow.nodes.request_router import router_failure

REQUEST = httpx.Request("POST", "https://model.invalid/v1/chat/completions")


@pytest.mark.parametrize(
    "message",
    [
        "stream error: stream disconnected before completion: stream closed before response.completed",
        "unexpected EOF",
        "empty_stream",
        "closed before first payload",
    ],
)
def test_model_stream_error_is_readable_and_does_not_expose_raw_error(message):
    exc = APIError(message, request=REQUEST, body=None)
    result = model_transport_message(exc)
    assert "LLM API 服务连接中断" in result
    assert message not in result
    assert router_failure(exc)["code"] == "model_connection"


def test_connection_timeout_and_chained_transport_error():
    assert "无法连接" in model_transport_message(APIConnectionError(request=REQUEST))
    assert "超时" in model_transport_message(APITimeoutError(request=REQUEST))
    wrapper = RuntimeError("workflow failed")
    wrapper.__cause__ = APIError("stream disconnected", request=REQUEST, body=None)
    assert "LLM API" in model_transport_message(wrapper)


def test_browser_tool_or_auth_errors_not_mislabelled_as_model_disconnect():
    assert model_transport_message(RuntimeError("stream disconnected")) is None
    assert model_transport_message(ValueError("kubectl failed")) is None
    response = httpx.Response(401, request=REQUEST)
    assert (
        model_transport_message(AuthenticationError("invalid key", response=response, body=None))
        is None
    )
