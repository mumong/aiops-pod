#!/usr/bin/env python3
"""Print the run report (ledger summary + engineering findings) for one or more runs.

Inside the pod:
    kubectl -n aiops exec -i <pod> -c aiops-copilot -- python - <run_id> [...] < scripts/run_report.py
Locally against copied archives:
    python scripts/run_report.py --root /path/to/context_archives <run_id>

Needs the app package importable (it is inside the pod; locally run from the repo root).
"""

import os
import sys

sys.path.insert(0, os.getcwd())
sys.path.insert(0, "/app")


def main(argv):
    root = None
    if "--root" in argv:
        index = argv.index("--root")
        root = argv[index + 1]
        argv = argv[:index] + argv[index + 2 :]
    if not argv:
        sys.exit(__doc__)
    from app.core.diagnostics.report import build_run_report, render_markdown

    for run_id in argv:
        print(render_markdown(build_run_report(run_id, root=root)))


if __name__ == "__main__":
    main(sys.argv[1:])
