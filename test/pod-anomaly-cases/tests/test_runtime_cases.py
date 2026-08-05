import unittest

try:
    from .helpers import render
except ImportError:
    from helpers import render


EXPECTED = {
    "crashloop-runtime": ("aiops-case-06", "runtime_exit"),
    "config-error-traced": ("aiops-case-07", "config_missing_exit"),
    "oomkilled-traced": ("aiops-case-08", "oom_growth"),
    "readiness-probe-failed": ("aiops-case-09", "readiness_fail"),
    "liveness-probe-failed": ("aiops-case-10", "liveness_fail"),
}


class RuntimeCaseTests(unittest.TestCase):
    def test_overlays_reuse_correlated_telemetry(self):
        for directory, (namespace, mode) in EXPECTED.items():
            with self.subTest(directory=directory):
                output = render(f"cases/{directory}")
                self.assertIn(f"name: {namespace}", output)
                for name in ("workload", "traffic-driver"):
                    self.assertIn(f"name: {name}", output)
                self.assertIn("kind: Service", output)
                self.assertIn(f"value: {mode}", output)
                self.assertIn("http://lgtm.monitor.svc:4318/v1/traces", output)
                self.assertIn("fieldPath: metadata.uid", output)
                self.assertIn("value: aiops-lab-workload", output)

    def test_case_specific_failure_controls(self):
        oom = render("cases/oomkilled-traced")
        self.assertIn("memory: 64Mi", oom)
        self.assertIn("name: OOM_STEP_MIB", oom)
        self.assertIn('value: "2"', oom)
        ready = render("cases/readiness-probe-failed")
        self.assertIn("readinessProbe:", ready)
        self.assertIn("path: /ready", ready)
        self.assertIn("publishNotReadyAddresses: true", ready)
        live = render("cases/liveness-probe-failed")
        self.assertIn("livenessProbe:", live)
        self.assertIn("path: /health", live)
        for directory in ("crashloop-runtime", "config-error-traced"):
            self.assertNotIn("livenessProbe:", render(f"cases/{directory}"))


if __name__ == "__main__":
    unittest.main()
