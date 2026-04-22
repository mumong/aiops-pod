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


def test_extract_runbook_accepts_reference_runbooks_without_core():
    test_accuracy = _load_test_accuracy_module()

    text = """
📋 诊断追踪

- **参考 Runbook**: private-k8s-health-reference, l2-oomkilled
- **工具调用**: 20 次
- **LLM 调用**: 4 次
"""

    runbook = test_accuracy.extract_runbook(text)

    assert runbook["core"] is None
    assert runbook["refs"] == ["private-k8s-health-reference", "l2-oomkilled"]
    assert "l2-oomkilled" in runbook["runbook_ids"]


def test_scenario_runbook_match_uses_reference_runbooks_when_core_missing():
    test_accuracy = _load_test_accuracy_module()

    scenario = test_accuracy.ScenarioResult(
        "l2-oomkilled",
        test_accuracy.SCENARIOS["l2-oomkilled"],
    )

    run = {
        "runbook_core": None,
        "runbook_refs": ["private-k8s-health-reference", "l2-oomkilled"],
        "runbook_ids": ["private-k8s-health-reference", "l2-oomkilled"],
    }

    assert scenario._is_runbook_match(run) is True
