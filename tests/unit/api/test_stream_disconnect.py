"""Client disconnects must cancel the workflow and close the blocking stream generator."""
import threading
import time

import anyio

from app.api.common import streaming_response


def _run_until_disconnect(response, chunks_before_disconnect=1):
    sent = []
    disconnected = anyio.Event()

    async def receive():
        await disconnected.wait()
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)
        bodies = [m for m in sent if m["type"] == "http.response.body" and m.get("body")]
        if len(bodies) >= chunks_before_disconnect:
            disconnected.set()

    scope = {"type": "http", "asgi": {"spec_version": "2.3"}, "method": "GET", "path": "/ask", "headers": []}

    async def main():
        with anyio.fail_after(10):
            await response(scope, receive, send)

    anyio.run(main)
    return sent


def test_disconnect_sets_cancel_and_closes_generator():
    cancel = threading.Event()
    closed = threading.Event()

    def body():
        try:
            yield "event: run_start\ndata: {}\n\n"
            while not cancel.is_set():  # a long-running workflow emitting heartbeats
                time.sleep(0.05)
                yield "event: heartbeat\ndata: {}\n\n"
        except GeneratorExit:
            closed.set()
            raise

    started = time.monotonic()
    _run_until_disconnect(streaming_response(body(), media_type="text/event-stream", cancel_event=cancel))
    assert cancel.wait(2)
    assert closed.wait(2)
    assert time.monotonic() - started < 5


def test_normal_completion_still_closes_and_signals():
    cancel = threading.Event()

    def body():
        yield "a"
        yield "b"

    sent = _run_until_disconnect(streaming_response(body(), cancel_event=cancel), chunks_before_disconnect=99)
    assert b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body") == b"ab"
    assert cancel.is_set()
