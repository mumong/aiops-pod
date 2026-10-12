"""Cross-tool contracts: no fixtures depend on one symptom or tool-name branch."""
import json
import random

import pytest

from app.core.aicall.builtin_tools import ReadContextArchiveTool
from app.core.context.budget import estimate_tokens
from app.core.context.evidence_view import (
    build_evidence_view, compact_json, decode_json, encode_json, resolve_pointer,
)
from app.core.context.observation import ObservationProcessor


@pytest.mark.parametrize("value", [None, False, 0, "", [], {}, [0, False, None, "0"],
                                    {"error": "Forbidden", "coverage": "unknown"}])
def test_small_values_exact(value):
    result = build_evidence_view(compact_json(value), "/archive/raw")
    assert result["view_complete"]
    assert compact_json(decode_json(result["data"])) == compact_json(value)


def test_common_fields_lossless_and_collision_safe():
    source = {"common": "user data", "rows": [{"value": 7}], "a/b~c": [
        {"namespace": "same" * 100, "value": i, "ready": False, "missing": None}
        for i in range(100)]}
    encoded = encode_json(source)
    assert encoded["encoding"] == "shared-fields.v1"
    assert decode_json(encoded) == source
    assert len(compact_json(encoded)) < len(compact_json(source)) / 5
    assert resolve_pointer(source, "/a~1b~0c/99/value") == 99


def test_common_field_equality_is_type_sensitive():
    source = [{"common": "x" * 500, "v": v} for v in [1, True, 1.0, 0, False, None]]
    assert compact_json(decode_json(encode_json(source))) == compact_json(source)


def test_random_nested_contracts_roundtrip():
    rng = random.Random(917)

    def value(depth):
        if depth == 0:
            return rng.choice([None, 0, False, "", "异常", "a/b~c", 1.5])
        return rng.choice([
            [value(depth - 1) for _ in range(3)],
            {k: value(depth - 1) for k in ["common", "rows", "value"]},
        ])

    for _ in range(40):
        original = value(3)
        assert compact_json(decode_json(encode_json(original))) == compact_json(original)


@pytest.mark.parametrize("pointer", ["no-slash", "/x~2", "/x~", "/x/01", "/x/-1", "/x/99"])
def test_invalid_pointers_report_error(pointer):
    result = build_evidence_view('{"x":[1]}', "/archive/raw", json_pointer=pointer)
    assert result["status"] == "invalid_pointer"
    assert result["view_complete"] is False


def test_distinct_edges_remain_distinct_even_with_same_relation():
    edges = [{"relation": "owned_by", "source": f"obj-{i}", "target": f"obj-{i + 1}",
              "scope": "cluster" * 400} for i in range(5)]
    result = build_evidence_view(compact_json({"facts": edges}), "/archive/raw")
    assert result["view_complete"]
    assert decode_json(result["data"])["facts"] == edges


def test_pages_reconstruct_exact_source_order_and_duplicates():
    source = [{"id": i, "message": f"{i}:" + "xyz" * 80} for i in range(70)]
    start, reconstructed = 0, []
    while True:
        view = build_evidence_view(compact_json(source), "/archive/raw",
                                   max_tokens=1300, start=start, limit=4)
        assert estimate_tokens(compact_json(view)) <= 1300
        reconstructed.extend(decode_json(row["data"]) for row in view["records"])
        if view["next_start"] is None:
            break
        assert view["next_start"] > start
        start = view["next_start"]
    assert reconstructed == source


def test_oversized_series_is_discoverable_and_samples_readable():
    source = {"status": "success", "data": {"resultType": "matrix", "result": [
        {"metric": {"instance": "node1"}, "values": [[i, str(i)] for i in range(5000)]}]}}
    raw = compact_json(source)
    index = build_evidence_view(raw, "/archive/raw", max_tokens=1400)
    assert not index["view_complete"]
    assert any(row.get("pointer") == "/data" for row in index["records"])
    sample = build_evidence_view(raw, "/archive/raw", json_pointer="/data/result/0/values/4999")
    assert decode_json(sample["data"]) == [4999, "4999"]


def test_late_records_search_and_selected_fields():
    records = [{"id": i, "message": "info", "padding": "x" * 500} for i in range(150)]
    records[-1]["message"] = "distinctive failure then recovery"
    view = build_evidence_view(compact_json(records), "/archive/raw", search="recovery",
                               fields=["/id", "/message", "/not-present"])
    assert not view["view_complete"]
    assert view["search_complete"]
    assert len(view["records"]) == 1
    record = decode_json(view["records"][0]["data"])
    assert record["/id"]["value"] == 149
    assert record["/not-present"] == {"missing": True}


