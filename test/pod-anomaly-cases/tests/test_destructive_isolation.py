import os
import unittest

try:
    from .helpers import ROOT
except ImportError:
    from helpers import ROOT


class DestructiveIsolationTests(unittest.TestCase):
    def test_manual_scenarios_are_not_in_safe_bundle(self):
        safe = (ROOT / "safe/kustomization.yaml").read_text(encoding="utf-8")
        self.assertNotIn("destructive", safe)

    def test_manual_runbooks_explain_controlled_operation(self):
        for name in ("node-lost", "evicted-node-pressure"):
            with self.subTest(name=name):
                text = (ROOT / f"destructive/{name}/README.md").read_text(encoding="utf-8").lower()
                for section in ("preflight", "blast radius", "manual confirmation", "trigger", "recovery", "cleanup"):
                    self.assertIn(section, text)

    def test_candidates_cannot_inject_node_failure(self):
        for path in (ROOT / "destructive").rglob("*"):
            if path.is_file() and path.suffix in {".sh", ".py"}:
                self.fail(f"executable fault injector is not allowed: {path}")
        for path in (ROOT / "destructive").rglob("candidate.yaml"):
            text = path.read_text(encoding="utf-8")
            for token in ("kind: DaemonSet", "privileged: true", "hostPath:", "hostPID: true", "hostNetwork: true"):
                self.assertNotIn(token, text)
            self.assertIn("resources:", text)
            self.assertIn("readOnlyRootFilesystem: true", text)


if __name__ == "__main__":
    unittest.main()
