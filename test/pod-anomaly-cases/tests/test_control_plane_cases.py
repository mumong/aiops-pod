import unittest

try:
    from .helpers import render
except ImportError:
    from helpers import render


EXPECTED = {
    "pending-unschedulable": "aiops-case-01",
    "imagepull-failed": "aiops-case-02",
    "volume-mount-failed": "aiops-case-03",
    "createcontainer-config-error": "aiops-case-04",
    "sandbox-create-failed": "aiops-case-05",
}


class ControlPlaneCaseTests(unittest.TestCase):
    def test_each_case_builds_with_opaque_bounded_workload(self):
        for directory, namespace in EXPECTED.items():
            with self.subTest(directory=directory):
                output = render(f"cases/{directory}")
                self.assertIn(f"name: {namespace}", output)
                self.assertIn("name: workload", output)
                self.assertIn("requests:", output)
                self.assertIn("limits:", output)
                self.assertIn("runAsNonRoot: true", output)
                self.assertIn("allowPrivilegeEscalation: false", output)
                self.assertIn("readOnlyRootFilesystem: true", output)
                self.assertIn("automountServiceAccountToken: false", output)

    def test_fault_inputs_are_real(self):
        self.assertIn("aiops.lab/unavailable: \"true\"", render("cases/pending-unschedulable"))
        image = render("cases/imagepull-failed")
        self.assertIn("registry.invalid/aiops/workload:missing", image)
        self.assertIn("imagePullPolicy: Always", image)
        volume = render("cases/volume-mount-failed")
        self.assertIn("name: unavailable-config", volume)
        config = render("cases/createcontainer-config-error")
        self.assertIn("xnet.registry.io:8443/observability/python:3-alpine", config)
        self.assertIn("secretKeyRef:", config)
        self.assertIn("key: unavailable-key", config)
        self.assertIn("optional: false", config)
        self.assertIn("kind: Secret", config)
        sandbox = render("cases/sandbox-create-failed")
        self.assertIn("k8s.v1.cni.cncf.io/networks: unavailable-network", sandbox)
        self.assertNotIn("runtimeClassName:", sandbox)

    def test_metadata_does_not_publish_expected_answer(self):
        forbidden = ("expected-root-cause", "pod_abnormal_type", "expected_runbook", "expected_layer")
        for directory in EXPECTED:
            output = render(f"cases/{directory}")
            for token in forbidden:
                self.assertNotIn(token, output)


if __name__ == "__main__":
    unittest.main()
