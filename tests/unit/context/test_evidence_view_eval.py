"""Evaluation infrastructure must not silently substitute or overclaim evidence."""
import json

import pytest

from scripts.evaluate_evidence_view import archive_reader, cases, validate_answer
from app.core.aicall.builtin_tools import LegacyReadContextArchiveTool, ReadContextArchiveTool


def test_missing_requested_fixture_fails_instead_of_silently_skipping(tmp_path):
    with pytest.raises(FileNotFoundError, match="topology"):
        cases(tmp_path, {"topology"})
    assert [c["name"] for c in cases(tmp_path, {"small"})] == ["small"]
    with pytest.raises(ValueError, match="Unknown cases"):
        cases(tmp_path, {"misspelled"})


@pytest.mark.parametrize("mode,tool_type", [("legacy", LegacyReadContextArchiveTool),
                                            ("raw", LegacyReadContextArchiveTool),
                                            ("compact", ReadContextArchiveTool)])
def test_actual_production_tool_contract_used(mode, tool_type, tmp_path):
    tool = archive_reader(mode, tmp_path)
    expected = tool_type(allowed_roots=[str(tmp_path)])
    assert tool.description == expected.description
    assert tool.get_input_schema().model_json_schema() == expected.get_input_schema().model_json_schema()


@pytest.mark.parametrize("value", ["all expected keywords but not JSON", {"answer": "done"}, None])
def test_keyword_matches_do_not_make_an_answer_contract_valid(value):
    _, valid = validate_answer(value)
    assert not valid


def test_valid_output_checked_against_application_contract():
    value = {"intent": "list", "scope": "ns", "status": "answered", "answer": "one Pod"}
    normalized, valid = validate_answer(value)
    assert valid
    assert normalized["missing"] == []
    normalized_json, valid = validate_answer(json.dumps(value))
    assert valid and normalized_json == normalized
