"""AIOps's own client certificate for the xnet tunnel (make mc-cert / mc-init).

xnet's tunnel (``/proxy``) accepts any client certificate its CA signed; xnet-management
uses its own ``xnet-client-cert`` for its internal calls. Copying that one would mean
talking as xnet-management with its private key. Instead we ask xnet's public API for a
certificate of our own, the same way an edge cluster gets one (README "申请接入证书"):

    POST /api/v1/auth/login                 -> Authorization: Bearer <jwt>
    POST /api/v1/registry/certificate       -> {clientid, ca_cert, client_cert, client_key}

The second call only signs a new key pair; it creates no Node, Secret or other object in
xnet (a Node appears only when a certificate is presented to the tunnel's ``/register``,
which we never call). Credentials come from XNET_USERNAME / XNET_PASSWORD and are never
printed. Validity is set by xnet (5 years by default).

    xnet_cert.py ensure --out DIR --api URL [--renew] [--min-days N]
    xnet_cert.py check DIR [--min-days N] [--not-same-as PEM]
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

FILES = ("cert.pem", "key.pem", "ca.pem")
MIN_DAYS = 30
ALIAS = "aiops-center"
DESCRIPTION = "AIOps center tunnel caller (MCP and AIOps), not a cluster; never used for /register"


class CertError(Exception):
    pass


def _openssl(*args, stdin=None):
    out = subprocess.run(
        ["openssl", *args], input=stdin, capture_output=True, text=True, check=False
    )
    if out.returncode:
        lines = (out.stderr or out.stdout).strip().splitlines()
        raise CertError(lines[-1] if lines else "openssl failed")
    return out.stdout


def fingerprint(pem_path):
    return _openssl("x509", "-in", str(pem_path), "-noout", "-fingerprint", "-sha256").strip()


def _same_cert(cert, other):
    """True when ``other`` (may be absent or empty: no xnet on this center) is the same cert."""
    if not other or not Path(other).is_file() or not Path(other).stat().st_size:
        return False
    try:
        return fingerprint(cert) == fingerprint(other)
    except CertError:
        return False


def inspect(directory, min_days=MIN_DAYS, not_same_as=None):
    """(summary, problems) for a cert.pem/key.pem/ca.pem directory; no problems = usable."""
    directory = Path(directory)
    missing = [name for name in FILES if not (directory / name).is_file()]
    if missing:
        return {}, [f"{directory} 缺少 {', '.join(missing)}"]
    cert, key, ca = (directory / name for name in FILES)
    problems, summary = [], {}
    try:
        text = _openssl(
            "x509", "-in", str(cert), "-noout", "-subject", "-enddate", "-ext", "extendedKeyUsage"
        )
    except CertError as exc:
        return {}, [f"cert.pem 不是有效证书：{exc}"]
    end = next(line.split("=", 1)[1] for line in text.splitlines() if line.startswith("notAfter="))
    not_after = datetime.datetime.strptime(end.strip(), "%b %d %H:%M:%S %Y %Z").replace(
        tzinfo=datetime.timezone.utc
    )
    days = (not_after - datetime.datetime.now(datetime.timezone.utc)).days
    summary.update(not_after=not_after.strftime("%Y-%m-%d"), days_left=days)
    if "TLS Web Client Authentication" not in text:
        problems.append("证书用途不含 clientAuth，隧道不会接受")
    if days < min_days:
        problems.append(
            f"证书剩余 {days} 天（要求至少 {min_days} 天），需重新签发：make mc-cert RENEW=1"
        )
    verify = subprocess.run(
        ["openssl", "verify", "-CAfile", str(ca), str(cert)],
        capture_output=True,
        text=True,
        check=False,
    )
    if verify.returncode:
        problems.append("cert.pem 不是由 ca.pem 签发")
    try:
        if _openssl("x509", "-in", str(cert), "-noout", "-pubkey") != _openssl(
            "pkey", "-in", str(key), "-pubout"
        ):
            problems.append("key.pem 与 cert.pem 不是一对（私钥不匹配）")
    except CertError as exc:
        problems.append(f"key.pem 无法读取（私钥）：{exc}")
    if _same_cert(cert, not_same_as):
        problems.append(
            "这是 xnet-management 自己的客户端证书，不能借用；执行 make mc-cert 申请 AIOps 专用证书"
        )
    meta = directory / "meta.json"
    if meta.is_file():
        try:
            summary["clientid"] = json.loads(meta.read_text()).get("clientid", "")
        except ValueError:
            pass
    return summary, problems


def _post(opener, url, payload, token=None):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers=headers, method="POST"
    )
    return opener.open(request, timeout=20)  # noqa: S310 - operator-given xnet API URL


def issue(api, username, password):
    """A new certificate from xnet's registry API: {clientid, ca_cert, client_cert, client_key}."""
    api = api.rstrip("/")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # intranet API, no proxy
    try:
        with _post(
            opener, f"{api}/api/v1/auth/login", {"username": username, "password": password}
        ) as resp:
            token = (resp.headers.get("Authorization") or "").removeprefix("Bearer ").strip()
    except urllib.error.HTTPError as exc:
        raise CertError(
            f"登录 xnet-management 失败（HTTP {exc.code}），检查 XNET_USERNAME / XNET_PASSWORD"
        ) from None
    except (urllib.error.URLError, OSError) as exc:
        raise CertError(
            f"连不上 xnet-management API {api}：{getattr(exc, 'reason', exc)}"
        ) from None
    if not token:
        raise CertError("xnet-management 登录响应里没有 Authorization 头")
    # jwttoken is required by the schema; xnet replaces it with the caller's token.
    body = {"jwttoken": "-", "alias": ALIAS, "description": DESCRIPTION}
    try:
        with _post(opener, f"{api}/api/v1/registry/certificate", body, token) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise CertError(f"xnet-management 签发证书失败（HTTP {exc.code}）") from None
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise CertError(f"xnet-management 签发证书失败：{exc}") from None
    if not all(data.get(k) for k in ("client_cert", "client_key", "ca_cert")):
        raise CertError("xnet-management 返回的证书不完整")
    return data


