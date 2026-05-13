#!/usr/bin/env python3
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class TestL4ConfigBootstrapAssets(unittest.TestCase):
    def test_manifest_exists(self) -> None:
        manifest = ROOT / "test/e2e/manifests/pod-config-error.yaml"
        self.assertTrue(manifest.exists(), f"missing manifest: {manifest}")

    def test_old_l4_assets_are_gone_from_e2e_surface(self) -> None:
        checked_files = [
            ROOT / "test/e2e/run_all.sh",
            ROOT / "test/e2e/validate.sh",
            ROOT / "test/e2e/test_scenarios.sh",
            ROOT / "test/e2e/test_accuracy.py",
            ROOT / "test/e2e/README.md",
            ROOT / "deploy/configmap/runbooks.yaml",
        ]
        for path in checked_files:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("l4-app-health-fail", text, f"old runbook id still present in {path}")
            self.assertNotIn("apphealth", text, f"old deployment name still present in {path}")

    def test_new_l4_assets_are_referenced(self) -> None:
        expectations = {
            ROOT / "test/e2e/run_all.sh": [
                "pod-config-error.yaml",
                "appconfigfail",
            ],
            ROOT / "test/e2e/validate.sh": [
                "appconfigfail",
                "Config Bootstrap Fail",
            ],
            ROOT / "test/e2e/test_scenarios.sh": [
                "L4-ConfigBootstrapFail",
                "appconfigfail",
            ],
            ROOT / "test/e2e/test_accuracy.py": [
                "pod-config-error",
                "pod-config-error",
            ],
            ROOT / "test/e2e/README.md": [
                "pod-config-error.yaml",
                "pod-config-error.md",
            ],
            ROOT / "deploy/configmap/runbooks.yaml": [
                "\"id\": \"pod-config-error\"",
                "pod-config-error.md",
            ],
        }

        for path, snippets in expectations.items():
            text = path.read_text(encoding="utf-8")
            for snippet in snippets:
                self.assertIn(snippet, text, f"{snippet!r} missing in {path}")


if __name__ == "__main__":
    unittest.main()
