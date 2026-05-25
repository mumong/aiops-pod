from tools.aiops_remediate_chat import parse_approval_hint


def test_parse_approval_hint_from_stream_line():
    line = (
        "curl -X POST http://<host>/remediation/approve "
        "-d run_id=run123 -d approval_id=approval456 -d approved=true"
    )

    hint = parse_approval_hint(line)

    assert hint == {"run_id": "run123", "approval_id": "approval456"}


def test_parse_approval_hint_ignores_non_approval_line():
    assert parse_approval_hint("普通诊断输出") is None