def store(out, data, source):
    """Write the certificate files (0600, directory 0700); each file is replaced atomically."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    out.chmod(0o700)
    meta = {
        "clientid": data.get("clientid", ""),
        "source": source,
        "issued_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }
    contents = {
        "cert.pem": data["client_cert"],
        "key.pem": data["client_key"],
        "ca.pem": data["ca_cert"],
        "meta.json": json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
    }
    for name, text in contents.items():
        fd, tmp = tempfile.mkstemp(dir=out, prefix=f".{name}.")
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.chmod(tmp, 0o600)
        os.replace(tmp, out / name)


def _describe(summary):
    clientid = f"clientid={summary['clientid']}，" if summary.get("clientid") else ""
    return f"{clientid}有效期至 {summary['not_after']}（剩余 {summary['days_left']} 天）"


def _fail(problems):
    for problem in problems:
        print(f"xnet 客户端证书不可用：{problem}", file=sys.stderr)
    return 1


def ensure(args):
    out = Path(args.out)
    if not args.renew and all((out / name).is_file() for name in FILES):
        summary, problems = inspect(out, args.min_days)
        if not problems:
            print(f"沿用 AIOps 专用 xnet 客户端证书 {out}：{_describe(summary)}")
            return 0
    username, password = os.environ.get("XNET_USERNAME", ""), os.environ.get("XNET_PASSWORD", "")
    if not username or not password:
        return _fail(
            [
                "缺少 XNET_USERNAME / XNET_PASSWORD（xnet-management 登录账号；make mc-cert 默认从中心 xnet/xnet-account 读取）"
            ]
        )
    try:
        data = issue(args.api, username, password)
    except CertError as exc:
        return _fail([str(exc)])
    store(out, data, f"{args.api.rstrip('/')}/api/v1/registry/certificate")
    summary, problems = inspect(out, args.min_days)
    if problems:
        return _fail(problems)
    print(
        f"已签发 AIOps 专用 xnet 客户端证书（经 xnet-management 签发接口生成新密钥对，不复用 xnet 自身证书）→ {out}：{_describe(summary)}"
    )
    return 0


def check(args):
    summary, problems = inspect(args.dir, args.min_days, args.not_same_as)
    if problems:
        return _fail(problems)
    print(f"xnet 客户端证书可用（{args.dir}）：{_describe(summary)}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("ensure", help="reuse a valid certificate in --out, else issue a new one")
    p.add_argument("--out", required=True)
    p.add_argument("--api", required=True, help="xnet-management API, e.g. http://10.2.5.85:30808")
    p.add_argument("--renew", action="store_true")
    p.add_argument("--min-days", type=int, default=MIN_DAYS)
    p.set_defaults(func=ensure)
    p = sub.add_parser("check", help="validate a certificate directory")
    p.add_argument("dir")
    p.add_argument("--min-days", type=int, default=MIN_DAYS)
    p.add_argument("--not-same-as", help="PEM that must not be ours (xnet-management's own)")
    p.set_defaults(func=check)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
