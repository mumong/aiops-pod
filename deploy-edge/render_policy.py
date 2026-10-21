#!/usr/bin/env python3
"""Print the center's workflow.remediation rules as JSON for the edge runner.

One source of truth: deploy/configmap/config.yaml (spec FR-015).
"""

import json
import sys
from pathlib import Path

import yaml

config = Path(sys.argv[1] if len(sys.argv) > 1 else "deploy/configmap/config.yaml")
raw = yaml.safe_load(yaml.safe_load(config.read_text())["data"]["config.yaml"])
print(json.dumps(raw["workflow"]["remediation"], ensure_ascii=False, sort_keys=True))
