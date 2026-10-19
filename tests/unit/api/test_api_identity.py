"""API callers (scripts, the A2A adapter) authenticate with a token instead of the cookie.

The browser keeps its HttpOnly owner cookie; a request with a valid token header acts
as that principal (a stable owner derived from its name); a bad token is rejected.
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.api.identity import API_TOKEN_HEADER, principal, principal_owner, request_owner


def _app(monkeypatch, tokens="a2a=tok-a2a,ci=tok-ci"):
    monkeypatch.setenv("AIOPS_API_TOKENS", tokens)
    app = FastAPI()

    @app.get("/who")
    def who(request: Request):
        p = principal(request)
        return {"principal": p.name if p else None, "owner": request_owner(request)}

    return TestClient(app)


def test_bearer_and_header_tokens_map_to_a_stable_owner(monkeypatch):
    client = _app(monkeypatch)
    a = client.get("/who", headers={"Authorization": "Bearer tok-a2a"}).json()
    b = client.get("/who", headers={API_TOKEN_HEADER: "tok-a2a"}).json()
    assert a == b == {"principal": "a2a", "owner": principal_owner("a2a")}
    assert len(a["owner"]) == 64 and a["owner"] != principal_owner("ci")


def test_cookie_flow_is_unchanged_without_a_token(monkeypatch):
    client = _app(monkeypatch)
    client.cookies.set("aiops_query_owner", "c" * 64)
    assert client.get("/who").json() == {"principal": None, "owner": "c" * 64}


@pytest.mark.parametrize("tokens", ["a2a=tok-a2a", ""])
def test_unknown_or_unconfigured_token_is_rejected(monkeypatch, tokens):
    client = _app(monkeypatch, tokens)
    response = client.get("/who", headers={"Authorization": "Bearer wrong"})
    assert response.status_code == 401
