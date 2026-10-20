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


def test_thread_handoff_carries_log_fields_but_not_the_callers_run_context():
    """Parallel lanes start inside the workflow graph's node. A full context copy also
    carried LangChain/LangGraph's run context, and only one lane's model tokens reached
    its stream (live runs f8e56239b1b74313, 9a414a4f611a4f4c: reasoning for one group)."""
    import contextvars
    import threading

    from app.core.log_context import _context, bind_current_context, log_context

    foreign = contextvars.ContextVar("caller_run_context", default="unset")
    seen = {}

    def worker():
        seen["log"] = dict(_context.get())
        seen["foreign"] = foreign.get()

    token = foreign.set("outer-graph-config")
    try:
        with log_context(run="r1", lane="g2"):
            thread = threading.Thread(target=bind_current_context(worker))
            thread.start()
            thread.join()
    finally:
        foreign.reset(token)
    assert seen == {"log": {"run": "r1", "lane": "g2"}, "foreign": "unset"}
