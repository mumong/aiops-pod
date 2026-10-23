import re
import unittest

try:
    from .helpers import render
except ImportError:
    from helpers import render


FORBIDDEN = ("oom", "imagepull", "config-error", "expected", "runbook", "pod_abnormal_type", "root-cause", "expected_layer")


def metadata_text(document):
    match = re.search(r"(?ms)^metadata:\n(.*?)(?=^[a-zA-Z][^\n]*:\s*(?:\n|$))", document)
    return match.group(1).lower() if match else ""


class AnswerLeakageTests(unittest.TestCase):
    def test_deployed_metadata_does_not_reveal_catalog_answers(self):
        for document in render("safe").split("\n---\n"):
            metadata = metadata_text(document)
            for token in FORBIDDEN:
                self.assertNotIn(token, metadata, (token, metadata))

    def test_catalog_is_not_deployed(self):
        output = render("safe")
        self.assertNotIn("aiops.pod-anomaly-catalog.v1", output)
        self.assertNotIn("evidence_examples", output)


if __name__ == "__main__":
    unittest.main()
