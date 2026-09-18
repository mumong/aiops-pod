import threading
from types import SimpleNamespace

import pytest

from app.core.query_sessions import QuerySessionStore, SessionBusy
from app.core.workflow.executor import WorkflowExecutor


def test_memory_isolation_expiry_busy_and_snapshot_immutability():
    clock = [0]
    store = QuerySessionStore(ttl=10, max_sessions=2, clock=lambda: clock[0])
    with store.checkout(('alice', 's')) as (memory, save):
        assert memory == {}
        assert save({'pods': ['xnet/pod']})
        with pytest.raises(SessionBusy):
            with store.checkout(('alice', 's')): pass
    with store.checkout(('bob', 's')) as (memory, _):
        assert memory == {}
    with store.checkout(('alice', 's')) as (memory, _):
        memory['pods'].append('not committed')
    with store.checkout(('alice', 's')) as (memory, _):
        assert memory == {'pods': ['xnet/pod']}
    clock[0] = 11
    with store.checkout(('alice', 's')) as (memory, _):
        assert memory == {}


def test_capacity_never_evicts_running_session_and_oversize_preserves_old():
    store = QuerySessionStore(max_sessions=1, max_bytes=40)
    with store.checkout(('a', '1')) as (_, save):
        save({'v': 'old'})
        assert not save({'v': 'x' * 100})
        with pytest.raises(SessionBusy):
            with store.checkout(('b', '1')): pass
    with store.checkout(('a', '1')) as (memory, _): assert memory == {'v': 'old'}
    with store.checkout(('b', '1')) as (memory, _): assert memory == {}
    assert len(store.entries) == 1


@pytest.mark.parametrize('mode', ['direct', 'auto'])
def test_executor_commits_before_final_and_cancel_does_not_overwrite(monkeypatch, mode):
    store = QuerySessionStore()
    monkeypatch.setattr('app.core.query_sessions.query_sessions', store)
    executor = WorkflowExecutor(SimpleNamespace(merged_catalog=None))
    seen = []
    def run(question, run_id, cancel, overrides):
        seen.append(overrides['_query_session_context'])
        yield {'type': 'run_start'}
        yield {'type': 'final', 'answer': question, '_query_session_memory': {'answer': question}}
    monkeypatch.setattr(executor, '_execute_stream', run)
    opts = {'query_mode': mode, '_query_session_key': ('owner', 'id')}
    first = list(executor.execute_stream('xnet pods', workflow_overrides=opts))
    assert first[-1]['session_memory'] == 'saved'
    assert '_query_session_memory' not in first[-1]
    second = list(executor.execute_stream('他们的 CPU？', workflow_overrides=opts))
    assert seen[-1] == {'answer': 'xnet pods'}
    assert second[0]['session_memory'] == 'restored'
    cancel = threading.Event(); cancel.set()
    list(executor.execute_stream('cancelled', cancel_event=cancel, workflow_overrides=opts))
    with store.checkout(('owner', 'id')) as (memory, _):
        assert memory == {'answer': '他们的 CPU？'}
