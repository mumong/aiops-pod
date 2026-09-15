"""Offline counterexamples, not an Agent benchmark or a production change.

Run from any directory: python3 docs/research/temporal_summary_feasibility.py
Extracts only the current MCP _stats function using AST; does not import its
module, contact services, or infer continuous-time behaviour from samples.
"""

import ast
import hashlib
import json
import math
from pathlib import Path
import unittest


SOURCE = (Path(__file__).resolve().parents[3] / "mcpstander" / "servers"
          / "aiops_observability" / "query" / "metrics.py")
SOURCE_TEXT = SOURCE.read_text()
TREE = ast.parse(SOURCE_TEXT)
STATS_NODE = next(n for n in TREE.body
                  if isinstance(n, ast.FunctionDef) and n.name == "_stats")
ENV = {"Any": object}
exec(compile(ast.Module(body=[STATS_NODE], type_ignores=[]), str(SOURCE), "exec"), ENV)
stats = ENV["_stats"]


def samples(values):
    return [[t, str(v)] for t, v in enumerate(values)]


def summary(points):
    return {"stats": stats(points), "last_point": points[-1],
            "sample_count": len(points)}


def with_peak_time(points):
    return {**summary(points),
            "first_max_timestamp": max(points, key=lambda p: float(p[1]))[0]}


def sampled_overlap(a, b, expected_times, threshold=9):
    """Existential predicate on a specified discrete grid, NOT a causal test.

    Missing either stream at an expected timestamp prevents a negative result.
    No nearest-neighbour join, interpolation or implicit timestamp tolerance.
    """
    if not expected_times:
        return "unknown"
    left = {t: float(v) for t, v in a}
    right = {t: float(v) for t, v in b}
    if len(left) != len(a) or len(right) != len(b):
        raise ValueError("duplicate timestamps require an explicit reduction rule")
    left = {t: v for t, v in left.items() if math.isfinite(v)}
    right = {t: v for t, v in right.items() if math.isfinite(v)}
    if any(left.get(t, float("-inf")) >= threshold
           and right.get(t, float("-inf")) >= threshold for t in expected_times):
        return "observed"
    if not all(t in left and t in right for t in expected_times):
        return "unknown"
    return "not_observed_on_grid"


class TemporalSummaryTests(unittest.TestCase):
    def test_current_summary_cannot_distinguish_peak_coincidence(self):
        a = samples([0, 10, 0, 0])
        later = samples([0, 0, 10, 0])
        self.assertEqual(summary(a), summary(later))
        self.assertEqual(sampled_overlap(a, a, range(4)), "observed")
        self.assertEqual(sampled_overlap(a, later, range(4)), "not_observed_on_grid")

    def test_adding_max_timestamp_still_loses_nonmax_overlap(self):
        a = samples([0, 10, 9, 0, 0, 0])
        overlap = samples([0, 0, 9, 10, 0, 0])
        separate = samples([0, 0, 0, 10, 9, 0])
        self.assertEqual(with_peak_time(overlap), with_peak_time(separate))
        self.assertEqual(sorted(v for _, v in overlap), sorted(v for _, v in separate))
        self.assertEqual(sampled_overlap(a, overlap, range(6)), "observed")
        self.assertEqual(sampled_overlap(a, separate, range(6)), "not_observed_on_grid")

    def test_missing_data_is_not_a_negative(self):
        self.assertEqual(sampled_overlap([[0, "0"]], [[0, "0"]], range(2)), "unknown")

    def test_positive_witness_does_not_require_complete_grid(self):
        self.assertEqual(sampled_overlap([[0, "10"]], [[0, "10"]], range(2)), "observed")

    def test_no_implicit_alignment(self):
        self.assertEqual(sampled_overlap([[0, "10"]], [[0.1, "10"]], [0]), "unknown")

    def test_empty_grid(self):
        self.assertEqual(sampled_overlap([], [], []), "unknown")

    def test_nonfinite_value_is_not_a_negative(self):
        self.assertEqual(sampled_overlap([[0, "NaN"]], [[0, "10"]], [0]), "unknown")

    def test_duplicate_timestamps_rejected(self):
        with self.assertRaises(ValueError):
            sampled_overlap([[0, "0"], [0, "10"]], [[0, "10"]], [0])


if __name__ == "__main__":
    print(json.dumps({"source": str(SOURCE),
                      "source_sha256": hashlib.sha256(SOURCE_TEXT.encode()).hexdigest(),
                      "scope": "synthetic samples; actual extracted _stats; no model calls"}))
    unittest.main()
