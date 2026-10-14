"""Golden prompt bytes captured before the compatibility-template extraction."""

import hashlib

import pytest

from app.core import prompts


@pytest.mark.parametrize(
    "name,digest",
    [
        ("FOCUSED_PROMPT", "0a6284e75fe91a0891c5598763e8d2cacc078bcc248f486d622aa753c49b0686"),
        (
            "FOCUSED_RESULT_PROMPT",
            "60e43bb766cfa4b70aad15e4c501f43169a77ba6872914feb7906bd882c36389",
        ),
        (
            "LEGACY_CONTEXT_COMPRESSION_PROMPT",
            "93607a1c021bfe307ec2f614839fa79d6d10c7515cca3a87a83458e4f5a74661",
        ),
        (
            "EVIDENCE_MEMORY_COMPRESSION_PROMPT",
            "4979155e45628eb49bbb2ff87afb87ae4c8d17976a1e8abe979b227d191834f1",
        ),
        (
            "FEDERATION_SYNTHESIS_PROMPT",
            "f5a71a6bd55818a066740de350f075283b0537ff5a2b8f0ebbfa11fb00e8a6b2",
        ),
        (
            "FEDERATION_COMPRESSION_PROMPT",
            "ebd98d95748e535e64db8c2e17b5b98c52bffc42ab90c5dfa7bc6c1160a97019",
        ),
        (
            "LEGACY_REMEDIATION_AGENT_PROMPT",
            "e9c0142d3ed76df19ef01a213f349baf6b83e9856bb8339df2c6c4d2e01af196",
        ),
    ],
)
def test_prompt_bytes_remain_unchanged(name, digest):
    # Arrange: load the public prompt configuration entry point.
    value = getattr(prompts, name)

    # Act: hash precisely what is sent to models, including whitespace.
    actual = hashlib.sha256(value.encode()).hexdigest()

    # Assert: moving templates must not change their model-facing behavior.
    assert actual == digest
