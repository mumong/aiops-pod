import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKENDS = {"kubernetes", "prometheus", "elasticsearch", "deepflow", "tempo"}


def load_catalog():
    return json.loads((ROOT / "catalog.yaml").read_text(encoding="utf-8"))


def render(relative):
    return subprocess.run(
        ["kubectl", "kustomize", str(ROOT / relative)],
        check=True,
        text=True,
        capture_output=True,
    ).stdout
