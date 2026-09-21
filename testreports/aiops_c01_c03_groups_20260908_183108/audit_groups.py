"""Read-only artifact checks; root-cause meaning is reviewed separately by a human."""
import json
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
ARCHIVES = Path("/data/redis/aiops-aiops-reports-pvc-pvc-52d8916d-bd02-4ad3-9c91-ea2e59356b51/context_archives")


def read(path):
    return json.loads(path.read_text())


def entities(groups):
    return [(e.get("namespace"), e.get("name"))
            for g in groups for e in g.get("entities", [])]


if __name__ == "__main__":
    for run in read(OUT / "runner.json")["runs"]:
        if run["status"] != "completed":
            continue
        directory = OUT / run["group"] / f"run-{run['index']:02d}"
        before = read(directory / "before.json")
        after = read(directory / "after.json")
        expected = {(p["metadata"]["namespace"], p["metadata"]["name"])
                    for case in before.values() for p in case["pods"]["items"]}
        base = ARCHIVES / run["run_id"]
        handoff = read(base / "layer/handoff.json")
        snapshot = read(base / "node_outputs/parallel_evidence.output.json")["snapshot"]
        groups = snapshot["groups"]
        assignments = entities(groups)
        parents = handoff["issue_groups"]
        scoped = []
        for g in groups:
            lane_input = read(ARCHIVES / f"{run['run_id']}-{g['group_id']}" /
                              "node_inputs/evidence.input.json")
            h = lane_input["layer_handoff"]
            if isinstance(h, str):
                h = json.loads(h)
            scoped.append({"group_id": g["group_id"], "entities": g["entities"],
                "single_entity": len(g["entities"]) == 1,
                "input_scope_matches": entities(h["issue_groups"]) == entities([g]),
                "diagnostic_status": g.get("diagnostic_status")})
        result = {"run_id": run["run_id"],
            "parent_groups": [{k: g.get(k) for k in ("group_id", "status_keywords", "entities")}
                              for g in parents],
            "layer_coverage_matches": set(entities(parents)) == expected,
            "lane_coverage_matches": set(assignments) == expected,
            "duplicate_assignments": [e for e, n in Counter(assignments).items() if n > 1],
            "uids_unchanged": all(
                v["pods"]["items"][0]["metadata"]["uid"] ==
                after[k]["pods"]["items"][0]["metadata"]["uid"] for k, v in before.items()),
            "join": {k: snapshot.get(k) for k in ("group_count", "expected_group_count",
                "terminal_group_count", "join_complete", "diagnosed_count", "inconclusive_count", "error_count")},
            "lanes": scoped}
        print(json.dumps(result, ensure_ascii=False, indent=2))
