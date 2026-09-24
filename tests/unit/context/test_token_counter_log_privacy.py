"""Counting failures must preserve fallback results without logging input data."""
import logging
import sys
from types import SimpleNamespace

import pytest

from app.core.context import budget


@pytest.mark.parametrize('backend', ['json', 'encoding'])
def test_counter_failure_keeps_fallback_and_omits_exception_contents(monkeypatch, caplog, backend):
    private_text = 'synthetic-private-input-do-not-log'

    def fail(*args, **kwargs):
        raise ValueError(private_text)

    monkeypatch.setattr(budget, '_TOKENIZER_CACHE', {})
    monkeypatch.delenv('AIOPS_TOKENIZER_JSON_PATH', raising=False)
    monkeypatch.delenv('AIOPS_TIKTOKEN_ENCODING', raising=False)
    if backend == 'json':
        monkeypatch.setenv('AIOPS_TOKENIZER_JSON_PATH', '/synthetic/counter.json')
        monkeypatch.setitem(sys.modules, 'tokenizers', SimpleNamespace(Tokenizer=SimpleNamespace(from_file=fail)))
    else:
        monkeypatch.setenv('AIOPS_TIKTOKEN_ENCODING', 'synthetic-encoding')
        monkeypatch.setitem(sys.modules, 'tiktoken', SimpleNamespace(get_encoding=fail))

    with caplog.at_level(logging.WARNING, logger=budget.__name__):
        result = budget.count_tokens(private_text)

    assert result == {
        'tokens': budget.estimate_tokens(private_text),
        'source': 'heuristic:utf8_bytes/3',
        'accuracy': 'estimated',
    }
    assert private_text not in caplog.text
    assert 'ValueError' in caplog.text
