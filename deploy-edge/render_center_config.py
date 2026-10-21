#!/usr/bin/env python3
"""Render the aiops-config ConfigMap for the test-env center: base config + overrides.

Usage: render_center_config.py deploy/configmap/config.yaml deploy-edge/center/overrides.yaml
"""

import sys
from pathlib import Path

import yaml


def merge(base, extra):
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value)
        else:
            base[key] = value
    return base


manifest = yaml.safe_load(Path(sys.argv[1]).read_text())
config = yaml.safe_load(manifest["data"]["config.yaml"])
merge(config, yaml.safe_load(Path(sys.argv[2]).read_text()) or {})
manifest["data"]["config.yaml"] = yaml.safe_dump(config, allow_unicode=True, sort_keys=False)
print(yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False))
