import asyncio
import threading
import time

import pytest

from app.core.async_bridge import run_coroutine_sync, run_until_cancelled


def test_returns_coroutine_result():
    async def work():
        return 42

    assert run_coroutine_sync(work) == 42


def test_works_while_caller_runs_an_event_loop():
    async def inner():
        return "ok"

    async def outer():
        return run_coroutine_sync(inner)

    assert asyncio.run(outer()) == "ok"


def test_timeout_cancels_coroutine_without_waiting_for_it():
    cancelled = threading.Event()

    async def slow():
        try:
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            cancelled.set()
            raise

    started = time.monotonic()
    with pytest.raises(TimeoutError):
        run_coroutine_sync(slow, timeout=0.2)
    assert time.monotonic() - started < 5
    assert cancelled.wait(2)


def test_worker_context_wraps_execution_in_worker_thread():
    seen = {}

    class _Scope:
        def __enter__(self):
            seen["enter_thread"] = threading.current_thread().name

        def __exit__(self, *exc):
            seen["exited"] = True
            return False

    async def work():
        seen["run_thread"] = threading.current_thread().name

    run_coroutine_sync(work, worker_context=_Scope, thread_name="bridge-test")
    assert seen["enter_thread"] == seen["run_thread"]
    assert seen["run_thread"].startswith("bridge-test")
    assert seen["exited"]


def test_run_until_cancelled_interrupts_a_silent_wait():
    cancel = threading.Event()
    interrupted = threading.Event()

    async def stalled():
        try:
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            interrupted.set()
            raise

    async def main():
        asyncio.get_running_loop().call_later(0.1, cancel.set)
        return await run_until_cancelled(stalled(), cancel, poll_seconds=0.05)

    started = time.monotonic()
    assert asyncio.run(main()) is None
    assert time.monotonic() - started < 2
    assert interrupted.is_set()


def test_run_until_cancelled_returns_result_when_not_cancelled():
    async def work():
        return "done"

    assert asyncio.run(run_until_cancelled(work(), threading.Event())) == "done"
    assert asyncio.run(run_until_cancelled(work(), None)) == "done"
