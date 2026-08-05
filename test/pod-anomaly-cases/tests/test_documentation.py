import unittest

try:
    from .helpers import ROOT, load_catalog
except ImportError:
    from helpers import ROOT, load_catalog


class DocumentationTests(unittest.TestCase):
    def test_operator_workflow_and_evidence_boundaries_are_documented(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        lower = text.lower()
        for heading in ("prerequisites", "quick start", "architecture", "current aiops behavior", "individual apply",
                        "safe apply", "validation", "cleanup", "backend configuration", "evidence matrix",
                        "expected absent signals", "observability conclusions", "mcp compatibility",
                        "aiops black-box", "destructive separation"):
            self.assertIn(heading, lower)
        for command in ("kubectl apply -k pod-anomaly-cases/cases/oomkilled-traced",
                        "kubectl apply -k pod-anomaly-cases/safe",
                        "pod-anomaly-cases/scripts/deploy-safe.sh",
                        "pod-anomaly-cases/scripts/validate.sh --case c08",
                        "pod-anomaly-cases/scripts/cleanup.sh"):
            self.assertIn(command, text)
        self.assertIn("Multus", text)

    def test_runtime_telemetry_boundaries_and_mcp_tools_are_explicit(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for command in (
            "kubectl apply -k pod-anomaly-cases/cases/config-error-traced",
            "kubectl -n aiops-case-11 wait --for=condition=Ready pod/workload --timeout=180s",
            "kubectl -n aiops-case-11 logs pod/workload --tail=20",
            "kubectl -n aiops-case-11 delete pod workload --wait=false",
        ):
            self.assertIn(command, text)
        for contract_term in (
            "execute_pod_promql",
            "query_pod_logs",
            "query_pod_tracing",
            "query_pod_topology",
            "deletionTimestamp + finalizer",
        ):
            self.assertIn(contract_term, text)
        self.assertIn("c04", text)
        self.assertIn("c07", text)

    def test_every_catalog_directory_is_documented(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for case in load_catalog()["cases"]:
            self.assertIn(case["directory"], text)

    def test_live_acceptance_and_aiops_scope_limit_are_documented(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for signal in ("## Live acceptance", "Prometheus", "Elasticsearch", "DeepFlow", "Tempo",
                       "single-case", "跨 namespace"):
            self.assertIn(signal, text)


if __name__ == "__main__":
    unittest.main()
