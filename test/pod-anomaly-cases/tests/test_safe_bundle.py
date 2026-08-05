import re
import unittest

try:
    from .helpers import ROOT, render
except ImportError:
    from helpers import ROOT, render


class SafeBundleTests(unittest.TestCase):
    def test_terminating_case_is_standalone_and_observable(self):
        output = render("cases/terminating-stuck")
        self.assertRegex(output, r"kind: Pod\nmetadata:\n(?:.*\n)*?  name: workload")
        self.assertIn("name: aiops-case-11", output)
        self.assertIn("finalizers:\n  - aiops.lab/hold", output)
        self.assertIn("name: traffic-driver", output)
        self.assertIn("kind: Service", output)
        self.assertIn("prometheus.io/scrape: \"true\"", output)
        documents = output.split("\n---\n")
        self.assertFalse(any("kind: Deployment" in doc and "name: workload\n" in doc for doc in documents))
        for token in ("hostNetwork: true", "hostPID: true", "hostPath:", "privileged: true"):
            self.assertNotIn(token, output)

    def test_terminating_case_reuses_exact_server_source(self):
        base = render("base/telemetry-app")
        case = render("cases/terminating-stuck")
        marker = "  server.py: |\n"
        base_server = base.split(marker, 1)[1].split("\nkind: ConfigMap", 1)[0]
        case_server = case.split(marker, 1)[1].split("\nkind: ConfigMap", 1)[0]
        self.assertEqual(case_server, base_server)

    def test_safe_bundle_lists_exactly_eleven_cases(self):
        text = (ROOT / "safe/kustomization.yaml").read_text(encoding="utf-8")
        resources = [line.strip()[2:] for line in text.splitlines() if line.strip().startswith("- ../cases/")]
        self.assertEqual(len(resources), 11)
        self.assertEqual(len(set(resources)), 11)
        self.assertNotIn("destructive", text)
        rendered = render("safe")
        self.assertEqual(len(re.findall(r"(?m)^kind: Namespace$", rendered)), 11)


if __name__ == "__main__":
    unittest.main()
