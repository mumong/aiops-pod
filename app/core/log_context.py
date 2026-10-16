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
_context: contextvars.ContextVar[Dict[str, str]] = contextvars.ContextVar(
    "aiops_log_context", default=_EMPTY
)

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


class JsonLogFormatter(logging.Formatter):
    """One JSON object per line with the bound run/node/lane fields (AIOPS_LOG_FORMAT=json)."""

    def format(self, record: logging.LogRecord) -> str:
        import json

        current = _context.get()
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            **{key: current[key] for key in _FIELDS if key in current},
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def log_formatter_for_env(**_ignored: Any) -> logging.Formatter:
    """Formatter factory for logging.config (`"()"`); uvicorn passes ``use_colors``."""
    import os

    if os.getenv("AIOPS_LOG_FORMAT", "text").strip().lower() == "json":
        return JsonLogFormatter()
    return logging.Formatter(LOG_FORMAT)


def uvicorn_log_config(level_name: str) -> dict:
    """dictConfig for uvicorn that keeps our formatter, context filter and app level."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"()": "app.core.log_context.log_formatter_for_env"},
            "access": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
        },
        "filters": {"log_context": {"()": LogContextFilter}},
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "filters": ["log_context"],
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
            # app.* keeps the user's level after uvicorn's dictConfig
            "app": {"handlers": ["default"], "level": level_name, "propagate": False},
        },
        "root": {"level": level_name, "handlers": ["default"]},
    }


class LogContextFilter(logging.Filter):
    """Expose bound fields as ``%(log_context)s`` (e.g. `` [run=ab12 node=layer]``)."""

    def filter(self, record: logging.LogRecord) -> bool:
        current = _context.get()
        parts = [f"{key}={current[key]}" for key in _FIELDS if key in current]
        record.log_context = f" [{' '.join(parts)}]" if parts else ""
        return True
