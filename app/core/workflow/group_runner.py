"""Bounded group scheduling shared by diagnosis and repair planning.

No diagnosis, repair strategy, approval or resource mutation belongs here.
Each worker owns its client and mutable state; results retain the input identity.
"""

from concurrent.futures import CancelledError, ThreadPoolExecutor, as_completed

from app.core.log_context import bind_current_context


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
