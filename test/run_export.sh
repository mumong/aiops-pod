#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/huhu/agent/robusta"

python3 "${ROOT}/test/export_holmes_builtin_toolsets.py" \
  --configmap "${ROOT}/deploy/configmap/config.yaml" \
  --out "${ROOT}/test/holmes_builtin_tools_dump.md"

echo "DONE: ${ROOT}/test/holmes_builtin_tools_dump.md"

