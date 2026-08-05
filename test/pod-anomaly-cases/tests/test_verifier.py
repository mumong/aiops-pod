import importlib.util
import io
import json
import ssl
import sys
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

try:
    from .helpers import ROOT
except ImportError:
    from helpers import ROOT


def load_module():
    path = ROOT / "scripts/verify_observability.py"
    spec = importlib.util.spec_from_file_location("verify_observability", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


class VerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = load_module()

    def test_status_gate_matches_real_container_state_and_events(self):
        pod = {
            "metadata": {"finalizers": []},
            "status": {
                "phase": "Running",
                "conditions": [{"type": "Ready", "status": "False"}],
                "containerStatuses": [{"restartCount": 2, "state": {"waiting": {"reason": "CrashLoopBackOff"}},
                                       "lastState": {"terminated": {"reason": "Error", "exitCode": 78}}}],
            },
        }
        gate = {"waiting_reasons": ["CrashLoopBackOff"], "terminated_exit_codes": [78], "minimum_restarts": 1}
        ok, facts = self.v.evaluate_status_gate(pod, [], gate)
        self.assertTrue(ok)
        self.assertIn("CrashLoopBackOff", facts["waiting_reasons"])

    def test_prometheus_query_is_exact_and_bounded(self):
        payload = {"status": "success", "data": {"resultType": "vector", "result": [{"metric": {"pod": "workload-x"}, "value": [1, "1"]}]}}
        with mock.patch.object(self.v.urllib.request, "urlopen", return_value=Response(json.dumps(payload).encode())) as opened:
            identity = self.v.PodIdentity("aiops-case-08", "workload-x", "uid-1", "10.0.0.8", "2026-08-03T00:00:00Z")
            result = self.v.query_prometheus(identity, "http://prometheus", 100, 200)
        self.assertEqual(result.coverage, "present")
        url = opened.call_args.args[0].full_url
        decoded = urllib.parse.unquote(url)
        self.assertIn('namespace="aiops-case-08"', decoded)
        self.assertIn('pod="workload-x"', decoded)
        self.assertIn("time=200", url)

    def test_oom_prometheus_gate_requires_reason_and_memory_history(self):
        vector = {"status": "success", "data": {"result": [{"metric": {}, "value": [1, "1"]}]}}
        matrix = {"status": "success", "data": {"result": [{"metric": {}, "values": [[100, "1"], [200, "2"]]}]}}
        responses = [Response(json.dumps(vector).encode()), Response(json.dumps(vector).encode()),
                     Response(json.dumps(vector).encode()), Response(json.dumps(matrix).encode())]
        with mock.patch.object(self.v.urllib.request, "urlopen", side_effect=responses) as opened:
            identity = self.v.PodIdentity("aiops-case-08", "workload-x", "uid-1", "10.0.0.8", "2026-08-03T00:00:00Z")
            result = self.v.query_prometheus(identity, "http://prometheus", 100, 200, "c08")
        self.assertEqual(result.coverage, "present")
        urls = "\n".join(call.args[0].full_url for call in opened.call_args_list)
        self.assertIn("kube_pod_container_status_last_terminated_reason", urllib.parse.unquote(urls))
        self.assertIn("kube_pod_container_resource_limits", urllib.parse.unquote(urls))
        self.assertIn("container_memory_working_set_bytes", urllib.parse.unquote(urls))
        self.assertIn("/api/v1/query_range?", urls)

    def test_elasticsearch_query_binds_uid_name_and_time(self):
        payload = {"hits": {"hits": [{"_source": {"message": "bounded sample", "trace_id": "a" * 32}}]}}
        with mock.patch.object(self.v.urllib.request, "urlopen", return_value=Response(json.dumps(payload).encode())) as opened:
            identity = self.v.PodIdentity("aiops-case-07", "workload-x", "uid-secret", "10.0.0.7", "2026-08-03T00:00:00Z")
            result = self.v.query_elasticsearch(identity, "run-1", "http://es", 100, 200, "user", "password")
        self.assertEqual(result.coverage, "present")
        request = opened.call_args.args[0]
        body = json.loads(request.data)
        rendered = json.dumps(body)
        self.assertIn("uid-secret", rendered)
        self.assertIn("workload-x", rendered)
        self.assertIn("aiops-case-07", rendered)
        self.assertIn("@timestamp", rendered)
        self.assertLessEqual(body["size"], 20)
        self.assertEqual(body["query"]["bool"]["minimum_should_match"], 1)
        self.assertNotIn("password", result.summary)

    def test_elasticsearch_tls_verification_can_only_be_disabled_explicitly(self):
        payload = {"hits": {"hits": []}}
        with mock.patch.object(self.v.urllib.request, "urlopen", return_value=Response(json.dumps(payload).encode())) as opened:
            identity = self.v.PodIdentity("aiops-case-07", "workload-x", "uid-1", "10.0.0.7", "2026-08-03T00:00:00Z")
            self.v.query_elasticsearch(identity, "run-1", "https://127.0.0.1:19200", 100, 200,
                                       "user", "password", tls_verify=False)
        context = opened.call_args.kwargs["context"]
        self.assertEqual(context.verify_mode, ssl.CERT_NONE)
        self.assertFalse(context.check_hostname)

    def test_runtime_logs_fail_closed_without_current_driver_uid(self):
        identity = self.v.PodIdentity("aiops-case-07", "workload-x", "uid-1", "10.0.0.7", "2026-08-03T00:00:00Z")
        case = {"runtime": True}
        result = self.v.query_case_elasticsearch(case, identity, "", "http://es", 100, 200)
        self.assertEqual(result.coverage, "error")
        self.assertIn("driver", result.summary)

    def test_missing_pod_ip_is_absent_not_error_for_flow(self):
        identity = self.v.PodIdentity("aiops-case-01", "workload-x", "uid-1", "", "2026-08-03T00:00:00Z")
        result = self.v.query_deepflow(identity, 100, 200, "xnet", "app=clickhouse")
        self.assertEqual(result.coverage, "absent")

    def test_deepflow_requires_direct_work_request_rows(self):
        pod = {"metadata": {"name": "clickhouse-0"}, "status": {"phase": "Running"}}
        flow = {"data": [{"src_ip": "10.0.0.1", "dst_ip": "10.0.0.8", "request_resource": "/work", "trace_id": "b" * 32}]}
        completed = mock.Mock(stdout=json.dumps(flow))
        identity = self.v.PodIdentity("aiops-case-08", "workload-x", "uid-1", "10.0.0.8", "2026-08-03T00:00:00Z")
        with mock.patch.object(self.v, "run_kubectl_json", return_value={"items": [pod]}), \
             mock.patch.object(self.v.subprocess, "run", return_value=completed) as ran:
            result = self.v.query_deepflow(identity, 100, 200, "monitor", "app.kubernetes.io/name=clickhouse")
        self.assertEqual(result.coverage, "present")
        sql = ran.call_args.args[0][-1]
        self.assertIn("FROM flow_log.l7_flow_log AS flow", sql)
        self.assertIn("flow.time >=", sql)
        self.assertIn("request_resource = '/work'", sql)
        self.assertIn("ip4_0 = '10.0.0.8' OR ip4_1 = '10.0.0.8'", sql)

    def test_only_shared_log_and_flow_trace_ids_are_correlated(self):
        logs = self.v.CoverageResult("elasticsearch", "present", "", trace_ids=("a" * 32, "b" * 32))
        flows = self.v.CoverageResult("deepflow", "present", "", trace_ids=("b" * 32, "c" * 32))
        self.assertEqual(self.v.correlated_trace_ids(logs, flows), ("b" * 32,))

    def test_expected_empty_and_absent_are_successful_coverage(self):
        actual = self.v.CoverageResult("tempo", "absent", "no trace ID")
        self.assertTrue(self.v.coverage_matches("absent", actual))
        self.assertTrue(self.v.coverage_matches("empty", self.v.CoverageResult("elasticsearch", "empty", "0 hits")))
        self.assertFalse(self.v.coverage_matches("present", actual))

    def test_wait_revalidates_previously_passing_cases_before_success(self):
        cases = [
            {"id": "c01", "coverage": {"kubernetes": "present"}},
            {"id": "c02", "coverage": {"kubernetes": "present"}},
        ]
        outcomes = {"c01": iter((True, False, True)), "c02": iter((False, True, True))}
        calls = []

        def verify(case):
            calls.append(case["id"])
            result = self.v.CoverageResult("kubernetes", "present", "current identity")
            return next(outcomes[case["id"]]), [result]

        with mock.patch.object(self.v, "load_catalog", return_value={"cases": cases}), \
             mock.patch.object(self.v, "verify_case", side_effect=verify), \
             mock.patch.object(self.v.time, "monotonic", return_value=0), \
             mock.patch.object(self.v.time, "sleep"), \
             mock.patch("sys.stdout", new_callable=io.StringIO):
            exit_code = self.v.main(["--wait", "--timeout", "1"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(calls, ["c01", "c02", "c01", "c02", "c01", "c02"])

    def test_wait_uses_catalog_timeout_and_exponential_backoff(self):
        cases = [
            {"id": "c01", "timeout_seconds": 3, "coverage": {"kubernetes": "present"}},
            {"id": "c02", "timeout_seconds": 10, "coverage": {"kubernetes": "present"}},
        ]
        result = self.v.CoverageResult("kubernetes", "empty", "not ready")
        with mock.patch.object(self.v, "load_catalog", return_value={"cases": cases}), \
             mock.patch.object(self.v, "verify_case", return_value=(False, [result])) as verified, \
             mock.patch.object(self.v.time, "monotonic", side_effect=(0, 0, 0, 3, 3, 300)), \
             mock.patch.object(self.v.time, "sleep") as slept, \
             mock.patch.dict(self.v.os.environ, {}, clear=True), \
             mock.patch("sys.stdout", new_callable=io.StringIO):
            exit_code = self.v.main(["--wait"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(verified.call_count, 6)
        self.assertEqual(slept.call_args_list, [mock.call(1), mock.call(2)])


if __name__ == "__main__":
    unittest.main()
