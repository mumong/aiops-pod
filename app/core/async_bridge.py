"""Run coroutines from synchronous code without touching the caller's event loop."""

from __future__ import annotations

import asyncio
import concurrent.futures
import threading
from contextlib import AbstractContextManager, nullcontext, suppress
from typing import Awaitable, Callable, Optional, TypeVar

from app.core.log_context import bind_current_context

T = TypeVar("T")

# Extra time the worker gets to unwind after its in-loop timeout cancels the
# coroutine; the caller stops waiting after this even if the worker ignores
# cancellation (e.g. blocked in synchronous I/O).
_CANCEL_GRACE_SECONDS = 5.0
_CANCEL_POLL_SECONDS = 0.5


def run_coroutine_sync(
    factory: Callable[[], Awaitable[T]],
    *,
    timeout: Optional[float] = None,
    worker_context: Optional[Callable[[], AbstractContextManager]] = None,
    thread_name: str = "async-bridge",
) -> T:
    """Run ``factory()`` in a private event loop on a dedicated worker thread.

    On timeout the coroutine is cancelled inside its own loop and
    ``TimeoutError`` is raised; the caller never blocks waiting for a worker
    that refuses to stop.
    """

    async def _bounded() -> T:
        if timeout is None:
            return await factory()
        return await asyncio.wait_for(factory(), timeout)

    def _worker() -> T:
        with (worker_context or nullcontext)():
            return asyncio.run(_bounded())

    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix=thread_name)
    try:
        future = pool.submit(bind_current_context(_worker))
        return future.result(timeout=None if timeout is None else timeout + _CANCEL_GRACE_SECONDS)
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


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
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
                return None
        return task.result()
    finally:
        if not task.done():
            task.cancel()
