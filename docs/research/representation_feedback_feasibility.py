"""Local data-transform prototype with injected replies, NOT an LLM test.

No production imports/network calls. Byte costs cover the encoded JSON only,
not prompts, outputs, tokenizer costs or cached inference billing.
"""
from copy import deepcopy
import hashlib
import json
import unittest


SHARED = ("uid", "role", "unit")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def size(value):
    return len(canonical(value).encode())


def encode(records):
    ids = [r["id"] for r in records]
    if any(type(i) is not str for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("unique string source IDs required")
    groups, keys, rows = {}, {}, []
    for record in records:
        shared = {k: deepcopy(record[k]) for k in SHARED if k in record}
        key = canonical(shared)
        if key not in keys:
            keys[key] = f"g{len(keys)}"
            groups[keys[key]] = shared
        rows.append({"id": record["id"], "g": keys[key],
                     "data": {k: deepcopy(v) for k, v in record.items()
                              if k not in SHARED and k != "id"}})
    result = {"source": digest(records), "groups": groups, "rows": rows}
    if canonical(decode(result)) != canonical(records):
        raise ValueError("roundtrip failed")
    return result


def decode(encoded):
    records, ids = [], set()
    for row in encoded["rows"]:
        if row["id"] in ids:
            raise ValueError("duplicate ID")
        ids.add(row["id"])
        shared = encoded["groups"][row["g"]]
        if "id" in shared or "id" in row["data"] or shared.keys() & row["data"].keys():
            raise ValueError("ambiguous field ownership")
        records.append({"id": row["id"], **deepcopy(shared), **deepcopy(row["data"])})
    if digest(records) != encoded["source"]:
        raise ValueError("source mismatch")
    return records


def adapt(encoded, reply, expected_layout, budget_bytes):
    """Expand one shared field for its source group after an injected mismatch.

    A mismatch is not proof of a compression-caused error. The caller would
    still need real full-format controls and held-out model evaluation.
    """
    if digest(encoded) != expected_layout:
        raise ValueError("stale layout")
    source = decode(encoded)
    indexed = {r["id"]: r for r in source}
    rid, field = reply["id"], reply["field"]
    if rid not in indexed:
        raise ValueError("unknown record ID")
    if field not in indexed[rid]:
        return "source_field_absent", deepcopy(encoded)
    if "value" in reply and canonical(reply["value"]) == canonical(indexed[rid][field]):
        return "read_matches", deepcopy(encoded)
    row = next(r for r in encoded["rows"] if r["id"] == rid)
    group_id = row["g"]
    if field not in encoded["groups"][group_id]:
        return "already_explicit_unresolved", deepcopy(encoded)
    candidate = deepcopy(encoded)
    value = candidate["groups"][group_id].pop(field)
    for member in candidate["rows"]:
        if member["g"] == group_id:
            member["data"][field] = deepcopy(value)
    if canonical(decode(candidate)) != canonical(source):
        raise ValueError("expansion changed source")
    if size(candidate) > budget_bytes:
        return "budget_unmet", deepcopy(encoded)
    return "expanded_not_model_verified", candidate


def fixture(n=100):
    return [{"id": f"m{i:03}", "uid": "pod-instance-a", "role":
             "limits" if i % 2 else "requests", "unit": "byte",
             "value": 268435456 if i % 2 else 134217728} for i in range(n)]


def wrong_reply():
    return {"id": "m001", "field": "role", "value": "requests"}


class RepresentationTests(unittest.TestCase):
    def test_roundtrip(self):
        rows = fixture()
        self.assertEqual(decode(encode(rows)), rows)

    def test_local_expansion_and_unchanged_source(self):
        original = encode(fixture())
        status, expanded = adapt(original, wrong_reply(), digest(original), 100000)
        self.assertEqual(status, "expanded_not_model_verified")
        self.assertEqual(decode(expanded), fixture())
        self.assertEqual(expanded["groups"]["g0"]["role"], "requests")
        self.assertNotIn("role", expanded["groups"]["g1"])
        for row in expanded["rows"]:
            self.assertEqual("role" in row["data"], row["g"] == "g1")
        self.assertEqual(original, encode(fixture()))

    def test_missing_distinct_from_null(self):
        rows = [{"id": "a", "uid": None}, {"id": "b"}]
        self.assertEqual(decode(encode(rows)), rows)
        packed = encode(rows)
        status, _ = adapt(packed, {"id": "b", "field": "uid", "value": None},
                          digest(packed), 10000)
        self.assertEqual(status, "source_field_absent")

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            encode([{"id": "a"}, {"id": "a"}])

    def test_unknown_id_rejected(self):
        packed = encode(fixture())
        with self.assertRaises(ValueError):
            adapt(packed, {**wrong_reply(), "id": "not-in-source"}, digest(packed), 10000)

    def test_stale_layout_rejected(self):
        packed = encode(fixture())
        _, expanded = adapt(packed, wrong_reply(), digest(packed), 100000)
        with self.assertRaises(ValueError):
            adapt(expanded, wrong_reply(), digest(packed), 100000)

    def test_budget_failure_is_atomic(self):
        packed = encode(fixture())
        status, result = adapt(packed, wrong_reply(), digest(packed), size(packed))
        self.assertEqual(status, "budget_unmet")
        self.assertEqual(result, packed)

    def test_explicit_field_mistake_does_not_trigger_more_expansion(self):
        packed = encode(fixture())
        status, _ = adapt(packed, {"id": "m001", "field": "value", "value": 0},
                          digest(packed), 100000)
        self.assertEqual(status, "already_explicit_unresolved")

    def test_correct_reply_changes_nothing(self):
        packed = encode(fixture())
        status, result = adapt(packed, {**wrong_reply(), "value": "limits"},
                               digest(packed), 100000)
        self.assertEqual(status, "read_matches")
        self.assertEqual(result, packed)

    def test_tampered_source_rejected(self):
        packed = encode(fixture())
        packed["groups"]["g0"]["role"] = "limits"
        with self.assertRaises(ValueError):
            decode(packed)


if __name__ == "__main__":
    rows = fixture()
    packed = encode(rows)
    _, expanded = adapt(packed, wrong_reply(), digest(packed), 100000)
    print(json.dumps({"records": len(rows), "source_json_bytes": size(rows),
                      "packed_bytes": size(packed), "expanded_bytes": size(expanded),
                      "two_input_payload_bytes": size(packed) + size(expanded)}))
    unittest.main(verbosity=2)