def test_consecutive_text_folding_preserves_error_recovery_order():
    raw = "ok\r\n" * 1000 + "ERROR\n" * 5 + "recovered\n" + "ok\n" * 3
    view = build_evidence_view(raw, "/archive/raw")
    assert view["view_complete"]
    restored = "".join(run["line"] * run["repeat"] for run in view["data"]["runs"])
    assert restored == raw


def test_bad_json_stays_text_not_empty_data():
    raw = '{"status":"error", bad json\n' * 500
    view = build_evidence_view(raw, "/archive/raw")
    assert view["source_format"] == "text"
    assert view["data"]["runs"][0]["line"] == raw.splitlines(keepends=True)[0]


def test_large_scalar_exact_segments():
    original = "memory\n异常🧪" * 1000
    raw = compact_json({"large": original})
    offset, parts = 0, []
    while True:
        view = build_evidence_view(raw, "/archive/raw", json_pointer="/large",
                                   start=offset, max_tokens=900)
        assert estimate_tokens(compact_json(view)) <= 900
        parts.append(view["data"])
        if view["next_start"] is None:
            break
        assert view["next_start"] > offset
        offset = view["next_start"]
    assert "".join(parts) == original


@pytest.mark.parametrize("name", ["custom_new_tool", "query_pod_lifecycle", "kubectl_logs",
                                  "query_pod_topology", "execute_prometheus_range_query"])
def test_new_mode_all_tool_names_same_raw_archive(tmp_path, name):
    raw = compact_json({"items": [{"id": i, "shared": "same" * 300} for i in range(90)]})
    processor = ObservationProcessor(archive_root=str(tmp_path), evidence_view_mode="compact")
    result = processor.process("r", "query_collect", 1, name, raw, preserve_raw=True)
    assert result["processor"] == "generic_evidence_view.v1"
    from pathlib import Path
    assert Path(result["raw_ref"]).read_text() == raw
    assert decode_json(json.loads(result["summary"])["data"]) == json.loads(raw)


def test_reader_schema_and_path_safety(tmp_path):
    root = tmp_path / "archive"
    root.mkdir()
    path = root / "tool.raw.txt"
    path.write_text('{"nested":{"value":0}}')
    tool = ReadContextArchiveTool(allowed_roots=[str(root)])
    data = json.loads(tool.invoke({"archive_path": str(path), "view": "compact",
                                  "json_pointer": "/nested"}))
    assert decode_json(data["data"]) == {"value": 0}
    outside = tmp_path / "outside"
    outside.write_text("not allowed")
    (root / "symlink").symlink_to(outside)
    assert "not under allowed" in tool._run(str(root / "symlink"), view="compact")
    assert "not found" in tool._run(str(root / "missing"), view="compact")


def test_explicit_archive_reads_never_reprojected(tmp_path):
    raw = "x" * 50000
    p = ObservationProcessor(archive_root=str(tmp_path), evidence_view_mode="compact")
    assert p.process("r", "evidence", 1, "read_context_archive", raw, preserve_raw=True)["summary"] == raw


def test_mode_disabled_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("AIOPS_EVIDENCE_VIEW_MODE", raising=False)
    assert ObservationProcessor(archive_root=str(tmp_path)).evidence_view_mode == "legacy"


def test_recent_termination_search_not_health_filter():
    pods = [{"name": f"pod-{i}", "phase": "Running", "ready": True,
             "last": None, "details": "x" * 400} for i in range(100)]
    pods[-1]["last"] = {"reason": "OOMKilled", "within_window": True, "recent_count": None}
    result = build_evidence_view(compact_json({"pods": pods}), "/archive/raw",
                                 json_pointer="/pods", search="OOMKilled")
    assert result["search_complete"]
    assert decode_json(result["records"][0]["data"])["name"] == "pod-99"


def test_oversized_keys_and_selectors_fail_explicitly_not_loop():
    result = build_evidence_view(compact_json({"k" * 10000: "value"}), "/archive/raw",
                                 max_tokens=512)
    assert result["status"] == "view_budget_too_small"
    assert estimate_tokens(compact_json(result)) <= 512
    result = build_evidence_view("{}", "/archive/raw", search="x" * 10000)
    assert result["status"] == "invalid_selector"


def test_minimum_budget_on_many_shapes():
    sources = [list(range(1000)), {str(i): "v" * 500 for i in range(100)},
               "日志\n" * 4000, "!" * 20000,
               [{"id": i, "values": list(range(500))} for i in range(50)]]
    for source in sources:
        for budget in [512, 800, 4096]:
            result = build_evidence_view(compact_json(source), "/archive/raw", max_tokens=budget)
            assert estimate_tokens(compact_json(result)) <= budget


def test_parallel_archive_isolation(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from pathlib import Path

    p = ObservationProcessor(archive_root=str(tmp_path), evidence_view_mode="compact")

    def run(i):
        raw = compact_json({"id": i, "items": list(range(3000))})
        return raw, p.process("parallel", f"group-{i}", 1, "unknown_tool", raw)

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, range(12)))
    assert len({r["raw_ref"] for _, r in results}) == 12
    for raw, result in results:
        assert Path(result["raw_ref"]).read_text() == raw


