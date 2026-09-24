"""Freeze complete evidence messages before relocating pure instructions."""

import hashlib
import json

import pytest

from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode as Node


QUESTION = "中文问题 {literal}\n`quote` \t"
HANDOFF = {"primary_pod": {"namespace": "demo", "name": "api"}}
PLAN = [{"id": "证据-1", "tool": "query_pod_logs", "tool_args": {"q": "原文"}}]
USER_CASES = {
    "empty": {},
    "legacy": {"layer_handoff": json.dumps(HANDOFF)},
    "autonomous": {"layer_handoff": json.dumps(HANDOFF), "observability_mode": "autonomous"},
    "existing": {"existing_plan": PLAN, "layer_handoff": json.dumps(HANDOFF)},
    "existing_autonomous": {
        "existing_plan": PLAN, "layer_handoff": json.dumps(HANDOFF),
        "observability_mode": "autonomous", "strict_mode": True,
        "failure_reason": "错误 {literal}\n原文",
    },
    "existing_invalid_item": {"existing_plan": [None]},
    "empty_plan_strict": {"existing_plan": [], "strict_mode": True},
    "strict_reason": {"strict_mode": True, "failure_reason": "没有结果 {raw}"},
    "react_only": {"plan_mode": "react_only"},
    "preplanned": {"plan_mode": "preplanned_execution"},
    "unknown_mode": {"plan_mode": "unknown"},
    "archive": {"context_archive_ref": "  archive://context  "},
    "handoff_archive": {"layer_archive_ref": {"handoff_ref": "archive://handoff"}},
    "both_archives": {
        "context_archive_ref": "archive://context",
        "layer_archive_ref": {"handoff_ref": "archive://handoff"},
    },
    "blank_archive": {"context_archive_ref": " \n\t"},
    "invalid_handoff": {"layer_handoff": "{broken\n原文"},
    "retry": {"layer_handoff": json.dumps({**HANDOFF, "diagnosis_retry": {"why": "错误"}})},
    "retry_long": {"layer_handoff": json.dumps({"diagnosis_retry": {"why": "文" * 18010}})},
    "retry_non_dict": {"layer_handoff": json.dumps({"diagnosis_retry": ["ignored"]})},
}


def outputs():
    """Run actual parsing, payload filtering and rendering without a model."""
    result = {}
    for name, overrides in USER_CASES.items():
        arguments = {"question": QUESTION, "layer": "L2", "layer_handoff": "{}"}
        arguments.update(overrides)
        result[name] = Node._build_evidence_user_message(**arguments)
    for mode in ("legacy", "autonomous", " AuToNoMoUs "):
        for count in (0, 1, 9):
            handoff = {"abnormal_pods": [
                {"namespace": "demo", "name": f"api-{i}"} for i in range(count)
            ]}
            result[f"guidance:{mode}:{count}"] = Node._build_live_observability_plan_guidance(
                QUESTION, handoff, observability_mode=mode
            )
    for name, failures in (
        ("empty", []),
        ("unicode", [{"error": "错误\n原文", "failed_tool_args": {"x": "{literal}"}}]),
        ("default_str", [{"value": complex(1, 2)}]),
    ):
        result[f"repair:{name}"] = Node._build_failed_observability_retry_message(
            question=QUESTION, failures=failures
        )
    return result


