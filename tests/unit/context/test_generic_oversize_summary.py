"""Any large tool result is bounded for the model; raw stays archived."""

import json

from app.core.context.observation import ObservationProcessor


def test_unlisted_large_tool_output_is_capped_with_omission_and_readback_hint(tmp_path):
    raw = json.dumps({"discoveredLabels": {f"label_{i}": "x" * 40 for i in range(600)}}, indent=2)
    assert len(raw) > 20000
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=3000)
    result = processor.process(
        run_id="r",
        node_id="query_collect",
        sequence=1,
        tool_name="get_prometheus_target",
        raw_content=raw,
    )
    assert result["summary_chars"] < 3500
    assert "省略" in result["summary"] and "read_context_archive" in result["summary"]
    assert result["raw_ref"].endswith(".raw.txt")
    assert open(result["raw_ref"], encoding="utf-8").read() == raw


def test_small_unlisted_output_still_passes_through(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=3000)
    result = processor.process(
        run_id="r",
        node_id="query_collect",
        sequence=2,
        tool_name="get_prometheus_target",
        raw_content='{"ok":true}',
    )
    assert result["summary"].startswith('{"ok":true}')
