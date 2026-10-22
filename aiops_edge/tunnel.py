"""Client for xnet's tunnel ``/proxy`` endpoint, addressed at our edge runner.

The tunnel forwards one buffered HTTP request with headers and body intact
(research R1). Failures are mapped to the error codes in
contracts/tool-result.md so tools can say exactly why a cluster was not
reached.
"""

from __future__ import annotations

import fcntl
import json
import os
import socket
import ssl
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from aiops_edge import signing
from aiops_edge.clusters import Cluster, XnetAccess

# xnet's /proxy caps one request at 20 s; stay below it so our error wins.
MAX_CALL_SECONDS = 15
SLOT_DIR = os.environ.get(
    "AIOPS_EDGE_SLOT_DIR", os.path.join(tempfile.gettempdir(), "aiops-edge-slots")
)


class EdgeError(Exception):
    def __init__(self, code: str, message: str, detail: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.detail = detail or {}


@contextmanager
def cluster_slot(cluster: str, limit: int, wait: float) -> Iterator[None]:
    """Cross-process limit on concurrent calls per cluster (shim calls are separate processes)."""
    Path(SLOT_DIR).mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + wait
    while True:
        for i in range(max(1, limit)):
            fd = os.open(os.path.join(SLOT_DIR, f"{cluster}.{i}"), os.O_CREAT | os.O_RDWR, 0o600)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                os.close(fd)
                continue
            try:
                yield
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
            return
        if time.monotonic() >= deadline:
            raise EdgeError("timeout", f"too many concurrent calls to cluster {cluster}")
        time.sleep(0.05)


def load_signing_key(path: str) -> bytes:
    try:
        key = Path(path).read_bytes().strip()
    except OSError as exc:
        raise EdgeError(
            "runner_auth_failed", f"cannot read runner signing key {path}: {exc}"
        ) from exc
    if len(key) < 32:
        raise EdgeError("runner_auth_failed", "runner signing key is shorter than 32 bytes")
    return key


class TunnelClient:
    def __init__(
        self, access: XnetAccess, signing_key: bytes, *, insecure_http: bool = False
    ) -> None:
        self.access = access
        self.key = signing_key
        self.insecure_http = insecure_http  # tests only: plain-http fake proxy

    @classmethod
    def from_access(cls, access: XnetAccess) -> "TunnelClient":
        return cls(access, load_signing_key(access.signing_key_file))

    def _context(self) -> Optional[ssl.SSLContext]:
        if self.insecure_http:
            return None
        try:
            ctx = ssl.create_default_context(cafile=self.access.ca_file or None)
            # xnet serves a certificate for CN=localhost; trust comes from its CA, not the name.
            ctx.check_hostname = False
            ctx.load_cert_chain(self.access.cert_file, self.access.key_file)
        except (OSError, ssl.SSLError) as exc:
            raise EdgeError(
                "tunnel_auth_failed",
                f"xnet client certificate unusable ({exc}); re-run make mc-init in the Agent repo, then restart MCP and AIOps",
            ) from exc
        return ctx

    def request(
        self,
        cluster: Cluster,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        method: str = "POST",
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        if not cluster.remote or not cluster.uuid:
            raise EdgeError("cluster_unknown", f"{cluster.name} is not reachable through xnet")
        timeout = min(float(timeout or self.access.call_timeout_seconds), MAX_CALL_SECONDS)
        body = b"" if payload is None else json.dumps(payload).encode()
        address = self.access.runner_url.rstrip("/") + path
        url = f"{self.access.proxy_url}?{urllib.parse.urlencode({'clientid': cluster.uuid, 'address': address})}"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        headers.update(signing.sign(self.key, method, urllib.parse.urlparse(address).path, body))
        ctx = self._context()
        req = urllib.request.Request(
            url, data=body if method != "GET" else None, headers=headers, method=method
        )
        with cluster_slot(cluster.name, self.access.per_cluster_concurrency, wait=timeout):
            try:
                with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:  # noqa: S310
                    return self._decode(resp.status, resp.read())
            except urllib.error.HTTPError as exc:
                raise self._http_error(exc.code, exc.read()) from None
            except ssl.SSLError as exc:
                raise EdgeError(
                    "tunnel_auth_failed", f"TLS with the xnet tunnel failed: {exc}"
                ) from None
            except (socket.timeout, TimeoutError):
                raise EdgeError(
                    "timeout", f"no answer from {cluster.name} within {timeout:.0f}s"
                ) from None
            except urllib.error.URLError as exc:
                if isinstance(exc.reason, (socket.timeout, TimeoutError)):
                    raise EdgeError(
                        "timeout", f"no answer from {cluster.name} within {timeout:.0f}s"
                    ) from None
                if isinstance(exc.reason, ssl.SSLError):
                    raise EdgeError(
                        "tunnel_auth_failed", f"TLS with the xnet tunnel failed: {exc.reason}"
                    ) from None
                raise EdgeError(
                    "cluster_unreachable", f"xnet tunnel unreachable: {exc.reason}"
                ) from None
            except ConnectionError as exc:
                raise EdgeError(
                    "cluster_unreachable", f"xnet tunnel connection failed: {exc}"
                ) from None

    @staticmethod
    def _decode(status: int, raw: bytes) -> Dict[str, Any]:
        try:
            return json.loads(raw or b"{}")
        except json.JSONDecodeError:
            raise EdgeError(
                "runner_error", f"runner returned non-JSON (HTTP {status}): {raw[:200]!r}"
            ) from None

    @staticmethod
    def _http_error(status: int, raw: bytes) -> EdgeError:
        text = raw.decode("utf-8", "replace")
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = {}
        if not isinstance(detail, dict):
            detail = {}
        if status == 400 and "not online" in text:
            return EdgeError(
                "cluster_unreachable", "the edge cluster is not connected to the xnet tunnel"
            )
        if status == 408:
            # xnet-agent could not reach the runner inside the edge cluster.
            return EdgeError(
                "cluster_unreachable",
                f"edge runner not reachable inside the cluster: {text[:200]}",
            )
        if status == 401:
            return EdgeError("runner_auth_failed", detail.get("reason") or text[:200], detail)
        if status == 403:
            code = (
                detail.get("error")
                if detail.get("error") in ("policy_denied", "mode_denied")
                else "policy_denied"
            )
            return EdgeError(
                code, detail.get("reason") or detail.get("rule") or text[:200], detail
            )
        if status == 404:
            return EdgeError("not_found", text[:200], detail)
        return EdgeError("runner_error", f"HTTP {status}: {text[:200]}", detail)
