import re
import unittest

try:
    from .helpers import ROOT, render
except ImportError:
    from helpers import ROOT, render


class TelemetryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = (ROOT / "base/telemetry-app/app-configmap.yaml").read_text(encoding="utf-8")
        cls.deployment = (ROOT / "base/telemetry-app/deployment.yaml").read_text(encoding="utf-8")
        cls.driver = (ROOT / "base/telemetry-app/driver.yaml").read_text(encoding="utf-8")

    def test_server_has_endpoints_modes_and_bounded_input(self):
        for endpoint in ("/work", "/ready", "/health", "/metrics"):
            self.assertIn(endpoint, self.config)
        for mode in ("normal", "runtime_exit", "config_missing_exit", "oom_growth", "readiness_fail", "liveness_fail"):
            self.assertIn(mode, self.config)
        self.assertIn("traceparent", self.config)
        self.assertIn("MAX_BODY_BYTES", self.config)
        self.assertIn("application/json", self.config)
        self.assertIn("/v1/traces", self.config)

    def test_embedded_python_compiles_and_exit_is_deferred_until_after_response(self):
        data = self.config.split("  server.py: |\n", 1)[1].split("  driver.py: |\n", 1)[0]
        source = "\n".join(line[4:] if line.startswith("    ") else line for line in data.splitlines())
        compile(source, "server.py", "exec")
        self.assertIn("pending_exit", source)
        self.assertLess(source.index("self.send_text(status", source.index("def do_GET")),
                        source.index("exit_later(pending_exit)", source.index("def do_GET")))

    def test_server_emits_correlated_logs_and_metrics(self):
        for key in ("timestamp", "event", "level", "message", "http_status", "path", "duration_ms",
                    "case_run_id", "trace_id", "span_id", "pod", "service", "allocated_mib"):
            self.assertIn(f'"{key}"', self.config)
        for metric in ("aiops_lab_requests_total", "aiops_lab_errors_total", "aiops_lab_duration_ms_total", "aiops_lab_allocated_mib"):
            self.assertIn(metric, self.config)

    def test_driver_uses_pod_uid_and_w3c_context(self):
        self.assertIn("fieldPath: metadata.uid", self.driver)
        self.assertIn("name: CASE_RUN_ID", self.driver)
        self.assertIn("traceparent", self.config)
        self.assertIn("x-aiops-case-run-id", self.config)
        self.assertRegex(self.config, r"sleep\(2\)")

    def test_deployment_is_bounded_and_restricted(self):
        rendered = render("base/telemetry-app")
        for token in ("runAsNonRoot: true", "runAsUser: 1000", "readOnlyRootFilesystem: true",
                      "allowPrivilegeEscalation: false", "automountServiceAccountToken: false",
                      "type: RuntimeDefault", "drop:", "- ALL", "requests:", "limits:"):
            self.assertIn(token, rendered)
        self.assertIn("prometheus.io/scrape: \"true\"", rendered)
        self.assertIn("PYTHONUNBUFFERED", rendered)
        self.assertIn("OTLP_HTTP_ENDPOINT", rendered)
        self.assertNotIn("privileged: true", rendered)


if __name__ == "__main__":
    unittest.main()
