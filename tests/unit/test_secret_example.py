"""Keep fresh-clone configuration usable without shipping real credentials."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_secret_example_satisfies_deployment_references():
    # Arrange: inspect public artifacts only, never a developer's private Secret.
    example = yaml.safe_load((ROOT / "config/examples/aiops-secret.yaml").read_text())
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
    named = [ref for ref in references if ref["name"] == example["metadata"]["name"]]
    required = {ref["key"] for ref in named if not ref.get("optional", False)}
    model_keys = {"LLM_API_KEY", "LLM_MODEL", "LLM_API_BASE", "MODEL_CONTEXT_WINDOW"}

    # Assert: the example remains deployable after local configuration, not as-is.
    assert model_keys <= {ref["key"] for ref in named}
    assert required | model_keys <= example["stringData"].keys()
    assert example["stringData"]["LLM_API_KEY"] == "<API key>"
    assert example["metadata"]["namespace"] == "aiops"
    assert (ROOT / "config/examples/aiops-secret.yaml").relative_to(ROOT).parts[0] != "deploy"
