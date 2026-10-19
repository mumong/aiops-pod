"""Bounded group scheduling shared by diagnosis and repair planning.

No diagnosis, repair strategy, approval or resource mutation belongs here.
Each worker owns its client and mutable state; results retain the input identity.
"""

import os
import re
from concurrent.futures import CancelledError, ThreadPoolExecutor, as_completed

from app.core.log_context import bind_current_context


def group_display_name(group_id):
    """ "g3" → "异常组 3" for people; the id itself stays the machine key."""
    value = str(group_id or "").strip()
    if value == "single":
        return "整体诊断"
    match = re.fullmatch(r"g(\d+)", value)
    return f"异常组 {match.group(1)}" if match else value


DEFAULT_LANE_WORKERS = 3
MAX_LANE_WORKERS = 16


def resolve_lane_workers(config_value=None):
    """Lanes run at once: config > AIOPS_AUTONOMOUS_PARALLEL_WORKERS > 3, clamped to 1..16.

    Shared by diagnosis lanes and repair planning so one setting governs both.
    """
    value = config_value
    if value in (None, "", 0):
        value = os.getenv("AIOPS_AUTONOMOUS_PARALLEL_WORKERS", DEFAULT_LANE_WORKERS)
    try:
        return max(1, min(MAX_LANE_WORKERS, int(value)))
    except (TypeError, ValueError):
        return DEFAULT_LANE_WORKERS


def iter_group_results(groups, worker, *, max_workers, cancel=None):
    groups = list(groups)
    if not groups:
        return

    def run(group):
        if cancel is not None and cancel.is_set():
            raise CancelledError("group task cancelled before start")
        return worker(group)

    if len(groups) == 1:
        group = groups[0]
        try:
            result = run(group)
        except Exception as exc:
            yield group, None, exc
        else:
            yield group, result, None
        return

    pool = ThreadPoolExecutor(max_workers=max(1, min(int(max_workers), len(groups))))
    completed = False
    try:
        futures = {pool.submit(bind_current_context(run), group): group for group in groups}
        for future in as_completed(futures):
            group = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                yield group, None, exc
            else:
                yield group, result, None
        completed = True
    finally:
        # Fatal consumer exit: cancel queued work and do not delay error
        # delivery waiting for already-running read requests to return.
        pool.shutdown(wait=completed, cancel_futures=not completed)
