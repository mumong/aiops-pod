"""make mc-cert: our own tunnel client certificate from xnet's registry API.

A fake xnet-management (login + POST /api/v1/registry/certificate) signs with a
throwaway CA, the same shape the real API returns (CN=localhost, clientAuth).
"""

import datetime
import importlib.util
import json
import stat
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("xnet_cert", ROOT / "deploy-edge/xnet_cert.py")
xnet_cert = importlib.util.module_from_spec(spec)
spec.loader.exec_module(xnet_cert)

USER, PASSWORD, TOKEN = "admin", "s3cret-pass", "jwt-token-value"


def _pem(obj):
    if isinstance(obj, x509.Certificate):
        return obj.public_bytes(serialization.Encoding.PEM).decode()
    return obj.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ).decode()


def _name(cn):
    return x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])


def make_ca():
    key = ec.generate_private_key(ec.SECP256R1())
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(_name("Test CA"))
        .issuer_name(_name("Test CA"))
        .public_key(key.public_key())
        .serial_number(1)
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    return cert, key


def make_client(ca, days=1825, usage=ExtendedKeyUsageOID.CLIENT_AUTH):
    ca_cert, ca_key = ca
    key = ec.generate_private_key(ec.SECP256R1())
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(_name("localhost"))
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(days=days))
        .add_extension(x509.ExtendedKeyUsage([usage]), critical=False)
        .sign(ca_key, hashes.SHA256())
    )
    return _pem(cert), _pem(key)


class FakeXnet:
    """xnet-management's login and certificate endpoints, recording what they receive."""

    def __init__(self, ca, days=1825):
        self.ca, self.days, self.requests = ca, days, []
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])) or b"{}")
                fake.requests.append((self.path, dict(self.headers), body))
                if self.path == "/api/v1/auth/login":
                    if body != {"username": USER, "password": PASSWORD}:
                        return self._reply(401, "Invalid username or password")
                    self.send_response(200)
                    self.send_header("Authorization", f"Bearer {TOKEN}")
                    self.end_headers()
                    return None
                if self.path == "/api/v1/registry/certificate":
                    if self.headers.get("Authorization") != f"Bearer {TOKEN}":
                        return self._reply(401, "Invalid token")
                    cert, key = make_client(fake.ca, fake.days)
                    return self._reply(
                        200,
                        {
                            "clientid": "9f0f69bc-0000-4000-8000-000000000001",
                            "ca_cert": _pem(fake.ca[0]),
                            "client_cert": cert,
                            "client_key": key,
                        },
                    )
                return self._reply(404, "not found")

            def _reply(self, code, payload):
                data = json.dumps(payload).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(data)

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def certificate_requests(self):
        return [r for r in self.requests if r[0] == "/api/v1/registry/certificate"]


@pytest.fixture
def ca():
    return make_ca()


@pytest.fixture
def xnet(ca):
    fake = FakeXnet(ca)
    yield fake
    fake.server.shutdown()


@pytest.fixture
def creds(monkeypatch):
    monkeypatch.setenv("XNET_USERNAME", USER)
    monkeypatch.setenv("XNET_PASSWORD", PASSWORD)


def write_dir(path, ca, cert_key):
    path.mkdir(parents=True, exist_ok=True)
    (path / "ca.pem").write_text(_pem(ca[0]))
    (path / "cert.pem").write_text(cert_key[0])
    (path / "key.pem").write_text(cert_key[1])


def test_issue_writes_our_own_key_pair_privately_and_says_what_it_is(
    xnet, creds, tmp_path, capsys
):
    out = tmp_path / "xnet-cert"

    code = xnet_cert.main(["ensure", "--out", str(out), "--api", xnet.url])

    assert code == 0
    for name in ("cert.pem", "key.pem", "ca.pem", "meta.json"):
        assert stat.S_IMODE((out / name).stat().st_mode) == 0o600
    assert stat.S_IMODE(out.stat().st_mode) == 0o700
    meta = json.loads((out / "meta.json").read_text())
    assert meta["clientid"] == "9f0f69bc-0000-4000-8000-000000000001"
    assert meta["source"] == f"{xnet.url}/api/v1/registry/certificate"
    # The request names us so xnet operators can tell this certificate apart.
    ((_, headers, body),) = xnet.certificate_requests()
    assert headers["Authorization"] == f"Bearer {TOKEN}"
    assert body["alias"] == "aiops-center" and "not a cluster" in body["description"]
    printed = capsys.readouterr()
    assert "签发" in printed.out and "9f0f69bc" in printed.out
    # Nothing secret reaches the terminal.
    text = printed.out + printed.err
    assert PASSWORD not in text and TOKEN not in text and "PRIVATE KEY" not in text


def test_a_valid_certificate_is_reused_not_reissued(xnet, creds, tmp_path, capsys):
    out = tmp_path / "xnet-cert"
    assert xnet_cert.main(["ensure", "--out", str(out), "--api", xnet.url]) == 0
    first = (out / "cert.pem").read_text()

    assert xnet_cert.main(["ensure", "--out", str(out), "--api", xnet.url]) == 0

    assert (out / "cert.pem").read_text() == first
    assert len(xnet.certificate_requests()) == 1
    assert "沿用" in capsys.readouterr().out


