"""Tool arguments are serialized data, not executable model output."""

import pytest

from app.core.federation.agent import FederationAgent


@pytest.mark.parametrize(
    "raw, expected",
    [
        (
            '{"cluster": "main", "count": 1, "enabled": true}',
            {"cluster": "main", "count": 1, "enabled": True},
        ),
        (
            "{'cluster': 'main', 'enabled': True, 'optional': None}",
            {"cluster": "main", "enabled": True, "optional": None},
        ),
        ('{"question": "查询 CPU 与内存"}', {"question": "查询 CPU 与内存"}),
    ],
)
def test_json_and_legacy_literal_arguments_are_preserved(raw, expected):
    # Arrange: parsing needs no client, credentials, or cluster connection.
    agent = object.__new__(FederationAgent)

    # Act.
    parsed = agent._parse_tool_args(raw)

    # Assert.
    assert parsed == expected


def test_nonliteral_python_calls_are_rejected():
    # Arrange: a harmless call demonstrates the data/code boundary without side effects.
    agent = object.__new__(FederationAgent)

    # Act/Assert: valid Python is not necessarily valid serialized tool arguments.
    with pytest.raises((ValueError, SyntaxError)):
        agent._parse_tool_args("{'cluster': str(1)}")
