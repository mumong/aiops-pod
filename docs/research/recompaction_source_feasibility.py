"""Offline helper-level audit: not an end-to-end Agent or loss benchmark.

Only extracts two actual methods. Token fitting is deliberately stubbed to
isolate source-preview behaviour; no model, archive read, or service is used.
"""

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
import unittest


SOURCE = Path(__file__).resolve().parents[2] / "app/core/aicall/client.py"
SOURCE_TEXT = SOURCE.read_text()
TREE = ast.parse(SOURCE_TEXT)
CLASS = next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == "AICall")
NAMES = {"_build_deterministic_runtime_compaction_summary", "_compact_thinking_events_in_place"}
ENV = {"Any": Any, "Dict": Dict, "List": List, "Tuple": Tuple, "json": json}
for node in CLASS.body:
    if isinstance(node, ast.FunctionDef) and node.name in NAMES:
        node.decorator_list = []
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), "exec"), ENV)


class Harness:
    def _fit_deterministic_runtime_summary_to_token_budget(self, summary, **kwargs):
        return summary


def build(events):
    return ENV["_build_deterministic_runtime_compaction_summary"](
        Harness(), events, max_tokens=1200)


MARKER = "FACT: limit=128Mi"


def original_events():
    text = "x" * 220 + MARKER + "y" * 1300
    return [{"type": "tool_result", "tool_name": "synthetic_metric",
             "semantic_success": True, "result": text, "result_preview": text,
             "raw_ref": "illustrative-reference-not-an-actual-file",
             "structured": {"limit": "128Mi"}}]


def two_stages():
    events = original_events()
    first = build(events)
    ENV["_compact_thinking_events_in_place"](
        events, {"type": "context_summary", "full_content": json.dumps(first)})
    return first, build(events), events


class RecompactionSourceTests(unittest.TestCase):
    def test_mutable_preview_changes_second_candidate(self):
        first, second, _ = two_stages()
        self.assertIn(MARKER, first["completed_items"][0]["result_preview"])
        self.assertNotIn(MARKER, second["completed_items"][0]["result_preview"])

    def test_reference_is_unchanged(self):
        first, second, _ = two_stages()
        self.assertEqual(first["completed_items"][0]["raw_ref"],
                         second["completed_items"][0]["raw_ref"])

    def test_not_global_information_loss(self):
        _, _, events = two_stages()
        self.assertEqual(events[1]["structured"]["limit"], "128Mi")
        self.assertIn(MARKER, events[0]["full_content"])

    def test_frozen_source_control(self):
        source = original_events()
        self.assertEqual(build(deepcopy(source)), build(deepcopy(source)))


if __name__ == "__main__":
    print(json.dumps({"source_sha256": hashlib.sha256(SOURCE_TEXT.encode()).hexdigest(),
                      "scope": "actual two helpers; token fitter stub; no runtime claim"}))
    unittest.main()
