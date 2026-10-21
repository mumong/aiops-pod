"""Runner request signatures (spec FR-014, contracts/runner-api.md)."""

from aiops_edge import signing

KEY = b"k" * 32


def _signed(body=b'{"a":1}', now=1_000_000, nonce="ab" * 16):
    return signing.sign(KEY, "POST", "/v1/kubectl", body, now=now, nonce=nonce)


def test_valid_signature_is_accepted():
    cache = signing.NonceCache()
    headers = _signed()
    assert (
        signing.verify(KEY, headers, "POST", "/v1/kubectl", b'{"a":1}', now=1_000_010, cache=cache)
        is None
    )


def test_header_lookup_is_case_insensitive():
    headers = {k.lower(): v for k, v in _signed().items()}
    assert (
        signing.verify(
            KEY,
            headers,
            "POST",
            "/v1/kubectl",
            b'{"a":1}',
            now=1_000_000,
            cache=signing.NonceCache(),
        )
        is None
    )


def test_missing_headers_rejected():
    reason = signing.verify(
        KEY, {}, "POST", "/v1/kubectl", b"", now=1_000_000, cache=signing.NonceCache()
    )
    assert reason and "missing" in reason


def test_tampered_body_rejected():
    reason = signing.verify(
        KEY,
        _signed(),
        "POST",
        "/v1/kubectl",
        b'{"a":2}',
        now=1_000_000,
        cache=signing.NonceCache(),
    )
    assert reason == "bad signature"


def test_other_path_or_method_rejected():
    headers = _signed()
    cache = signing.NonceCache()
    assert signing.verify(KEY, headers, "POST", "/v1/jobs", b'{"a":1}', now=1_000_000, cache=cache)
    assert signing.verify(
        KEY, headers, "GET", "/v1/kubectl", b'{"a":1}', now=1_000_000, cache=cache
    )


def test_wrong_key_rejected():
    reason = signing.verify(
        b"x" * 32,
        _signed(),
        "POST",
        "/v1/kubectl",
        b'{"a":1}',
        now=1_000_000,
        cache=signing.NonceCache(),
    )
    assert reason == "bad signature"


def test_expired_and_future_timestamps_rejected():
    cache = signing.NonceCache()
    assert "skew" in signing.verify(
        KEY, _signed(now=1_000_000), "POST", "/v1/kubectl", b'{"a":1}', now=1_000_061, cache=cache
    )
    assert "skew" in signing.verify(
        KEY, _signed(now=1_000_100), "POST", "/v1/kubectl", b'{"a":1}', now=1_000_000, cache=cache
    )


def test_replay_rejected():
    cache = signing.NonceCache()
    headers = _signed()
    assert (
        signing.verify(KEY, headers, "POST", "/v1/kubectl", b'{"a":1}', now=1_000_000, cache=cache)
        is None
    )
    assert (
        signing.verify(KEY, headers, "POST", "/v1/kubectl", b'{"a":1}', now=1_000_001, cache=cache)
        == "replayed nonce"
    )


def test_nonce_cache_forgets_after_ttl():
    cache = signing.NonceCache(ttl=300)
    assert not cache.seen("n1", now=0)
    assert cache.seen("n1", now=10)
    assert not cache.seen("n1", now=400)


def test_sign_generates_fresh_nonce():
    a = signing.sign(KEY, "POST", "/p", b"", now=1)
    b = signing.sign(KEY, "POST", "/p", b"", now=1)
    assert a[signing.HEADER_NONCE] != b[signing.HEADER_NONCE]