EXPECTED = {
    "empty": "c728c4542cdd1fff79627c04fcc38e6a70d35717e67a8d458fe0842b435bf83e",
    "legacy": "0c45f3e9b36559e433a5768140a8bdd644fae86186a1e9cc9b4bd8c1ff1206db",
    "autonomous": "8c6e886c8d1f0c2db2ef4d0fdfcaf45cc26f7209436146b20924a627cbd895cc",
    "existing": "e747f0e9a3344b7a894b4b6194f51523b2369c91597332dbd47d184bd182c4ec",
    "existing_autonomous": "05f57f120bb9ab0480d559d865b28038883b7c3dcf2484ff8cbc8fa10d8e5bb3",
    "existing_invalid_item": "59ab63fd1a73776b6821338a49cbd533ab473b63709430ca2fc1e72a1cd1a1c9",
    "empty_plan_strict": "97dec1d7863a42a4cffe7d97f6621dc7297405a5236490f6447240ae9c0e12dc",
    "strict_reason": "e665fc72382328cfbbf97008597d955bf98fd83840d5732973ba0f202671f15a",
    "react_only": "1592233557effc192218a1a6e09e782d4f2cedfc22232dd3da082fbb5c963e6b",
    "preplanned": "f10a9d74595001ccaa7885a3578d24516cfcdff7e49ed5ca80b4385d327d206b",
    "unknown_mode": "c728c4542cdd1fff79627c04fcc38e6a70d35717e67a8d458fe0842b435bf83e",
    "archive": "5a1b569a43768580c4cdaaf885109b849c8fee14923a72de377b77cac089bfce",
    "handoff_archive": "e8732aa45cab0cfd1d60aabf77dbf7e7b9e14d225a1da21db5df263d74ecb034",
    "both_archives": "ab0b86222cd96122be8727ecb47f33ff533567b75a4c67f31375a6543a1db4d2",
    "blank_archive": "c728c4542cdd1fff79627c04fcc38e6a70d35717e67a8d458fe0842b435bf83e",
    "invalid_handoff": "e8dce0bbb846905a056221c95963424211634a366eebd19cbac8b242d5edcd95",
    "retry": "00200d62cc7014334fda4319a3b930cefb195894c420c8eb6a56a737d5336796",
    "retry_long": "6ae5ae6e17655becbe96cc946ad0da48c8895798601ea85f55d669691a8c38f3",
    "retry_non_dict": "e8f70dace48e0b72f05b7d0140b402e8338ccce6562b013cc10fe7651c310d99",
    "guidance:legacy:0": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "guidance:legacy:1": "e66fa41f74f03a0bbfd828d46e45a244ec652f509354d6d6980fbf04e262b359",
    "guidance:legacy:9": "a9b9ec0ac4ad20b76f3871d3c86a5f5ed64c589240b27b36c07df935d7885668",
    "guidance:autonomous:0": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "guidance:autonomous:1": "276dfb2a2b4103f95e449865a96ce2b12fedf7a49ae67c0a8f77e41a97a83cb3",
    "guidance:autonomous:9": "3d07ff8707e0387132b9656df7fdadd0f4a71bfde5ebd1653c851fba8d3864a8",
    "guidance: AuToNoMoUs :0": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "guidance: AuToNoMoUs :1": "276dfb2a2b4103f95e449865a96ce2b12fedf7a49ae67c0a8f77e41a97a83cb3",
    "guidance: AuToNoMoUs :9": "3d07ff8707e0387132b9656df7fdadd0f4a71bfde5ebd1653c851fba8d3864a8",
    "repair:empty": "8ad7efdfda59ed8cc6dd27090dfa4843985d4ecb32d8154d0dfd463adfcd3134",
    "repair:unicode": "988248aa326a53f7b7eec2409690022e38c49d8fc3390f1419457862cd8e2fa3",
    "repair:default_str": "31fab307c0eafa144852cbc4c3bbfbc7b17082efccffcb226cc4f306209f8dae",
}


@pytest.mark.parametrize("case", list(USER_CASES) + [
    f"guidance:{mode}:{count}"
    for mode in ("legacy", "autonomous", " AuToNoMoUs ") for count in (0, 1, 9)
] + ["repair:empty", "repair:unicode", "repair:default_str"])
def test_complete_evidence_message_utf8_bytes(case):
    # Arrange/Act: full production method output, not the extracted constants.
    message = outputs()[case]

    # Assert: SHA-256 freezes every UTF-8 byte, including whitespace and JSON.
    assert hashlib.sha256(message.encode("utf-8")).hexdigest() == EXPECTED[case]


def test_retry_compatibility_alias():
    args = {"question": QUESTION, "failures": [{"error": "错误"}]}
    assert Node._build_failed_baseline_retry_message(**args) == (
        Node._build_failed_observability_retry_message(**args)
    )
