"""Isolated feasibility checks for a proposed relation-preserving context view.

Synthetic records only. No app imports, network, LLM, cluster or file writes.
This is NOT an Agent implementation or a patent novelty demonstration.
Run: python3 docs/research/joint_context_feasibility.py
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import unittest
from dataclasses import dataclass
from typing import Callable


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def byte_cost(value):
    # A reproducible engineering budget, not a claim about any model tokenizer.
    return len(wire(value).encode("utf-8"))


@dataclass
class Snapshot:
    scope: str
    fields: tuple[str, ...]
    rows: tuple[tuple, ...]

    def __post_init__(self):
        if not self.scope or not self.fields or len(set(self.fields)) != len(self.fields):
            raise ValueError("explicit scope and distinct field paths required")
        if not self.rows:
            raise ValueError("empty source is not negative co-occurrence evidence")
        self.rows = tuple(tuple(row) for row in self.rows)
        for row in self.rows:
            if len(row) != len(self.fields):
                raise ValueError("ragged records require a separate missingness policy")
            if any(v is None or isinstance(v, (dict, list)) for v in row):
                raise ValueError("missing/compound values are outside this prototype")
            if any(isinstance(v, float) and not math.isfinite(v) for v in row):
                raise ValueError("non-finite numeric values unsupported")
        self.version = hashlib.sha256(wire([self.scope, self.fields, self.rows]).encode()).hexdigest()[:16]
        self.keys = {wire(row) for row in self.rows}
        self.domains = tuple(
            tuple({wire(row[i]): row[i] for row in self.rows}.values())
            for i in range(len(self.fields))
        )

    def projection(self, columns):
        # Count and witness ordinals refer to this snapshot, not real-world frequency.
        projected = {}
        for ordinal, row in enumerate(self.rows):
            values = tuple(row[i] for i in columns)
            key = wire(values)
            entry = projected.setdefault(key, {"values": values, "witnesses": []})
            entry["witnesses"].append(ordinal)
        return projected

    def alternatives(self, cap=4096):
        cardinality = math.prod(len(domain) for domain in self.domains)
        if cardinality > cap:
            raise ValueError("exhaustive counterexample universe exceeds prototype cap")
        return tuple(itertools.product(*self.domains))


def build_view(source: Snapshot, budget: int, max_width=2,
               proposed_priority: tuple[str, ...] = (),
               cost: Callable = byte_cost):
    """Select exact joint projections that exclude source-absent recombinations.

    A proposed (possibly model-produced) priority only breaks equal gain/cost ties.
    Invalid IDs are discarded. The prototype does not call or evaluate a model.
    No false tuple is ever placed into the model-facing view.
    """
    if max_width < 1:
        raise ValueError("max_width must be positive")
    universe = source.alternatives()
    negatives = {wire(row): row for row in universe if wire(row) not in source.keys}
    initial_count = len(negatives)
    view = {
        "scope": source.scope, "snapshot": source.version,
        "meaning": "source-supported projections; not exhaustive event enumeration",
        "marginals": {name: source.domains[i] for i, name in enumerate(source.fields)},
        "relation_check": {"scope": "finite_snapshot_domains", "unexcluded": initial_count},
        "joint": [],
    }
    if cost(view) > budget:
        return {"status": "budget_insufficient", "required": cost(view), "budget": budget}
    candidates = {}
    for width in range(2, min(max_width, len(source.fields)) + 1):
        for cols in itertools.combinations(range(len(source.fields)), width):
            ident = "+".join(source.fields[i] for i in cols)
            projected = source.projection(cols)
            blocked = {
                key for key, row in negatives.items()
                if wire(tuple(row[i] for i in cols)) not in projected
            }
            candidates[ident] = {
                "columns": cols, "blocked": blocked,
                "view": {"id": ident, "fields": [source.fields[i] for i in cols],
                         "tuples": [entry["values"] for entry in projected.values()]},
            }
    priority = {ident: i for i, ident in enumerate(proposed_priority) if ident in candidates}
    selected = []
    while negatives:
        options = []
        for ident, candidate in candidates.items():
            if ident in selected:
                continue
            gain = len(set(negatives) & candidate["blocked"])
            updated = {**view, "joint": [*view["joint"], candidate["view"]],
                       "relation_check": {"scope": "finite_snapshot_domains",
                                          "unexcluded": len(negatives) - gain}}
            extra = cost(updated) - cost(view)
            if gain and extra > 0 and cost(updated) <= budget:
                options.append((gain / extra, -priority.get(ident, 10**6), ident, updated))
        if not options:
            break
        _, _, ident, view = max(options, key=lambda item: (item[0], item[1], item[2]))
        selected.append(ident)
        negatives = {key: row for key, row in negatives.items()
                     if key not in candidates[ident]["blocked"]}
    assert cost(view) <= budget
    # Archive-side manifest is not silently included in the model budget.
    manifest = {
        "snapshot": source.version,
        "projections": {ident: source.projection(candidates[ident]["columns"])
                        for ident in selected},
    }
    return {
        "status": "built", "view": view, "manifest": manifest,
        "bytes": byte_cost(view), "cost": cost(view), "budget": budget,
        "selected": selected, "initial_spurious": initial_count,
        "remaining_spurious": len(negatives),
        "scope_of_check": "exhaustive finite Cartesian universe of this synthetic snapshot",
    }


def reread(source, manifest, projection_id, values, expected_version):
    if expected_version != source.version or manifest["snapshot"] != source.version:
        return {"status": "snapshot_mismatch"}
    block = manifest["projections"].get(projection_id)
    if block is None:
        return {"status": "unknown_projection"}
    item = block.get(wire(values))
    if item is None:
        return {"status": "no_match_in_snapshot"}
    return {"status": "found", "rows": [source.rows[i] for i in item["witnesses"]]}


HTTP = Snapshot("synthetic/pod-A/window-1", ("path", "code", "ms"),
                (("/work", 200, 2000), ("/ready", 503, 20)))
PARITY = Snapshot("synthetic/three-way", ("x", "y", "z"),
                  ((0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)))
FACTORIZED = Snapshot(
    "synthetic/factorized", tuple(f"f{i}" for i in range(8)),
    tuple((a, a, b, b, c, d, e, f)
          for a, b, c, d, e, f in itertools.product((0, 1), repeat=6)),
)


def full_rows_view(source):
    """An honest exact-row baseline with the same scope and version metadata."""
    return {"scope": source.scope, "snapshot": source.version,
            "meaning": "exact source tuples, multiplicity retained",
            "fields": source.fields, "rows": source.rows}


class Feasibility(unittest.TestCase):
    def test_marginal_collision(self):
        other = Snapshot(HTTP.scope, HTTP.fields,
                         (("/work", 200, 20), ("/ready", 503, 2000)))
        self.assertEqual([set(d) for d in HTTP.domains], [set(d) for d in other.domains])
        self.assertNotEqual(HTTP.keys, other.keys)

    def test_joint_projections_remove_http_recombinations(self):
        result = build_view(HTTP, 1200)
        self.assertEqual(result["initial_spurious"], 6)
        self.assertEqual(result["remaining_spurious"], 0)

    def test_true_records_never_rejected(self):
        result = build_view(HTTP, 1200)
        for block in result["view"]["joint"]:
            cols = tuple(HTTP.fields.index(f) for f in block["fields"])
            represented = {wire(v) for v in block["tuples"]}
            for row in HTTP.rows:
                self.assertIn(wire(tuple(row[i] for i in cols)), represented)

    def test_pairwise_cannot_resolve_three_way_relation(self):
        result = build_view(PARITY, 1200, max_width=2)
        self.assertEqual(result["remaining_spurious"], 4)
        self.assertEqual(result["selected"], [])

    def test_three_way_can_resolve_parity(self):
        self.assertEqual(build_view(PARITY, 1200, max_width=3)["remaining_spurious"], 0)

    def test_budget_failure_explicit(self):
        self.assertEqual(build_view(HTTP, 10)["status"], "budget_insufficient")

    def test_partial_budget_does_not_claim_completeness(self):
        full = build_view(HTTP, 1200)
        result = build_view(HTTP, full["cost"] - 1)
        self.assertGreater(result["remaining_spurious"], 0)
        self.assertEqual(result["view"]["relation_check"]["unexcluded"],
                         result["remaining_spurious"])
        self.assertLessEqual(result["cost"], result["budget"])

    def test_arbitrary_model_id_cannot_inject_values(self):
        result = build_view(HTTP, 1200, proposed_priority=("invented",))
        self.assertNotIn("invented", wire(result["view"]))

    def test_reread_uses_exact_source_witnesses(self):
        result = build_view(HTTP, 1200)
        ident = result["selected"][0]
        entry = next(iter(result["manifest"]["projections"][ident].values()))
        got = reread(HTTP, result["manifest"], ident, entry["values"], HTTP.version)
        self.assertEqual(got["status"], "found")
        self.assertEqual(got["rows"], [HTTP.rows[i] for i in entry["witnesses"]])

    def test_changed_snapshot_rejects_old_manifest(self):
        result = build_view(HTTP, 1200)
        changed = Snapshot(HTTP.scope, HTTP.fields, HTTP.rows + (("/ready", 503, 2000),))
        self.assertEqual(reread(changed, result["manifest"], "x", (), HTTP.version)["status"],
                         "snapshot_mismatch")

    def test_missing_not_synthetic_negative(self):
        with self.assertRaises(ValueError):
            Snapshot("s", ("x", "y"), ((1, None),))

    def test_cartesian_cap(self):
        source = Snapshot("s", ("x", "y"), tuple((i, i) for i in range(70)))
        with self.assertRaises(ValueError):
            build_view(source, 100000)

    def test_full_cartesian_data_has_no_spurious_combinations(self):
        source = Snapshot("s", ("x", "y"), tuple(itertools.product((0, 1), repeat=2)))
        result = build_view(source, 1200)
        self.assertEqual(result["initial_spurious"], 0)
        self.assertEqual(result["selected"], [])

    def test_factorized_relation_can_fit_where_all_rows_do_not(self):
        result = build_view(FACTORIZED, 1000)
        self.assertEqual(result["remaining_spurious"], 0)
        self.assertGreater(byte_cost(full_rows_view(FACTORIZED)), 1000)
        self.assertLessEqual(result["cost"], 1000)

    def test_small_relation_full_rows_are_cheaper(self):
        # Prevent claiming the candidate always beats existing row-preserving views.
        self.assertLess(byte_cost(full_rows_view(HTTP)), build_view(HTTP, 1200)["cost"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Feasibility)
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    for source, width in ((HTTP, 2), (PARITY, 2), (PARITY, 3), (FACTORIZED, 2)):
        result = build_view(source, 1200, max_width=width)
        print(wire({"scope": source.scope, "full_rows_bytes": byte_cost(full_rows_view(source)),
                    **{key: value for key, value in result.items() if key not in ("view", "manifest")}}))
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
