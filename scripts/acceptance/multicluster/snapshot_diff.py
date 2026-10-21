#!/usr/bin/env python3
"""X1 / SC-007: xnet and monitor namespaces must not change during a phase."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mc_common as mc  # noqa: E402


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: snapshot_diff.py BEFORE.json AFTER.json")
    before = json.loads(Path(sys.argv[1]).read_text())
    after = json.loads(Path(sys.argv[2]).read_text())
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(k for k in set(before) & set(after) if before[k] != after[k])
    for label, keys in (("added", added), ("removed", removed), ("changed", changed)):
        for key in keys:
            print(f"  {label}: {key}")
    mc.check("X1-snapshot-unchanged", not (added or removed or changed),
             f"objects={len(after)} added={len(added)} removed={len(removed)} changed={len(changed)}")
    mc.finish()


if __name__ == "__main__":
    main()
