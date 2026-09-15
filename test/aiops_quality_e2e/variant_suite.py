"""Opt-in fixture variants; hidden expectations never alter the user question."""
from dataclasses import replace
import json
from pathlib import Path
import sys

import yaml

from evaluator import EvidenceExpectation, RootCauseExpectation, score_runbooks

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent / "pod-anomaly-cases"


def fixture_manager():
    scripts = str(FIXTURES / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import manage_cases
    return manage_cases


def extend_scenarios(scenarios):
    catalog = fixture_manager().catalog()
    definitions = yaml.safe_load((HERE / "variant_cases.yaml").read_text())["variants"]
    registered = set()
    for definition in definitions:
        case_id = definition["id"]
        if case_id in scenarios or case_id in registered:
            raise ValueError(f"duplicate variant {case_id}")
        registered.add(case_id)
        case = catalog[case_id]
        base = scenarios[definition["base"]]
        roots = tuple(RootCauseExpectation.from_mapping(
            dict(item, namespace=case["namespace"]), fallback_id=case_id
        ) for item in definition["expected_root_causes"])
        if not roots or any(not root.mechanisms_any for root in roots):
            raise ValueError(f"variant {case_id} must declare a causal mechanism")
        # The fixed contract is audit-only. Never inherit an unrelated base cause.
        audit = EvidenceExpectation.from_mapping({
            "id": f"{case_id}-kubernetes-observation", "weight": 1,
            "dimensions": ["kubernetes"], "include_all": [case["namespace"]],
        }, fallback_id=case_id)
        scenarios[case_id] = replace(
            base, id=case_id, name=case["fault_scenario"],
            fault_scenario=case["fault_scenario"], members=(case_id,),
            expected_root_causes=roots, expected_evidence=(audit,),
        )
    missing = {key for key, case in catalog.items() if case["variant"]} - registered
    if missing:
        raise ValueError(f"fixtures without scoring rules: {sorted(missing)}")
    for base in [key for key in scenarios if len(key) == 3 and key.startswith("c")]:
        if not any(item["base"] == base for item in definitions):
            raise ValueError(f"base scenario {base} has no variant")
    return scenarios


def combine_scenarios(selected, catalog):
    """Every member retains its own namespace and expected Runbook assignment."""
    if len(selected) < 2 or any(len(s.members) != 1 for s in selected):
        raise ValueError("--combine requires at least two distinct single-member scenarios")
    members = tuple(s.members[0] for s in selected)
    if len(set(members)) != len(members):
        raise ValueError("--combine contains duplicate members")
    namespaces = [catalog[member]["namespace"] for member in members]
    if len(set(namespaces)) != len(namespaces):
        raise ValueError("combined members must use distinct namespaces")
    roots = tuple(replace(root, id=f"{s.id}:{root.id}", namespace=catalog[s.members[0]]["namespace"])
                  for s in selected for root in s.expected_root_causes)
    assignments = tuple((catalog[s.members[0]]["namespace"], s.expected_runbooks) for s in selected)
    return replace(selected[0], id="mix-" + "-".join(s.id for s in selected),
                   name="多对象同时部署", anomaly_type="Mixed",
                   fault_scenario="；".join(f"{s.id}: {s.fault_scenario}" for s in selected),
                   members=members, expected_root_causes=roots,
                   expected_runbooks=tuple(dict.fromkeys(b for s in selected for b in s.expected_runbooks)),
                   runbook_targets=assignments,
                   expected_evidence=tuple(replace(e, id=f"{s.id}:{e.id}") for s in selected for e in s.expected_evidence),
                   settle_after_gate_seconds=max(s.settle_after_gate_seconds for s in selected))


def score_target_runbooks(targets, report, claims):
    """Report references must be attributed to the target, not found anywhere."""
    import re
    section = re.search(r"(?ms)^[# 📋]*Runbook 参考[^\n]*\n(.*?)(?=^## |\Z)", report)
    lines = (section.group(1) if section else "").splitlines()
    expected, found, matched, details = [], [], [], []
    for namespace, books in targets:
        groups = {c.group for c in claims if c.namespaces == (namespace,)}
        scoped = []
        for line in lines:
            owners = set(re.findall(r"(?<![\w-])([a-z0-9][a-z0-9-]*)/[a-z0-9][a-z0-9.-]*", line))
            by_group = any(re.search(r"(?<![\w-])" + re.escape(g) + r"(?![\w-])", line) for g in groups)
            if owners == {namespace} or (not owners and by_group):
                scoped.append(line)
        score = score_runbooks(books, "📋 Runbook 参考\n\n" + "\n".join(scoped))
        expected.extend(f"{namespace}:{b}" for b in score.expected)
        found.extend(f"{namespace}:{b}" for b in score.found)
        matched.extend(f"{namespace}:{b}" for b in score.matched)
        details.append({"namespace": namespace, "coverage": score.coverage,
                        "expected": score.expected, "matched": score.matched})
    values = [d["coverage"] for d in details if d["coverage"] is not None]
    return {"expected": expected, "found": found, "matched": matched,
            "coverage": sum(values) / len(values) if values else None,
            "passed": bool(expected) and len(expected) == len(matched),
            "targets": details, "source": "target_scoped_report_references"}
