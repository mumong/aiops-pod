"""Explicitly synthetic lifecycle inputs for model boundary tests, not cluster data."""
import copy


def make_fixture(kind):
    payload = {
        "contract_version": "pod-lifecycle.v1", "status": "success",
        "source": "synthetic_test_not_a_cluster", "observed_at": "2026-10-09T00:10:00Z",
        "scope": {"namespace": "lab-evidence", "pod": None, "label_selector": None},
        "coverage": "present", "history_complete": False, "next_continue_token": None,
        "remaining_item_count": 0,
        "window": {"minutes": 10, "start": "2026-10-09T00:00:00Z", "end": "2026-10-09T00:10:00Z"},
        "limitations": ["Synthetic frozen test data; not a real cluster.",
                        "Current snapshot and last termination only, not full window history.",
                        "Lifetime restart totals do not establish window counts."],
        "pods": [
            {"namespace": "lab-evidence", "name": "recovered", "uid": "synthetic-recovered",
             "node": "node-a", "phase": "Running", "containers": [
                 {"name": "app", "role": "app", "ready": True, "status_observed": True,
                  "restart_count_total": 7, "restart_count_in_window": None,
                  "termination_within_window": True,
                  "latest_observed_termination_at": "2026-10-09T00:09:00Z",
                  "state": {"running": {"startedAt": "2026-10-09T00:09:10Z"}},
                  "last_state": {"terminated": {"reason": "OOMKilled", "exitCode": 137,
                                                "finishedAt": "2026-10-09T00:09:00Z"}}},
                 {"name": "sidecar", "role": "app", "ready": False, "status_observed": True,
                  "restart_count_total": 1, "restart_count_in_window": None,
                  "termination_within_window": False,
                  "latest_observed_termination_at": "2026-10-08T23:50:00Z",
                  "state": {"waiting": {"reason": "ContainerCreating"}},
                  "last_state": {"terminated": {"reason": "Completed", "exitCode": 0,
                                                "finishedAt": "2026-10-08T23:50:00Z"}}},
             ]},
            {"namespace": "lab-evidence", "name": "status-unknown", "uid": "synthetic-unknown",
             "node": "node-a", "phase": "Pending", "containers": [
                 {"name": "app", "role": "app", "status_observed": False, "ready": None,
                  "restart_count_total": None, "restart_count_in_window": None,
                  "termination_within_window": None, "state": {}, "last_state": {}},
             ]},
            {"namespace": "lab-evidence", "name": "no-restarts", "uid": "synthetic-zero",
             "node": "node-b", "phase": "Running", "containers": [
                 {"name": "app", "role": "app", "status_observed": True, "ready": True,
                  "restart_count_total": 0, "restart_count_in_window": None,
                  "termination_within_window": None,
                  "state": {"running": {"startedAt": "2026-10-09T00:00:00Z"}}, "last_state": {}},
             ]},
        ],
    }
    if kind == "partial":
        payload.update(coverage="partial", next_continue_token="synthetic-next-page", remaining_item_count=17)
    elif kind == "empty":
        payload.update(coverage="empty", pods=[])
    elif kind == "error":
        payload.update(status="error", coverage="unknown", pods=[],
                       error="Synthetic API access denied; no resource state was retrieved.",
                       remaining_item_count=None)
    elif kind != "complete":
        raise ValueError("unknown synthetic fixture")
    payload["returned_count"] = len(payload["pods"])
    return copy.deepcopy(payload)
