import json
import logging

from app.core.log_context import JsonLogFormatter, log_context, log_formatter_for_env


def test_json_formatter_carries_run_context(monkeypatch):
    record = logging.LogRecord("app.x", logging.WARNING, __file__, 1, "hello %s", ("w",), None)
    with log_context(run="abc123", node="layer"):
        line = JsonLogFormatter().format(record)
    data = json.loads(line)
    assert (
        data["msg"] == "hello w"
        and data["run"] == "abc123"
        and data["node"] == "layer"
        and data["level"] == "WARNING"
    )
    monkeypatch.setenv("AIOPS_LOG_FORMAT", "json")
    assert isinstance(log_formatter_for_env(), JsonLogFormatter)
    monkeypatch.setenv("AIOPS_LOG_FORMAT", "text")
    assert not isinstance(log_formatter_for_env(), JsonLogFormatter)
