"""Markdown reporting must preserve scoring and expose per-case results."""
import copy
import json
import sys
from pathlib import Path

import pytest

DEMO = Path(__file__).resolve().parents[3] / "test/aiops_quality_e2e"
sys.path.insert(0, str(DEMO))
from run_quality_demo import build_readme, write_readme_reports, write_checkpoint


def run(index=1, *, root=True, rb=1.0, evidence=1.0):
    return {"run_index": index, "run_id": f"id{index}", "success": True,
            "elapsed_seconds": 60, "root_cause": {"passed": root},
            "runbook": {"coverage": rb},
            "evidence": {"planned": 4, "collected": 4, "completeness": evidence}}


def sample_stats():
    return {"status": "completed", "scoring_version": "unchanged", "planned_runs": 3,
            "scenarios": [
                {"id": "c01", "anomaly_type": "Pending", "runs": [run()]},
                {"id": "c02", "anomaly_type": "ImagePull", "runs": [run(root=False, rb=.5, evidence=.5), run(2)]},
            ]}


def test_root_and_case_readmes_use_case_means_and_preserve_source(tmp_path):
    stats = sample_stats()
    before = copy.deepcopy(stats)
    source = tmp_path / "c01/run-01-id1"
    source.mkdir(parents=True)
    (source / "report.md").write_text("original report")
    (source / "score.json").write_text("original score")
    (tmp_path / "stats.json").write_text("original stats")
    write_readme_reports(tmp_path, stats)
    root = (tmp_path / "readme.md").read_text()
    assert "[c01](c01/readme.md)" in root
    assert "[c02](c02/readme.md)" in root
    assert "| 根因准确率 | 75.0%" in root  # not pooled 2/3
    assert "| Runbook 覆盖率 | 87.5%" in root
    assert "| 证据完整度 | 87.5%" in root
    case = (tmp_path / "c02/readme.md").read_text()
    assert "| 根因准确率 | 50.0%" in case
    assert "## 每次运行" in case
    assert "run-01-id1/report.md" in (tmp_path / "c01/readme.md").read_text()
    assert stats == before
    assert (source / "report.md").read_text() == "original report"
    assert (source / "score.json").read_text() == "original score"
    assert (tmp_path / "stats.json").read_text() == "original stats"


def test_checkpoint_publishes_readmes_for_future_runs(tmp_path):
    stats = sample_stats()
    write_checkpoint(tmp_path, stats)
    assert json.loads((tmp_path / "stats.json").read_text()) == stats
    assert (tmp_path / "readme.md").is_file()
    assert (tmp_path / "c01/readme.md").is_file()


def test_partial_missing_and_failed_samples_are_visible(tmp_path):
    stats = sample_stats()
    stats["status"] = "running"
    stats["rescore_complete"] = False
    stats["scenarios"][0]["runs"] = [run(evidence=None)]
    stats["scenarios"][1]["runs"] = [{"success": False, "run_index": 1, "elapsed_seconds": 1200}]
    write_readme_reports(tmp_path, stats)
    root = (tmp_path / "readme.md").read_text()
    assert "任务状态：running" in root
    assert "待复核" in root
    assert "证据完整度有效样本 0/1" in root
    assert "无成功样本" in root
    assert "N/A" in (tmp_path / "c02/readme.md").read_text()


def test_rescore_readme_links_original_report_and_separates_audit(tmp_path):
    stats = sample_stats()
    source = tmp_path / "source/c01/run-01-id1"
    source.mkdir(parents=True)
    report = source / "report.md"
    report.write_text("original")
    revision = tmp_path / "revision"
    revision.mkdir()
    stats["source_report_dir"] = str(tmp_path / "source")
    (revision / "manual_review.md").write_text("independent review")
    write_readme_reports(revision, stats)
    assert "../../source/c01/run-01-id1/report.md" in (revision / "c01/readme.md").read_text()
    assert "manual_review.md" in (revision / "readme.md").read_text()
    assert (revision / "manual_review.md").read_text() == "independent review"


def test_markdown_escaping_and_unsafe_case_directory(tmp_path):
    stats = sample_stats()
    stats["scenarios"][0]["anomaly_type"] = "A|B\nC"
    assert "A\\|B C" in build_readme(stats, tmp_path)
    stats["scenarios"][0]["id"] = "../escape"
    with pytest.raises(ValueError, match="unsafe scenario"):
        write_readme_reports(tmp_path, stats)
