"""Read-only audit of archived model inputs; no LLM calls or cluster writes."""
import argparse
import json
from pathlib import Path


def size(value):
    return len(json.dumps(value, ensure_ascii=False))


def audit(root):
    def read(path):
        return json.loads(path.read_text())
    parallel = (root / 'parallel/results.json').exists()
    cases = ([row['case_result'] for row in read(root / 'parallel/results.json')]
             if parallel else [read(root / 'cases/result.json')])
    overview = read(root / 'node_inputs/conclusion.input.json')
    requests = overview['overview_requests']
    assert overview['case_count'] == len(cases)
    for payload in requests:
        assert 'parallel_results' not in payload and 'observations' not in payload
        for index in payload['results']:
            assert 'report' not in index and 'key_facts' not in index
    branches = []
    for case in cases:
        branch = root.parent / f"{root.name}-{case['group_id']}" if parallel else root
        evidence = read(branch / 'node_inputs/evidence.input.json')
        rca = read(branch / 'node_inputs/rca.input.json')
        evidence = evidence.get('after_compaction', evidence)
        rca = rca.get('after_compaction', rca)
        assert len(evidence['protected_handoff']['diagnosis_handoff']['targets']) == 1
        assert not evidence['observations'] and not evidence['recent_interactions']
        assert 'lifecycle_core' not in rca['protected_handoff']
        assert 'evidence_handoff' in rca['protected_handoff']
        refs = [ref for f in case.get('key_facts', []) for ref in f.get('evidence_refs', [])]
        branches.append({'group': case['group_id'], 'evidence_input_chars': size(evidence),
            'rca_input_chars': size(rca), 'rca_protected_chars': size(rca['protected_handoff']),
            'facts': len(case.get('key_facts', [])), 'evidence_refs': len(refs)})
    return {'run_id': root.name, 'cases': len(cases), 'branches': branches,
            'overview_request_chars': [size(r) for r in requests]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.archive), ensure_ascii=False, indent=2))
