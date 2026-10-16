"""Non-streaming /ask runs the synchronous workflow in a worker thread, not on the event loop."""

import asyncio
import threading

from app.api import ask_routes


def test_sync_response_runs_execute_query_in_threadpool(monkeypatch):
    seen = {}

    class _Service:
        def execute_query(self, **kwargs):
            seen["thread"] = threading.current_thread().name
            seen["kwargs"] = kwargs
            return {"success": True, "result": "ok"}

    monkeypatch.setattr(ask_routes, "current_service", lambda: _Service())

    async def go():
        seen["loop_thread"] = threading.current_thread().name
        response = await ask_routes._sync_response("q", 8, {"x": 1}, "t")
        return response

    response = asyncio.run(go())
    assert response.body == b"ok"
    assert seen["kwargs"]["question"] == "q" and seen["kwargs"]["max_steps"] == 8
    assert seen["thread"] != seen["loop_thread"]
