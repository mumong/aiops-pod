"""HTTP server of the edge runner (contracts/runner-api.md).

Standard library only. Reached from the center solely via the xnet tunnel; the
Service is ClusterIP. Every request except /healthz must carry a valid
signature. Reads run as the ``reader`` ServiceAccount, exec/write as
``writer``.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from aiops_edge import kubectl_args, signing
from aiops_edge.runner.gate import evaluate
from aiops_edge.runner.jobs import JobStore
from aiops_edge.streams import decode_streams, encode_streams  # noqa: F401 (decode re-exported)
from app.core.remediation.policy import CommandPolicy

API_VERSION = 1
MAX_SYNC_SECONDS = 15
MAX_JOB_SECONDS = 600
MAX_BODY_BYTES = 64 * 1024
log = logging.getLogger("aiops-edge-runner")


@dataclass
class RunnerConfig:
    signing_key: bytes
    policy: CommandPolicy
    kubectl: str
    kubeconfigs: Dict[str, str]
    job_dir: str
    max_output: int = 4 * 1024 * 1024
    version: str = "dev"
    nonces: signing.NonceCache = field(default_factory=signing.NonceCache)
    jobs: Optional[JobStore] = None

    def job_store(self) -> JobStore:
        if self.jobs is None:
            self.jobs = JobStore(self.job_dir)
        return self.jobs

    @property
    def policy_version(self) -> str:
        return hashlib.sha256(
            json.dumps(self.policy.summary(), sort_keys=True).encode()
        ).hexdigest()[:12]


def cap(text: str, limit: int) -> Tuple[str, bool]:
    data = text.encode("utf-8")
    if len(data) <= limit:
        return text, False
    return data[:limit].decode("utf-8", "ignore"), True


def run_kubectl(cfg: RunnerConfig, argv, identity: str, timeout: float) -> Dict[str, Any]:
    env = {k: v for k, v in os.environ.items() if k not in ("KUBECONFIG",)}
    env["KUBECONFIG"] = cfg.kubeconfigs[identity]
    started = time.monotonic()
    try:
        proc = subprocess.run(
            [cfg.kubectl, *argv[1:]],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            check=False,
        )
        stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = f"command timed out after {timeout:.0f}s; it may have partially taken effect\n"
        code = 124
    budget = cfg.max_output
    stdout, cut_out = cap(stdout, budget)
    stderr, cut_err = cap(stderr, max(0, budget - len(stdout.encode())))
    return {
        "exit_code": code,
        "stdout": stdout,
        "stderr": stderr,
        "truncated": cut_out or cut_err,
        "duration_ms": int((time.monotonic() - started) * 1000),
    }


def make_handler(cfg: RunnerConfig):
    class Handler(BaseHTTPRequestHandler):
        server_version = "aiops-edge-runner"

        def log_message(self, fmt, *args):  # route to logging, not stderr noise
            log.info("%s %s", self.address_string(), fmt % args)

        def _send(self, status: int, body: Dict[str, Any]) -> None:
            data = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/healthz":
                return self._send(
                    200,
                    {
                        "version": cfg.version,
                        "api": API_VERSION,
                        "policy_version": cfg.policy_version,
                        "capabilities": ["read", "exec", "write", "jobs"],
                    },
                )
            if self.path.startswith("/v1/jobs/"):
                reason = signing.verify(
                    cfg.signing_key, self.headers, "GET", self.path, b"", cache=cfg.nonces
                )
                if reason:
                    return self._send(401, {"error": "runner_auth_failed", "reason": reason})
                job = cfg.job_store().get(self.path.rsplit("/", 1)[-1])
                if job is None:
                    return self._send(404, {"error": "not_found"})
                return self._send(200, job)
            return self._send(404, {"error": "not_found"})

        def _body(self) -> Optional[bytes]:
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY_BYTES:
                return None
            return self.rfile.read(length)

        def do_POST(self):
            body = self._body()
            if body is None:
                return self._send(
                    413, {"error": "bad_request", "reason": "request body too large"}
                )
            reason = signing.verify(
                cfg.signing_key, self.headers, "POST", self.path, body, cache=cfg.nonces
            )
            if reason:
                log.warning("refused unsigned request %s: %s", self.path, reason)
                return self._send(401, {"error": "runner_auth_failed", "reason": reason})
            try:
                payload = json.loads(body or b"{}")
                if not isinstance(payload, dict):
                    raise ValueError("payload must be an object")
            except ValueError as exc:
                return self._send(400, {"error": "bad_request", "reason": str(exc)})
            if self.path == "/v1/kubectl":
                return self._kubectl(payload)
            if self.path == "/v1/jobs":
                return self._submit_job(payload)
            return self._send(404, {"error": "not_found"})

        def _submit_job(self, payload: Dict[str, Any]) -> None:
            argv = payload.get("argv")
            key = str(payload.get("idempotency_key") or "").strip()
            if not key or not isinstance(argv, list) or not all(isinstance(a, str) for a in argv):
                return self._send(
                    400,
                    {"error": "bad_request", "reason": "idempotency_key and argv are required"},
                )
            existing = cfg.job_store().by_key(key)
            if existing:
                return self._send(
                    202, {"job_id": existing["job_id"], "status": existing["status"]}
                )
            mode, reason = kubectl_args.classify(argv)
            if mode == "read":
                return self._send(
                    400, {"error": "bad_request", "reason": "read commands use /v1/kubectl"}
                )
            approval = str(payload.get("approval_id") or "")
            decision = evaluate(argv, mode or "write", approval, cfg.policy)
            audit = {
                "job": key,
                "argv": argv,
                "approval_id": approval,
                "allowed": decision.ok,
                "rule": decision.rule,
            }
            if not decision.ok:
                log.warning("AUDIT %s", json.dumps(audit, ensure_ascii=False))
                return self._send(decision.status, decision.body() | {"command": " ".join(argv)})
            job = cfg.job_store().create(key, argv, approval)
            if job.pop("created"):
                timeout = min(float(payload.get("timeout_s") or MAX_JOB_SECONDS), MAX_JOB_SECONDS)

                def work(job_id=job["job_id"]):
                    result = run_kubectl(cfg, argv, "write", timeout)
                    cfg.job_store().finish(job_id, result)
                    log.info(
                        "AUDIT %s",
                        json.dumps(
                            {**audit, "exit_code": result["exit_code"]}, ensure_ascii=False
                        ),
                    )

                threading.Thread(target=work, daemon=True).start()
            return self._send(202, {"job_id": job["job_id"], "status": job["status"]})

        def _kubectl(self, payload: Dict[str, Any]) -> None:
            argv = payload.get("argv")
            if not isinstance(argv, list) or not all(isinstance(a, str) for a in argv):
                return self._send(
                    400, {"error": "bad_request", "reason": "argv must be a list of strings"}
                )
            mode = str(payload.get("mode") or "")
            approval = str(payload.get("approval_id") or "")
            decision = evaluate(argv, mode, approval, cfg.policy)
            audit = {
                "argv": argv,
                "mode": mode,
                "approval_id": approval,
                "allowed": decision.ok,
                "rule": decision.rule,
            }
            if not decision.ok:
                log.warning("AUDIT %s", json.dumps(audit, ensure_ascii=False))
                return self._send(decision.status, decision.body() | {"command": " ".join(argv)})
            timeout = min(float(payload.get("timeout_s") or MAX_SYNC_SECONDS), MAX_SYNC_SECONDS)
            result = run_kubectl(cfg, argv, "read" if mode == "read" else "write", timeout)
            audit["exit_code"] = result["exit_code"]
            log.info("AUDIT %s", json.dumps(audit, ensure_ascii=False))
            return self._send(200, encode_streams(result) if payload.get("compress") else result)

    return Handler


def _kubeconfig(path: Path, token_file: str, ca_file: str) -> str:
    host = os.environ["KUBERNETES_SERVICE_HOST"]
    port = os.environ.get("KUBERNETES_SERVICE_PORT", "443")
    config = {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [
            {
                "name": "local",
                "cluster": {"server": f"https://{host}:{port}", "certificate-authority": ca_file},
            }
        ],
        "users": [{"name": "sa", "user": {"tokenFile": token_file}}],
        "contexts": [{"name": "local", "context": {"cluster": "local", "user": "sa"}}],
        "current-context": "local",
    }
    path.write_text(json.dumps(config))
    path.chmod(0o600)
    return str(path)


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s"
    )
    sa = "/var/run/secrets/kubernetes.io/serviceaccount"
    writer = os.environ.get("RUNNER_WRITER_TOKEN_DIR", "/etc/aiops-edge-writer")
    state = Path(os.environ.get("RUNNER_STATE_DIR", "/var/lib/aiops-edge-runner"))
    state.mkdir(parents=True, exist_ok=True)
    policy_raw = json.loads(
        Path(
            os.environ.get("RUNNER_POLICY_FILE", "/etc/aiops-edge-runner/policy.json")
        ).read_text()
    )
    cfg = RunnerConfig(
        signing_key=Path(os.environ.get("RUNNER_KEY_FILE", "/etc/aiops-edge-key/key"))
        .read_bytes()
        .strip(),
        policy=CommandPolicy.from_config(policy_raw),
        kubectl=os.environ.get("RUNNER_KUBECTL", "/usr/local/bin/kubectl"),
        kubeconfigs={
            "read": _kubeconfig(state / "reader.kubeconfig", f"{sa}/token", f"{sa}/ca.crt"),
            "write": _kubeconfig(
                state / "writer.kubeconfig", f"{writer}/token", f"{writer}/ca.crt"
            ),
        },
        job_dir=str(state / "jobs"),
        max_output=int(os.environ.get("RUNNER_MAX_OUTPUT_BYTES", 4 * 1024 * 1024)),
        version=os.environ.get("VERSION", "dev"),
    )
    if len(cfg.signing_key) < 32:
        raise SystemExit("runner signing key must be at least 32 bytes")
    port = int(os.environ.get("RUNNER_PORT", "8090"))
    log.info(
        "aiops-edge-runner %s listening on :%d (policy %s)", cfg.version, port, cfg.policy_version
    )
    ThreadingHTTPServer(("0.0.0.0", port), make_handler(cfg)).serve_forever()  # noqa: S104 - ClusterIP only


if __name__ == "__main__":
    main()
