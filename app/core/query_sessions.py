"""Bounded anonymous short-term memory; one active writer per conversation."""
import copy
import json
import threading
import time
from collections import OrderedDict
from contextlib import contextmanager


class SessionBusy(RuntimeError):
    pass


class QuerySessionStore:
    def __init__(self, ttl=1800, max_sessions=64, max_bytes=262144, clock=time.monotonic):
        self.ttl, self.max_sessions, self.max_bytes, self.clock = ttl, max_sessions, max_bytes, clock
        self.entries = OrderedDict()
        self.lock = threading.Lock()

    @contextmanager
    def checkout(self, key):
        with self.lock:
            now = self.clock()
            for old, entry in list(self.entries.items()):
                if not entry['busy'] and now - entry['touched'] >= self.ttl:
                    del self.entries[old]
            if key not in self.entries:
                if len(self.entries) >= self.max_sessions:
                    victim = next((k for k, e in self.entries.items() if not e['busy']), None)
                    if victim is None:
                        raise SessionBusy('会话容量已满，请稍后重试')
                    del self.entries[victim]
                self.entries[key] = {'memory': {}, 'busy': False, 'touched': now}
            entry = self.entries[key]
            if entry['busy']:
                raise SessionBusy('同一会话已有查询运行，请等待完成后再发送')
            entry['busy'] = True
            self.entries.move_to_end(key)
            snapshot = copy.deepcopy(entry['memory'])
        def commit(memory):
            encoded = json.dumps(memory, ensure_ascii=False, default=str).encode()
            if len(encoded) > self.max_bytes:
                return False
            with self.lock:
                entry['memory'] = copy.deepcopy(memory)
            return True
        try:
            yield snapshot, commit
        finally:
            with self.lock:
                entry['busy'] = False
                entry['touched'] = self.clock()

    def is_busy(self, key):
        with self.lock:
            return bool(self.entries.get(key, {}).get('busy'))


query_sessions = QuerySessionStore()
