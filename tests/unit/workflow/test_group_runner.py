import threading
from concurrent.futures import CancelledError
from app.core.workflow.group_runner import iter_group_results


def test_parallel_groups_keep_identity_and_isolate_failure():
    barrier = threading.Barrier(3)
    def worker(group):
        barrier.wait(timeout=3)
        if group == "bad":
            raise ValueError("test failure")
        return group + " result"
    results = {g: (value, error) for g, value, error in
               iter_group_results(["a", "bad", "b"], worker, max_workers=3)}
    assert results["a"] == ("a result", None)
    assert results["b"] == ("b result", None)
    assert isinstance(results["bad"][1], ValueError)


def test_single_group_same_contract_and_cancel_before_start():
    assert list(iter_group_results(["a"], lambda g: g, max_workers=5)) == [("a", "a", None)]
    assert list(iter_group_results([], lambda g: g, max_workers=5)) == []
    cancelled = threading.Event()
    cancelled.set()
    calls = []
    results = list(iter_group_results(["a", "b"], calls.append, max_workers=2, cancel=cancelled))
    assert not calls and all(isinstance(error, CancelledError) for _, _, error in results)
