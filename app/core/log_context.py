"""Per-run log correlation.

Fields bound with :func:`log_context` (``run``, ``node``, ``lane``) are added
to every log record by :class:`LogContextFilter`, so concurrent runs and
parallel lanes can be told apart. Threads do not inherit context variables;
use :func:`bind_current_context` when handing work to another thread.
"""

from __future__ import annotations

import contextvars
import logging
from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterator, TypeVar

T = TypeVar("T")

_FIELDS = ("run", "node", "lane")
_EMPTY: Dict[str, str] = {}
_context: contextvars.ContextVar[Dict[str, str]] = contextvars.ContextVar("aiops_log_context", default=_EMPTY)

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s -%(log_context)s %(message)s"


@contextmanager
def log_context(**fields: Any) -> Iterator[None]:
    """Bind correlation fields for the current context (nested bindings merge)."""
    values = {key: str(value) for key, value in fields.items() if key in _FIELDS and value}
    token = _context.set({**_context.get(), **values})
    try:
        yield
    finally:
        _context.reset(token)


def bind_current_context(fn: Callable[..., T]) -> Callable[..., T]:
    """Wrap ``fn`` so it runs in a copy of the caller's context (for threads)."""
    ctx = contextvars.copy_context()

    def _run(*args: Any, **kwargs: Any) -> T:
        return ctx.run(fn, *args, **kwargs)

    return _run


class LogContextFilter(logging.Filter):
    """Expose bound fields as ``%(log_context)s`` (e.g. `` [run=ab12 node=layer]``)."""

    def filter(self, record: logging.LogRecord) -> bool:
        current = _context.get()
        parts = [f"{key}={current[key]}" for key in _FIELDS if key in current]
        record.log_context = f" [{' '.join(parts)}]" if parts else ""
        return True
