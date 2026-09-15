import unittest

try:
    from .helpers import ROOT, load_catalog
except ImportError:
    from helpers import ROOT, load_catalog


class DocumentationTests(unittest.TestCase):
    def test_operator_workflow_and_evidence_boundaries_are_documented(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        lower = text.lower()
        for heading in ("前置条件", "部署、验证和清理", "基础场景", "遥测如何产生",
                        "后端连接与验收", "agent 与实验库的边界", "节点级场景"):
            self.assertIn(heading, lower)
        for command in ("kubectl apply -k test/pod-anomaly-cases/cases/oomkilled-traced",
                        "kubectl kustomize test/pod-anomaly-cases/safe",
                        "make case-deploy-all", "make case-deploy-errors",
                        "test/pod-anomaly-cases/scripts/validate.sh --case c08",
                        "make case-clean", "make case-clean-variants"):
            self.assertIn(command, text)
        self.assertIn("Multus", text)

    def test_runtime_telemetry_boundaries_and_mcp_tools_are_explicit(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for command in (
            "kubectl apply -k test/pod-anomaly-cases/cases/terminating-stuck",
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

    def test_safety_and_aiops_scope_limit_are_documented(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for signal in ("专用测试集群", "不要提交凭据", "不自动停止 kubelet",
                       "不属于 safe 批量入口", "清理会删除对应 namespace 内的资源",
                       "不能用 Node IP flow 冒充", "应用未启动",
                       "Prometheus", "Elasticsearch", "DeepFlow", "Tempo", "跨 namespace"):
            self.assertIn(signal, text)


if __name__ == "__main__":
    unittest.main()
