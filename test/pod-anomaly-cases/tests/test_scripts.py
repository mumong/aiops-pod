import unittest
import subprocess
import json
import tempfile
from pathlib import Path

try:
    from .helpers import ROOT
except ImportError:
    from helpers import ROOT


class ScriptContractTests(unittest.TestCase):
    def test_oom_testpoint1_is_one_safe_self_configuring_entry(self):
        path = ROOT / "scripts/oom-testpoint1.sh"
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        self.assertIn("set -euo pipefail", text)
        for command in ("run", "collect", "cleanup"):
            self.assertIn(command, text)
        self.assertIn("--namespace", text)
        self.assertIn("--pod", text)
        self.assertIn("case_namespace=aiops-case-08", text)
        self.assertIn('kubectl delete namespace "${case_namespace}"', text)
        self.assertIn("collect_case.py", text)
        self.assertIn("summarize_oom_case.py", text)
        self.assertIn("audit_aiops_case.py", text)
        self.assertIn("port-forward", text)
        self.assertIn("trap", text)
        self.assertIn("elasticsearch-master-credentials", text)
        self.assertIn("observability_wait_seconds=90", text)
        self.assertIn("kubectl version -o json", text)
        self.assertIn("kubectl python3 base64 jq", text)
        self.assertNotIn("set -x", text)
        for unsafe in ("--all", "aiops-case-*", "delete node", "delete namespace -A"):
            self.assertNotIn(unsafe, text)

    def test_oom_testpoint1_view_prints_core_multimodal_evidence(self):
        script = ROOT / "scripts/oom-testpoint1.sh"
        with tempfile.TemporaryDirectory() as temporary:
            case_dir = Path(temporary)
            evidence = case_dir / "evidence"
            evidence.mkdir()
            summary = {
                "status": "PASS",
                "case_id": "oom-fixture",
                "input": {"namespace": "aiops-case-08", "pod": "workload-fixture"},
                "oom": {"reason": "OOMKilled", "exit_code": 137, "restart_count": 2},
                "metrics": {
                    "memory_working_set_bytes": {"start": 1048576, "max": 62914560, "last": 2097152},
                    "memory_limit_bytes": 67108864,
                    "restart_count": {"start": 0, "last": 1},
                },
                "evidence_counts": {
                    "kubernetes": 10, "metrics": 4, "logging": 2,
                    "deepflow_l4": 1, "deepflow_l7": 1, "tempo_traces": 1,
                },
                "correlation": {"common_trace_ids": ["a" * 32]},
                "errors": [],
            }
            (case_dir / "acceptance-summary.json").write_text(json.dumps(summary), encoding="utf-8")
            rows = {
                "metrics.jsonl": [{
                    "query_id": "prometheus:kube_pod_container_status_last_terminated_reason",
                    "summary": "last terminated reason=OOMKilled",
                }],
                "logs.jsonl": [{
                    "summary": "memory allocation advanced",
                    "raw": {"message": json.dumps({"allocated_mib": 60, "trace_id": "a" * 32})},
                }],
                "deepflow_l7.jsonl": [{
                    "raw": {"ip4_0": "10.0.0.1", "ip4_1": "10.0.0.2", "request_type": "GET",
                            "request_resource": "/work", "response_code": 200, "trace_id": "a" * 32},
                }],
                "tempo_traces.jsonl": [{
                    "raw": {"trace_id": "a" * 32, "spans": [{"service": "aiops-lab-workload",
                            "name": "GET /work", "duration_ms": 3.7}]},
                }],
            }
            for name, content in rows.items():
                (evidence / name).write_text(
                    "".join(json.dumps(row) + "\n" for row in content), encoding="utf-8"
                )
            (evidence / "k8s_pod.yaml").write_text("{}\n", encoding="utf-8")

            completed = subprocess.run(
                [str(script), "view", "--case", str(case_dir)],
                cwd=ROOT.parent,
                text=True,
                capture_output=True,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        for heading in ("KUBERNETES", "PROMETHEUS", "LOGGING", "DEEPFLOW", "TEMPO", "RAW EVIDENCE"):
            self.assertIn(heading, completed.stdout)
        self.assertIn("OOMKilled", completed.stdout)
        self.assertIn("max=60 MiB", completed.stdout)
        self.assertIn("allocated_mib=60", completed.stdout)
        self.assertIn("correlated_log: allocated_mib=60", completed.stdout)
        self.assertIn("trace_id=" + "a" * 32, completed.stdout)
        self.assertIn("jq .", completed.stdout)

    def test_oom_testpoint1_reuses_existing_namespace_without_applying(self):
        text = (ROOT / "scripts/oom-testpoint1.sh").read_text(encoding="utf-8")
        run_case = text[text.index("run_case() {"):text.index("\ncleanup_case() {")]
        self.assertIn("REUSING_EXISTING_CASE", run_case)
        self.assertIn("reuse_existing=true", run_case)
        self.assertIn('if [[ "${reuse_existing}" == false ]]', run_case)
        self.assertNotIn("already exists", run_case)

    def test_deploy_is_preflighted_and_c11_trigger_is_exact(self):
        text = (ROOT / "scripts/deploy-safe.sh").read_text(encoding="utf-8")
        self.assertIn("set -euo pipefail", text)
        self.assertLess(text.index("kubectl kustomize"), text.index("kubectl apply"))
        self.assertIn("kubectl -n aiops-case-11 wait", text)
        self.assertIn("kubectl -n aiops-case-11 delete pod workload --wait=false", text)
        self.assertIn("deletionTimestamp", text)
        self.assertIn("http_request", text)
        self.assertIn("validate.sh", text)

    def test_cleanup_uses_only_exact_catalog_namespaces(self):
        text = (ROOT / "scripts/cleanup.sh").read_text(encoding="utf-8")
        self.assertIn("set -euo pipefail", text)
        for i in range(1, 12):
            self.assertIn(f"aiops-case-{i:02d}", text)
        self.assertIn("pod workload", text)
        self.assertIn("remove", text)
        self.assertNotIn("--wait=false", text)
        for unsafe in ("--all", "aiops-case-*", "delete node", "delete namespace -A"):
            self.assertNotIn(unsafe, text)

    def test_validation_wrapper_does_not_publish_credentials(self):
        text = (ROOT / "scripts/validate.sh").read_text(encoding="utf-8")
        self.assertIn("verify_observability.py", text)
        self.assertNotIn("set -x", text)

    def test_local_backend_credentials_file_is_ignored(self):
        completed = subprocess.run(
            ["git", "check-ignore", "pod-anomaly-cases/config.env"],
            cwd=ROOT.parent, text=True, capture_output=True,
        )
        self.assertEqual(completed.returncode, 0)


if __name__ == "__main__":
    unittest.main()
