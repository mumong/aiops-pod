"""read_context_archive explains how to read a runbook instead of a bare path error."""

from app.core.aicall.builtin_tools import ReadContextArchiveTool


def test_runbook_like_path_gets_fetch_runbook_hint(tmp_path):
    tool = ReadContextArchiveTool(allowed_roots=[str(tmp_path)])
    text = tool._run("raw_ref/runbook_ref/private-k8s-query-promql-reference.md")
    assert "fetch_runbook(runbook_id='private-k8s-query-promql-reference')" in text
    other = tool._run("/etc/passwd")
    assert "not under allowed archive roots" in other
