import unittest

try:
    from .helpers import BACKENDS, load_catalog
except ImportError:
    from helpers import BACKENDS, load_catalog


class CatalogTests(unittest.TestCase):
    def test_safe_catalog_is_complete(self):
        catalog = load_catalog()
        self.assertEqual(catalog["schema_version"], "aiops.pod-anomaly-catalog.v1")
        cases = catalog["cases"]
        self.assertEqual([item["id"] for item in cases], [f"c{i:02d}" for i in range(1, 12)])
        self.assertTrue(all(item["safe"] for item in cases))
        self.assertEqual(len({item["directory"] for item in cases}), 11)
        self.assertEqual(len({item["namespace"] for item in cases}), 11)
        for item in cases:
            self.assertEqual(set(item["coverage"]), BACKENDS)
            self.assertGreater(item["timeout_seconds"], 0)
            self.assertTrue(item["status_gate"])
            self.assertEqual(item["cleanup"]["namespace"], item["namespace"])
            self.assertEqual(item["workload_name"], "workload")
            self.assertIn("evidence_examples", item)

    def test_control_plane_cases_do_not_claim_runtime_telemetry(self):
        for item in load_catalog()["cases"][:5]:
            self.assertIn(item["coverage"]["elasticsearch"], {"empty", "absent"})
            self.assertEqual(item["coverage"]["deepflow"], "absent")
            self.assertEqual(item["coverage"]["tempo"], "absent")

    def test_runtime_cases_require_real_backend_evidence(self):
        for item in load_catalog()["cases"][5:]:
            for backend in ("prometheus", "elasticsearch", "deepflow"):
                self.assertEqual(item["coverage"][backend], "present", (item["id"], backend))

    def test_current_cluster_deepflow_defaults_are_safe_and_discoverable(self):
        config = (self._root() / "config.env.example").read_text(encoding="utf-8")
        self.assertIn("DEEPFLOW_NAMESPACE=monitor", config)
        self.assertIn("DEEPFLOW_CLICKHOUSE_SELECTOR=app.kubernetes.io/name=clickhouse", config)

    @staticmethod
    def _root():
        try:
            from .helpers import ROOT
        except ImportError:
            from helpers import ROOT
        return ROOT


if __name__ == "__main__":
    unittest.main()
