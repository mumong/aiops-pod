import re
import unittest
from pathlib import Path


RUNBOOKS_FILE = Path(__file__).resolve().parents[2] / "deploy/configmap/runbooks.yaml"

TARGET_RUNBOOKS = [
    "pod-evicted.md",
    "pod-volume-mount-failed.md",
    "pod-oomkilled.md",
    "pod-imagepull-failed.md",
    "pod-config-error.md",
    "pod-pending-unschedulable.md",
    "pod-node-lost-unknown.md",
    "pod-terminating-stuck.md",
    "pod-crashloop-runtime.md",
    "pod-sandbox-create-failed.md",
    "pod-notready-probe-failed.md",
]


def _runbook_body(name: str) -> str:
    text = RUNBOOKS_FILE.read_text(encoding="utf-8")
    pattern = rf"^  {re.escape(name)}: \|\n(?P<body>.*?)(?=^  [a-z0-9-]+\.md: \||^  private-k8s-query-promql-reference\.md: \||\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        raise AssertionError(f"runbook {name} not found")
    return match.group("body")


class RunbookRemediationGuidanceTest(unittest.TestCase):
    def test_all_active_pod_runbooks_have_standard_remediation_section(self):
        missing = [name for name in TARGET_RUNBOOKS if "## 标准修复建议" not in _runbook_body(name)]
        self.assertEqual([], missing)

    def test_terminating_finalizer_patch_is_preferred_over_force_delete(self):
        body = _runbook_body("pod-terminating-stuck.md")
        self.assertIn("kubectl patch pod <pod> -n <namespace> -p '{\"metadata\":{\"finalizers\":null}}' --type=merge", body)
        self.assertIn("finalizers 为空时禁止按 finalizer 清理", body)
        self.assertIn("delete --force", body)
        self.assertLess(body.index("kubectl patch pod"), body.index("delete --force"))

    def test_dangerous_actions_are_marked_as_fallbacks(self):
        body = _runbook_body("pod-terminating-stuck.md")
        self.assertIn("delete --force", body)
        fallback_window = body[body.index("delete --force") - 80 : body.index("delete --force") + 160]
        self.assertRegex(fallback_window, r"应急|最后|fallback|兜底|风险")


if __name__ == "__main__":
    unittest.main()
