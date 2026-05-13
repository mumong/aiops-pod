import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.aicall.builtin_tools import FetchRunbookTool, ReadContextArchiveTool


def test_read_context_archive_tool_reads_allowed_file(tmp_path):
    archive_root = tmp_path / "context_archives"
    archive_file = archive_root / "run-1" / "tools" / "001-layer-kubectl_events.summary.txt"
    archive_file.parent.mkdir(parents=True)
    archive_file.write_text("Failed to pull image: i/o timeout", encoding="utf-8")

    tool = ReadContextArchiveTool(allowed_roots=[str(archive_root)], default_length=200)
    result = tool._run(str(archive_file))

    assert "archive_path:" in result
    assert "Failed to pull image" in result


def test_read_context_archive_tool_rejects_path_outside_allowed_roots(tmp_path):
    archive_root = tmp_path / "context_archives"
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("secret", encoding="utf-8")

    tool = ReadContextArchiveTool(allowed_roots=[str(archive_root)], default_length=200)
    result = tool._run(str(outside_file))

    assert "not under allowed archive roots" in result


def test_fetch_runbook_tool_rejects_disabled_runbook(tmp_path):
    runbook_dir = tmp_path / "runbooks"
    runbook_dir.mkdir()
    (runbook_dir / "private-k8s-health-reference.md").write_text("# private health", encoding="utf-8")

    tool = FetchRunbookTool(
        runbook_dirs=[str(runbook_dir)],
        allowed_runbook_ids=["pod-oomkilled", "private-k8s-query-promql-reference"],
    )
    result = tool._run("private-k8s-health-reference.md")

    assert "disabled by the current runtime profile" in result


def test_fetch_runbook_tool_allows_pod_abnormal_status_runbook(tmp_path):
    runbook_dir = tmp_path / "runbooks"
    runbook_dir.mkdir()
    (runbook_dir / "pod-sandbox-create-failed.md").write_text("# sandbox failed", encoding="utf-8")

    tool = FetchRunbookTool(runbook_dirs=[str(runbook_dir)])
    result = tool._run("pod-sandbox-create-failed.md")

    assert "<runbook>" in result
    assert "sandbox failed" in result
