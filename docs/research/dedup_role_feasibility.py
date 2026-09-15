"""Offline demonstration of result deduplication and explicit label-role gates.

Actual MCP helper vs a proposed conservative baseline. No query parser, model,
Prometheus engine, service, or archive implementation is exercised here.
"""

import ast
from copy import deepcopy
import json
from pathlib import Path
from typing import Any
import unittest


SOURCE = (Path(__file__).resolve().parents[3] / "mcpstander/servers"
          / "aiops_observability/query/metrics.py")
TREE = ast.parse(SOURCE.read_text())
ENV = {"Any": Any}
FUNCTIONS = {"compact_prometheus_result", "_stats", "_point_count"}
CONSTANTS = {"MAX_SERIES", "SCRAPER_LABELS"}
for node in TREE.body:
    if (isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id in CONSTANTS for t in node.targets)):
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), "exec"), ENV)
    if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS:
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), "exec"), ENV)


def current(rows):
    return ENV["compact_prometheus_result"](
        {"status": "success", "data": {"resultType": "vector", "result": rows}})


def proposed(rows, replica_labels, protected_labels):
    """Caller-supplied roles, not inferred from metric names or values.

    Groups only ignore explicitly declared replica labels that are not
    protected. Different full sample payloads remain separate variants. This
    is a control baseline, not the complete patent candidate or HA merging.
    """
    removable = set(replica_labels) - set(protected_labels)
    groups = {}
    for row in rows:
        key_labels = {k: v for k, v in row["metric"].items() if k not in removable}
        key = json.dumps(key_labels, sort_keys=True)
        payload = {k: v for k, v in row.items() if k != "metric"}
        payload_key = json.dumps(payload, sort_keys=True)
        group = groups.setdefault(key, {"labels": key_labels, "variants": {}})
        variant = group["variants"].setdefault(
            payload_key, {"sample": deepcopy(payload), "sources": []})
        variant["sources"].append(deepcopy(row["metric"]))
    out = []
    for key in sorted(groups):
        group = groups[key]
        variants = []
        for payload_key in sorted(group["variants"]):
            variant = group["variants"][payload_key]
            variant["sources"].sort(key=lambda v: json.dumps(v, sort_keys=True))
            variants.append(variant)
        out.append({"labels": group["labels"], "variants": variants,
                    "merge_status": "equal_payloads" if len(variants) == 1 else "distinct_payloads"})
    return out


def sample(instance, value="128", timestamp=100):
    return {"metric": {"__name__": "synthetic_gauge", "namespace": "n",
                       "pod": "p", "container": "app", "instance": instance},
            "value": [timestamp, value]}


def serialized_bytes(value):
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode())


def factor_labels(rows):
    """Lossless control: share common label text without merging logical rows.

    This deliberately needs no query AST or guessed replica semantics. It is
    an ordinary encoding baseline, not a novel method or tested LLM format.
    """
    if not rows:
        return []
    common = deepcopy(rows[0]["metric"])
    for row in rows[1:]:
        common = {k: v for k, v in common.items() if k in row["metric"] and row["metric"][k] == v}
    residuals = []
    for row in rows:
        residual = deepcopy(row)
        residual["metric"] = {k: v for k, v in row["metric"].items() if k not in common}
        residuals.append(residual)
    encoded = {"representation": "shared_labels_v1", "labels": common, "rows": residuals}
    return encoded if serialized_bytes(encoded) < serialized_bytes(rows) else deepcopy(rows)


def restore_labels(encoded):
    if isinstance(encoded, list):
        return deepcopy(encoded)
    if encoded.get("representation") != "shared_labels_v1":
        raise ValueError("unsupported representation")
    rows = []
    for residual in encoded["rows"]:
        row = deepcopy(residual)
        row["metric"] = {**encoded["labels"], **row["metric"]}
        rows.append(row)
    return rows


class DedupRoleTests(unittest.TestCase):
    def test_actual_helper_selects_first_conflicting_value(self):
        a, b = sample("a"), sample("b", "256")
        self.assertNotEqual(current([a, b])["series"][0]["value"],
                            current([b, a])["series"][0]["value"])
        self.assertFalse(current([a, b])["truncated"])

    def test_actual_helper_merges_equal_distinct_group_labels(self):
        self.assertEqual(current([sample("a"), sample("b")])["series_count"], 1)

    def test_protected_query_dimension_remains_distinct_even_if_equal(self):
        groups = proposed([sample("a"), sample("b")], {"instance"}, {"instance"})
        self.assertEqual(len(groups), 2)

    def test_declared_equal_replicas_can_share_payload(self):
        groups = proposed([sample("a"), sample("b")], {"instance"}, set())
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]["variants"]), 1)
        self.assertEqual(len(groups[0]["variants"][0]["sources"]), 2)

    def test_distinct_values_are_not_silently_resolved(self):
        groups = proposed([sample("a"), sample("b", "256")], {"instance"}, set())
        self.assertEqual(len(groups[0]["variants"]), 2)

    def test_distinct_timestamps_are_not_equivalent(self):
        groups = proposed([sample("a"), sample("b", timestamp=101)], {"instance"}, set())
        self.assertEqual(len(groups[0]["variants"]), 2)

    def test_undeclared_source_labels_cannot_be_erased(self):
        self.assertEqual(len(proposed([sample("a"), sample("b")], set(), set())), 2)

    def test_proposed_output_is_order_invariant(self):
        rows = [sample("a"), sample("b", "256"), sample("c")]
        self.assertEqual(proposed(rows, {"instance"}, set()),
                         proposed(list(reversed(rows)), {"instance"}, set()))

    def test_factoring_preserves_distinct_equal_output_groups(self):
        rows = [sample(str(i), "1") for i in range(20)]
        encoded = factor_labels(rows)
        self.assertLess(serialized_bytes(encoded), serialized_bytes(rows))
        self.assertEqual(restore_labels(encoded), rows)
        self.assertEqual(len(restore_labels(encoded)), 20)

    def test_factoring_preserves_disagreement(self):
        rows = [sample("a"), sample("b", "256")]
        self.assertEqual(restore_labels(factor_labels(rows)), rows)

    def test_factoring_preserves_multiplicity(self):
        rows = [sample("a")] * 20
        self.assertEqual(restore_labels(factor_labels(rows)), rows)
        self.assertEqual(len(restore_labels(factor_labels(rows))), 20)

    def test_factoring_preserves_absent_labels_and_time_fields(self):
        rows = [sample("a"), sample("b", timestamp=101)]
        del rows[1]["metric"]["container"]
        self.assertEqual(restore_labels(factor_labels(rows)), rows)

    def test_factoring_singleton_falls_back_when_overhead_larger(self):
        rows = [sample("a")]
        self.assertEqual(factor_labels(rows), rows)

    def test_factoring_empty(self):
        self.assertEqual(restore_labels(factor_labels([])), [])


if __name__ == "__main__":
    for count in (1, 2, 20):
        rows = [sample(str(i), "1") for i in range(count)]
        encoded = factor_labels(rows)
        print(json.dumps({"rows": count, "raw_bytes": serialized_bytes(rows),
                          "shared_label_bytes": serialized_bytes(encoded),
                          "roundtrip_equal": restore_labels(encoded) == rows}))
    unittest.main()
