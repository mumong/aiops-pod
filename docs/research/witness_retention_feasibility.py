"""Synthetic helper-level comparison; no model, server, or token fitter runs.

Extracts current projection ordering functions. Proposed refinement and pinning
are research baselines, not claims about deployed behavior or patent novelty.
"""
import ast
from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable
import unittest


SOURCE = Path(__file__).resolve().parents[2] / "app/core/context/observability_projection.py"
SOURCE_TEXT = SOURCE.read_text()
NAMES = {"compact_json", "_message_template", "_selection_bucket",
         "_selection_value_state", "_selection_priority", "_selection_family",
         "_diverse_order"}
NODES = [n for n in ast.parse(SOURCE_TEXT).body
         if isinstance(n, ast.FunctionDef) and n.name in NAMES]
assert {n.name for n in NODES} == NAMES
ENV = dict(globals())
exec(compile(ast.Module(body=NODES, type_ignores=[]), str(SOURCE), "exec"), ENV)
order = ENV["_diverse_order"]
bucket = ENV["_selection_bucket"]


def fixture():
    return [{"id": f"r{i:03}", "uid": "pod-a", "path": "/ready",
             "timestamp": i, "http_status": 200 if i == 50 else 503,
             "message": f"GET /ready status {200 if i == 50 else 503}",
             "event": "http_response", "level": "info"} for i in range(100)]


def scoped(rows):
    # Scope is provided explicitly, not inferred by an LLM in this experiment.
    return [r for r in rows if r.get("uid") == "pod-a"
            and r.get("path") == "/ready"
            and isinstance(r.get("timestamp"), int) and 0 <= r["timestamp"] < 100]


def truth(row):
    value = row.get("http_status")
    return None if type(value) is not int else value == 503


def check(rows):
    selected = scoped(rows)
    false_ids = [r["id"] for r in selected if truth(r) is False]
    if false_ids:
        return "refuted", false_ids
    if not selected or any(truth(r) is None for r in selected):
        return "unknown", []
    return "holds_in_provided_records", []


def refined(rows, slots):
    groups = OrderedDict()
    for row in scoped(rows):
        groups.setdefault((bucket(row), truth(row)), []).append(row)
    representatives = [v[0] for v in groups.values()]
    if len(representatives) > slots:
        return {"status": "budget_unmet", "records": []}
    return {"status": "represented", "records": deepcopy(representatives)}


def pinned(rows, witness_ids, slots):
    indexed = {r["id"]: r for r in scoped(rows)}
    if len(indexed) != len(scoped(rows)):
        raise ValueError("ambiguous record IDs")
    if any(i not in indexed for i in witness_ids):
        raise ValueError("witness not in current provided scope")
    ids = list(dict.fromkeys(witness_ids))
    if len(ids) > slots:
        return {"status": "budget_unmet", "records": []}
    for row in order(list(indexed.values())):
        if row["id"] not in ids and len(ids) < slots:
            ids.append(row["id"])
    return {"status": "represented", "records": [deepcopy(indexed[i]) for i in ids]}


class RetentionTests(unittest.TestCase):
    def test_numeric_log_statuses_share_real_bucket(self):
        rows = fixture()
        self.assertEqual(bucket(rows[0]), bucket(rows[50]))

    def test_first_two_real_ordered_records_miss_middle_counterexample(self):
        selected = order(fixture())[:2]
        self.assertEqual([r["id"] for r in selected], ["r000", "r099"])
        self.assertEqual(check(selected)[0], "holds_in_provided_records")
        self.assertEqual(check(fixture()), ("refuted", ["r050"]))

    def test_two_representatives_and_simple_pinning_both_work(self):
        rows = fixture()
        for result in (refined(rows, 2), pinned(rows, ["r050"], 2)):
            self.assertEqual(result["status"], "represented")
            self.assertEqual(check(result["records"])[0], "refuted")

    def test_one_slot_refinement_fails_but_counterexample_alone_refutes(self):
        self.assertEqual(refined(fixture(), 1)["status"], "budget_unmet")
        self.assertEqual(check(pinned(fixture(), ["r050"], 1)["records"])[0], "refuted")

    def test_scope_excludes_different_path_uid_and_time(self):
        base = fixture()[0]
        for field, value in (("path", "/work"), ("uid", "pod-b"), ("timestamp", 100)):
            outside = {**fixture()[50], field: value}
            self.assertEqual(check([base, outside])[0], "holds_in_provided_records")

    def test_missing_field_and_empty_are_unknown(self):
        self.assertEqual(check([{**fixture()[0], "http_status": None}])[0], "unknown")
        self.assertEqual(check([])[0], "unknown")

    def test_absent_witness_is_not_recreated(self):
        with self.assertRaises(ValueError):
            pinned(fixture()[:10], ["r050"], 2)

    def test_repeated_construction_keeps_witness_without_partition_state(self):
        rows = fixture()
        for _ in range(4):
            self.assertEqual(check(pinned(rows, ["r050"], 2)["records"])[0], "refuted")
        self.assertEqual(rows, fixture())


if __name__ == "__main__":
    print("source_sha256", hashlib.sha256(SOURCE_TEXT.encode()).hexdigest())
    unittest.main(verbosity=2)
