"""The process must start with our logging config under uvicorn (12.0.25 crashed on it)."""

import logging
import logging.config

from app.core.log_context import JsonLogFormatter, log_formatter_for_env, uvicorn_log_config


def _snapshot(logger):
    return (list(logger.handlers), logger.level, logger.propagate, logger.disabled)


def _restore(logger, state):
    handlers, level, propagate, disabled = state
    logger.handlers[:] = handlers
    logger.setLevel(level)
    logger.propagate = propagate
    logger.disabled = disabled


def test_dict_config_accepts_uvicorns_use_colors_injection(monkeypatch):
    # dictConfig mutates process-wide logging (root/app/uvicorn); restore it so other
    # tests' caplog still receives app.* records.
    saved = {
        name: _snapshot(logging.getLogger(name))
        for name in ("", "app", "uvicorn", "uvicorn.access")
    }
    try:
        for fmt in ("text", "json"):
            monkeypatch.setenv("AIOPS_LOG_FORMAT", fmt)
            config = uvicorn_log_config("INFO")
            # uvicorn.Config.configure_logging() adds use_colors to the default/access formatters
            config["formatters"]["default"]["use_colors"] = False
            config["formatters"]["access"]["use_colors"] = False
            logging.config.dictConfig(config)  # must not raise
            handler = logging.getLogger("app").handlers[0]
            assert isinstance(handler.formatter, JsonLogFormatter) == (fmt == "json")
        assert isinstance(log_formatter_for_env(use_colors=True), logging.Formatter)
    finally:
        for name, state in saved.items():
            _restore(logging.getLogger(name), state)
