"""Bounded real-fixture cleanup check; no Agent calls or quality-score changes."""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "test/aiops_quality_e2e"))
from variant_suite import fixture_manager

manager = fixture_manager()
results = []
try:
    for case_id in ("c11-prestop", "c11-prestop", "c11-prestop", "c11-grace"):
        case = manager.catalog()[case_id]
        manager.clean(case)
        manager.deploy(case)
        assert manager.validate_variant(case, 90), "real fixture gate failed"
        started = time.monotonic()
        manager.clean(case)
        assert not manager.variant_namespace(case), "namespace remains"
        result = {"case": case_id, "cleanup_seconds": round(time.monotonic() - started, 3), "passed": True}
        results.append(result)
        print(json.dumps(result), flush=True)
except BaseException as exc:
    results.append({"passed": False, "error": repr(exc)})
    raise
finally:
    Path(__file__).with_suffix(".json").write_text(json.dumps(results, indent=2))
