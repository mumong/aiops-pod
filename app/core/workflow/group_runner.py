"""Bounded group scheduling shared by diagnosis and repair planning.

No diagnosis, repair strategy, approval or resource mutation belongs here.
Each worker owns its client and mutable state; results retain the input identity.
"""
from concurrent.futures import CancelledError, ThreadPoolExecutor, as_completed


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

    with ThreadPoolExecutor(max_workers=max(1, min(int(max_workers), len(groups)))) as pool:
        futures = {pool.submit(run, group): group for group in groups}
        for future in as_completed(futures):
            group = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                yield group, None, exc
            else:
                yield group, result, None