@pytest.mark.parametrize("raw", ['{"value":1,"value":2}', '{"v":NaN}',
                                '{"v":"\\ud800"}', '[1e400]'])
def test_ambiguous_or_nonstandard_json_retained_as_text(raw):
    result = build_evidence_view(raw, "/archive/raw")
    assert result["source_format"] == "text"
    assert "".join(r["line"] * r["repeat"] for r in result["data"]["runs"]) == raw


def test_long_metadata_respects_budget():
    result = build_evidence_view('{"x":"' + 'q' * 10000 + '"}', "/" + "a" * 2000,
                                 json_pointer="/x", max_tokens=512)
    assert estimate_tokens(compact_json(result)) <= 512
    assert result["status"] == "view_budget_too_small"


def test_collection_schema_and_plain_field_names():
    payload = {"objects": [{"name": f"n{i}", "a/b": False, "large": str(i) + "x" * 10000}
                           for i in range(10)]}
    raw = compact_json(payload)
    view = build_evidence_view(raw, "/archive/raw")
    assert view["datasets"][0]["item_fields"] == ["name", "a/b", "large"]
    subset = build_evidence_view(raw, "/archive/raw", json_pointer="/objects",
                                 fields=["name", "a/b", "/a~1b"], search="n9")
    assert decode_json(subset["records"][0]["data"]) == {
        "name": {"value": "n9"}, "a/b": {"value": False}, "/a~1b": {"value": False}}


@pytest.mark.parametrize("payload,success", [
    ({"status": "error", "error": "Forbidden"}, False),
    ({"ok": False, "error": "timeout", "coverage": "unknown"}, False),
    ({"success": False, "stdout": "", "returncode": 1}, False),
    ({"status": "success", "data": {"resultType": "vector", "result": []}}, True),
    ({"status": "success", "resource": {"status": "failed", "ready": False}}, True),
])
def test_generic_execution_signals_not_resource_health(tmp_path, payload, success):
    p = ObservationProcessor(archive_root=str(tmp_path), evidence_view_mode="compact")
    result = p.process("r", "query_collect", 1, "previously_unseen_tool", compact_json(payload))
    assert result["semantic_success"] is success
    assert json.loads(result["summary"]) == payload


def test_fields_on_single_object_select_that_objects_fields():
    raw = compact_json({"outer": {"metric": {"instance": "node"}, "values": [0, False, None]}})
    view = build_evidence_view(raw, "/archive/raw", json_pointer="/outer",
                               fields=["metric", "/values", "missing"])
    assert view["unit"] == "selected_field"
    assert [(r["pointer"], decode_json(r["data"])) for r in view["records"][:2]] == [
        ("/outer/metric", {"instance": "node"}), ("/outer/values", [0, False, None])]
    assert view["records"][2] == {"index": 2, "pointer": "/outer/missing", "missing": True}


def test_roll_back_mode_restores_reader_schema_and_description(monkeypatch):
    from app.core.aicall.builtin_tools import get_builtin_tools

    monkeypatch.setenv("AIOPS_EVIDENCE_VIEW_MODE", "compact")
    tool = next(t for t in get_builtin_tools() if t.name == "read_context_archive")
    assert "json_pointer" in tool.get_input_schema().model_json_schema()["properties"]
    monkeypatch.setenv("AIOPS_EVIDENCE_VIEW_MODE", "legacy")
    tool = next(t for t in get_builtin_tools() if t.name == "read_context_archive")
    assert set(tool.get_input_schema().model_json_schema()["properties"]) == {"archive_path", "offset", "length"}
    assert "json_pointer" not in tool.description


@pytest.mark.parametrize("raw", [
    '{"status":"success","pods":[]}',
    '{"contract_version":"pod-lifecycle.v1","status":"success","pods":"invalid"}',
    '{"contract_version":"pod-lifecycle.v1","status":"success","pods":[]}',
    '{"status":"error","error":"Forbidden"}',
    'not json', '[]',
])
def test_display_mode_preserves_existing_producer_validation(tmp_path, raw):
    legacy = ObservationProcessor(archive_root=str(tmp_path), evidence_view_mode="legacy").process(
        "legacy", "evidence", 1, "query_pod_lifecycle", raw, preserve_raw=True)
    compact = ObservationProcessor(archive_root=str(tmp_path), evidence_view_mode="compact").process(
        "compact", "evidence", 1, "query_pod_lifecycle", raw, preserve_raw=True)
    assert compact["semantic_success"] == legacy["semantic_success"]
    assert compact["structured"]["parse_status"] == legacy["structured"]["parse_status"]
    assert compact["summary"] == legacy["summary"] == raw
