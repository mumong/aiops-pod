import re
import unittest

try:
    from .helpers import render
except ImportError:
    from helpers import render


class ManifestSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = render("safe")

    def test_safe_bundle_has_no_node_or_privileged_capability(self):
        for token in ("privileged: true", "hostPath:", "hostNetwork: true", "hostPID: true",
                      "readOnlyRootFilesystem: false", "kind: Node", "resources: [\"*\"]", "verbs: [\"*\"]"):
            self.assertNotIn(token, self.output)
        self.assertNotIn("../destructive", self.output)

    def test_all_pod_containers_are_bounded_and_restricted(self):
        pod_docs = [doc for doc in self.output.split("\n---\n") if "containers:" in doc]
        self.assertTrue(pod_docs)
        for document in pod_docs:
            container_count = len(re.findall(r"(?m)^[ ]{4,8}name: (?:app|driver)$", document))
            self.assertGreater(container_count, 0)
            self.assertGreaterEqual(document.count("resources:"), container_count)
            self.assertGreaterEqual(document.count("allowPrivilegeEscalation: false"), container_count)
            self.assertGreaterEqual(document.count("readOnlyRootFilesystem: true"), container_count)
            self.assertIn("automountServiceAccountToken: false", document)

    def test_namespace_scope_is_exact(self):
        namespaces = set(re.findall(r"(?m)^  namespace: (aiops-case-\d{2})$", self.output))
        self.assertEqual(namespaces, {f"aiops-case-{i:02d}" for i in range(1, 12)})


if __name__ == "__main__":
    unittest.main()
