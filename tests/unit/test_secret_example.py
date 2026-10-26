"""Keep the committed default Secret deployable as-is from a fresh clone."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_default_secret_satisfies_deployment_references():
    # Arrange: the committed default Secret and the Deployment that reads it.
    secret = yaml.safe_load((ROOT / "deploy/secrets/core.yaml").read_text())
    deployment = next(
        item
        for item in yaml.safe_load_all((ROOT / "deploy/k8s-simple.yaml").read_text())
        if item and item.get("kind") == "Deployment"
    )

    # Act: collect the actual keys requested from this named Secret.
    references = [
        env["valueFrom"]["secretKeyRef"]
        for container in deployment["spec"]["template"]["spec"]["containers"]
        for env in container.get("env", [])
        if "secretKeyRef" in env.get("valueFrom", {})
    ]
    named = [ref for ref in references if ref["name"] == secret["metadata"]["name"]]
    required = {ref["key"] for ref in named if not ref.get("optional", False)}
    model_keys = {"LLM_API_KEY", "LLM_MODEL", "LLM_API_BASE", "MODEL_CONTEXT_WINDOW"}
    values = secret["stringData"]

    # Assert: every referenced key has a real value, so `make deploy` works without editing.
    assert model_keys <= {ref["key"] for ref in named}
    assert required | model_keys <= values.keys()
    assert all(values[key] and not values[key].startswith("<") for key in model_keys)
    assert secret["metadata"]["namespace"] == "aiops"
    # The A2A sidecar authenticates with the a2a principal from AIOPS_API_TOKENS.
    principals = dict(pair.split("=", 1) for pair in values["AIOPS_API_TOKENS"].split(","))
    assert principals["a2a"] == values["A2A_BACKEND_API_TOKEN"]
