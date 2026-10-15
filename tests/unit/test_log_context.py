import asyncio
import logging
import threading

from app.core.async_bridge import run_coroutine_sync
from app.core.log_context import LogContextFilter, bind_current_context, log_context
from app.core.workflow.group_runner import iter_group_results


def _rendered(name="t"):
    record = logging.LogRecord(name, logging.INFO, __file__, 1, "msg", None, None)
    LogContextFilter().filter(record)
    return record.log_context


def test_filter_renders_bound_fields_and_nothing_when_unbound():
    assert _rendered() == ""
    with log_context(run="r1"):
        with log_context(node="layer", lane="g2"):
            assert _rendered() == " [run=r1 node=layer lane=g2]"
        assert _rendered() == " [run=r1]"
    assert _rendered() == ""


def test_context_follows_work_into_threads():
    seen = {}

    def work():
        seen["thread"] = _rendered()

    with log_context(run="r2"):
        t = threading.Thread(target=bind_current_context(work))
        t.start()
        t.join()
    assert seen["thread"] == " [run=r2]"


def test_group_runner_and_async_bridge_propagate_context():
    async def coro():
        return _rendered()

    with log_context(run="r3", node="parallel_evidence"):
        lanes = sorted(
            result
            for _, result, _ in iter_group_results(
                ["g1", "g2"], lambda g: _rendered(), max_workers=2
            )
        )
        bridged = run_coroutine_sync(coro)
    assert lanes == [" [run=r3 node=parallel_evidence]"] * 2
    assert bridged == " [run=r3 node=parallel_evidence]"
    assert asyncio.run(coro()) == ""
