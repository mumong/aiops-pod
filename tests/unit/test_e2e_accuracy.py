import importlib.util
from pathlib import Path

import requests


def _load_test_accuracy_module():
    module_path = (
        Path(__file__).resolve().parents[2] / "test" / "e2e" / "test_accuracy.py"
    )
    spec = importlib.util.spec_from_file_location("test_accuracy_module", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_run_single_request_classifies_stream_read_timeout_and_keeps_partial_body(
    monkeypatch,
    tmp_path,
):
    test_accuracy = _load_test_accuracy_module()

    class _Response:
        status_code = 200

        def iter_content(self, chunk_size=None, decode_unicode=True):
            yield "prefix-chunk\n"
            raise requests.exceptions.ConnectionError("Read timed out.")

    monkeypatch.setattr(
        test_accuracy.requests,
        "get",
        lambda *args, **kwargs: _Response(),
    )

    result = test_accuracy.run_single_request(
        "http://example.com",
        "我的集群有什么问题",
        30,
        1,
        tmp_path,
    )

    saved = (tmp_path / "response_1.md").read_text(encoding="utf-8")

    assert result["success"] is False
    assert "超时" in result["error"]
    assert "prefix-chunk" in saved
    assert "Read timed out" in saved