def test_renew_or_near_expiry_issues_a_new_one(ca, creds, tmp_path):
    fake = FakeXnet(ca, days=10)  # xnet configured with a short duration
    try:
        out = tmp_path / "xnet-cert"
        assert xnet_cert.main(["ensure", "--out", str(out), "--api", fake.url]) == 1
        # 10 days left < 30: issued but reported as unusable, and every rerun asks again.
        assert len(fake.certificate_requests()) == 1
        fake.days = 1825
        assert xnet_cert.main(["ensure", "--out", str(out), "--api", fake.url]) == 0
        assert len(fake.certificate_requests()) == 2
        assert xnet_cert.main(["ensure", "--out", str(out), "--api", fake.url, "--renew"]) == 0
        assert len(fake.certificate_requests()) == 3
    finally:
        fake.server.shutdown()


def test_wrong_credentials_fail_without_echoing_them(xnet, monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("XNET_USERNAME", USER)
    monkeypatch.setenv("XNET_PASSWORD", "wrong-password")

    code = xnet_cert.main(["ensure", "--out", str(tmp_path / "c"), "--api", xnet.url])

    assert code == 1
    err = capsys.readouterr().err
    assert "登录" in err and "401" in err and "wrong-password" not in err
    assert not (tmp_path / "c" / "cert.pem").exists()


def test_missing_credentials_say_where_they_come_from(xnet, monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("XNET_USERNAME", raising=False)
    monkeypatch.delenv("XNET_PASSWORD", raising=False)

    assert xnet_cert.main(["ensure", "--out", str(tmp_path / "c"), "--api", xnet.url]) == 1
    assert "XNET_USERNAME" in capsys.readouterr().err
    assert xnet.requests == []


def test_check_accepts_an_operator_provided_directory(ca, tmp_path, capsys):
    write_dir(tmp_path, ca, make_client(ca))

    assert xnet_cert.main(["check", str(tmp_path)]) == 0
    assert "有效期至" in capsys.readouterr().out


@pytest.mark.parametrize(
    "broken, reason",
    [
        ("other_ca", "不是由 ca.pem 签发"),
        ("server_usage", "clientAuth"),
        ("expiring", "剩余"),
        ("key_mismatch", "私钥"),
        ("missing", "缺少"),
    ],
)
def test_check_rejects_unusable_certificates(ca, tmp_path, capsys, broken, reason):
    if broken == "other_ca":
        write_dir(tmp_path, ca, make_client(make_ca()))
    elif broken == "server_usage":
        write_dir(tmp_path, ca, make_client(ca, usage=ExtendedKeyUsageOID.SERVER_AUTH))
    elif broken == "expiring":
        write_dir(tmp_path, ca, make_client(ca, days=5))
    elif broken == "key_mismatch":
        cert, _ = make_client(ca)
        _, other_key = make_client(ca)
        write_dir(tmp_path, ca, (cert, other_key))
    else:
        write_dir(tmp_path, ca, make_client(ca))
        (tmp_path / "key.pem").unlink()

    assert xnet_cert.main(["check", str(tmp_path)]) == 1
    assert reason in capsys.readouterr().err


def test_check_refuses_xnet_managements_own_certificate(ca, tmp_path, capsys):
    """The tunnel accepts any CA-signed client cert; ours must not be xnet's identity."""
    pair = make_client(ca)
    write_dir(tmp_path / "ours", ca, pair)
    (tmp_path / "xnet-own.pem").write_text(pair[0])

    code = xnet_cert.main(
        ["check", str(tmp_path / "ours"), "--not-same-as", str(tmp_path / "xnet-own.pem")]
    )

    assert code == 1
    assert "xnet-management 自己的" in capsys.readouterr().err
    other = tmp_path / "other.pem"
    other.write_text(make_client(ca)[0])
    assert xnet_cert.main(["check", str(tmp_path / "ours"), "--not-same-as", str(other)]) == 0


def test_mc_init_no_longer_copies_xnet_managements_certificate():
    makefile = (ROOT / "Makefile").read_text()
    mc_init = makefile[makefile.index("\nmc-init:") : makefile.index("\n# 旧名称")]
    # xnet's private key is never read; its public cert only for the --not-same-as guard.
    assert "key\\.pem" not in mc_init and "xnet-ca-cert" not in mc_init
    assert "xnet_cert.py check" in mc_init and "--not-same-as" in mc_init


def test_no_xnet_certificate_to_compare_against_is_not_an_error(ca, tmp_path):
    write_dir(tmp_path / "ours", ca, make_client(ca))
    (tmp_path / "empty.pem").write_text("")

    for other in ("empty.pem", "absent.pem"):
        assert (
            xnet_cert.main(
                ["check", str(tmp_path / "ours"), "--not-same-as", str(tmp_path / other)]
            )
            == 0
        )
