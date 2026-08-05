#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
lab_dir=$(cd -- "${script_dir}/.." && pwd)

if [[ -f "${lab_dir}/config.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${lab_dir}/config.env"
  set +a
fi

exec python3 "${script_dir}/verify_observability.py" "$@"
