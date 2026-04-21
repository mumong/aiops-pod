import os
import sys

import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.federation.client import SubAgentClient
from app.core.federation.registry import SubAgentConfig


class _FakeResponse:
    def __init__(self, text="ok"):
        self.text = text
        self.status_code = 200

    def raise_for_status(self):
        return None


class _FakeStreamResponse:
    def __init__(self, chunks):
        self._chunks = chunks
        self.status_code = 200
        self.text = "".join(chunks)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self):
        return None

    async def aiter_text(self):
        for chunk in self._chunks:
            yield chunk


class _FakeAsyncClient:
    last_post_url = None
    last_stream_url = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, data):
        type(self).last_post_url = url
        return _FakeResponse(text="query-ok")

    def stream(self, method, url, data):
        type(self).last_stream_url = url
        return _FakeStreamResponse(["hello", " world"])


def test_subagent_query_uses_query_endpoint(monkeypatch):
    monkeypatch.setattr("app.core.federation.client.httpx.AsyncClient", _FakeAsyncClient)
    agent = SubAgentConfig(name="cluster-a", url="http://cluster-a", enabled=True)

    result = asyncio.run(
        SubAgentClient().query(
            agent=agent,
            question="查询 CPU",
            endpoint_path="/query",
        )
    )

    assert result.success is True
    assert _FakeAsyncClient.last_post_url == "http://cluster-a/query"


def test_subagent_query_stream_uses_query_endpoint(monkeypatch):
    monkeypatch.setattr("app.core.federation.client.httpx.AsyncClient", _FakeAsyncClient)
    agent = SubAgentConfig(name="cluster-a", url="http://cluster-a", enabled=True)

    result = asyncio.run(
        SubAgentClient().query_stream(
            agent=agent,
            question="查询 CPU",
            endpoint_path="/query",
        )
    )

    assert result.success is True
    assert result.text == "hello world"
    assert _FakeAsyncClient.last_stream_url == "http://cluster-a/query"
