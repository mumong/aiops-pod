"""Run coroutines from synchronous code without touching the caller's event loop."""

from __future__ import annotations

import asyncio
import concurrent.futures
import threading
import time
from contextlib import AbstractContextManager, nullcontext
from typing import Awaitable, Callable, Optional, TypeVar

from app.core.log_context import bind_current_context

T = TypeVar("T")

# Extra time the worker gets to unwind after its in-loop timeout cancels the
# coroutine; the caller stops waiting after this even if the worker ignores
# cancellation (e.g. blocked in synchronous I/O).
_CANCEL_GRACE_SECONDS = 5.0
_CANCEL_POLL_SECONDS = 0.5
_OUTCOME_POLL_SECONDS = 0.05


def run_coroutine_sync(
    factory: Callable[[], Awaitable[T]],
    *,
    timeout: Optional[float] = None,
    worker_context: Optional[Callable[[], AbstractContextManager]] = None,
    thread_name: str = "async-bridge",
) -> T:
    """Run ``factory()`` in a private event loop on a dedicated worker thread.

    The outcome is handed to the caller as soon as the coroutine finishes or the
    timeout fires - before the loop's teardown, which waits for cancelled tasks.
    A coroutine slow to honour cancellation (e.g. a stream whose cleanup awaits an
    in-flight HTTP request) therefore never delays the caller; it finishes
    unwinding in the background worker thread.
    """
    outcome: concurrent.futures.Future = concurrent.futures.Future()

    async def _main() -> None:
        try:
            task = asyncio.ensure_future(factory())
            done, _ = await asyncio.wait({task}, timeout=timeout)
            if not done:
                task.cancel()  # do not await: cancellation may be slow
                raise TimeoutError(f"coroutine did not finish within {timeout}s")
            outcome.set_result(task.result())
        except BaseException as exc:  # deliver every outcome, including cancellation
            if not outcome.done():
                outcome.set_exception(exc)

    def _worker() -> None:
        with (worker_context or nullcontext)():
            asyncio.run(_main())

    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix=thread_name)
    try:
        worker = pool.submit(bind_current_context(_worker))
        return _await_outcome(
            outcome, worker, None if timeout is None else timeout + _CANCEL_GRACE_SECONDS
        )
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def _await_outcome(outcome, worker, timeout: Optional[float]):
    """Return the coroutine outcome; surface a worker that failed before producing one
    (e.g. its context manager raised) instead of waiting forever."""
    deadline = None if timeout is None else time.monotonic() + timeout
    while True:
        # Check done() first: the outcome itself may be a TimeoutError, which is the
        # same class as concurrent.futures.TimeoutError.
        concurrent.futures.wait([outcome], timeout=_OUTCOME_POLL_SECONDS)
        if outcome.done():
            return outcome.result()
        try:
            worker.result(timeout=0)
        except concurrent.futures.TimeoutError:
            pass  # worker still running
        else:
            if not outcome.done():
                raise RuntimeError("async bridge worker exited without an outcome")
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError("async bridge worker did not report an outcome in time")


async def run_until_cancelled(
    coro: Awaitable[T],
    cancel_event: Optional[threading.Event],
    *,
    poll_seconds: float = _CANCEL_POLL_SECONDS,
) -> Optional[T]:
    """Await ``coro`` but stop it as soon as ``cancel_event`` is set.

    Cooperative checks inside a stream loop only run when a chunk arrives; this
    watcher also interrupts silent waits (e.g. a stalled model response).
    Returns ``None`` when cancelled.
    """
    task = asyncio.ensure_future(coro)
    if cancel_event is None:
        return await task
    try:
        while not task.done():
            await asyncio.wait({task}, timeout=poll_seconds)
            if cancel_event.is_set() and not task.done():
                task.cancel()  # do not await: a slow-to-cancel stream must not delay the stop
                return None
        return task.result()
    finally:
        if not task.done():
            task.cancel()
