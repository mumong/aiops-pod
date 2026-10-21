"""Tunnel client error classification (contracts/tool-result.md error codes).

A local HTTP server stands in for xnet's /proxy so the classification is tested
end-to-end over a socket without touching the real tunnel.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import pytest

from aiops_edge import signing
from aiops_edge.clusters import Cluster, XnetAccess
from aiops_edge.tunnel import EdgeError, TunnelClient

KEY = b"s" * 32
EDGE = Cluster(
    name="vc-942nkkozc8o5fyb9q3bznb1ws", access="xnet", uuid="99eea57d-4cbe-4047-a7a0-ced9c658316c"
)


class FakeProxy(BaseHTTPRequestHandler):
    behaviour = "ok"
    seen = []

    def log_message(self, *args):
        pass

    def _reply(self, status, body):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length)
        query = parse_qs(urlparse(self.path).query)
        FakeProxy.seen.append({"query": query, "headers": dict(self.headers), "body": body})
        b = FakeProxy.behaviour
        if b == "ok":
            address = urlparse(query["address"][0])
            reason = signing.verify(
                KEY, self.headers, "POST", address.path, body, cache=signing.NonceCache()
            )
            if reason:
                return self._reply(401, {"error": "runner_auth_failed", "reason": reason})
            return self._reply(200, {"exit_code": 0, "stdout": "pods", "stderr": ""})
        if b == "offline":
            return self._reply(400, b"The side client is not online!\n")
        if b == "runner_missing":
            return self._reply(408, b"dial tcp: lookup aiops-edge-runner.aiops.svc: no such host")
        if b == "denied":
            return self._reply(
                403, {"error": "policy_denied", "rule": "denied_executables", "command": "reboot"}
            )
        if b == "unauth":
            return self._reply(401, {"error": "runner_auth_failed", "reason": "bad signature"})
        if b == "slow":
            import time

            time.sleep(2)
            return self._reply(200, {})
        return self._reply(500, b"boom")


@pytest.fixture
def proxy():
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeProxy)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    FakeProxy.seen = []
    yield f"http://127.0.0.1:{server.server_address[1]}/proxy"
    server.shutdown()


def client(url, **kw):
    access = XnetAccess(proxy_url=url, runner_url="http://aiops-edge-runner.aiops.svc:8090", **kw)
    return TunnelClient(access, KEY, insecure_http=True)


def test_successful_call_is_signed_and_addressed(proxy):
    FakeProxy.behaviour = "ok"
    result = client(proxy).request(EDGE, "/v1/kubectl", {"argv": ["kubectl", "get", "pods"]})
    assert result["stdout"] == "pods"
    seen = FakeProxy.seen[-1]
    assert seen["query"]["clientid"] == [EDGE.uuid]
    assert seen["query"]["address"] == ["http://aiops-edge-runner.aiops.svc:8090/v1/kubectl"]


@pytest.mark.parametrize(
    "behaviour,code",
    [
        ("offline", "cluster_unreachable"),
        ("runner_missing", "cluster_unreachable"),
        ("denied", "policy_denied"),
        ("unauth", "runner_auth_failed"),
        ("error", "runner_error"),
    ],
)
def test_error_classification(proxy, behaviour, code):
    FakeProxy.behaviour = behaviour
    with pytest.raises(EdgeError) as exc:
        client(proxy).request(EDGE, "/v1/kubectl", {"argv": ["kubectl", "get", "pods"]})
    assert exc.value.code == code


def test_policy_denial_keeps_rule(proxy):
    FakeProxy.behaviour = "denied"
    with pytest.raises(EdgeError) as exc:
        client(proxy).request(
            EDGE, "/v1/kubectl", {"argv": ["kubectl", "exec", "x", "--", "reboot"]}
        )
    assert exc.value.detail["rule"] == "denied_executables"


def test_timeout(proxy):
    FakeProxy.behaviour = "slow"
    with pytest.raises(EdgeError) as exc:
        client(proxy).request(
            EDGE, "/v1/kubectl", {"argv": ["kubectl", "get", "pods"]}, timeout=0.5
        )
    assert exc.value.code == "timeout"


def test_tunnel_down():
    with pytest.raises(EdgeError) as exc:
        client("http://127.0.0.1:9/proxy").request(
            EDGE, "/v1/kubectl", {"argv": ["kubectl", "get", "pods"]}
        )
    assert exc.value.code == "cluster_unreachable"


def test_missing_cert_file_is_auth_failure(tmp_path):
    access = XnetAccess(
        proxy_url="https://127.0.0.1:9/proxy",
        runner_url="http://r:8090",
        cert_file=str(tmp_path / "nope.pem"),
        key_file=str(tmp_path / "nope.key"),
    )
    with pytest.raises(EdgeError) as exc:
        TunnelClient(access, KEY).request(EDGE, "/v1/kubectl", {})
    assert exc.value.code == "tunnel_auth_failed"
